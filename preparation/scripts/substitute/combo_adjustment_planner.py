# -*- coding: utf-8 -*-
"""
组合调整计划生成器

功能：
1. 生成组合调整的两步计划
2. 输出详细的计划信息
3. 与 batch 脚本集成
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.substitute.combo_adjustment_generator import generate_combo_adjustment_candidates, evaluate_candidates
from scripts.substitute.combo_adjustment_evaluator import ComboAdjustmentEvaluator

class ComboAdjustmentPlanner:
    """
    组合调整计划生成器类
    """
    
    def __init__(self):
        """
        初始化计划生成器
        """
        self.evaluator = ComboAdjustmentEvaluator(lambda_edit=0.01)
    
    def generate_plan(self, ingredients: List[Dict], target_ingredient: Dict, candidate: Dict) -> Optional[Dict]:
        """
        生成组合调整计划
        
        参数:
        ingredients: 原配方原料列表
        target_ingredient: 目标原料
        candidate: 单替代候选
        
        返回:
        组合调整计划
        """
        # print("[INFO] 生成组合调整计划...")
        
        # 生成组合调整候选计划
        candidates = generate_combo_adjustment_candidates(ingredients, target_ingredient, candidate)
        
        # 评估候选计划
        evaluated_candidates = self.evaluator.evaluate_candidates(candidates)
        
        # 选择最佳候选计划
        best_candidate = self._select_best_candidate(evaluated_candidates)
        
        if not best_candidate:
            # print("[INFO] 没有找到可接受的组合调整计划")
            return None
        
        # 生成计划
        plan = self._create_plan(best_candidate)
        
        return plan
    
    def _select_best_candidate(self, evaluated_candidates: List[Dict]) -> Optional[Dict]:
        """
        选择最佳候选计划
        
        参数:
        evaluated_candidates: 带评估结果的候选计划列表
        
        返回:
        最佳候选计划
        """
        # 过滤出可接受的候选计划
        accepted_candidates = [c for c in evaluated_candidates if c['evaluation']['combo_accept']]
        
        if not accepted_candidates:
            # 如果没有可接受的，返回 score_combo 最高的
            if evaluated_candidates:
                return evaluated_candidates[0]
            return None
        
        # 按 score_combo 降序排序，返回第一个
        accepted_candidates.sort(key=lambda x: x['evaluation']['score_combo'], reverse=True)
        return accepted_candidates[0]
    
    def _create_plan(self, candidate: Dict) -> Dict:
        """
        创建组合调整计划
        
        参数:
        candidate: 最佳候选计划
        
        返回:
        组合调整计划
        """
        eval_result = candidate['evaluation']
        
        # 第一步：单步替代
        step1 = {
            'action': 'replace',
            'target_ingredient': candidate['target_ingredient']['ingredient_name'],
            'target_ingredient_id': candidate['target_ingredient']['ingredient_id'],
            'replacement': candidate['candidate_ingredient']['ingredient_name'],
            'replacement_id': candidate['candidate_ingredient']['ingredient_id']
        }
        
        # 第二步：调整
        step2 = {
            'action': 'adjust_amount',
            'ingredient': candidate['adjusted_ingredient']['ingredient_name'],
            'ingredient_id': candidate['adjusted_ingredient']['ingredient_id'],
            'alpha': candidate['alpha']
        }
        
        # 计算与单步替代的比较
        delta_improvement = eval_result['delta_sqe_combo'] - eval_result['delta_sqe_single']
        
        # 生成计划
        plan = {
            'step1': step1,
            'step2': step2,
            'final_delta_sqe': eval_result['delta_sqe_combo'],
            'compared_with_single': delta_improvement,
            'single_delta_sqe': eval_result['delta_sqe_single'],
            'original_score': eval_result['original_score']['sqe_total'],
            'single_score': eval_result['single_score']['sqe_total'],
            'combo_score': eval_result['combo_score']['sqe_total'],
            'accept': eval_result['combo_accept'],
            'score_combo': eval_result['score_combo'],
            'lambda_edit': eval_result['lambda_edit']
        }
        
        # 添加详细信息
        plan['details'] = {
            'delta_synergy': candidate.get('delta_synergy', 0),
            'delta_conflict': candidate.get('delta_conflict', 0),
            'delta_balance': candidate.get('delta_balance', 0),
            'worst_dimension': candidate.get('worst_dimension', 'unknown')
        }
        
        return plan
    
    def generate_plans_for_recipe(self, recipe_id: int, target_ingredient_id: int) -> List[Dict]:
        """
        为指定配方和目标原料生成组合调整计划
        
        参数:
        recipe_id: 配方 ID
        target_ingredient_id: 目标原料 ID
        
        返回:
        组合调整计划列表
        """
        from scripts.substitute.combo_adjustment_utils import load_recipe_ingredients, load_canonical_mapping, load_candidate_ingredients
        
        # print(f"[INFO] 为配方 {recipe_id} 的原料 {target_ingredient_id} 生成组合调整计划...")
        
        # 加载配方原料
        ingredients = load_recipe_ingredients(recipe_id)
        
        # 找到目标原料
        target_ingredient = next((ing for ing in ingredients if ing['ingredient_id'] == target_ingredient_id), None)
        if not target_ingredient:
            print(f"[ERROR] 配方 {recipe_id} 中未找到原料 {target_ingredient_id}")
            return []
        
        # 加载 canonical 映射
        canonical_map = load_canonical_mapping()
        
        # 加载候选替代原料
        candidate_ingredients = load_candidate_ingredients(target_ingredient_id, target_ingredient['role'], canonical_map)
        
        # 为每个候选生成计划
        plans = []
        for candidate in candidate_ingredients[:5]:  # 只处理前 5 个候选
            plan = self.generate_plan(ingredients, target_ingredient, candidate)
            if plan:
                # 添加配方和原料信息
                plan['recipe_id'] = recipe_id
                plan['target_ingredient_id'] = target_ingredient_id
                plans.append(plan)
        
        # 按 final_delta_sqe 降序排序
        plans.sort(key=lambda x: x['final_delta_sqe'], reverse=True)
        
        return plans

def save_plans(plans: List[Dict], output_file: str):
    """
    保存组合调整计划
    
    参数:
    plans: 组合调整计划列表
    output_file: 输出文件路径
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 保存到 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(plans, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] 组合调整计划已保存到: {output_file}")

def print_plan(plan: Dict):
    """
    打印组合调整计划
    
    参数:
    plan: 组合调整计划
    """
    print("\n[INFO] 组合调整计划:")
    print(f"Step 1: {plan['step1']['target_ingredient']} -> {plan['step1']['replacement']}")
    print(f"Step 2: {plan['step2']['ingredient']} amount × {plan['step2']['alpha']}")
    print(f"Final: delta_sqe_total = {plan['final_delta_sqe']:.4f}")
    print(f"Compared with single replacement: 提升了 {plan['compared_with_single']:.4f}")
    print(f"Accept: {plan['accept']}")

def main():
    """
    主函数
    """
    print("开始生成组合调整计划...")
    
    # 创建计划生成器
    planner = ComboAdjustmentPlanner()
    
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
    
    # 生成计划
    plan = planner.generate_plan(sample_ingredients, target_ingredient, candidate)
    
    if plan:
        # 打印计划
        print_plan(plan)
        
        # 保存计划
        output_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "substitute", "combo_adjustment_plan.json")
        save_plans([plan], output_file)
    else:
        print("[INFO] 没有生成组合调整计划")

if __name__ == "__main__":
    main()
