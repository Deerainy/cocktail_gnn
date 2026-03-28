# -*- coding: utf-8 -*-
"""
Balance 评分器参数验证脚本

功能：
1. 验证优化得到的 balance 评分器参数
2. 使用更多的食谱进行评估
3. 计算不同扰动类型的性能
4. 输出详细的验证结果
"""

import os
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
from typing import List, Dict, Tuple, Optional, Any

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_script_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 数据库导入
from src.db import get_engine
from sqlalchemy import text

# 导入 balance 评分器
from scripts.SQE.phase_A.sqe_scorer_balance import calculate_balance_score_from_ingredients

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 验证参数
    MAX_RECIPES = 100  # 最大评估食谱数量
    
    # 输入输出
    OUTPUT_FILE = os.path.join(_project_root, "data", "balance_param_validation_results.csv")
    
    # 扰动类型
    BALANCE_PERTURB_TYPES = [
        "balance_break_flavor_balance",
        "balance_break_role_balance",
        "balance_remove_key_role"
    ]

# =========================================================
# 数据加载函数
# =========================================================

def load_recipe_ids() -> List[int]:
    """
    从数据库加载 recipe_id 列表
    """
    engine = get_engine()
    sql = text("""
    SELECT DISTINCT recipe_id
    FROM recipe_ingredient
    WHERE recipe_id IN (
        SELECT recipe_id
        FROM recipe_ingredient
        GROUP BY recipe_id
        HAVING COUNT(*) >= 3
    )
    LIMIT 200
    """)
    
    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()
    
    recipe_ids = [row["recipe_id"] for row in rows]
    print(f"[INFO] 加载了 {len(recipe_ids)} 个食谱 ID")
    return recipe_ids

def load_recipe_ingredients() -> pd.DataFrame:
    """
    加载所有食谱的原料信息
    """
    engine = get_engine()
    sql = text("""
    SELECT recipe_id, ingredient_id, line_no, amount, unit, role, raw_text
    FROM recipe_ingredient
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条原料信息")
    return df

# =========================================================
# 扰动生成函数
# =========================================================

def get_recipe_ingredients(recipe_id: int, ingredients_df: pd.DataFrame) -> List[Dict]:
    """
    获取指定食谱的原料列表
    """
    recipe_ingredients = ingredients_df[ingredients_df['recipe_id'] == recipe_id]
    return recipe_ingredients.to_dict('records')

def generate_balance_perturbation(recipe_id: int, ingredients_df: pd.DataFrame) -> Optional[Tuple[List[Dict], str]]:
    """
    生成 balance 相关的扰动
    """
    # 获取原始食谱的原料
    original_ingredients = get_recipe_ingredients(recipe_id, ingredients_df)
    if len(original_ingredients) < 3:
        return None
    
    # 随机选择扰动类型
    import random
    perturb_type = random.choice(Config.BALANCE_PERTURB_TYPES)
    perturbed_ingredients = [ing.copy() for ing in original_ingredients]
    
    if perturb_type == "balance_break_flavor_balance":
        # 破坏风味平衡：添加多个相同类型的原料
        # 统计当前原料的角色分布
        role_counts = {}
        for ing in perturbed_ingredients:
            role = ing['role'].lower()
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # 选择出现次数最多的角色
        if role_counts:
            most_common_role = max(role_counts, key=role_counts.get)
            # 复制该角色的一个原料并添加到食谱中
            role_ingredients = [ing for ing in perturbed_ingredients if ing['role'].lower() == most_common_role]
            if role_ingredients:
                ingredient_to_duplicate = random.choice(role_ingredients)
                new_ingredient = ingredient_to_duplicate.copy()
                new_ingredient['line_no'] = len(perturbed_ingredients) + 1
                new_ingredient['raw_text'] = f"1 oz {new_ingredient['raw_text']}"
                perturbed_ingredients.append(new_ingredient)
            else:
                return None
        else:
            return None
    
    elif perturb_type == "balance_break_role_balance":
        # 破坏角色平衡：添加多个 modifier
        # 统计当前原料的角色分布
        modifier_count = sum(1 for ing in perturbed_ingredients if 'modifier' in ing['role'].lower())
        # 添加多个 modifier
        for i in range(3):  # 添加 3 个 modifier
            # 选择一个现有的原料作为模板
            if perturbed_ingredients:
                template_ingredient = random.choice(perturbed_ingredients)
                new_ingredient = template_ingredient.copy()
                new_ingredient['role'] = 'modifier'
                new_ingredient['line_no'] = len(perturbed_ingredients) + 1
                new_ingredient['raw_text'] = f"1 oz Modifier {i+1}"
                perturbed_ingredients.append(new_ingredient)
            else:
                return None
    
    else:  # balance_remove_key_role
        # 移除关键角色：移除 base、acid 或 sweetener
        key_roles = ['base', 'acid', 'sweetener']
        key_ingredients = []
        for ing in perturbed_ingredients:
            for key_role in key_roles:
                if key_role in ing['role'].lower():
                    key_ingredients.append(ing)
                    break
        
        if len(key_ingredients) > 1:  # 确保至少保留一个关键角色
            ingredient_to_remove = random.choice(key_ingredients)
            # 移除原料
            perturbed_ingredients = [ing for ing in perturbed_ingredients if ing['line_no'] != ingredient_to_remove['line_no']]
            # 重新编号 line_no
            for i, ing in enumerate(perturbed_ingredients, 1):
                ing['line_no'] = i
        else:
            return None
    
    return perturbed_ingredients, perturb_type

# =========================================================
# 验证函数
# =========================================================

def calculate_balance_score(ingredients: List[Dict], mu1: float, mu2: float) -> float:
    """
    计算 balance 评分，使用指定的权重
    """
    # 计算评分
    result = calculate_balance_score_from_ingredients(ingredients)
    flavor_balance_score = result.get("flavor_balance_score", 0.0)
    role_balance_score = result.get("role_balance_score", 0.0)
    
    # 使用指定的权重计算最终分数
    final_balance_score = mu1 * flavor_balance_score + mu2 * role_balance_score
    
    return final_balance_score

def validate_weight_combination(weights: Tuple[float, float], 
                             recipe_id: int, 
                             original_ingredients: List[Dict],
                             perturbed_ingredients: List[Dict],
                             perturb_type: str) -> Dict:
    """
    验证权重组合的性能
    """
    mu1, mu2 = weights
    
    # 计算原始配方和扰动配方的评分
    original_score = calculate_balance_score(original_ingredients, mu1, mu2)
    perturbed_score = calculate_balance_score(perturbed_ingredients, mu1, mu2)
    
    # 计算指标（平衡分数越大越好，所以原始配方的分数应该大于扰动配方）
    correct = 1 if original_score > perturbed_score else 0
    margin = original_score - perturbed_score  # 原始配方分数减去扰动配方分数，越大越好
    
    return {
        "weights": weights,
        "recipe_id": recipe_id,
        "perturb_type": perturb_type,
        "correct": correct,
        "margin": margin,
        "original_score": original_score,
        "perturbed_score": perturbed_score
    }

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("Balance 评分器参数验证...")
    
    # 加载数据
    print("[INFO] 加载数据...")
    recipe_ids = load_recipe_ids()
    ingredients_df = load_recipe_ingredients()
    
    # 随机选择部分食谱进行评估
    if len(recipe_ids) > Config.MAX_RECIPES:
        recipe_ids = np.random.choice(recipe_ids, Config.MAX_RECIPES, replace=False)
    
    # 准备评估数据
    print("[INFO] 准备评估数据...")
    eval_data = []
    
    # 为每个食谱生成扰动
    for recipe_id in tqdm(recipe_ids, desc="生成扰动"):
        original_ingredients = get_recipe_ingredients(recipe_id, ingredients_df)
        if len(original_ingredients) >= 3:
            result = generate_balance_perturbation(recipe_id, ingredients_df)
            if result:
                perturbed_ingredients, perturb_type = result
                if len(perturbed_ingredients) >= 2:
                    eval_data.append((recipe_id, original_ingredients, perturbed_ingredients, perturb_type))
    
    print(f"[INFO] 准备了 {len(eval_data)} 个食谱用于评估")
    
    # 验证不同的权重组合
    print("[INFO] 验证权重组合...")
    weight_combinations = [
        (0.6521, 0.3479),  # 最优权重
        (0.5, 0.5),        # 均衡权重
        (0.7, 0.3),        # 强调 flavor
        (0.3, 0.7),        # 强调 role
        (0.9, 0.1),        # 极端强调 flavor
        (0.1, 0.9),        # 极端强调 role
    ]
    
    results = []
    for weights in tqdm(weight_combinations, desc="验证权重"):
        total_correct = 0
        total_margin = 0.0
        total_evaluations = 0
        perturb_type_results = {}
        
        for recipe_id, original_ingredients, perturbed_ingredients, perturb_type in eval_data:
            try:
                eval_result = validate_weight_combination(weights, recipe_id, original_ingredients, perturbed_ingredients, perturb_type)
                total_correct += eval_result["correct"]
                total_margin += eval_result["margin"]
                total_evaluations += 1
                
                # 按扰动类型统计
                if perturb_type not in perturb_type_results:
                    perturb_type_results[perturb_type] = {"correct": 0, "total": 0, "margin": 0.0}
                perturb_type_results[perturb_type]["correct"] += eval_result["correct"]
                perturb_type_results[perturb_type]["total"] += 1
                perturb_type_results[perturb_type]["margin"] += eval_result["margin"]
            except Exception as e:
                # 跳过失败的评估
                continue
        
        if total_evaluations > 0:
            accuracy = total_correct / total_evaluations
            avg_margin = total_margin / total_evaluations
            
            # 计算各扰动类型的准确率
            perturb_type_accuracies = {}
            for perturb_type, stats in perturb_type_results.items():
                if stats["total"] > 0:
                    perturb_type_accuracies[perturb_type] = stats["correct"] / stats["total"]
                else:
                    perturb_type_accuracies[perturb_type] = 0.0
            
            results.append({
                "weights": weights,
                "accuracy": accuracy,
                "average_margin": avg_margin,
                "evaluations": total_evaluations,
                "perturb_type_accuracies": perturb_type_accuracies
            })
    
    # 按 accuracy 排序
    results.sort(key=lambda x: x["accuracy"], reverse=True)
    
    # 准备输出数据
    output_data = []
    for i, result in enumerate(results):
        mu1, mu2 = result["weights"]
        row = {
            "rank": i + 1,
            "mu1_flavor": mu1,
            "mu2_role": mu2,
            "accuracy": result["accuracy"],
            "average_margin": result["average_margin"],
            "evaluations": result["evaluations"]
        }
        
        # 添加各扰动类型的准确率
        for perturb_type, accuracy in result["perturb_type_accuracies"].items():
            row[f"accuracy_{perturb_type}"] = accuracy
        
        output_data.append(row)
    
    # 转换为 DataFrame
    output_df = pd.DataFrame(output_data)
    
    # 保存结果
    os.makedirs(os.path.dirname(Config.OUTPUT_FILE), exist_ok=True)
    output_df.to_csv(Config.OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"[INFO] 验证结果已保存到: {Config.OUTPUT_FILE}")
    
    # 打印最优权重
    print("\n[INFO] 验证结果:")
    for i, result in enumerate(results[:3]):
        mu1, mu2 = result["weights"]
        print(f"[INFO] 排名 {i+1}:")
        print(f"[INFO] Mu1 (Flavor): {mu1:.4f}")
        print(f"[INFO] Mu2 (Role): {mu2:.4f}")
        print(f"[INFO] Accuracy: {result['accuracy']:.4f}")
        print(f"[INFO] Average Margin: {result['average_margin']:.4f}")
        print(f"[INFO] 各扰动类型准确率:")
        for perturb_type, accuracy in result["perturb_type_accuracies"].items():
            print(f"[INFO]   {perturb_type}: {accuracy:.4f}")
        print()

if __name__ == "__main__":
    main()
