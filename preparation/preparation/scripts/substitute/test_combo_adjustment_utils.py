# -*- coding: utf-8 -*-
"""
测试组合调整工具函数
"""

import sys
from pathlib import Path

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

def test_all_functions():
    """
    测试所有核心函数
    """
    print("开始测试组合调整工具函数...")
    
    # 测试 1: 加载最优参数
    print("\n1. 测试加载最优参数...")
    params = load_optimal_params()
    print(f"   成功加载参数: {params.keys()}")
    print(f"   SQE 权重: {params.get('sqe', {})}")
    
    # 测试 2: 设置最优权重
    print("\n2. 测试设置最优权重...")
    set_optimal_weights()
    
    # 测试 3: 加载配方原料
    print("\n3. 测试加载配方原料...")
    try:
        ingredients = load_recipe_ingredients(1)  # 使用配方 ID 1 作为测试
        print(f"   成功加载 {len(ingredients)} 个原料")
        if ingredients:
            print(f"   第一个原料: {ingredients[0]['ingredient_name']}")
    except Exception as e:
        print(f"   加载配方原料失败: {e}")
    
    # 测试 4: 加载 canonical 映射
    print("\n4. 测试加载 canonical 映射...")
    try:
        canonical_map = load_canonical_mapping()
        print(f"   成功加载 {len(canonical_map)} 个 canonical 映射")
        # 打印前 5 个映射
        for i, (k, v) in enumerate(list(canonical_map.items())[:5]):
            print(f"   {i+1}. {k} -> {v['canonical_name']}")
    except Exception as e:
        print(f"   加载 canonical 映射失败: {e}")
    
    # 测试 5: 加载候选原料
    print("\n5. 测试加载候选原料...")
    try:
        canonical_map = load_canonical_mapping()
        if canonical_map:
            # 使用第一个原料 ID 作为测试
            test_ingredient_id = list(canonical_map.keys())[0]
            candidates = load_candidate_ingredients(test_ingredient_id, 'base_spirit', canonical_map)
            print(f"   成功加载 {len(candidates)} 个候选原料")
            if candidates:
                print(f"   第一个候选: {candidates[0]['ingredient_name']} (兼容性得分: {candidates[0].get('compatibility_score', 0):.4f})")
    except Exception as e:
        print(f"   加载候选原料失败: {e}")
    
    # 测试 6: 计算 SQE 分数
    print("\n6. 测试计算 SQE 分数...")
    try:
        ingredients = load_recipe_ingredients(1)
        if ingredients:
            score = calculate_sqe_score(ingredients)
            print(f"   成功计算 SQE 分数: {score['sqe_total']:.4f}")
            print(f"   协同分数: {score['synergy_score']:.4f}")
            print(f"   冲突分数: {score['conflict_score']:.4f}")
            print(f"   平衡分数: {score['final_balance_score']:.4f}")
    except Exception as e:
        print(f"   计算 SQE 分数失败: {e}")
    
    # 测试 7: 测试替代接受判断
    print("\n7. 测试替代接受判断...")
    test_cases = [0.1, -0.01, -0.05, -0.1]
    for delta in test_cases:
        accept = determine_acceptance(delta)
        print(f"   ΔSQE = {delta:.4f} -> {'接受' if accept else '拒绝'}")
    
    print("\n所有测试完成！")

if __name__ == "__main__":
    test_all_functions()
