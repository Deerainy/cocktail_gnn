# -*- coding: utf-8 -*-
"""
Phase A Baseline 生成脚本 (v2)

功能：
1. 加载最新的协同、冲突、平衡评分数据
2. 统一标准化方法
3. 计算 SQE 总分
4. 生成标准化的 Phase A baseline 表
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import List, Dict

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# =========================================================
# 配置参数
# =========================================================
# 权重配置
# LAMBDA_SYNERGY = 0.4    # 协同权重
# LAMBDA_CONFLICT = 0.3   # 冲突权重
# LAMBDA_BALANCE = 0.3    # 平衡权重
LAMBDA_SYNERGY = 0.3521    # 协同权重
LAMBDA_CONFLICT = 0.3067   # 冲突权重
LAMBDA_BALANCE = 0.3412    # 平衡权重
# 配置参数接口
def set_sqe_weights(synergy_weight=0.3521, conflict_weight=0.3067, balance_weight=0.3412):
    """
    设置整体 SQE 评分的权重参数
    
    参数:
    synergy_weight: 协同权重
    conflict_weight: 冲突权重
    balance_weight: 平衡权重
    
    注意: 权重和必须为 1
    """
    global LAMBDA_SYNERGY, LAMBDA_CONFLICT, LAMBDA_BALANCE
    LAMBDA_SYNERGY = synergy_weight
    LAMBDA_CONFLICT = conflict_weight
    LAMBDA_BALANCE = balance_weight
    
    # 验证权重和
    assert abs(LAMBDA_SYNERGY + LAMBDA_CONFLICT + LAMBDA_BALANCE - 1.0) < 1e-6, "权重和必须为 1"

# =========================================================
# 工具函数
# =========================================================
def min_max_normalize(series: pd.Series) -> pd.Series:
    """
    Min-Max 标准化
    """
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)

def load_synergy_data() -> pd.DataFrame:
    """
    加载协同评分数据
    """
    synergy_file = os.path.join(_project_root, "data", "phaseA", "recipe_scores.csv")
    if not os.path.exists(synergy_file):
        raise FileNotFoundError(f"协同评分文件不存在: {synergy_file}")
    
    df = pd.read_csv(synergy_file)
    print(f"[INFO] 加载了 {len(df)} 条协同评分数据")
    return df

def load_conflict_data() -> pd.DataFrame:
    """
    加载冲突评分数据（使用新的 v4 版本）
    """
    conflict_file = os.path.join(_project_root, "data", "phaseA", "sqe_conflict_results_v4.csv")
    if not os.path.exists(conflict_file):
        # 尝试其他可能的文件名
        conflict_file = os.path.join(_project_root, "data", "phaseA", "recipe_conflict_scores.csv")
        if not os.path.exists(conflict_file):
            raise FileNotFoundError(f"冲突评分文件不存在")
    
    df = pd.read_csv(conflict_file)
    print(f"[INFO] 加载了 {len(df)} 条冲突评分数据")
    return df

def load_balance_data() -> pd.DataFrame:
    """
    加载平衡评分数据
    """
    balance_file = os.path.join(_project_root, "data", "phaseA", "sqe_balance_results.csv")
    if not os.path.exists(balance_file):
        raise FileNotFoundError(f"平衡评分文件不存在: {balance_file}")
    
    df = pd.read_csv(balance_file)
    print(f"[INFO] 加载了 {len(df)} 条平衡评分数据")
    return df

def load_recipe_info() -> pd.DataFrame:
    """
    加载食谱基本信息
    """
    from src.db import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    sql = text("""
    SELECT recipe_id, COUNT(*) as n_ingredients
    FROM recipe_ingredient
    GROUP BY recipe_id
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条食谱基本信息")
    return df

def load_ingredient_roles() -> pd.DataFrame:
    """
    加载原料角色信息
    """
    from src.db import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    sql = text("""
    SELECT recipe_id, role, COUNT(*) as count
    FROM recipe_ingredient
    GROUP BY recipe_id, role
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条原料角色信息")
    return df

def calculate_baseline_scores_from_ingredients(ingredients: List[Dict]) -> Dict:
    """
    计算给定配方的基线分数
    
    参数:
    ingredients: 原料列表，每个原料是一个字典，包含以下字段:
        - ingredient_id: 原料 ID
        - amount: 原料用量
        - unit: 单位
        - role: 角色
        - line_no: 行号
        - raw_text: 原始文本
    
    返回:
    包含标准化分数和 SQE 总分的字典
    """
    try:
        if not ingredients:
            return {
                "recipe_id": "custom",
                "synergy_score": 0.0,
                "conflict_score": 0.0,
                "final_balance_score": 0.0,
                "synergy_normalized": 0.0,
                "conflict_normalized": 0.0,
                "balance_normalized": 0.0,
                "conflict_good": 1.0,
                "sqe_total": 0.0
            }
        
        # 导入评分接口函数
        from scripts.SQE.sqe_scorer_conflict_v2 import calculate_conflict_score_from_ingredients
        from scripts.SQE.phase_A.sqe_scorer_balance import calculate_balance_score_from_ingredients
        from scripts.SQE.phase_A.sqe_scorer_synergy import score_recipe_from_ingredients
        
        # 计算各维度分数
        synergy_result = score_recipe_from_ingredients(ingredients)
        syn_score = synergy_result["synergy_score"]
        
        conflict_result = calculate_conflict_score_from_ingredients(ingredients)
        conf_score = conflict_result["conflict_score"]
        conf_norm = conflict_result["conflict_normalized"]
        
        balance_result = calculate_balance_score_from_ingredients(ingredients)
        bal_score = balance_result["final_balance_score"]
        
        # 加载基线统计信息
        baseline_file = os.path.join(_project_root, "data", "phaseA_baseline_v2.csv")
        if not os.path.exists(baseline_file):
            raise FileNotFoundError(f"Phase A 基线评分表不存在: {baseline_file}")
        
        df = pd.read_csv(baseline_file)
        
        # 计算各维度的 min/max
        syn_min = df['synergy_score'].min()
        syn_max = df['synergy_score'].max()
        bal_min = df['final_balance_score'].min()
        bal_max = df['final_balance_score'].max()
        
        # 标准化分数
        def normalize(score, min_val, max_val):
            if max_val == min_val:
                return 0.5
            return max(0.0, min(1.0, (score - min_val) / (max_val - min_val)))
        
        syn_norm = normalize(syn_score, syn_min, syn_max)
        bal_norm = normalize(bal_score, bal_min, bal_max)
        
        # 转换冲突分数为越大越好的形式
        conf_good = 1 - conf_norm
        
        # 计算 SQE 总分
        sqe_total = (
            LAMBDA_SYNERGY * syn_norm +
            LAMBDA_CONFLICT * conf_good +
            LAMBDA_BALANCE * bal_norm
        )
        
        return {
            "recipe_id": "custom",
            "synergy_score": syn_score,
            "conflict_score": conf_score,
            "final_balance_score": bal_score,
            "synergy_normalized": syn_norm,
            "conflict_normalized": conf_norm,
            "balance_normalized": bal_norm,
            "conflict_good": conf_good,
            "sqe_total": sqe_total
        }
    except Exception as e:
        print(f"[ERROR] 处理自定义配方时出错: {e}")
        # 记录错误但返回默认值
        return {
            "recipe_id": "custom",
            "synergy_score": 0.0,
            "conflict_score": 0.0,
            "final_balance_score": 0.0,
            "synergy_normalized": 0.0,
            "conflict_normalized": 0.0,
            "balance_normalized": 0.0,
            "conflict_good": 1.0,
            "sqe_total": 0.0
        }

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("生成 Phase A Baseline (v2)...")
    
    # 加载数据
    synergy_df = load_synergy_data()
    conflict_df = load_conflict_data()
    balance_df = load_balance_data()
    recipe_info = load_recipe_info()
    ingredient_roles = load_ingredient_roles()
    
    # 合并数据
    # 以 recipe_id 为键进行合并
    merged_df = synergy_df.merge(
        conflict_df[['recipe_id', 'conflict_score', 'conflict_normalized']],
        on='recipe_id',
        how='inner'
    )
    
    merged_df = merged_df.merge(
        balance_df[['recipe_id', 'final_balance_score']],
        on='recipe_id',
        how='inner'
    )
    
    merged_df = merged_df.merge(
        recipe_info,
        on='recipe_id',
        how='left'
    )
    
    print(f"[INFO] 合并后的数据行数: {len(merged_df)}")
    
    # 标准化各模块分数
    # 协同分数（越大越好）
    merged_df['synergy_normalized'] = min_max_normalize(merged_df['synergy_score'])
    
    # 冲突分数（越小越好，转换为 conflict_good）
    merged_df['conflict_good'] = 1 - merged_df['conflict_normalized']
    
    # 平衡分数（越大越好）
    merged_df['balance_normalized'] = min_max_normalize(merged_df['final_balance_score'])
    
    # 计算 SQE 总分
    merged_df['sqe_total'] = (
        LAMBDA_SYNERGY * merged_df['synergy_normalized'] +
        LAMBDA_CONFLICT * merged_df['conflict_good'] +
        LAMBDA_BALANCE * merged_df['balance_normalized']
    )
    
    # 计算角色统计信息
    # 转换角色计数为宽格式
    role_pivot = ingredient_roles.pivot(
        index='recipe_id',
        columns='role',
        values='count'
    ).fillna(0)
    
    # 重命名列
    role_mapping = {
        'base_spirit': 'base_count',
        'modifier': 'modifier_count',
        'acid': 'acid_count',
        'sweetener': 'sweetener_count'
    }
    role_pivot = role_pivot.rename(columns=role_mapping)
    
    # 只保留需要的列
    role_columns = ['base_count', 'modifier_count', 'acid_count', 'sweetener_count']
    for col in role_columns:
        if col not in role_pivot.columns:
            role_pivot[col] = 0
    
    # 合并角色信息
    merged_df = merged_df.merge(
        role_pivot[role_columns],
        on='recipe_id',
        how='left'
    )
    
    # 填充缺失值
    merged_df = merged_df.fillna({
        'n_ingredients': 0,
        'base_count': 0,
        'modifier_count': 0,
        'acid_count': 0,
        'sweetener_count': 0
    })
    
    # 生成角色摘要
    def generate_roles_summary(row):
        roles = []
        if row.get('base_count', 0) > 0:
            roles.append(f"base:{int(row['base_count'])}")
        if row.get('modifier_count', 0) > 0:
            roles.append(f"modifier:{int(row['modifier_count'])}")
        if row.get('acid_count', 0) > 0:
            roles.append(f"acid:{int(row['acid_count'])}")
        if row.get('sweetener_count', 0) > 0:
            roles.append(f"sweetener:{int(row['sweetener_count'])}")
        return ",".join(roles)
    
    merged_df['roles_summary'] = merged_df.apply(generate_roles_summary, axis=1)
    
    # 保存结果
    output_file = os.path.join(_project_root, "data", "phaseA_baseline_v2.csv")
    output_columns = [
        'recipe_id', 'synergy_score', 'conflict_score', 'final_balance_score',
        'synergy_normalized', 'conflict_normalized', 'balance_normalized',
        'conflict_good', 'sqe_total', 'n_ingredients', 'roles_summary',
        'base_count', 'modifier_count', 'acid_count', 'sweetener_count'
    ]
    
    merged_df[output_columns].to_csv(output_file, index=False, encoding="utf-8")
    print(f"[INFO] Phase A Baseline 已保存到: {output_file}")
    
    # 统计信息
    print("\n[INFO] 统计信息:")
    print(f"[INFO] 平均协同分数: {merged_df['synergy_score'].mean():.4f}")
    print(f"[INFO] 平均冲突分数: {merged_df['conflict_score'].mean():.4f}")
    print(f"[INFO] 平均平衡分数: {merged_df['final_balance_score'].mean():.4f}")
    print(f"[INFO] 平均 SQE 总分: {merged_df['sqe_total'].mean():.4f}")
    print(f"[INFO] 协同分数范围: [{merged_df['synergy_score'].min():.4f}, {merged_df['synergy_score'].max():.4f}]")
    print(f"[INFO] 冲突分数范围: [{merged_df['conflict_score'].min():.4f}, {merged_df['conflict_score'].max():.4f}]")
    print(f"[INFO] 平衡分数范围: [{merged_df['final_balance_score'].min():.4f}, {merged_df['final_balance_score'].max():.4f}]")
    print(f"[INFO] SQE 总分范围: [{merged_df['sqe_total'].min():.4f}, {merged_df['sqe_total'].max():.4f}]")

if __name__ == "__main__":
    main()
