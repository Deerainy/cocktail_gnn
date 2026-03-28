# -*- coding: utf-8 -*-
"""
组合调整评估器

功能：
1. 评估组合调整方案的效果
2. 计算各种 SQE 分数和 delta 值
3. 应用复杂度惩罚
4. 确定是否接受组合调整
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.substitute.combo_adjustment_utils import calculate_sqe_score

class ComboAdjustmentEvaluator:
    """
    组合调整评估器类
    """
    
    def __init__(self, lambda_edit: float = 0.01):
        """
        初始化评估器
        
        参数:
        lambda_edit: 复杂度惩罚因子
        """
        self.lambda_edit = lambda_edit
    
    def evaluate(self, original_ingredients: List[Dict], substituted_ingredients: List[Dict], adjusted_ingredients: List[Dict]) -> Dict:
        """
        评估组合调整方案
        
        参数:
        original_ingredients: 原始配方原料列表
        substituted_ingredients: 单步替代后的原料列表
        adjusted_ingredients: 组合调整后的原料列表
        
        返回:
        评估结果
        """
        # print("[INFO] 评估组合调整方案...")
        
        # 计算原始配方的 SQE 分数
        old_score = calculate_sqe_score(original_ingredients)
        # print(f"[INFO] 原始配方 SQE 分数: {old_score['sqe_total']:.4f}")
        
        # 计算单步替代后的 SQE 分数
        single_score = calculate_sqe_score(substituted_ingredients)
        # print(f"[INFO] 单步替代后 SQE 分数: {single_score['sqe_total']:.4f}")
        
        # 计算组合调整后的 SQE 分数
        combo_score = calculate_sqe_score(adjusted_ingredients)
        # print(f"[INFO] 组合调整后 SQE 分数: {combo_score['sqe_total']:.4f}")
        
        # 计算 delta 值
        delta_sqe_single = single_score['sqe_total'] - old_score['sqe_total']
        delta_sqe_combo = combo_score['sqe_total'] - old_score['sqe_total']
        
        # print(f"[INFO] ΔSQE_single: {delta_sqe_single:.4f}")
        # print(f"[INFO] ΔSQE_combo: {delta_sqe_combo:.4f}")
        
        # 应用复杂度惩罚
        score_combo = delta_sqe_combo - self.lambda_edit
        # print(f"[INFO] 应用复杂度惩罚后 score_combo: {score_combo:.4f}")
        
        # 确定单步替代是否可接受
        single_accept = delta_sqe_single > -0.05
        # print(f"[INFO] 单步替代是否可接受: {single_accept}")
        
        # 确定组合调整是否可接受
        combo_accept = self._determine_acceptance(delta_sqe_single, delta_sqe_combo, score_combo, single_accept)
        # print(f"[INFO] 组合调整是否可接受: {combo_accept}")
        
        # 生成评估结果
        result = {
            'original_score': old_score,
            'single_score': single_score,
            'combo_score': combo_score,
            'delta_sqe_single': delta_sqe_single,
            'delta_sqe_combo': delta_sqe_combo,
            'score_combo': score_combo,
            'single_accept': single_accept,
            'combo_accept': combo_accept,
            'lambda_edit': self.lambda_edit
        }
        
        return result
    
    def _determine_acceptance(self, delta_sqe_single: float, delta_sqe_combo: float, score_combo: float, single_accept: bool) -> bool:
        """
        确定组合调整是否可接受
        
        接受规则：
        1. 如果 combo_score 比 single_score 高（放宽为只要有提升）
        2. 或者 combo 把原本 reject 的 single 替代修成了 accept
        3. 或者 combo 本身的 delta_sqe_combo > -0.03（比单步替代的阈值更宽松）
        
        参数:
        delta_sqe_single: 单步替代的 SQE 变化
        delta_sqe_combo: 组合调整的 SQE 变化
        score_combo: 应用复杂度惩罚后的组合调整分数
        single_accept: 单步替代是否可接受
        
        返回:
        是否接受组合调整
        """
        # 规则 1: combo_score 比 single_score 高（放宽为只要有提升）
        rule1 = score_combo > delta_sqe_single
        
        # 规则 2: combo 把原本 reject 的 single 替代修成了 accept
        rule2 = not single_accept and (delta_sqe_combo > -0.05)
        
        # 规则 3: combo 本身可接受 (delta_sqe_combo > -0.05 与单步替代阈值一致)
        rule3 = delta_sqe_combo > -0.05
        
        # print(f"[INFO] 规则 1 (combo 比 single 高): {rule1}")
        # print(f"[INFO] 规则 2 (把 reject 修成 accept): {rule2}")
        # print(f"[INFO] 规则 3 (combo 本身可接受): {rule3}")
        
        return rule1 or rule2 or rule3
    
    def evaluate_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """
        评估多个组合调整候选计划
        
        参数:
        candidates: 组合调整候选计划列表
        
        返回:
        带评估结果的候选计划列表
        """
        evaluated_candidates = []
        
        for candidate in candidates:
            # 评估组合调整方案
            result = self.evaluate(
                candidate['original_ingredients'],
                candidate['substituted_ingredients'],
                candidate['adjusted_ingredients']
            )
            
            # 更新候选计划
            candidate['evaluation'] = result
            evaluated_candidates.append(candidate)
        
        # 按 score_combo 降序排序
        evaluated_candidates.sort(key=lambda x: x['evaluation']['score_combo'], reverse=True)
        
        return evaluated_candidates

def load_candidates(input_file: str) -> List[Dict]:
    """
    加载组合调整候选计划
    
    参数:
    input_file: 输入文件路径
    
    返回:
    组合调整候选计划列表
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        candidates = json.load(f)
    
    print(f"[INFO] 加载了 {len(candidates)} 个组合调整候选计划")
    return candidates

def save_evaluations(evaluations: List[Dict], output_file: str):
    """
    保存评估结果
    
    参数:
    evaluations: 带评估结果的候选计划列表
    output_file: 输出文件路径
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 保存到 JSON 文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(evaluations, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] 评估结果已保存到: {output_file}")

def main():
    """
    主函数
    """
    print("开始评估组合调整方案...")
    
    # 加载组合调整候选计划
    input_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "substitute", "combo_adjustment_candidates.json")
    candidates = load_candidates(input_file)
    
    # 创建评估器
    evaluator = ComboAdjustmentEvaluator(lambda_edit=0.01)
    
    # 评估候选计划
    evaluated_candidates = evaluator.evaluate_candidates(candidates)
    
    # 保存评估结果
    output_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "substitute", "combo_adjustment_evaluations.json")
    save_evaluations(evaluated_candidates, output_file)
    
    # 显示前 5 个评估结果
    print("\n[INFO] 前 5 个评估结果:")
    for i, candidate in enumerate(evaluated_candidates[:5]):
        eval_result = candidate['evaluation']
        print(f"{i+1}. 调整 {candidate['adjusted_ingredient']['ingredient_name']} (α={candidate['alpha']})")
        print(f"   ΔSQE_single: {eval_result['delta_sqe_single']:.4f}, ΔSQE_combo: {eval_result['delta_sqe_combo']:.4f}")
        print(f"   score_combo: {eval_result['score_combo']:.4f}, 单步接受: {eval_result['single_accept']}, 组合接受: {eval_result['combo_accept']}")

if __name__ == "__main__":
    main()
