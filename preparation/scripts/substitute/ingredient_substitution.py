# -*- coding: utf-8 -*-
"""
原料替代推理脚本

功能：
1. 给定一个配方和一个目标原料，找出候选替代原料
2. 计算替代前后的 SQE 分数
3. 生成替代建议和解释
4. 保存结果到指定文件
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

def serialize_decimal(obj):
    """
    处理 Decimal 类型的 JSON 序列化
    """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

from src.db import get_engine
from sqlalchemy import text
from scripts.sqe.phase_A.phaseA_baseline_v2 import set_sqe_weights, calculate_baseline_scores_from_ingredients
from scripts.sqe.phase_A.sqe_scorer_conflict_v2 import calculate_conflict_score_from_ingredients
from scripts.sqe.phase_A.sqe_scorer_balance import calculate_balance_score_from_ingredients
from scripts.sqe.phase_A.sqe_scorer_synergy import score_recipe_from_ingredients

class Config:
    """配置类"""
    # 输入文件
    NODE_IMPORTANCE_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "key", "node_importance_scores.csv")
    EDGE_IMPORTANCE_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "key", "edge_importance_scores.csv")
    PHASE_C_PARAMS_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseC", "optimal_params.json")
    
    # 输出文件
    SUBSTITUTION_RESULTS_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "substitute", "substitution_results.csv")
    SUBSTITUTION_DETAILS_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "substitute", "substitution_details.json")

def load_optimal_params() -> dict:
    """
    加载最优参数
    """
    with open(Config.PHASE_C_PARAMS_FILE, 'r', encoding='utf-8') as f:
        params = json.load(f)
    return params

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
        candidates = rank_candidates_by_compatibility(candidates, target_canonical_id, target_role)
    
    print(f"[INFO] 加载了 {len(candidates)} 个候选替代原料")
    return candidates

def rank_candidates_by_compatibility(candidates: list, target_canonical_id: int, target_role: str) -> list:
    """
    根据多维度特征对候选原料进行排序
    包括：风味互补性、共现关系、风味相似度、角色匹配度、anchor 兼容性、SQE 适配度等
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
        anchor_info = {row.ingredient_id: {'anchor_name': row.anchor_name, 'anchor_form': row.anchor_form} for row in result}
    
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
        if candidate_id in anchor_info and target_canonical_id in anchor_info:
            target_anchor = anchor_info.get(target_canonical_id, {})
            candidate_anchor = anchor_info.get(candidate_id, {})
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
        
        # 加载基线统计信息
        baseline_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseA_baseline_v2.csv")
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

def generate_substitution_explanation(original_score, new_score, target_ingredient, candidate_ingredient, ingredients):
    """
    生成替代解释
    """
    delta_sqe = new_score['sqe_total'] - original_score['sqe_total']
    
    explanation = []
    
    # 整体变化
    if delta_sqe > 0:
        explanation.append(f"替代后整体结构质量提升，SQE 总分增加了 {delta_sqe:.4f}")
    elif delta_sqe > -0.05:
        explanation.append(f"替代后整体结构质量基本保持稳定，SQE 总分变化不大 ({delta_sqe:.4f})")
    else:
        explanation.append(f"替代后整体结构质量下降，SQE 总分减少了 {abs(delta_sqe):.4f}")
    
    # 各维度变化
    delta_synergy = new_score['synergy_normalized'] - original_score['synergy_normalized']
    delta_conflict = new_score['conflict_good'] - original_score['conflict_good']
    delta_balance = new_score['balance_normalized'] - original_score['balance_normalized']
    
    if delta_synergy > 0.05:
        explanation.append(f"协同作用增强 ({delta_synergy:.4f})")
    elif delta_synergy < -0.05:
        explanation.append(f"协同作用减弱 ({delta_synergy:.4f})")
    
    if delta_conflict > 0.05:
        explanation.append(f"冲突减少 ({delta_conflict:.4f})")
    elif delta_conflict < -0.05:
        explanation.append(f"冲突增加 ({delta_conflict:.4f})")
    
    if delta_balance > 0.05:
        explanation.append(f"平衡度提升 ({delta_balance:.4f})")
    elif delta_balance < -0.05:
        explanation.append(f"平衡度下降 ({delta_balance:.4f})")
    
    # 角色匹配
    target_role = next((ing['role'] for ing in ingredients if ing['ingredient_id'] == target_ingredient['ingredient_id']), 'unknown')
    candidate_role = candidate_ingredient['role']
    
    if target_role == candidate_role:
        explanation.append(f"候选原料与目标原料角色相同 ({target_role})")
    else:
        explanation.append(f"候选原料角色与目标原料不同 ({candidate_role} vs {target_role})")
    
    # Canonical 信息
    target_canonical = target_ingredient.get('canonical_name', target_ingredient['ingredient_name'])
    candidate_canonical = candidate_ingredient.get('canonical_name', candidate_ingredient['ingredient_name'])
    
    if target_canonical != candidate_canonical:
        explanation.append(f"候选原料与目标原料属于不同的 canonical 类别 ({candidate_canonical} vs {target_canonical})")
    
    # 兼容性得分
    compatibility_score = candidate_ingredient.get('compatibility_score', 0)
    if compatibility_score > 0.7:
        explanation.append(f"候选原料与目标原料兼容性高 ({compatibility_score:.2f})")
    elif compatibility_score > 0.4:
        explanation.append(f"候选原料与目标原料兼容性中等 ({compatibility_score:.2f})")
    else:
        explanation.append(f"候选原料与目标原料兼容性较低 ({compatibility_score:.2f})")
    
    return " ".join(explanation)

def determine_acceptance(delta_sqe: float, threshold: float = 0.05) -> bool:
    """
    确定替代是否可接受
    """
    return delta_sqe > -threshold

def perform_substitution(recipe_id: int, target_ingredient_id: int):
    """
    执行原料替代推理
    
    返回:
    substitution_results: 替代结果列表
    substitution_details: 详细信息列表
    """
    # 加载 canonical 映射
    canonical_map = load_canonical_mapping()
    
    # 加载配方原料
    ingredients = load_recipe_ingredients(recipe_id)
    
    # 找到目标原料
    target_ingredient = next((ing for ing in ingredients if ing['ingredient_id'] == target_ingredient_id), None)
    if not target_ingredient:
        print(f"[ERROR] 配方 {recipe_id} 中未找到原料 {target_ingredient_id}")
        return [], []
    
    # 添加 canonical 信息到目标原料
    if target_ingredient_id in canonical_map:
        target_ingredient['canonical_id'] = canonical_map[target_ingredient_id]['canonical_id']
        target_ingredient['canonical_name'] = canonical_map[target_ingredient_id]['canonical_name']
    else:
        target_ingredient['canonical_id'] = None
        target_ingredient['canonical_name'] = target_ingredient['ingredient_name']
    
    print(f"[INFO] 目标原料: {target_ingredient['ingredient_name']} (canonical: {target_ingredient['canonical_name']}, 角色: {target_ingredient['role']})")
    
    # 加载候选替代原料
    candidate_ingredients = load_candidate_ingredients(target_ingredient_id, target_ingredient['role'], canonical_map)
    
    # 计算原始配方的 SQE 分数
    original_score = calculate_sqe_score(ingredients)
    print(f"[INFO] 原始配方 SQE 分数: {original_score['sqe_total']:.4f}")
    
    # 执行替代并计算新分数
    substitution_results = []
    substitution_details = []
    
    for candidate in candidate_ingredients:
        # 创建新的原料列表，替换目标原料
        new_ingredients = []
        for ing in ingredients:
            if ing['ingredient_id'] == target_ingredient_id:
                # 替换为候选原料，保持其他属性不变
                new_ing = ing.copy()
                new_ing['ingredient_id'] = candidate['ingredient_id']
                new_ing['ingredient_name'] = candidate['ingredient_name']
                # 添加 canonical 信息
                if 'canonical_id' in candidate:
                    new_ing['canonical_id'] = candidate['canonical_id']
                    new_ing['canonical_name'] = candidate['canonical_name']
                new_ingredients.append(new_ing)
            else:
                new_ingredients.append(ing)
        
        # 计算新配方的 SQE 分数
        new_score = calculate_sqe_score(new_ingredients)
        delta_sqe = new_score['sqe_total'] - original_score['sqe_total']
        
        # 生成解释
        explanation = generate_substitution_explanation(original_score, new_score, target_ingredient, candidate, ingredients)
        
        # 确定是否接受
        accept = determine_acceptance(delta_sqe)
        
        # 保存结果
        result = {
            'recipe_id': recipe_id,
            'target_ingredient_id': target_ingredient_id,
            'target_ingredient_name': target_ingredient['ingredient_name'],
            'target_canonical_name': target_ingredient['canonical_name'],
            'candidate_ingredient_id': candidate['ingredient_id'],
            'candidate_ingredient_name': candidate['ingredient_name'],
            'candidate_canonical_name': candidate.get('canonical_name', candidate['ingredient_name']),
            'original_sqe': original_score['sqe_total'],
            'new_sqe': new_score['sqe_total'],
            'delta_sqe': delta_sqe,
            'accept_or_reject': 'accept' if accept else 'reject',
            'explanation': explanation
        }
        substitution_results.append(result)
        
        # 详细信息
        detail = {
            'recipe_id': recipe_id,
            'target_ingredient': target_ingredient,
            'candidate_ingredient': candidate,
            'original_score': original_score,
            'new_score': new_score,
            'delta_sqe': delta_sqe,
            'accept_or_reject': 'accept' if accept else 'reject',
            'explanation': explanation
        }
        substitution_details.append(detail)
    
    # 按 delta_sqe 降序排序
    substitution_results.sort(key=lambda x: x['delta_sqe'], reverse=True)
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(Config.SUBSTITUTION_RESULTS_FILE), exist_ok=True)
    
    # 保存结果到 CSV 文件
    results_df = pd.DataFrame(substitution_results)
    results_df.to_csv(Config.SUBSTITUTION_RESULTS_FILE, index=False, encoding='utf-8')
    print(f"[INFO] 替代结果已保存到: {Config.SUBSTITUTION_RESULTS_FILE}")
    
    # 保存详细信息到 JSON 文件
    with open(Config.SUBSTITUTION_DETAILS_FILE, 'w', encoding='utf-8') as f:
        json.dump(substitution_details, f, ensure_ascii=False, indent=2, default=serialize_decimal)
    print(f"[INFO] 替代详细信息已保存到: {Config.SUBSTITUTION_DETAILS_FILE}")
    
    # 显示前 10 个替代建议
    print("\n[INFO] 前 10 个替代建议:")
    for i, result in enumerate(substitution_results[:10]):
        print(f"{i+1}. {result['candidate_ingredient_name']} (canonical: {result['candidate_canonical_name']}, ΔSQE: {result['delta_sqe']:.4f}, 状态: {result['accept_or_reject']})")
        print(f"   解释: {result['explanation']}")
        print()
    
    return substitution_results, substitution_details

def main():
    """
    主函数
    """
    print("开始原料替代推理...")
    
    # 设置最优权重
    set_optimal_weights()
    
    # 示例：使用配方 1 和原料 1 进行替代推理
    recipe_id = 1
    target_ingredient_id = 1
    
    perform_substitution(recipe_id, target_ingredient_id)

if __name__ == "__main__":
    main()
