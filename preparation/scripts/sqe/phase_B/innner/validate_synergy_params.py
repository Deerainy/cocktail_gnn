# -*- coding: utf-8 -*-
"""
Synergy 评分器参数验证脚本

功能：
1. 验证优化得到的 synergy 评分器参数
2. 使用更多的食谱进行评估
3. 计算不同扰动类型的性能
4. 输出详细的验证结果
"""

import os
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
from typing import List, Dict, Tuple, Optional

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_script_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 数据库导入
from src.db import get_engine
from sqlalchemy import text

# 导入 synergy 评分器
from scripts.SQE.phase_A.sqe_scorer_synergy import score_recipe_from_ingredients

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 验证参数
    MAX_RECIPES = 100  # 最大评估食谱数量
    
    # 输入输出
    OUTPUT_FILE = os.path.join(_project_root, "data", "synergy_param_validation_results.csv")
    
    # 扰动类型
    SYNERGY_PERTURB_TYPES = [
        "synergy_replace_with_different_type",
        "synergy_replace_with_different_anchor",
        "synergy_insert_different_type",
        "synergy_remove_key_ingredient"
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

def load_ingredient_info() -> pd.DataFrame:
    """
    加载原料信息，用于扰动生成
    """
    engine = get_engine()
    sql = text("""
    SELECT ingredient_id, anchor_name, type_tag
    FROM ingredient_flavor_anchor
    JOIN ingredient_type USING (ingredient_id)
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条原料详细信息")
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

def generate_synergy_perturbation(recipe_id: int, ingredients_df: pd.DataFrame, 
                                ingredient_info: pd.DataFrame) -> Optional[Tuple[List[Dict], str]]:
    """
    生成 synergy 相关的扰动
    """
    # 获取原始食谱的原料
    original_ingredients = get_recipe_ingredients(recipe_id, ingredients_df)
    if len(original_ingredients) < 3:
        return None
    
    # 随机选择扰动类型
    import random
    perturb_type = random.choice(Config.SYNERGY_PERTURB_TYPES)
    perturbed_ingredients = [ing.copy() for ing in original_ingredients]
    
    if perturb_type == "synergy_replace_with_different_type":
        # 替换为不同类型的原料，破坏 flavor compatibility
        # 优先选择主要原料进行替换
        key_ingredients = [ing for ing in perturbed_ingredients if ing['role'] in ['base_spirit', 'sweetener', 'acid']]
        if not key_ingredients:
            key_ingredients = perturbed_ingredients
        
        ingredient_to_replace = random.choice(key_ingredients)
        original_type = ingredient_info[ingredient_info['ingredient_id'] == ingredient_to_replace['ingredient_id']]['type_tag'].values
        if len(original_type) > 0:
            original_type = original_type[0]
            # 选择不同类型的原料
            different_type_ingredients = ingredient_info[ingredient_info['type_tag'] != original_type]
            if len(different_type_ingredients) > 0:
                new_ingredient = different_type_ingredients.sample(1).iloc[0]
                # 替换原料
                for ing in perturbed_ingredients:
                    if ing['line_no'] == ingredient_to_replace['line_no']:
                        ing['ingredient_id'] = new_ingredient['ingredient_id']
                        ing['raw_text'] = f"1 oz Ingredient {new_ingredient['ingredient_id']}"
                        break
            else:
                return None
        else:
            return None
    
    elif perturb_type == "synergy_replace_with_different_anchor":
        # 替换为不同锚点的原料，破坏 anchor 相似性
        # 优先选择主要原料进行替换
        key_ingredients = [ing for ing in perturbed_ingredients if ing['role'] in ['base_spirit', 'sweetener', 'acid']]
        if not key_ingredients:
            key_ingredients = perturbed_ingredients
        
        ingredient_to_replace = random.choice(key_ingredients)
        original_anchor = ingredient_info[ingredient_info['ingredient_id'] == ingredient_to_replace['ingredient_id']]['anchor_name'].values
        if len(original_anchor) > 0:
            original_anchor = original_anchor[0]
            # 选择不同锚点的原料
            different_anchor_ingredients = ingredient_info[ingredient_info['anchor_name'] != original_anchor]
            if len(different_anchor_ingredients) > 0:
                new_ingredient = different_anchor_ingredients.sample(1).iloc[0]
                # 替换原料
                for ing in perturbed_ingredients:
                    if ing['line_no'] == ingredient_to_replace['line_no']:
                        ing['ingredient_id'] = new_ingredient['ingredient_id']
                        ing['raw_text'] = f"1 oz Ingredient {new_ingredient['ingredient_id']}"
                        break
            else:
                return None
        else:
            return None
    
    elif perturb_type == "synergy_remove_key_ingredient":
        # 移除关键原料，直接破坏 synergy
        # 优先选择主要原料进行移除
        key_ingredients = [ing for ing in perturbed_ingredients if ing['role'] in ['base_spirit', 'sweetener', 'acid']]
        if len(key_ingredients) >= 2:  # 确保至少保留一个关键原料
            ingredient_to_remove = random.choice(key_ingredients)
            # 移除原料
            perturbed_ingredients = [ing for ing in perturbed_ingredients if ing['line_no'] != ingredient_to_remove['line_no']]
            # 重新编号 line_no
            for i, ing in enumerate(perturbed_ingredients, 1):
                ing['line_no'] = i
        else:
            return None
    
    else:  # synergy_insert_different_type
        # 插入不同类型的原料，可能破坏 cooccur
        existing_ingredient_ids = [ing['ingredient_id'] for ing in perturbed_ingredients]
        existing_types = set(ingredient_info[ingredient_info['ingredient_id'].isin(existing_ingredient_ids)]['type_tag'].unique())
        # 选择不同类型的原料
        different_type_ingredients = ingredient_info[~ingredient_info['type_tag'].isin(existing_types)]
        if len(different_type_ingredients) > 0:
            new_ingredient = different_type_ingredients.sample(1).iloc[0]
            # 插入原料
            new_ingredient_dict = {
                "recipe_id": recipe_id,
                "ingredient_id": new_ingredient['ingredient_id'],
                "line_no": len(perturbed_ingredients) + 1,
                "amount": "1",
                "unit": "oz",
                "role": "modifier",
                "raw_text": f"1 oz Ingredient {new_ingredient['ingredient_id']}"
            }
            perturbed_ingredients.append(new_ingredient_dict)
        else:
            return None
    
    return perturbed_ingredients, perturb_type

# =========================================================
# 验证函数
# =========================================================

def calculate_synergy_score(ingredients: List[Dict], alpha1: float, alpha2: float, alpha3: float) -> float:
    """
    计算 synergy 评分，使用指定的权重
    """
    # 临时修改全局参数
    import scripts.SQE.phase_A.sqe_scorer_synergy as synergy_scorer
    original_lambda_flavor = synergy_scorer.LAMBDA_FLAVOR
    original_lambda_cooccur = synergy_scorer.LAMBDA_COOCCUR
    original_lambda_anchor = synergy_scorer.LAMBDA_ANCHOR
    
    try:
        # 设置新的权重
        synergy_scorer.LAMBDA_FLAVOR = alpha1
        synergy_scorer.LAMBDA_COOCCUR = alpha2
        synergy_scorer.LAMBDA_ANCHOR = alpha3
        
        # 计算评分
        result = score_recipe_from_ingredients(ingredients)
        return result.get("synergy_score", 0.0)
    finally:
        # 恢复原始参数
        synergy_scorer.LAMBDA_FLAVOR = original_lambda_flavor
        synergy_scorer.LAMBDA_COOCCUR = original_lambda_cooccur
        synergy_scorer.LAMBDA_ANCHOR = original_lambda_anchor

def validate_weight_combination(weights: Tuple[float, float, float], 
                             recipe_id: int, 
                             original_ingredients: List[Dict],
                             perturbed_ingredients: List[Dict],
                             perturb_type: str) -> Dict:
    """
    验证权重组合的性能
    """
    alpha1, alpha2, alpha3 = weights
    
    # 计算原始配方和扰动配方的评分
    original_score = calculate_synergy_score(original_ingredients, alpha1, alpha2, alpha3)
    perturbed_score = calculate_synergy_score(perturbed_ingredients, alpha1, alpha2, alpha3)
    
    # 计算指标
    correct = 1 if original_score > perturbed_score else 0
    margin = original_score - perturbed_score
    
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
    print("Synergy 评分器参数验证...")
    
    # 加载数据
    print("[INFO] 加载数据...")
    recipe_ids = load_recipe_ids()
    ingredients_df = load_recipe_ingredients()
    ingredient_info = load_ingredient_info()
    
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
            result = generate_synergy_perturbation(recipe_id, ingredients_df, ingredient_info)
            if result:
                perturbed_ingredients, perturb_type = result
                if len(perturbed_ingredients) >= 2:
                    eval_data.append((recipe_id, original_ingredients, perturbed_ingredients, perturb_type))
    
    print(f"[INFO] 准备了 {len(eval_data)} 个食谱用于评估")
    
    # 验证不同的权重组合
    print("[INFO] 验证权重组合...")
    weight_combinations = [
        (0.45, 0.45, 0.1),     # 最优权重
        (0.525, 0.375, 0.1),   # 次优权重
        (0.375, 0.525, 0.1),   # 次优权重
        (0.4, 0.3, 0.3),       # 原始权重
        (0.6, 0.3, 0.1),       # 更强调 flavor
        (0.3, 0.6, 0.1),       # 更强调 cooccur
        (0.3, 0.3, 0.4),       # 更强调 anchor
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
        alpha1, alpha2, alpha3 = result["weights"]
        row = {
            "rank": i + 1,
            "alpha1_flavor": alpha1,
            "alpha2_cooccur": alpha2,
            "alpha3_anchor": alpha3,
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
        alpha1, alpha2, alpha3 = result["weights"]
        print(f"[INFO] 排名 {i+1}:")
        print(f"[INFO] Alpha1 (Flavor): {alpha1:.4f}")
        print(f"[INFO] Alpha2 (Cooccur): {alpha2:.4f}")
        print(f"[INFO] Alpha3 (Anchor): {alpha3:.4f}")
        print(f"[INFO] Accuracy: {result['accuracy']:.4f}")
        print(f"[INFO] Average Margin: {result['average_margin']:.4f}")
        print(f"[INFO] 各扰动类型准确率:")
        for perturb_type, accuracy in result["perturb_type_accuracies"].items():
            print(f"[INFO]   {perturb_type}: {accuracy:.4f}")
        print()

if __name__ == "__main__":
    main()
