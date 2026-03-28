# -*- coding: utf-8 -*-
"""
Phase C 数据准备脚本

功能：
1. 冻结 Phase B 结果，准备监督数据
2. 整合每个 recipe 的三项分数
3. 整合扰动样本对和 pairwise 标签
4. 生成包含所有必要信息的训练文件
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
# 向上三级目录才是项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 输入文件
    PHASE_B_RESULTS_FILE = os.path.join(_project_root, "data", "phaseB", "phaseB_optimal_weights.json")
    RECIPE_SCORES_FILE = os.path.join(_project_root, "data", "phaseA", "recipe_scores.csv")
    CONFLICT_RESULTS_FILE = os.path.join(_project_root, "data", "phaseA", "sqe_conflict_results_v4.csv")
    BALANCE_RESULTS_FILE = os.path.join(_project_root, "data", "phaseA", "sqe_balance_results.csv")
    PHASE_A_BASELINE_FILE = os.path.join(_project_root, "data", "phaseA", "phaseA_baseline_v2.csv")
    PHASE_B_PAIRS_FILE = os.path.join(_project_root, "data", "phaseB", "phaseB_pairwise_dataset_v3_valid.csv")
    
    # 输出文件
    PHASE_C_RECIPES_FILE = os.path.join(_project_root, "data", "phaseC", "recipes_data.jsonl")
    PHASE_C_PAIRS_FILE = os.path.join(_project_root, "data", "phaseC", "pairs_data.jsonl")
    
    # 最优参数
    OPTIMAL_PARAMS = {
        "synergy": {
            "alpha1": 0.45,  # 风味兼容度权重
            "alpha2": 0.45,  # 共现权重
            "alpha3": 0.10   # 锚点相似度权重
        },
        "conflict": {
            "eta1": 0.3033,  # 风味冲突权重
            "eta2": 0.2315,  # 角色冲突权重
            "eta3": 0.3128,  # 类型冲突权重
            "eta4": 0.1523   # 比例冲突权重
        },
        "balance": {
            "mu1": 0.6521,   # 风味平衡权重
            "mu2": 0.3479    # 角色平衡权重
        },
        "sqe": {
            "lambda_synergy": 0.3521,
            "lambda_conflict": 0.3067,
            "lambda_balance": 0.3412
        }
    }

# =========================================================
# 数据加载函数
# =========================================================

def load_recipe_scores() -> pd.DataFrame:
    """
    加载 recipe 评分数据
    """
    if not os.path.exists(Config.RECIPE_SCORES_FILE):
        raise FileNotFoundError(f"Recipe 评分文件不存在: {Config.RECIPE_SCORES_FILE}")
    
    df = pd.read_csv(Config.RECIPE_SCORES_FILE)
    print(f"[INFO] 加载了 {len(df)} 条 Recipe 评分数据")
    return df

def load_conflict_results() -> pd.DataFrame:
    """
    加载冲突评分数据
    """
    if not os.path.exists(Config.CONFLICT_RESULTS_FILE):
        raise FileNotFoundError(f"冲突评分文件不存在: {Config.CONFLICT_RESULTS_FILE}")
    
    df = pd.read_csv(Config.CONFLICT_RESULTS_FILE)
    print(f"[INFO] 加载了 {len(df)} 条冲突评分数据")
    return df

def load_balance_results() -> pd.DataFrame:
    """
    加载平衡评分数据
    """
    if not os.path.exists(Config.BALANCE_RESULTS_FILE):
        raise FileNotFoundError(f"平衡评分文件不存在: {Config.BALANCE_RESULTS_FILE}")
    
    df = pd.read_csv(Config.BALANCE_RESULTS_FILE)
    print(f"[INFO] 加载了 {len(df)} 条平衡评分数据")
    return df

def load_phaseA_baseline() -> pd.DataFrame:
    """
    加载 Phase A 基线数据
    """
    if not os.path.exists(Config.PHASE_A_BASELINE_FILE):
        raise FileNotFoundError(f"Phase A 基线文件不存在: {Config.PHASE_A_BASELINE_FILE}")
    
    df = pd.read_csv(Config.PHASE_A_BASELINE_FILE)
    print(f"[INFO] 加载了 {len(df)} 条 Phase A 基线数据")
    return df

def load_phaseB_pairs() -> pd.DataFrame:
    """
    加载 Phase B 配对数据
    """
    if not os.path.exists(Config.PHASE_B_PAIRS_FILE):
        raise FileNotFoundError(f"Phase B 配对文件不存在: {Config.PHASE_B_PAIRS_FILE}")
    
    df = pd.read_csv(Config.PHASE_B_PAIRS_FILE)
    print(f"[INFO] 加载了 {len(df)} 条 Phase B 配对数据")
    return df

def load_recipe_ingredients() -> pd.DataFrame:
    """
    加载 recipe 原料数据
    """
    from src.db import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    sql = text("""
    SELECT recipe_id, ingredient_id, amount, unit, role, line_no, raw_text
    FROM recipe_ingredient
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条原料数据")
    return df

# =========================================================
# 数据处理函数
# =========================================================

def prepare_recipe_data(recipe_id: int, 
                      ingredients_df: pd.DataFrame, 
                      scores_df: pd.DataFrame, 
                      conflict_df: pd.DataFrame, 
                      balance_df: pd.DataFrame) -> Optional[Dict]:
    """
    准备单个 recipe 的数据
    """
    # 获取原料信息
    recipe_ingredients = ingredients_df[ingredients_df['recipe_id'] == recipe_id]
    if len(recipe_ingredients) == 0:
        return None
    
    # 构建 nodes
    nodes = []
    ingredient_ids = []
    for _, row in recipe_ingredients.iterrows():
        node = {
            "id": row['ingredient_id'],
            "amount": row['amount'],
            "unit": row['unit'],
            "role": row['role'],
            "line_no": row['line_no'],
            "raw_text": row['raw_text']
        }
        nodes.append(node)
        ingredient_ids.append(row['ingredient_id'])
    
    # 构建 edges（这里简化处理，实际应该基于共现和风味兼容度）
    edges = []
    for i in range(len(ingredient_ids)):
        for j in range(i + 1, len(ingredient_ids)):
            edge = {
                "source": ingredient_ids[i],
                "target": ingredient_ids[j]
            }
            edges.append(edge)
    
    # 构建 graph_level_features
    graph_level_features = {
        "n_ingredients": len(ingredient_ids),
        "roles": list(recipe_ingredients['role'].unique()),
        "n_roles": len(recipe_ingredients['role'].unique())
    }
    
    # 获取评分
    syn_row = scores_df[scores_df['recipe_id'] == recipe_id]
    conf_row = conflict_df[conflict_df['recipe_id'] == recipe_id]
    bal_row = balance_df[balance_df['recipe_id'] == recipe_id]
    
    if len(syn_row) == 0 or len(conf_row) == 0 or len(bal_row) == 0:
        return None
    
    syn_B = float(syn_row['synergy_score'].iloc[0])
    conf_B = float(conf_row['conflict_score'].iloc[0])
    bal_B = float(bal_row['final_balance_score'].iloc[0])
    
    # 计算 sqe_B
    # 使用 Phase A 基线中的标准化分数
    baseline_df = load_phaseA_baseline()
    baseline_row = baseline_df[baseline_df['recipe_id'] == recipe_id]
    if len(baseline_row) == 0:
        return None
    
    sqe_B = float(baseline_row['sqe_total'].iloc[0])
    
    # 构建结果
    result = {
        "recipe_id": int(recipe_id),  # 确保是 Python int
        "nodes": nodes,
        "edges": edges,
        "graph_level_features": graph_level_features,
        "syn_B": float(syn_B),  # 确保是 Python float
        "conf_B": float(conf_B),  # 确保是 Python float
        "bal_B": float(bal_B),  # 确保是 Python float
        "sqe_B": float(sqe_B)   # 确保是 Python float
    }
    
    return result

def prepare_pairs_data(pairs_df: pd.DataFrame) -> List[Dict]:
    """
    准备配对数据
    """
    results = []
    
    for _, row in pairs_df.iterrows():
        pair_data = {
            "pos_recipe_id": row.get("recipe_id_pos", ""),
            "neg_recipe_id": row.get("recipe_id_neg", ""),
            "perturb_type": row.get("perturb_type", "")
        }
        results.append(pair_data)
    
    return results

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("准备 Phase C 数据...")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(Config.PHASE_C_RECIPES_FILE), exist_ok=True)
    
    # 加载数据
    print("[INFO] 加载数据...")
    ingredients_df = load_recipe_ingredients()
    scores_df = load_recipe_scores()
    conflict_df = load_conflict_results()
    balance_df = load_balance_results()
    pairs_df = load_phaseB_pairs()
    
    # 准备 recipe 数据
    print("[INFO] 准备 recipe 数据...")
    recipe_ids = scores_df['recipe_id'].unique()
    recipe_count = 0
    
    with open(Config.PHASE_C_RECIPES_FILE, 'w', encoding='utf-8') as f:
        for recipe_id in recipe_ids:
            recipe_data = prepare_recipe_data(recipe_id, ingredients_df, scores_df, conflict_df, balance_df)
            if recipe_data:
                json.dump(recipe_data, f, ensure_ascii=False)
                f.write('\n')
                recipe_count += 1
    
    print(f"[INFO] 保存了 {recipe_count} 条 recipe 数据到 {Config.PHASE_C_RECIPES_FILE}")
    
    # 准备 pairs 数据
    print("[INFO] 准备 pairs 数据...")
    pairs_data = prepare_pairs_data(pairs_df)
    
    with open(Config.PHASE_C_PAIRS_FILE, 'w', encoding='utf-8') as f:
        for pair_data in pairs_data:
            json.dump(pair_data, f, ensure_ascii=False)
            f.write('\n')
    
    print(f"[INFO] 保存了 {len(pairs_data)} 条 pairs 数据到 {Config.PHASE_C_PAIRS_FILE}")
    
    # 保存最优参数
    optimal_params_file = os.path.join(_project_root, "data", "phaseC", "optimal_params.json")
    with open(optimal_params_file, 'w', encoding='utf-8') as f:
        json.dump(Config.OPTIMAL_PARAMS, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] 保存了最优参数到 {optimal_params_file}")
    
    print("[INFO] Phase C 数据准备完成！")

if __name__ == "__main__":
    main()
