# -*- coding: utf-8 -*-
"""
替代原料推理脚本

功能：
1. 给定一个配方和一个目标原料，找出哪些候选原料替代后，整体结构质量下降不明显，甚至更好
2. 计算每个候选原料的 new_sqe / delta_sqe / accept_or_reject / explanation
3. 基于结构质量变化评估替代方案
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.db import get_engine
from sqlalchemy import text

class Config:
    """配置类"""
    # 输入文件
    NODE_IMPORTANCE_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "node_importance_scores.csv")
    PHASE_A_BASELINE_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseA_baseline_v2.csv")
    
    # 输出文件
    SUBSTITUTION_RESULT_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "substitution_results.json")
    
    # 替代阈值
    TAU = 0.05  # 允许的结构损失阈值

def load_recipe_ingredients(recipe_id: int) -> pd.DataFrame:
    """
    加载指定配方的原料信息
    """
    engine = get_engine()
    sql = text("""
    SELECT ri.recipe_id, ri.ingredient_id, i.name_norm, ri.role, ri.amount, ri.unit, ri.line_no, ri.raw_text
    FROM recipe_ingredient ri
    JOIN ingredient i ON ri.ingredient_id = i.ingredient_id
    WHERE ri.recipe_id = :recipe_id
    ORDER BY ri.line_no
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn, params={"recipe_id": recipe_id})
    
    print(f"[INFO] 加载了配方 {recipe_id} 的 {len(df)} 个原料")
    return df

def load_candidate_ingredients(target_ingredient_id: int) -> pd.DataFrame:
    """
    加载候选替代原料
    """
    engine = get_engine()
    
    # 首先获取目标原料的角色
    target_role_sql = text("""
    SELECT role
    FROM recipe_ingredient
    WHERE ingredient_id = :ingredient_id
    GROUP BY role
    ORDER BY COUNT(*) DESC
    LIMIT 1
    """)
    
    with engine.begin() as conn:
        target_role_df = pd.read_sql(target_role_sql, conn, params={"ingredient_id": target_ingredient_id})
    
    target_role = target_role_df.iloc[0]['role'] if not target_role_df.empty else 'unknown'
    print(f"[INFO] 目标原料的主要角色: {target_role}")
    
    # 加载相同角色的原料作为候选
    candidate_sql = text("""
    SELECT DISTINCT i.ingredient_id, i.name_norm
    FROM recipe_ingredient ri
    JOIN ingredient i ON ri.ingredient_id = i.ingredient_id
    WHERE ri.role = :role AND ri.ingredient_id != :target_id
    GROUP BY i.ingredient_id, i.name_norm
    ORDER BY COUNT(*) DESC
    LIMIT 50
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(candidate_sql, conn, params={"role": target_role, "target_id": target_ingredient_id})
    
    print(f"[INFO] 加载了 {len(df)} 个候选替代原料")
    return df

def load_sqe_scores() -> pd.DataFrame:
    """
    加载 SQE 分数数据
    """
    if os.path.exists(Config.PHASE_A_BASELINE_FILE):
        df = pd.read_csv(Config.PHASE_A_BASELINE_FILE)
        print(f"[INFO] 加载了 {len(df)} 条 SQE 分数数据")
        return df
    else:
        print(f"[WARNING] {Config.PHASE_A_BASELINE_FILE} 文件不存在，将使用默认 SQE 分数")
        return pd.DataFrame()

def calculate_sqe(recipe_id: int, ingredients: pd.DataFrame) -> float:
    """
    计算配方的 SQE 分数
    """
    # 尝试从文件中获取 SQE 分数
    sqe_df = load_sqe_scores()
    if not sqe_df.empty and recipe_id in sqe_df['recipe_id'].values:
        return float(sqe_df[sqe_df['recipe_id'] == recipe_id]['sqe_total'].iloc[0])
    else:
        # 如果没有 SQE 分数，使用默认值
        return 0.5

def substitute_ingredient(recipe_ingredients: pd.DataFrame, target_ingredient_id: int, candidate_ingredient_id: int) -> pd.DataFrame:
    """
    替换配方中的目标原料
    """
    # 创建副本
    substituted_ingredients = recipe_ingredients.copy()
    
    # 替换目标原料
    substituted_ingredients.loc[substituted_ingredients['ingredient_id'] == target_ingredient_id, 'ingredient_id'] = candidate_ingredient_id
    
    # 获取候选原料的名称
    engine = get_engine()
    sql = text("""
    SELECT name_norm
    FROM ingredient
    WHERE ingredient_id = :ingredient_id
    """)
    
    with engine.begin() as conn:
        candidate_name_df = pd.read_sql(sql, conn, params={"ingredient_id": candidate_ingredient_id})
    
    if not candidate_name_df.empty:
        candidate_name = candidate_name_df.iloc[0]['name_norm']
        substituted_ingredients.loc[substituted_ingredients['ingredient_id'] == candidate_ingredient_id, 'name_norm'] = candidate_name
    
    return substituted_ingredients

def generate_explanation(original_sqe: float, new_sqe: float, delta_sqe: float, tau: float) -> str:
    """
    生成替代方案的解释
    """
    if delta_sqe > 0:
        return f"替代后整体结构质量提升了 {delta_sqe:.4f}，新的 SQE 分数为 {new_sqe:.4f}，高于原始分数 {original_sqe:.4f}。"
    elif delta_sqe >= -tau:
        return f"替代后整体结构质量下降了 {abs(delta_sqe):.4f}，但在允许的阈值范围内，新的 SQE 分数为 {new_sqe:.4f}，原始分数为 {original_sqe:.4f}。"
    else:
        return f"替代后整体结构质量显著下降了 {abs(delta_sqe):.4f}，超过了允许的阈值，新的 SQE 分数为 {new_sqe:.4f}，原始分数为 {original_sqe:.4f}。"

def reason