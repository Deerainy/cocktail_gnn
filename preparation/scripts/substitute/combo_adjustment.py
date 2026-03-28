# -*- coding: utf-8 -*-
"""
组合调整方法（4.2）

功能：
1. 从单步替代结果开始，进行组合调整
2. 支持多种组合调整策略
3. 评估组合调整效果
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.substitute.combo_adjustment_utils import (
    load_optimal_params,
    set_optimal_weights,
    load_recipe_ingredients,
    load_canonical_mapping,
    load_candidate_ingredients,
    rank_candidates_by_compatibility,
    calculate_sqe_score,
    determine_acceptance
)
from scripts.substitute.ingredient_substitution import perform_substitution as perform_single_substitution

class Config:
    """配置类"""
    # 输出文件
    COMBO_ADJUSTMENT_RESULTS_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "substitute", "combo_adjustment_results.csv")
    COMBO_ADJUSTMENT_DETAILS_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "substitute", "combo_adjustment_details.json")

def get_single_substitution_results(recipe_id: int, target_ingredient_id: int) -> List[Dict]:
    """
    获取单步替代结果
    
    参数:
    recipe_id: 配方 ID
    target_ingredient_id: 目标原料 ID
    
    返回:
    单步替代结果列表
    """
    print(f"[INFO] 获取配方 {recipe_id} 中原料 {target_ingredient_id} 的单步替代结果...")
    
    # 直接调用 perform_substitution 函数获取结果
    results, _ = perform_single_substitution(recipe_id, target_ingredient_id)
    
    print(f"[INFO] 成功获取 {len(results)} 个单步替代结果")
    return results

def filter_candidates(results: List[Dict], top_n: int = 5) -> List[Dict]:
    """
    筛选候选替代方案
    
    参数:
    results: 单步替代结果列表
    top_n: 保留前 N 个结果
    
    返回:
    筛选后的候选列表
    """
    # 按 delta_sqe 降序排序
    sorted_results = sorted(results, key=lambda x: x['delta_sqe'], reverse=True)
    
    # 筛选可接受的或前 top_n 个结果
    filtered = []
    for result in sorted_results:
        if result['accept_or_reject'] == 'accept' or len(filtered) < top_n:
            filtered.append(result)
        if len(filtered) >= top_n:
            break
    
    print(f"[INFO] 筛选出 {len(filtered)} 个候选替代方案")
    return filtered

def generate_combo_adjustment_input(single_result: Dict, recipe_id: int, target_ingredient_id: int) -> Dict:
    """
    生成组合调整的输入
    
    参数:
    single_result: 单步替代结果
    recipe_id: 配方 ID
    target_ingredient_id: 目标原料 ID
    
    返回:
    组合调整输入
    """
    # 加载原始配方原料
    ingredients = load_recipe_ingredients(recipe_id)
    
    # 找到目标原料
    target_ingredient = next((ing for ing in ingredients if ing['ingredient_id'] == target_ingredient_id), None)
    if not target_ingredient:
        return None
    
    # 创建替代后的原料列表
    new_ingredients = []
    for ing in ingredients:
        if ing['ingredient_id'] == target_ingredient_id:
            # 替换为候选原料
            new_ing = ing.copy()
            new_ing['ingredient_id'] = single_result['candidate_ingredient_id']
            new_ing['ingredient_name'] = single_result['candidate_ingredient_name']
            # 添加 canonical 信息
            new_ing['canonical_name'] = single_result['candidate_canonical_name']
            new_ingredients.append(new_ing)
        else:
            new_ingredients.append(ing)
    
    # 计算各维度的 delta 值
    # 加载原始配方的 SQE 分数
    original_score = calculate_sqe_score(ingredients)
    # 加载替代后的 SQE 分数
    substituted_score = calculate_sqe_score(new_ingredients)
    
    # 计算 delta 值
    delta_synergy = substituted_score['synergy_normalized'] - original_score['synergy_normalized']
    delta_conflict = substituted_score['conflict_good'] - original_score['conflict_good']
    delta_balance = substituted_score['balance_normalized'] - original_score['balance_normalized']
    
    # 更新 single_result，添加 delta 值
    single_result_with_delta = single_result.copy()
    single_result_with_delta['delta_synergy'] = delta_synergy
    single_result_with_delta['delta_conflict'] = delta_conflict
    single_result_with_delta['delta_balance'] = delta_balance
    
    return {
        'recipe_id': recipe_id,
        'target_ingredient_id': target_ingredient_id,
        'target_ingredient': target_ingredient,
        'candidate_ingredient': {
            'ingredient_id': single_result['candidate_ingredient_id'],
            'ingredient_name': single_result['candidate_ingredient_name'],
            'canonical_name': single_result['candidate_canonical_name']
        },
        'original_ingredients': ingredients,
        'substituted_ingredients': new_ingredients,
        'single_substitution_result': single_result_with_delta
    }

def perform_combo_adjustment(recipe_id: int, target_ingredient_id: int, strategies: List[str] = None):
    """
    执行组合调整
    
    参数:
    recipe_id: 配方 ID
    target_ingredient_id: 目标原料 ID
    strategies: 组合调整策略列表
    """
    if strategies is None:
        strategies = ['ratio_adjustment', 'supplement_addition']
    
    print(f"[INFO] 开始组合调整: 配方 {recipe_id}, 原料 {target_ingredient_id}")
    
    # 1. 获取单步替代结果
    single_results = get_single_substitution_results(recipe_id, target_ingredient_id)
    if not single_results:
        print("[ERROR] 没有获取到单步替代结果")
        return
    
    # 2. 筛选候选方案
    filtered_candidates = filter_candidates(single_results)
    if not filtered_candidates:
        print("[ERROR] 没有筛选出候选替代方案")
        return
    
    # 3. 对每个候选方案进行组合调整
    combo_results = []
    combo_details = []
    
    for i, candidate in enumerate(filtered_candidates):
        print(f"\n[INFO] 处理第 {i+1}/{len(filtered_candidates)} 个候选方案: {candidate['candidate_ingredient_name']}")
        
        # 生成组合调整输入
        combo_input = generate_combo_adjustment_input(candidate, recipe_id, target_ingredient_id)
        if not combo_input:
            continue
        
        # 计算单步替代后的 SQE 分数
        substituted_score = calculate_sqe_score(combo_input['substituted_ingredients'])
        
        # 执行各种组合调整策略
        for strategy in strategies:
            print(f"[INFO] 应用策略: {strategy}")
            
            if strategy == 'ratio_adjustment':
                # 比例微调策略
                adjusted_results = apply_ratio_adjustment(combo_input)
                for result in adjusted_results:
                    combo_results.append(result)
                    combo_details.append({
                        'candidate': candidate,
                        'strategy': result['strategy'],
                        'result': result
                    })
            elif strategy == 'supplement_addition':
                # 补充添加策略
                adjusted_result = apply_supplement_addition(combo_input)
                if adjusted_result:
                    combo_results.append(adjusted_result)
                    combo_details.append({
                        'candidate': candidate,
                        'strategy': strategy,
                        'result': adjusted_result
                    })
            else:
                continue
    
    # 保存结果
    save_combo_adjustment_results(combo_results, combo_details)
    
    print(f"\n[INFO] 组合调整完成，共生成 {len(combo_results)} 个调整方案")

def get_adjustment_targets(combo_input: Dict) -> List[Dict]:
    """
    根据结构偏移类型选择修正对象
    
    参数:
    combo_input: 组合调整输入
    
    返回:
    修正对象列表，每个对象包含原料信息和建议的调整因子范围
    """
    # 获取单步替代结果
    single_result = combo_input['single_substitution_result']
    
    # 提取 delta 值
    delta_synergy = single_result.get('delta_synergy', 0)
    delta_conflict = single_result.get('delta_conflict', 0)
    delta_balance = single_result.get('delta_balance', 0)
    
    # 计算各维度的偏移程度（绝对值）
    abs_delta_synergy = abs(delta_synergy)
    abs_delta_conflict = abs(delta_conflict)
    abs_delta_balance = abs(delta_balance)
    
    # 确定最差的维度
    worst_dimension = max([('synergy', abs_delta_synergy), ('conflict', abs_delta_conflict), ('balance', abs_delta_balance)], key=lambda x: x[1])[0]
    
    print(f"[INFO] 最差维度: {worst_dimension}")
    print(f"[INFO] Delta values - synergy: {delta_synergy:.4f}, conflict: {delta_conflict:.4f}, balance: {delta_balance:.4f}")
    
    # 获取原料列表
    ingredients = combo_input['substituted_ingredients']
    target_role = combo_input['target_ingredient']['role']
    
    adjustment_targets = []
    
    if worst_dimension == 'balance':
        # Balance 最差，修酸甜相关节点
        print("[INFO] 平衡偏移，优先修正酸甜相关节点")
        
        if target_role == 'acid':
            # 目标是酸，优先改甜或修饰剂
            targets = [ing for ing in ingredients if ing['role'] in ['sweetener', 'modifier']]
        elif target_role == 'sweetener':
            # 目标是甜，优先改酸
            targets = [ing for ing in ingredients if ing['role'] == 'acid']
        elif target_role == 'modifier':
            # 目标是修饰剂，优先改酸或甜
            targets = [ing for ing in ingredients if ing['role'] in ['acid', 'sweetener']]
        elif target_role == 'base':
            # 目标是基酒，只改修饰剂
            targets = [ing for ing in ingredients if ing['role'] == 'modifier']
        else:
            # 其他角色，改酸甜
            targets = [ing for ing in ingredients if ing['role'] in ['acid', 'sweetener', 'modifier']]
        
        # 调整因子：平衡问题需要双向调整
        alpha_values = [0.85, 0.90, 1.10, 1.15]
        
    elif worst_dimension == 'conflict':
        # Conflict 最差，下调可能产生冲突的节点
        print("[INFO] 冲突增加，优先下调可能产生冲突的节点")
        
        # 优先试 modifier, other, bitters
        targets = [ing for ing in ingredients if ing['role'] in ['modifier', 'other', 'bitters']]
        
        # 调整因子：只下调
        alpha_values = [0.85, 0.90]
        
    elif worst_dimension == 'synergy':
        # Synergy 最差，上调支持型节点
        print("[INFO] 协同减弱，优先上调支持型节点")
        
        # 优先选择和目标原料 role 互补的节点
        if target_role == 'base':
            # 基酒的支持型节点：酸、甜、修饰剂
            targets = [ing for ing in ingredients if ing['role'] in ['acid', 'sweetener', 'modifier']]
        elif target_role == 'acid':
            # 酸的支持型节点：甜、修饰剂
            targets = [ing for ing in ingredients if ing['role'] in ['sweetener', 'modifier']]
        elif target_role == 'sweetener':
            # 甜的支持型节点：酸、修饰剂
            targets = [ing for ing in ingredients if ing['role'] in ['acid', 'modifier']]
        else:
            # 其他角色的支持型节点：酸、甜、修饰剂
            targets = [ing for ing in ingredients if ing['role'] in ['acid', 'sweetener', 'modifier']]
        
        # 调整因子：只上调
        alpha_values = [1.10, 1.15]
    
    # 如果没有找到合适的目标，使用默认目标
    if not targets:
        print("[INFO] 未找到合适的修正目标，使用默认目标")
        # 默认改同角色的原料
        targets = [ing for ing in ingredients if ing['role'] == target_role]
        # 默认调整因子
        alpha_values = [0.85, 0.90, 1.10, 1.15]
    
    # 构建修正目标列表
    for target in targets:
        adjustment_targets.append({
            'ingredient': target,
            'alpha_values': alpha_values
        })
    
    print(f"[INFO] 选择了 {len(adjustment_targets)} 个修正目标")
    for i, target in enumerate(adjustment_targets):
        print(f"[INFO] 目标 {i+1}: {target['ingredient']['ingredient_name']} (role: {target['ingredient']['role']}), 调整因子: {target['alpha_values']}")
    
    return adjustment_targets

def apply_ratio_adjustment(combo_input: Dict) -> List[Dict]:
    """
    应用比例微调策略
    
    参数:
    combo_input: 组合调整输入
    
    返回:
    调整结果列表
    """
    results = []
    try:
        # 获取替代后的原料列表
        ingredients = combo_input['substituted_ingredients']
        
        # 计算原始 SQE 分数
        original_score = calculate_sqe_score(ingredients)
        
        # 根据结构偏移类型选择修正对象
        adjustment_targets = get_adjustment_targets(combo_input)
        
        for target_info in adjustment_targets:
            target = target_info['ingredient']
            alpha_values = target_info['alpha_values']
            
            for alpha in alpha_values:
                # 创建调整后的原料列表
                adjusted_ingredients = []
                for ing in ingredients:
                    new_ing = ing.copy()
                    if ing['ingredient_id'] == target['ingredient_id']:
                        # 应用调整因子
                        if new_ing['amount'] is not None:
                            new_ing['amount'] *= alpha
                    adjusted_ingredients.append(new_ing)
                
                # 计算调整后的 SQE 分数
                adjusted_score = calculate_sqe_score(adjusted_ingredients)
                delta_sqe = adjusted_score['sqe_total'] - original_score['sqe_total']
                
                # 确定是否接受
                accept = determine_acceptance(delta_sqe)
                
                results.append({
                    'recipe_id': combo_input['recipe_id'],
                    'target_ingredient_id': combo_input['target_ingredient_id'],
                    'strategy': f'ratio_adjustment_{alpha}',
                    'adjusted_ingredient_id': target['ingredient_id'],
                    'adjusted_ingredient_name': target['ingredient_name'],
                    'alpha': alpha,
                    'original_sqe': original_score['sqe_total'],
                    'adjusted_sqe': adjusted_score['sqe_total'],
                    'delta_sqe': delta_sqe,
                    'accept': accept,
                    'adjusted_ingredients': adjusted_ingredients
                })
    except Exception as e:
        print(f"[ERROR] 应用比例微调策略失败: {e}")
    
    return results

def apply_supplement_addition(combo_input: Dict) -> Optional[Dict]:
    """
    应用补充添加策略
    
    参数:
    combo_input: 组合调整输入
    
    返回:
    调整结果
    """
    try:
        # 获取替代后的原料列表
        ingredients = combo_input['substituted_ingredients']
        
        # 计算原始 SQE 分数
        original_score = calculate_sqe_score(ingredients)
        
        # 添加补充原料
        # 这里简单实现为添加一个同角色的辅助原料
        adjusted_ingredients = ingredients.copy()
        
        # 查找同角色的其他原料作为补充
        target_role = combo_input['target_ingredient']['role']
        canonical_map = load_canonical_mapping()
        
        # 加载候选原料
        candidates = load_candidate_ingredients(
            combo_input['candidate_ingredient']['ingredient_id'],
            target_role,
            canonical_map
        )
        
        if candidates:
            # 选择第一个候选作为补充原料
            supplement = candidates[0]
            
            # 创建补充原料
            supplement_ing = {
                'ingredient_id': supplement['ingredient_id'],
                'ingredient_name': supplement['ingredient_name'],
                'amount': 5.0,  # 少量添加
                'unit': 'ml',
                'role': target_role,
                'line_no': len(adjusted_ingredients) + 1,
                'raw_text': supplement['ingredient_name']
            }
            
            adjusted_ingredients.append(supplement_ing)
        
        # 计算调整后的 SQE 分数
        adjusted_score = calculate_sqe_score(adjusted_ingredients)
        delta_sqe = adjusted_score['sqe_total'] - original_score['sqe_total']
        
        # 确定是否接受
        accept = determine_acceptance(delta_sqe)
        
        return {
            'recipe_id': combo_input['recipe_id'],
            'target_ingredient_id': combo_input['target_ingredient_id'],
            'strategy': 'supplement_addition',
            'original_sqe': original_score['sqe_total'],
            'adjusted_sqe': adjusted_score['sqe_total'],
            'delta_sqe': delta_sqe,
            'accept': accept,
            'adjusted_ingredients': adjusted_ingredients
        }
    except Exception as e:
        print(f"[ERROR] 应用补充添加策略失败: {e}")
        return None

def save_combo_adjustment_results(results: List[Dict], details: List[Dict]):
    """
    保存组合调整结果
    
    参数:
    results: 组合调整结果列表
    details: 详细信息列表
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(Config.COMBO_ADJUSTMENT_RESULTS_FILE), exist_ok=True)
    
    # 保存结果到 CSV 文件
    if results:
        results_df = pd.DataFrame(results)
        # 只保存关键列
        key_columns = ['recipe_id', 'target_ingredient_id', 'strategy', 'adjusted_ingredient_id', 'adjusted_ingredient_name', 'alpha', 'original_sqe', 'adjusted_sqe', 'delta_sqe', 'accept']
        # 确保所有列都存在
        for col in key_columns:
            if col not in results_df.columns:
                results_df[col] = None
        results_df = results_df[key_columns]
        results_df.to_csv(Config.COMBO_ADJUSTMENT_RESULTS_FILE, index=False, encoding='utf-8')
        print(f"[INFO] 组合调整结果已保存到: {Config.COMBO_ADJUSTMENT_RESULTS_FILE}")
    
    # 保存详细信息到 JSON 文件
    if details:
        with open(Config.COMBO_ADJUSTMENT_DETAILS_FILE, 'w', encoding='utf-8') as f:
            json.dump(details, f, ensure_ascii=False, indent=2)
        print(f"[INFO] 组合调整详细信息已保存到: {Config.COMBO_ADJUSTMENT_DETAILS_FILE}")

def main():
    """
    主函数
    """
    print("开始组合调整...")
    
    # 设置最优权重
    set_optimal_weights()
    
    # 示例：使用配方 1 和原料 1 进行组合调整
    recipe_id = 1
    target_ingredient_id = 1
    
    perform_combo_adjustment(recipe_id, target_ingredient_id)

if __name__ == "__main__":
    main()
