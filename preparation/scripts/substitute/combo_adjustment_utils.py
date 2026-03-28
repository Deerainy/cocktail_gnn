# -*- coding: utf-8 -*-
"""
组合调整工具函数

功能：
1. 提供原料替代所需的核心函数
2. 支持 4.2 组合调整方法的复用
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from decimal import Decimal

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.db import get_engine
from scripts.sqe.phase_A.phaseA_baseline_v2 import set_sqe_weights
from scripts.sqe.phase_A.sqe_scorer_conflict_v2 import calculate_conflict_score_from_ingredients
from scripts.sqe.phase_A.sqe_scorer_balance import calculate_balance_score_from_ingredients
from scripts.sqe.phase_A.sqe_scorer_synergy import score_recipe_from_ingredients

class Config:
    """配置类"""
    # 输入文件
    PHASE_C_PARAMS_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseC", "optimal_params.json")
    PHASE_A_BASELINE_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseA_baseline_v2.csv")

def load_optimal_params() -> dict:
    """
    加载最优参数
    """
    try:
        with open(Config.PHASE_C_PARAMS_FILE, 'r', encoding='utf-8') as f:
            params = json.load(f)
        return params
    except Exception as e:
        print(f"[WARNING] 加载最优参数失败: {e}")
        # 返回默认值
        return {
            "synergy": {
                "alpha1": 0.45,
                "alpha2": 0.45,
                "alpha3": 0.1
            },
            "conflict": {
                "eta1": 0.3033,
                "eta2": 0.2315,
                "eta3": 0.3128,
                "eta4": 0.1523
            },
            "balance": {
                "mu1": 0.6521,
                "mu2": 0.3479
            },
            "sqe": {
                "lambda_synergy": 0.3521,
                "lambda_conflict": 0.3067,
                "lambda_balance": 0.3412
            }
        }

def set_optimal_weights():
    """
    设置最优权重
    """
    params = load_optimal_params()
    sqe_params = params.get('sqe', {})
    
    lambda_synergy = sqe_params.get('lambda_synergy', 0.4)
    lambda_conflict = sqe_params.get('lambda_conflict', 0.3)
    lambda_balance = sqe_params.get('lambda_balance', 0.3)
    
    set_sqe_weights(lambda_synergy, lambda_conflict, lambda_balance)
    
    print(f"[INFO] 设置最优权重: synergy={lambda_synergy}, conflict={lambda_conflict}, balance={lambda_balance}")

def load_recipe_ingredients(recipe_id: int) -> list:
    """
    加载配方的原料列表
    """
    engine = get_engine()
    sql = text("""
    SELECT ri.ingredient_id, i.name_norm, ri.amount, ri.unit, ri.role, ri.line_no, ri.raw_text
    FROM recipe_ingredient ri
    JOIN ingredient i ON ri.ingredient_id = i.ingredient_id
    WHERE ri.recipe_id = :recipe_id
    ORDER BY ri.line_no
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql, {'recipe_id': recipe_id})
        ingredients = []
        for row in result:
            ingredient = {
                'ingredient_id': row.ingredient_id,
                'ingredient_name': row.name_norm,
                'amount': float(row.amount) if row.amount is not None else None,
                'unit': row.unit,
                'role': row.role,
                'line_no': row.line_no,
                'raw_text': row.raw_text
            }
            ingredients.append(ingredient)
    
    print(f"[INFO] 加载了配方 {recipe_id} 的 {len(ingredients)} 个原料")
    return ingredients

def load_canonical_mapping() -> dict:
    """
    加载 canonical 映射信息
    """
    engine = get_engine()
    sql = text("""
    SELECT src_ingredient_id, canonical_id, canonical_name
    FROM llm_canonical_map
    WHERE status = 'ok'
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql)
        canonical_map = {}
        for row in result:
            canonical_map[row.src_ingredient_id] = {
                'canonical_id': row.canonical_id,
                'canonical_name': row.canonical_name
            }
    
    print(f"[INFO] 加载了 {len(canonical_map)} 个 canonical 映射")
    return canonical_map

def load_candidate_ingredients(target_ingredient_id: int, target_role: str, canonical_map: dict) -> list:
    """
    加载候选替代原料，参考风味互补和共现信息
    """
    engine = get_engine()
    
    # 获取目标原料的 canonical 信息
    target_canonical = canonical_map.get(target_ingredient_id, {})
    target_canonical_id = target_canonical.get('canonical_id')
    
    # 查找与目标原料同角色的其他原料，且 canonical 不同
    sql = text("""
    SELECT DISTINCT i.ingredient_id, i.name_norm, ri.role
    FROM ingredient i
    JOIN recipe_ingredient ri ON i.ingredient_id = ri.ingredient_id
    LEFT JOIN llm_canonical_map lcm ON i.ingredient_id = lcm.src_ingredient_id AND lcm.status = 'ok'
    WHERE ri.role = :target_role 
    AND i.ingredient_id != :target_ingredient_id
    AND (lcm.canonical_id != :target_canonical_id OR lcm.canonical_id IS NULL)
    GROUP BY i.ingredient_id, i.name_norm, ri.role
    ORDER BY COUNT(*) DESC
    LIMIT 100
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql, {
            'target_role': target_role, 
            'target_ingredient_id': target_ingredient_id,
            'target_canonical_id': target_canonical_id
        })
        candidates = []
        for row in result:
            candidate = {
                'ingredient_id': row.ingredient_id,
                'ingredient_name': row.name_norm,
                'role': row.role
            }
            # 添加 canonical 信息
            if row.ingredient_id in canonical_map:
                candidate['canonical_id'] = canonical_map[row.ingredient_id]['canonical_id']
                candidate['canonical_name'] = canonical_map[row.ingredient_id]['canonical_name']
            else:
                candidate['canonical_id'] = None
                candidate['canonical_name'] = row.name_norm
            candidates.append(candidate)
    
    # 参考风味互补边信息排序
    if target_canonical_id:
        candidates = rank_candidates_by_compatibility(candidates, target_canonical_id, target_role, canonical_map)
    
    print(f"[INFO] 加载了 {len(candidates)} 个候选替代原料")
    return candidates

def rank_candidates_by_compatibility(candidates: list, target_canonical_id: int, target_role: str, canonical_map: dict) -> list:
    """
    根据多维度特征对候选原料进行排序
    包括：风味互补性、共现关系、风味相似度、角色匹配度、anchor 兼容性等
    """
    engine = get_engine()
    
    # 加载风味互补边信息
    sql = text("""
    SELECT j_canonical_id, weight
    FROM graph_flavor_compat_edge_stats
    WHERE i_canonical_id = :target_canonical_id
    ORDER BY weight DESC
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql, {'target_canonical_id': target_canonical_id})
        compat_scores = {row.j_canonical_id: row.weight for row in result}
    
    # 加载共现边信息
    sql = text("""
    SELECT j_id, weight
    FROM graph_edge_stats_v2
    WHERE i_id = :target_canonical_id
    ORDER BY weight DESC
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql, {'target_canonical_id': target_canonical_id})
        cooccur_scores = {row.j_id: row.weight for row in result}
    
    # 加载风味相似度信息
    sql = text("""
    SELECT j_id, weight
    FROM graph_flavor_edge_stats
    WHERE i_id = :target_canonical_id
    ORDER BY weight DESC
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql, {'target_canonical_id': target_canonical_id})
        similarity_scores = {row.j_id: row.weight for row in result}
    
    # 加载 anchor 信息
    sql = text("""
    SELECT ingredient_id, anchor_name, anchor_form
    FROM ingredient_flavor_anchor
    WHERE review_status = 'approved'
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql)
        # 先构建 ingredient_id 到 anchor 信息的映射
        ingredient_anchor_map = {row.ingredient_id: {'anchor_name': row.anchor_name, 'anchor_form': row.anchor_form} for row in result}
    
    # 构建 canonical_id 到 anchor 信息的映射
    anchor_info = {}
    for ingredient_id, anchor_data in ingredient_anchor_map.items():
        if ingredient_id in canonical_map:
            canonical_id = canonical_map[ingredient_id]['canonical_id']
            anchor_info[canonical_id] = anchor_data
    
    # 计算综合得分
    for candidate in candidates:
        canonical_id = candidate.get('canonical_id')
        candidate_id = candidate.get('ingredient_id')
        candidate_role = candidate.get('role')
        
        # 基础得分
        if canonical_id:
            # 综合三种得分，将 Decimal 转换为 float
            compat_score = float(compat_scores.get(canonical_id, 0))
            cooccur_score = float(cooccur_scores.get(canonical_id, 0))
            similarity_score = float(similarity_scores.get(canonical_id, 0))
        else:
            compat_score = 0
            cooccur_score = 0
            similarity_score = 0
        
        # 角色匹配度得分
        role_score = 1.0 if candidate_role == target_role else 0.5
        
        # Anchor 兼容性得分
        anchor_score = 1.0
        if canonical_id in anchor_info and target_canonical_id in anchor_info:
            target_anchor = anchor_info.get(target_canonical_id, {})
            candidate_anchor = anchor_info.get(canonical_id, {})
            if target_anchor.get('anchor_name') == candidate_anchor.get('anchor_name'):
                anchor_score = 1.0
            elif target_anchor.get('anchor_form') == candidate_anchor.get('anchor_form'):
                anchor_score = 0.8
            else:
                anchor_score = 0.6
        
        # 计算综合得分
        candidate['compatibility_score'] = (
            0.3 * compat_score +      # 风味互补性
            0.2 * cooccur_score +     # 共现关系
            0.2 * similarity_score +  # 风味相似度
            0.15 * role_score +       # 角色匹配度
            0.15 * anchor_score       # Anchor 兼容性
        )
    
    # 按综合得分排序
    candidates.sort(key=lambda x: x.get('compatibility_score', 0), reverse=True)
    
    # 限制返回数量
    return candidates[:50]

def calculate_sqe_score(ingredients: list) -> dict:
    """
    计算配方的 SQE 分数
    """
    try:
        # 计算各维度分数
        synergy_result = score_recipe_from_ingredients(ingredients)
        syn_score = synergy_result.get("synergy_score", 0.0)
        
        conflict_result = calculate_conflict_score_from_ingredients(ingredients)
        conf_score = conflict_result.get("conflict_score", 0.0)
        conf_norm = conflict_result.get("conflict_normalized", 0.0)
        
        balance_result = calculate_balance_score_from_ingredients(ingredients)
        bal_score = balance_result.get("final_balance_score", 0.0)
        
        # 标准化分数
        def normalize(score, min_val, max_val):
            if max_val == min_val:
                return 0.5
            return max(0.0, min(1.0, (score - min_val) / (max_val - min_val)))
        
        # 对于 balance 分数，使用固定的范围 [-1, 0] 进行标准化
        bal_min = -1.0
        bal_max = 0.0
        bal_norm = normalize(bal_score, bal_min, bal_max)
        
        # 对于 synergy 分数，使用固定的范围 [0, 20] 进行标准化
        syn_min = 0.0
        syn_max = 20.0
        syn_norm = normalize(syn_score, syn_min, syn_max)
        
        # 转换冲突分数为越大越好的形式
        conf_good = 1 - conf_norm
        
        # 加载最优权重
        params = load_optimal_params()
        sqe_params = params.get('sqe', {})
        lambda_synergy = sqe_params.get('lambda_synergy', 0.4)
        lambda_conflict = sqe_params.get('lambda_conflict', 0.3)
        lambda_balance = sqe_params.get('lambda_balance', 0.3)
        
        # 计算 SQE 总分
        sqe_total = (
            lambda_synergy * syn_norm +
            lambda_conflict * conf_good +
            lambda_balance * bal_norm
        )
        
        return {
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
        print(f"[ERROR] 计算 SQE 分数时出错: {e}")
        return {
            "synergy_score": 0.0,
            "conflict_score": 0.0,
            "final_balance_score": 0.0,
            "synergy_normalized": 0.0,
            "conflict_normalized": 0.0,
            "balance_normalized": 0.0,
            "conflict_good": 1.0,
            "sqe_total": 0.0
        }

def determine_acceptance(delta_sqe: float, threshold: float = 0.05) -> bool:
    """
    确定替代是否可接受
    """
    return delta_sqe > -threshold
