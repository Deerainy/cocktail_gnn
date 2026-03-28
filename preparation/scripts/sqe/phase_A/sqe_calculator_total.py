# -*- coding: utf-8 -*-
"""
计算总的 SQE 分数

功能：
1. 读取 synergy、conflict 和 balance 三个部分的评分结果
2. 对各部分进行标准化处理
3. 按照权重计算最终的 SQE 分数
4. 保存结果到 CSV 文件
"""

import os
import sys
import pandas as pd

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
# 向上两级到项目根目录
_root = os.path.dirname(os.path.dirname(_script_dir))
if _root not in sys.path:
    sys.path.insert(0, _root)

# 配置参数
LAMBDA_SYNERGY = 0.4    # 协同权重
LAMBDA_CONFLICT = 0.3   # 冲突权重
LAMBDA_BALANCE = 0.3    # 平衡权重

# 验证权重和为 1
assert abs(LAMBDA_SYNERGY + LAMBDA_CONFLICT + LAMBDA_BALANCE - 1.0) < 1e-6, "权重和必须为 1"

def load_synergy_scores() -> pd.DataFrame:
    """
    加载协同评分结果
    """
    synergy_file = os.path.join(_root, "data", "recipe_scores.csv")
    if not os.path.exists(synergy_file):
        raise FileNotFoundError(f"协同评分文件不存在: {synergy_file}")
    
    df = pd.read_csv(synergy_file)
    print(f"[INFO] 加载了 {len(df)} 条协同评分数据")
    return df[["recipe_id", "synergy_score"]]

def load_conflict_scores() -> pd.DataFrame:
    """
    加载冲突评分结果
    """
    conflict_file = os.path.join(_root, "data", "recipe_conflict_scores.csv")
    if not os.path.exists(conflict_file):
        raise FileNotFoundError(f"冲突评分文件不存在: {conflict_file}")
    
    df = pd.read_csv(conflict_file)
    print(f"[INFO] 加载了 {len(df)} 条冲突评分数据")
    return df[["recipe_id", "conflict_score"]]

def load_balance_scores() -> pd.DataFrame:
    """
    加载平衡评分结果
    """
    balance_file = os.path.join(_root, "data", "sqe_balance_results.csv")
    if not os.path.exists(balance_file):
        raise FileNotFoundError(f"平衡评分文件不存在: {balance_file}")
    
    df = pd.read_csv(balance_file)
    print(f"[INFO] 加载了 {len(df)} 条平衡评分数据")
    return df[["recipe_id", "final_balance_score"]]

def min_max_normalize(series: pd.Series) -> pd.Series:
    """
    Min-Max 标准化，将数据映射到 [0, 1] 区间
    """
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)

def calculate_total_sqe() -> pd.DataFrame:
    """
    计算总的 SQE 分数
    """
    # 加载各部分评分
    synergy_df = load_synergy_scores()
    conflict_df = load_conflict_scores()
    balance_df = load_balance_scores()
    
    # 合并数据
    merged_df = synergy_df.merge(conflict_df, on="recipe_id", how="outer")
    merged_df = merged_df.merge(balance_df, on="recipe_id", how="outer")
    
    # 处理缺失值
    merged_df = merged_df.dropna()
    print(f"[INFO] 合并后共有 {len(merged_df)} 条有效数据")
    
    # 标准化各部分评分
    merged_df["synergy_normalized"] = min_max_normalize(merged_df["synergy_score"])
    merged_df["conflict_normalized"] = min_max_normalize(merged_df["conflict_score"])
    merged_df["balance_normalized"] = min_max_normalize(merged_df["final_balance_score"])
    
    # 计算最终 SQE 分数
    merged_df["sqe_total"] = (
        LAMBDA_SYNERGY * merged_df["synergy_normalized"] +
        LAMBDA_CONFLICT * merged_df["conflict_normalized"] +
        LAMBDA_BALANCE * merged_df["balance_normalized"]
    )
    
    return merged_df

def save_results(df: pd.DataFrame, output_file: str):
    """
    保存结果到 CSV 文件
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 保存结果
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"[INFO] 结果已保存到: {output_file}")

def main():
    """
    主函数
    """
    print("计算总的 SQE 分数...")
    
    # 计算总分
    results_df = calculate_total_sqe()
    
    # 保存结果
    output_file = os.path.join(_root, "data", "sqe_total_scores.csv")
    save_results(results_df, output_file)
    
    # 统计信息
    print("\n[INFO] 统计信息:")
    print(f"[INFO] 平均 SQE 分数: {results_df['sqe_total'].mean():.4f}")
    print(f"[INFO] 最大 SQE 分数: {results_df['sqe_total'].max():.4f}")
    print(f"[INFO] 最小 SQE 分数: {results_df['sqe_total'].min():.4f}")
    print(f"[INFO] SQE 分数标准差: {results_df['sqe_total'].std():.4f}")
    
    # 权重信息
    print("\n[INFO] 权重配置:")
    print(f"[INFO] 协同 (Synergy) 权重: {LAMBDA_SYNERGY}")
    print(f"[INFO] 冲突 (Conflict) 权重: {LAMBDA_CONFLICT}")
    print(f"[INFO] 平衡 (Balance) 权重: {LAMBDA_BALANCE}")

if __name__ == "__main__":
    main()
