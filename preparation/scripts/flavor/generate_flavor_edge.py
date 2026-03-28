# -*- coding: utf-8 -*-
"""
从 ingredient_flavor_feature 计算风味相似边，并写入 graph_flavor_edge_stats

功能：
1. 读取每个 ingredient 的 6 维风味向量
2. 计算 cosine similarity 和 l2 distance
3. 每个 ingredient 保留 Top-K 相似邻居
4. 转成无向边（固定 i_id < j_id）
5. 批量写入 MySQL 表 graph_flavor_edge_stats

适用前提：
- ingredient_flavor_feature 中每个 ingredient_id 只有一条记录
- graph_flavor_edge_stats 表已经创建好
"""

import os
import sys
import math
import time
from typing import List, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import text

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

# 从 src/db 导入数据库连接函数
from src.db import get_engine


# 数据库引擎
engine = get_engine()


# =========================================================
# 2. 运行参数
# =========================================================
SNAPSHOT_ID = "f1"  # form-aware 版
WEIGHT_METHOD = "form_penalized_top10_v1"
TOP_K = 10
BATCH_SIZE = 5000  # 批量写入数据库时每批条数

# =========================================================
# 3. Form 惩罚系数
# =========================================================
FORM_GAMMA = {
    # 同类型组合
    ("spirit", "spirit"): 1.0,
    ("liqueur", "liqueur"): 1.0,
    ("fortified_wine", "fortified_wine"): 1.0,
    ("juice", "juice"): 1.0,
    ("syrup", "syrup"): 1.0,
    ("cordial", "cordial"): 1.0,
    ("bitters", "bitters"): 1.0,
    ("other", "other"): 1.0,

    # 相近 form
    ("syrup", "cordial"): 0.7,
    ("cordial", "syrup"): 0.7,
    ("fortified_wine", "liqueur"): 0.7,
    ("liqueur", "fortified_wine"): 0.7,
    ("spirit", "liqueur"): 0.7,
    ("liqueur", "spirit"): 0.7,

    # 差异较大
    ("juice", "syrup"): 0.4,
    ("syrup", "juice"): 0.4,
    ("syrup", "liqueur"): 0.4,
    ("liqueur", "syrup"): 0.4,
    ("fortified_wine", "spirit"): 0.4,
    ("spirit", "fortified_wine"): 0.4,

    # 很不相近
    ("spirit", "juice"): 0.2,
    ("juice", "spirit"): 0.2,
    ("bitters", "juice"): 0.2,
    ("juice", "bitters"): 0.2,
    ("bitters", "syrup"): 0.2,
    ("syrup", "bitters"): 0.2,
}

# 默认惩罚系数
DEFAULT_GAMMA = 0.3


# =========================================================
# 3. 读取原料风味向量
# =========================================================
def load_flavor_features() -> pd.DataFrame:
    """
    从 ingredient_flavor_feature 读取有效风味向量，并从 ingredient_flavor_anchor 读取 anchor_form

    返回字段：
    - ingredient_id
    - anchor_form
    - sour, sweet, bitter, aroma, fruity, body
    """
    # 直接从 ingredient_flavor_anchor 表中读取 anchor_form
    print("[INFO] 从 ingredient_flavor_anchor 表中读取 anchor_form...")
    sql = """
    SELECT
        iff.ingredient_id,
        ifa.anchor_form,
        iff.sour,
        iff.sweet,
        iff.bitter,
        iff.aroma,
        iff.fruity,
        iff.body
    FROM ingredient_flavor_feature iff
    JOIN ingredient_flavor_anchor ifa ON iff.ingredient_id = ifa.ingredient_id
    WHERE iff.sour   IS NOT NULL
      AND iff.sweet  IS NOT NULL
      AND iff.bitter IS NOT NULL
      AND iff.aroma  IS NOT NULL
      AND iff.fruity IS NOT NULL
      AND iff.body   IS NOT NULL
      AND ifa.anchor_form IS NOT NULL
    ORDER BY iff.ingredient_id
    """
    df = pd.read_sql(sql, engine)

    # 检查是否有重复 ingredient_id
    dup = df["ingredient_id"].duplicated().sum()
    if dup > 0:
        raise ValueError(f"发现重复 ingredient_id：{dup} 条，请先去重。")

    if df.empty:
        raise ValueError("没有可用的风味特征数据。")

    # 确保 anchor_form 列存在
    if "anchor_form" not in df.columns:
        raise ValueError("无法获取 anchor_form 数据。")

    # 填充缺失的 anchor_form 为 "other"
    df["anchor_form"] = df["anchor_form"].fillna("other")

    print(f"[INFO] 读取到 {len(df)} 个原料节点。")
    print(f"[INFO] 各 form 分布：")
    form_counts = df["anchor_form"].value_counts()
    for form, count in form_counts.items():
        print(f"[INFO]   {form}: {count}")
    
    return df


# =========================================================
# 4. 计算余弦相似度矩阵
# =========================================================
def compute_similarity(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    输入：
    - df: 包含 ingredient_id 和 6 维风味特征

    输出：
    - sim_matrix: 余弦相似度矩阵 shape=(n,n)
    - dist_matrix: 欧氏距离矩阵 shape=(n,n)
    """
    feature_cols = ["sour", "sweet", "bitter", "aroma", "fruity", "body"]

    # 转成 numpy 矩阵，shape=(n,6)
    X = df[feature_cols].to_numpy(dtype=np.float64)

    # ---------- 计算 cosine similarity ----------
    # 先算每一行向量的 L2 范数
    norms = np.linalg.norm(X, axis=1, keepdims=True)

    # 防止出现全零向量导致除零
    norms[norms == 0] = 1e-12

    # 单位化
    X_norm = X / norms

    # 余弦相似度矩阵 = 归一化后的矩阵乘法
    sim_matrix = X_norm @ X_norm.T

    # 数值误差修正到 [-1,1]
    sim_matrix = np.clip(sim_matrix, -1.0, 1.0)

    # ---------- 计算 Euclidean distance ----------
    # 利用广播计算两两距离
    # shape = (n,1,6) - (1,n,6) => (n,n,6)
    diff = X[:, None, :] - X[None, :, :]
    dist_matrix = np.sqrt(np.sum(diff * diff, axis=2))

    print(f"[INFO] 相似度矩阵 shape = {sim_matrix.shape}")
    return sim_matrix, dist_matrix


# =========================================================
# 5. 从相似度矩阵中提取 Top-K 邻居边
# =========================================================
def build_topk_edges(
    ingredient_ids: np.ndarray,
    anchor_forms: np.ndarray,
    sim_matrix: np.ndarray,
    dist_matrix: np.ndarray,
    top_k: int = 10
) -> pd.DataFrame:
    """
    对每个 ingredient 保留 Top-K 相似邻居，再合并为无向边

    返回字段：
    - i_id
    - j_id
    - sim_cosine
    - dist_l2
    - weight
    """
    n = len(ingredient_ids)

    # 不允许自己和自己连边：把对角线设为极小值，确保不会被选进 top-k
    np.fill_diagonal(sim_matrix, -np.inf)

    # 用字典去重无向边，key=(min_id, max_id)
    edge_dict = {}

    for idx in range(n):
        # 取当前节点的距离向量
        dists = dist_matrix[idx]
        
        # 计算基础风味接近度：base(i,j) = 1 / (1 + dist_l2(i,j))
        base_scores = 1.0 / (1.0 + dists)
        
        # 获取当前节点的 form
        current_form = anchor_forms[idx]
        
        # 计算最终权重：base_score * form_penalty
        final_scores = np.copy(base_scores)
        for jdx in range(n):
            if idx == jdx:
                continue
            other_form = anchor_forms[jdx]
            # 获取 form 惩罚系数
            form_penalty = FORM_GAMMA.get((current_form, other_form), DEFAULT_GAMMA)
            # 计算最终得分
            final_scores[jdx] *= form_penalty

        # 取 Top-K 的索引
        # argpartition 比 argsort 更快，适合只取前 K 个
        candidate_idx = np.argpartition(-final_scores, top_k)[:top_k]

        # 为了结果稳定，再对这 K 个按最终得分排序
        candidate_idx = candidate_idx[np.argsort(-final_scores[candidate_idx])]

        src_id = int(ingredient_ids[idx])
        src_form = current_form

        for jdx in candidate_idx:
            dst_id = int(ingredient_ids[jdx])
            
            # 跳过自环
            if src_id == dst_id:
                continue
                
            dst_form = anchor_forms[jdx]

            # 固定无向边方向：小的放前面
            i_id, j_id = sorted((src_id, dst_id))
            i_form, j_form = (src_form, dst_form) if i_id == src_id else (dst_form, src_form)

            sim_val = float(sim_matrix[idx, jdx])
            dist_val = float(dist_matrix[idx, jdx])
            base_score = float(base_scores[jdx])
            
            # 计算 form 惩罚系数
            form_penalty = FORM_GAMMA.get((src_form, dst_form), DEFAULT_GAMMA)
            
            # 计算最终权重
            final_weight = base_score * form_penalty

            # 计算 is_exact_match
            is_exact_match = 1 if dist_val == 0 else 0

            # 跳过非法值
            if not np.isfinite(final_weight):
                continue

            # 同一条无向边可能被两端都选中，这里保留“更优”的那条
            key = (i_id, j_id)
            old = edge_dict.get(key)

            if old is None:
                edge_dict[key] = {
                    "i_id": i_id,
                    "j_id": j_id,
                    "sim_cosine": sim_val,
                    "dist_l2": dist_val,
                    "weight": final_weight,
                    "form_i": i_form,
                    "form_j": j_form,
                    "form_penalty": form_penalty,
                    "is_exact_match": is_exact_match
                }
            else:
                # 若出现数值差异，则保留 weight 更大的版本
                if final_weight > old["weight"]:
                    edge_dict[key] = {
                        "i_id": i_id,
                        "j_id": j_id,
                        "sim_cosine": sim_val,
                        "dist_l2": dist_val,
                        "weight": final_weight,
                        "form_i": i_form,
                        "form_j": j_form,
                        "form_penalty": form_penalty,
                        "is_exact_match": is_exact_match
                    }

        if (idx + 1) % 100 == 0 or (idx + 1) == n:
            pct = int(100 * (idx + 1) / n)
            print(f"[进度 {pct}%] Top-K 处理中：{idx + 1}/{n}")

    edge_df = pd.DataFrame(edge_dict.values())
    
    # 再次过滤自环边
    edge_df = edge_df[edge_df["i_id"] != edge_df["j_id"]]
    
    edge_df = edge_df.sort_values(
        by=["weight", "dist_l2", "i_id", "j_id"],
        ascending=[False, True, True, True]
    ).reset_index(drop=True)

    # 统计 form 组合分布
    if not edge_df.empty:
        form_combinations = edge_df.groupby(["form_i", "form_j"]).size().reset_index(name="count")
        form_combinations = form_combinations.sort_values(by="count", ascending=False)
        print(f"[INFO] 边的 form 组合分布（前 10）：")
        for _, row in form_combinations.head(10).iterrows():
            print(f"[INFO]   ({row['form_i']}, {row['form_j']}): {row['count']}")

    print(f"[INFO] 最终无向风味边数：{len(edge_df)}")
    return edge_df


# =========================================================
# 6. 清空指定 snapshot 的旧结果
# =========================================================
def clear_old_snapshot(snapshot_id: str):
    """
    删除 graph_flavor_edge_stats 中同一 snapshot_id 的旧数据
    """
    sql = text("""
        DELETE FROM graph_flavor_edge_stats
        WHERE snapshot_id = :snapshot_id
    """)

    with engine.begin() as conn:
        conn.execute(sql, {"snapshot_id": snapshot_id})

    print(f"[INFO] 已清空旧快照数据：snapshot_id = {snapshot_id}")


# =========================================================
# 7. 批量写入数据库
# =========================================================
def insert_edges(edge_df: pd.DataFrame, snapshot_id: str, weight_method: str):
    """
    将边结果批量写入 graph_flavor_edge_stats
    """
    if edge_df.empty:
        print("[WARN] 没有边可写入。")
        return

    # 打印 edge_df 的前 20 条数据和数据类型
    print("[INFO] 边数据预览（前 20 条）：")
    print(edge_df.head(20))
    print("[INFO] 边数据类型：")
    print(edge_df.dtypes)

    # 运行时断言
    assert (edge_df["i_id"] != edge_df["j_id"]).all(), "存在自环边"
    assert edge_df["sim_cosine"].between(-1, 1).all(), "sim_cosine 不在 [-1, 1] 范围内"
    assert (edge_df["dist_l2"] >= 0).all(), "dist_l2 小于 0"
    assert edge_df["weight"].between(0, 1).all(), "weight 不在 [0, 1] 范围内"
    assert edge_df["is_exact_match"].isin([0, 1]).all(), "is_exact_match 不是 0 或 1"

    insert_df = edge_df.copy()
    insert_df["snapshot_id"] = snapshot_id
    insert_df["weight_method"] = weight_method

    # 处理无穷大值和NaN值
    # 将 inf 和 -inf 替换为 0
    insert_df = insert_df.replace([np.inf, -np.inf], 0)
    # 将 NaN 替换为 0
    insert_df = insert_df.fillna(0)

    # 调整列顺序，和目标表保持一致
    # 只包含数据库表中存在的字段
    insert_df = insert_df[
        ["snapshot_id", "i_id", "j_id", "sim_cosine", "dist_l2", "weight", 
         "weight_method", "is_exact_match"]
    ]
    
    # 打印 insert_df 的前 20 条数据
    print("[INFO] 插入数据预览（前 20 条）：")
    print(insert_df.head(20))

    total = len(insert_df)
    batches = math.ceil(total / BATCH_SIZE)

    for b in range(batches):
        start = b * BATCH_SIZE
        end = min((b + 1) * BATCH_SIZE, total)
        chunk = insert_df.iloc[start:end]

        chunk.to_sql(
            name="graph_flavor_edge_stats",
            con=engine,
            if_exists="append",
            index=False,
            method="multi"
        )

        print(f"[INFO] 已写入批次 {b + 1}/{batches}，本批 {len(chunk)} 条")

    print(f"[INFO] 全部写入完成，共 {total} 条边。")


# =========================================================
# 8. 简单检查结果
# =========================================================
def inspect_result(snapshot_id: str):
    """
    打印写入后的基本统计和前几条高权重边
    """
    sql_count = text("""
        SELECT COUNT(*) AS cnt
        FROM graph_flavor_edge_stats
        WHERE snapshot_id = :snapshot_id
    """)

    sql_top = text("""
        SELECT *
        FROM graph_flavor_edge_stats
        WHERE snapshot_id = :snapshot_id
        ORDER BY weight DESC, dist_l2 ASC
        LIMIT 10
    """)

    with engine.begin() as conn:
        cnt = conn.execute(sql_count, {"snapshot_id": snapshot_id}).fetchone()[0]
        top_rows = conn.execute(sql_top, {"snapshot_id": snapshot_id}).fetchall()

    print(f"[INFO] snapshot={snapshot_id} 的边数：{cnt}")
    print("[INFO] 权重最高的前 10 条边：")
    for row in top_rows:
        print(row)


# =========================================================
# 9. 主流程
# =========================================================
def main():
    t0 = time.time()

    print("[INFO] 开始生成风味边...")
    print(f"[INFO] 配置参数: SNAPSHOT_ID={SNAPSHOT_ID}, TOP_K={TOP_K}, BATCH_SIZE={BATCH_SIZE}")

    # 1) 读取节点风味特征
    print("[步骤 1] 读取原料风味特征...")
    df = load_flavor_features()
    node_count = len(df)

    # 2) 计算相似度矩阵和距离矩阵
    print("[步骤 2] 计算相似度矩阵和距离矩阵...")
    start_time = time.time()
    sim_matrix, dist_matrix = compute_similarity(df)
    elapsed = time.time() - start_time
    print(f"[INFO] 相似度计算完成，用时 {elapsed:.2f} 秒")

    # 3) 生成 Top-K 无向风味边
    print("[步骤 3] 生成 Top-K 无向风味边...")
    start_time = time.time()
    edge_df = build_topk_edges(
        ingredient_ids=df["ingredient_id"].to_numpy(),
        anchor_forms=df["anchor_form"].to_numpy(),
        sim_matrix=sim_matrix,
        dist_matrix=dist_matrix,
        top_k=TOP_K
    )
    edge_count = len(edge_df)
    elapsed = time.time() - start_time
    print(f"[INFO] 边生成完成，共 {edge_count} 条边，用时 {elapsed:.2f} 秒")

    # 4) 清空当前快照旧数据
    print("[步骤 4] 清空旧快照数据...")
    clear_old_snapshot(SNAPSHOT_ID)

    # 5) 写入数据库
    print("[步骤 5] 批量写入数据库...")
    start_time = time.time()
    insert_edges(edge_df, SNAPSHOT_ID, WEIGHT_METHOD)
    elapsed = time.time() - start_time
    print(f"[INFO] 数据库写入完成，用时 {elapsed:.2f} 秒")

    # 6) 检查结果
    print("[步骤 6] 检查结果...")
    inspect_result(SNAPSHOT_ID)

    t1 = time.time()
    total_elapsed = t1 - t0
    print(f"[INFO] 全流程完成！")
    print(f"[INFO] 节点数: {node_count}, 边数: {edge_count}")
    print(f"[INFO] 总用时: {total_elapsed:.2f} 秒")
    print(f"[INFO] 平均处理每条边: {total_elapsed/edge_count:.4f} 秒/条")


if __name__ == "__main__":
    main()