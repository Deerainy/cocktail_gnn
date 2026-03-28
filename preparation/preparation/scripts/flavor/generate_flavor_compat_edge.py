# -*- coding: utf-8 -*-
"""
从 ingredient_flavor_feature 和 ingredient_role 计算风味搭配/互补边，并写入 graph_flavor_compat_edge_stats

功能：
1. 读取每个 ingredient 的 6 维风味向量和角色信息
2. 计算两两原料之间的兼容度
3. 计算角色互补分、酸甜苦香体的互补分、anchor 加分
4. 生成无向边（固定 i_id < j_id）
5. 批量写入 MySQL 表 graph_flavor_compat_edge_stats

适用前提：
- ingredient_flavor_feature 中每个 ingredient_id 只有一条记录
- ingredient_flavor_anchor 中每个 ingredient_id 只有一条记录
- recipe_ingredient 中包含角色信息
- graph_flavor_compat_edge_stats 表已经创建好
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
# 向上两级到达项目根目录
_root = os.path.dirname(os.path.dirname(_script_dir))
if _root not in sys.path:
    sys.path.insert(0, _root)

# 从 src/db 导入数据库连接函数
from src.db import get_engine


# 数据库引擎
engine = get_engine()


# =========================================================
# 2. 运行参数
# =========================================================
SNAPSHOT_ID = "compat_v1"  # 兼容度版本
WEIGHT_METHOD = "flavor_compat_v1"
BATCH_SIZE = 5000  # 批量写入数据库时每批条数

# =========================================================
# 3. 角色互补系数
# =========================================================
ROLE_BONUS = {
    # 经典互补组合
    ("base_spirit", "sweetener"): 1.2,
    ("sweetener", "base_spirit"): 1.2,
    ("base_spirit", "acid"): 1.2,
    ("acid", "base_spirit"): 1.2,
    ("sweetener", "acid"): 1.1,
    ("acid", "sweetener"): 1.1,
    ("base_spirit", "modifier"): 1.1,
    ("modifier", "base_spirit"): 1.1,
    
    # 一般组合
    ("modifier", "modifier"): 0.9,
    ("modifier", "sweetener"): 1.0,
    ("sweetener", "modifier"): 1.0,
    ("modifier", "acid"): 1.0,
    ("acid", "modifier"): 1.0,
    
    # 特殊组合
    ("garnish", "base_spirit"): 0.6,
    ("base_spirit", "garnish"): 0.6,
    ("garnish", "sweetener"): 0.6,
    ("sweetener", "garnish"): 0.6,
    ("garnish", "acid"): 0.6,
    ("acid", "garnish"): 0.6,
    ("garnish", "modifier"): 0.6,
    ("modifier", "garnish"): 0.6,
}

# 默认角色互补系数
DEFAULT_ROLE_BONUS = 0.8

# =========================================================
# 4. 读取原料信息
# =========================================================
def load_ingredient_info() -> pd.DataFrame:
    """
    从多个表读取原料信息：
    - ingredient_flavor_feature: 风味特征
    - ingredient_flavor_anchor: anchor 信息
    - recipe_ingredient: 角色信息（取最常见的角色）
    - llm_canonical_map: canonical id 信息

    返回字段：
    - canonical_id
    - role: 最常见的角色
    - anchor_name
    - anchor_form
    - sour, sweet, bitter, aroma, fruity, body
    """
    # 读取风味特征、anchor 信息和 canonical id
    print("[INFO] 读取原料信息...")
    sql = """
    SELECT
        lcm.canonical_id,
        ifa.anchor_name,
        ifa.anchor_form,
        iff.sour,
        iff.sweet,
        iff.bitter,
        iff.aroma,
        iff.fruity,
        iff.body
    FROM ingredient_flavor_feature iff
    JOIN ingredient_flavor_anchor ifa ON iff.ingredient_id = ifa.ingredient_id
    JOIN llm_canonical_map lcm ON iff.ingredient_id = lcm.src_ingredient_id
    WHERE iff.sour   IS NOT NULL
      AND iff.sweet  IS NOT NULL
      AND iff.bitter IS NOT NULL
      AND iff.aroma  IS NOT NULL
      AND iff.fruity IS NOT NULL
      AND iff.body   IS NOT NULL
      AND ifa.anchor_form IS NOT NULL
    """
    flavor_df = pd.read_sql(sql, engine)
    
    # 读取角色信息（取每个 ingredient 最常见的角色）
    role_sql = """
    SELECT
        ri.ingredient_id,
        lcm.canonical_id,
        ri.role,
        COUNT(*) as role_count
    FROM recipe_ingredient ri
    JOIN llm_canonical_map lcm ON ri.ingredient_id = lcm.src_ingredient_id
    WHERE ri.role IS NOT NULL AND ri.role != ''
    GROUP BY ri.ingredient_id, lcm.canonical_id, ri.role
    ORDER BY ri.ingredient_id, role_count DESC
    """
    role_df = pd.read_sql(role_sql, engine)
    
    # 取每个 canonical_id 的最常见角色
    most_common_roles = role_df.groupby('canonical_id').first().reset_index()
    
    # 合并风味信息和角色信息
    df = flavor_df.merge(most_common_roles[['canonical_id', 'role']], on='canonical_id', how='left')
    
    # 填充缺失的角色
    df['role'] = df['role'].fillna('other')
    
    # 去重，保留每个 canonical_id 的第一条记录
    df = df.drop_duplicates(subset=['canonical_id'], keep='first')

    if df.empty:
        raise ValueError("没有可用的原料数据。")

    print(f"[INFO] 读取到 {len(df)} 个原料节点。")
    print(f"[INFO] 各角色分布：")
    role_counts = df["role"].value_counts()
    for role, count in role_counts.items():
        print(f"[INFO]   {role}: {count}")
    
    print(f"[INFO] 各 anchor_form 分布：")
    form_counts = df["anchor_form"].value_counts()
    for form, count in form_counts.items():
        print(f"[INFO]   {form}: {count}")
    
    return df


# =========================================================
# 5. 计算口味互补得分
# =========================================================
def compute_taste_complement_score(flavor_i: np.ndarray, flavor_j: np.ndarray) -> float:
    """
    计算两个原料之间的口味互补得分
    基于酸甜苦香体的互补性
    """
    # 计算口味差异
    diff = np.abs(flavor_i - flavor_j)
    
    # 互补得分：差异适中的得分更高
    # 使用高斯函数，峰值在差异为 0.5 左右
    complement_score = np.mean(np.exp(-((diff - 0.5) ** 2) / 0.1))
    
    return float(complement_score)


# =========================================================
# 6. 计算 anchor 加分
# =========================================================
def compute_anchor_bonus(anchor_name_i: str, anchor_form_i: str, anchor_name_j: str, anchor_form_j: str) -> float:
    """
    计算 anchor 相关的加分
    """
    # 相同 anchor_name 加分
    if anchor_name_i == anchor_name_j and anchor_name_i is not None:
        return 1.3
    
    # 相同 anchor_form 加分
    if anchor_form_i == anchor_form_j and anchor_form_i is not None:
        return 1.1
    
    # 合理的 anchor 组合加分
    # 这里可以根据需要添加更多合理组合
    合理组合 = [
        ("citrus", "citrus"),
        ("berry", "berry"),
        ("herb", "herb"),
        ("spice", "spice"),
    ]
    
    for combo in 合理组合:
        if (anchor_name_i in combo) and (anchor_name_j in combo):
            return 1.2
    
    return 1.0


# =========================================================
# 7. 生成兼容度边
# =========================================================
def build_compat_edges(df: pd.DataFrame) -> pd.DataFrame:
    """
    生成所有原料对的兼容度边
    
    返回字段：
    - i_canonical_id
    - j_canonical_id
    - compat_score
    - role_bonus
    - taste_complement_score
    - anchor_bonus
    - cooccur_bonus
    - penalty_score
    - weight
    """
    n = len(df)
    canonical_ids = df["canonical_id"].to_numpy()
    roles = df["role"].to_numpy()
    anchor_names = df["anchor_name"].to_numpy()
    anchor_forms = df["anchor_form"].to_numpy()
    flavor_matrix = df[["sour", "sweet", "bitter", "aroma", "fruity", "body"]].to_numpy(dtype=np.float64)
    
    edges = []
    
    for idx_i in range(n):
        for idx_j in range(idx_i + 1, n):
            i_canonical_id = canonical_ids[idx_i]
            j_canonical_id = canonical_ids[idx_j]
            
            # 计算角色互补分
            role_i = roles[idx_i]
            role_j = roles[idx_j]
            role_bonus = ROLE_BONUS.get((role_i, role_j), DEFAULT_ROLE_BONUS)
            
            # 计算口味互补分
            flavor_i = flavor_matrix[idx_i]
            flavor_j = flavor_matrix[idx_j]
            taste_complement_score = compute_taste_complement_score(flavor_i, flavor_j)
            
            # 计算 anchor 加分
            anchor_name_i = anchor_names[idx_i]
            anchor_name_j = anchor_names[idx_j]
            anchor_form_i = anchor_forms[idx_i]
            anchor_form_j = anchor_forms[idx_j]
            anchor_bonus = compute_anchor_bonus(anchor_name_i, anchor_form_i, anchor_name_j, anchor_form_j)
            
            # 计算共现加分（可选，当前版本暂设为 0）
            cooccur_bonus = 0.0
            
            # 计算惩罚分（可选，当前版本暂设为 0）
            penalty_score = 0.0
            
            # 计算总兼容分
            compat_score = role_bonus * taste_complement_score * anchor_bonus
            
            # 计算最终权重
            weight = min(1.0, (compat_score + cooccur_bonus - penalty_score) / 2.0)  # 归一化
            
            edges.append({
                "i_canonical_id": i_canonical_id,
                "j_canonical_id": j_canonical_id,
                "compat_score": compat_score,
                "role_bonus": role_bonus,
                "taste_complement_score": taste_complement_score,
                "anchor_bonus": anchor_bonus,
                "cooccur_bonus": cooccur_bonus,
                "penalty_score": penalty_score,
                "weight": weight
            })
        
        if (idx_i + 1) % 100 == 0 or (idx_i + 1) == n:
            pct = int(100 * (idx_i + 1) / n)
            edge_count = len(edges)
            print(f"[进度 {pct}%] 边生成中：{idx_i + 1}/{n}, 已生成 {edge_count} 条边")
    
    edge_df = pd.DataFrame(edges)
    
    # 排序
    edge_df = edge_df.sort_values(
        by=["weight", "compat_score", "i_canonical_id", "j_canonical_id"],
        ascending=[False, False, True, True]
    ).reset_index(drop=True)
    
    print(f"[INFO] 最终无向兼容度边数：{len(edge_df)}")
    return edge_df


# =========================================================
# 8. 清空指定 snapshot 的旧结果
# =========================================================
def clear_old_snapshot(snapshot_id: str):
    """
    删除 graph_flavor_compat_edge_stats 中同一 snapshot_id 的旧数据
    """
    sql = text("""
        DELETE FROM graph_flavor_compat_edge_stats
        WHERE snapshot_id = :snapshot_id
    """)

    with engine.begin() as conn:
        conn.execute(sql, {"snapshot_id": snapshot_id})

    print(f"[INFO] 已清空旧快照数据：snapshot_id = {snapshot_id}")


# =========================================================
# 9. 批量写入数据库
# =========================================================
def insert_edges(edge_df: pd.DataFrame, snapshot_id: str, weight_method: str):
    """
    将边结果批量写入 graph_flavor_compat_edge_stats
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
    assert (edge_df["i_canonical_id"] != edge_df["j_canonical_id"]).all(), "存在自环边"
    assert (edge_df["weight"] >= 0).all(), "weight 小于 0"
    assert (edge_df["weight"] <= 1).all(), "weight 大于 1"

    insert_df = edge_df.copy()
    insert_df["snapshot_id"] = snapshot_id
    insert_df["weight_method"] = weight_method
    insert_df["rule_version"] = "v1"
    insert_df["computed_at"] = pd.Timestamp.now()
    insert_df["note"] = "Flavor compatibility edges computed from role, taste, and anchor information"

    # 处理无穷大值和NaN值
    # 将 inf 和 -inf 替换为 0
    insert_df = insert_df.replace([np.inf, -np.inf], 0)
    # 将 NaN 替换为 0
    insert_df = insert_df.fillna(0)

    # 调整列顺序，和目标表保持一致
    # 只包含数据库表中存在的字段
    insert_df = insert_df[
        ["snapshot_id", "i_canonical_id", "j_canonical_id", "compat_score", "role_bonus", 
         "taste_complement_score", "anchor_bonus", "cooccur_bonus", 
         "penalty_score", "weight", "weight_method", "rule_version", 
         "note", "computed_at"]
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
            name="graph_flavor_compat_edge_stats",
            con=engine,
            if_exists="append",
            index=False,
            method="multi"
        )

        print(f"[INFO] 已写入批次 {b + 1}/{batches}，本批 {len(chunk)} 条")

    print(f"[INFO] 全部写入完成，共 {total} 条边。")


# =========================================================
# 10. 简单检查结果
# =========================================================
def inspect_result(snapshot_id: str):
    """
    打印写入后的基本统计和前几条高权重边
    """
    sql_count = text("""
        SELECT COUNT(*) AS cnt
        FROM graph_flavor_compat_edge_stats
        WHERE snapshot_id = :snapshot_id
    """)

    sql_top = text("""
        SELECT *
        FROM graph_flavor_compat_edge_stats
        WHERE snapshot_id = :snapshot_id
        ORDER BY weight DESC, compat_score DESC
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
# 11. 主流程
# =========================================================
def main():
    t0 = time.time()

    print("[INFO] 开始生成风味兼容度边...")
    print(f"[INFO] 配置参数: SNAPSHOT_ID={SNAPSHOT_ID}, BATCH_SIZE={BATCH_SIZE}")

    # 1) 读取原料信息
    print("[步骤 1] 读取原料信息...")
    df = load_ingredient_info()
    node_count = len(df)

    # 2) 生成兼容度边
    print("[步骤 2] 生成兼容度边...")
    start_time = time.time()
    edge_df = build_compat_edges(df)
    edge_count = len(edge_df)
    elapsed = time.time() - start_time
    print(f"[INFO] 边生成完成，共 {edge_count} 条边，用时 {elapsed:.2f} 秒")

    # 3) 清空当前快照旧数据
    print("[步骤 3] 清空旧快照数据...")
    clear_old_snapshot(SNAPSHOT_ID)

    # 4) 写入数据库
    print("[步骤 4] 批量写入数据库...")
    start_time = time.time()
    insert_edges(edge_df, SNAPSHOT_ID, WEIGHT_METHOD)
    elapsed = time.time() - start_time
    print(f"[INFO] 数据库写入完成，用时 {elapsed:.2f} 秒")

    # 5) 检查结果
    print("[步骤 5] 检查结果...")
    inspect_result(SNAPSHOT_ID)

    t1 = time.time()
    total_elapsed = t1 - t0
    print("[INFO] 全流程完成！")
    print(f"[INFO] 节点数: {node_count}, 边数: {edge_count}")
    print(f"[INFO] 总用时: {total_elapsed:.2f} 秒")
    print(f"[INFO] 平均处理每条边: {total_elapsed/edge_count:.4f} 秒/条")


if __name__ == "__main__":
    main()
