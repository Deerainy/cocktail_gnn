# -*- coding: utf-8 -*-
"""
组合调整候选生成器

功能：
1. 给定一个单步替代方案 (t→s)，生成一组 4.2 候选计划
2. 根据结构偏移类型选择修正对象
3. 生成不同的 amount 调整因子
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.substitute.combo_adjustment_utils import calculate_sqe_score

def normalize_role(role: str) -> str:
    """
    归一化原料角色
    
    参数:
    role: 原料角色
    
    返回:
    归一化后的角色
    """
    if role in {'base', 'base_spirit'}:
        return 'base_spirit'
    return role

def generate_combo_adjustment_candidates(ingredients: List[Dict], target_ingredient: Dict, candidate: Dict) -> List[Dict]:
    """
    生成组合调整候选计划
    
    参数:
    ingredients: 原配方原料列表
    target_ingredient: 目标原料
    candidate: 单替代候选
    
    返回:
    组合调整候选计划列表
    """
    # print("[INFO] 生成组合调整候选计划...")
    
    # 1. 应用单步替代 t -> s
    substituted_ingredients = []
    for ing in ingredients:
        if ing['ingredient_id'] == target_ingredient['ingredient_id']:
            # 替换为候选原料
            new_ing = ing.copy()
            new_ing['ingredient_id'] = candidate['ingredient_id']
            new_ing['ingredient_name'] = candidate['ingredient_name']
            # 添加 canonical 信息
            if 'canonical_id' in candidate:
                new_ing['canonical_id'] = candidate['canonical_id']
                new_ing['canonical_name'] = candidate['canonical_name']
            substituted_ingredients.append(new_ing)
        else:
            substituted_ingredients.append(ing)
    
    # 2. 计算单替代后的分数
    original_score = calculate_sqe_score(ingredients)
    substituted_score = calculate_sqe_score(substituted_ingredients)
    
    # 3. 计算各维度的 delta 值
    delta_synergy = substituted_score['synergy_normalized'] - original_score['synergy_normalized']
    delta_conflict = substituted_score['conflict_good'] - original_score['conflict_good']
    delta_balance = substituted_score['balance_normalized'] - original_score['balance_normalized']
    
    # print(f"[INFO] Delta values - synergy: {delta_synergy:.4f}, conflict: {delta_conflict:.4f}, balance: {delta_balance:.4f}")
    
    # 4. 确定最差的维度
    deltas = {
        'synergy': delta_synergy,
        'conflict': delta_conflict,
        'balance': delta_balance
    }
    worst_dimension = min(deltas.items(), key=lambda x: x[1])[0]
    # print(f"[INFO] 最差维度: {worst_dimension}")
    
    # 5. 按规则挑出可修正原料
    adjustment_targets = get_adjustment_targets(substituted_ingredients, target_ingredient['role'], worst_dimension)
    
    # 6. 生成候选计划
    candidates = []
    for target_info in adjustment_targets:
        target = target_info['ingredient']
        alpha_values = target_info['alpha_values']
        
        for alpha in alpha_values:
            # 创建调整后的原料列表
            adjusted_ingredients = []
            for ing in substituted_ingredients:
                new_ing = ing.copy()
                if ing['ingredient_id'] == target['ingredient_id']:
                    # 应用调整因子
                    if new_ing['amount'] is not None:
                        new_ing['amount'] *= alpha
                adjusted_ingredients.append(new_ing)
            
            # 创建候选计划
            candidate_plan = {
                'original_ingredients': ingredients,
                'substituted_ingredients': substituted_ingredients,
                'adjusted_ingredients': adjusted_ingredients,
                'target_ingredient': target_ingredient,
                'candidate_ingredient': candidate,
                'adjusted_ingredient': target,
                'alpha': alpha,
                'original_score': original_score,
                'substituted_score': substituted_score,
                'delta_synergy': delta_synergy,
                'delta_conflict': delta_conflict,
                'delta_balance': delta_balance,
                'worst_dimension': worst_dimension
            }
            
            candidates.append(candidate_plan)
    
    # print(f"[INFO] 生成了 {len(candidates)} 个组合调整候选计划")
    return candidates

def get_adjustment_targets(ingredients: List[Dict], target_role: str, worst_dimension: str) -> List[Dict]:
    """
    根据结构偏移类型选择修正对象
    
    参数:
    ingredients: 替代后的原料列表
    target_role: 目标原料角色
    worst_dimension: 最差维度
    
    返回:
    修正对象列表，每个对象包含原料信息和建议的调整因子范围
    """
    adjustment_targets = []
    
    # 归一化目标原料角色
    normalized_target_role = normalize_role(target_role)
    
    if worst_dimension == 'balance':
        # Balance 最差，修酸甜相关节点
        # print("[INFO] 平衡偏移，优先修正酸甜相关节点")
        
        if normalized_target_role == 'acid':
            # 目标是酸，优先改甜或修饰剂
            targets = [ing for ing in ingredients if ing['role'] in ['sweetener', 'modifier']]
        elif normalized_target_role == 'sweetener':
            # 目标是甜，优先改酸
            targets = [ing for ing in ingredients if ing['role'] == 'acid']
        elif normalized_target_role == 'modifier':
            # 目标是修饰剂，优先改酸或甜
            targets = [ing for ing in ingredients if ing['role'] in ['acid', 'sweetener']]
        elif normalized_target_role == 'base_spirit':
            # 目标是基酒，只改修饰剂
            targets = [ing for ing in ingredients if ing['role'] == 'modifier']
        else:
            # 其他角色，改酸甜
            targets = [ing for ing in ingredients if ing['role'] in ['acid', 'sweetener', 'modifier']]
        
        # 调整因子：平衡问题需要双向调整，扩展范围
        alpha_values = [0.80, 0.85, 0.90, 0.95, 1.05, 1.10, 1.15, 1.20]
        
    elif worst_dimension == 'conflict':
        # Conflict 最差，下调可能产生冲突的节点
        # print("[INFO] 冲突增加，优先下调可能产生冲突的节点")
        
        # 优先试 modifier, other, bitters
        targets = [ing for ing in ingredients if ing['role'] in ['modifier', 'other', 'bitters']]
        
        # 调整因子：只下调，扩展范围
        alpha_values = [0.75, 0.80, 0.85, 0.90, 0.95]
        
    elif worst_dimension == 'synergy':
        # Synergy 最差，上调支持型节点
        # print("[INFO] 协同减弱，优先上调支持型节点")
        
        # 优先选择和目标原料 role 互补的节点
        if normalized_target_role == 'base_spirit':
            # 基酒的支持型节点：酸、甜、修饰剂
            targets = [ing for ing in ingredients if ing['role'] in ['acid', 'sweetener', 'modifier']]
        elif normalized_target_role == 'acid':
            # 酸的支持型节点：甜、修饰剂
            targets = [ing for ing in ingredients if ing['role'] in ['sweetener', 'modifier']]
        elif normalized_target_role == 'sweetener':
            # 甜的支持型节点：酸、修饰剂
            targets = [ing for ing in ingredients if ing['role'] in ['acid', 'modifier']]
        else:
            # 其他角色的支持型节点：酸、甜、修饰剂
            targets = [ing for ing in ingredients if ing['role'] in ['acid', 'sweetener', 'modifier']]
        
        # 调整因子：只上调，扩展范围
        alpha_values = [1.05, 1.10, 1.15, 1.20, 1.25]
    
    # 如果没有找到合适的目标，使用默认目标
    if not targets:
        # print("[INFO] 未找到合适的修正目标，使用默认目标")
        # 默认改同角色的原料
        targets = [ing for ing in ingredients if normalize_role(ing['role']) == normalized_target_role]
        # 默认调整因子
        alpha_values = [0.85, 0.90, 1.10, 1.15]
    
    # 构建修正目标列表，过滤掉 amount 为 None 的原料
    for target in targets:
        if target.get('amount') is not None:
            adjustment_targets.append({
                'ingredient': target,
                'alpha_values': alpha_values
            })
    
    # print(f"[INFO] 选择了 {len(adjustment_targets)} 个修正目标")
    # for i, target in enumerate(adjustment_targets):
    #     print(f"[INFO] 目标 {i+1}: {target['ingredient']['ingredient_name']} (role: {target['ingredient']['role']}), 调整因子: {target['alpha_values']}")
    
    return adjustment_targets

def evaluate_candidates(candidates: List[Dict]) -> List[Dict]:
    """
    评估组合调整候选计划
    
    参数:
    candidates: 组合调整候选计划列表
    
    返回:
    带评估结果的候选计划列表
    """
    evaluated_candidates = []
    
    for candidate in candidates:
        # 计算调整后的 SQE 分数
        adjusted_score = calculate_sqe_score(candidate['adjusted_ingredients'])
        delta_sqe = adjusted_score['sqe_total'] - candidate['original_score']['sqe_total']
        
        # 确定是否接受
        accept = delta_sqe > -0.05
        
        # 更新候选计划
        candidate['adjusted_score'] = adjusted_score
        candidate['delta_sqe'] = delta_sqe
        candidate['accept'] = accept
        
        evaluated_candidates.append(candidate)
    
    # 按 delta_sqe 降序排序
    evaluated_candidates.sort(key=lambda x: x['delta_sqe'], reverse=True)
    
    return evaluated_candidates

def save_candidates(candidates: List[Dict], output_file: str):
    """
    保存组合调整候选计划
    
    参数:
    candidates: 组合调整候选计划列表
    output_file: 输出文件路径
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 保存到 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] 组合调整候选计划已保存到: {output_file}")

def main():
    """
    主函数
    """
    print("开始生成组合调整候选计划...")
    
    # 示例原料列表
    sample_ingredients = [
        {
            'ingredient_id': 1,
            'ingredient_name': 'mezcal',
            'amount': 50.0,
            'unit': 'ml',
            'role': 'base_spirit',
            'line_no': 1,
            'raw_text': 'mezcal'
        },
        {
            'ingredient_id': 2,
            'ingredient_name': 'hibiscus simple syrup',
            'amount': 15.0,
            'unit': 'ml',
            'role': 'sweetener',
            'line_no': 2,
            'raw_text': 'hibiscus simple syrup'
        },
        {
            'ingredient_id': 3,
            'ingredient_name': 'lime juice',
            'amount': 25.0,
            'unit': 'ml',
            'role': 'acid',
            'line_no': 3,
            'raw_text': 'lime juice'
        },
        {
            'ingredient_id': 4,
            'ingredient_name': 'soda water',
            'amount': 100.0,
            'unit': 'ml',
            'role': 'modifier',
            'line_no': 4,
            'raw_text': 'soda water'
        }
    ]
    
    # 目标原料
    target_ingredient = sample_ingredients[0]
    
    # 单替代候选
    candidate = {
        'ingredient_id': 17,
        'ingredient_name': 'barsol primero quebranta pisco',
        'canonical_id': 17,
        'canonical_name': 'pisco',
        'role': 'base_spirit'
    }
    
    # 生成组合调整候选计划
    candidates = generate_combo_adjustment_candidates(sample_ingredients, target_ingredient, candidate)
    
    # 评估候选计划
    evaluated_candidates = evaluate_candidates(candidates)
    
    # 保存结果
    output_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "substitute", "combo_adjustment_candidates.json")
    save_candidates(evaluated_candidates, output_file)
    
    # 显示前 5 个候选计划
    print("\n[INFO] 前 5 个组合调整候选计划:")
    for i, candidate in enumerate(evaluated_candidates[:5]):
        print(f"{i+1}. 调整 {candidate['adjusted_ingredient']['ingredient_name']} (α={candidate['alpha']}), ΔSQE: {candidate['delta_sqe']:.4f}, 状态: {'接受' if candidate['accept'] else '拒绝'}")

if __name__ == "__main__":
    main()
