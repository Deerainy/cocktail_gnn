# -*- coding: utf-8 -*-
"""
Synergy 评分器参数优化脚本 (v2)

功能：
1. 专门优化 synergy 评分器的内部参数（α1, α2, α3）
2. 使用 "原配方 > 扰动配方" 的 pairwise preference
3. 优先使用 synergy 相关扰动集，如 flavor compatibility 被破坏、cooccur 被削弱、anchor 相似性被破坏
4. 采用网格搜索和 Dirichlet 分布采样相结合的方法
5. 评估参数组合的 pairwise accuracy 和平均 margin
"""

import os
import sys
import random
import numpy as np
import pandas as pd
from scipy.stats import dirichlet
from typing import List, Dict, Tuple, Optional
from tqdm import tqdm

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
    # 搜索参数
    NUM_GRID_SAMPLES = 50  # 网格搜索样本数
    NUM_DIRICHLET_SAMPLES = 150  # Dirichlet 分布采样数
    TOP_K = 5  # 输出 top-k 最优权重
    MAX_RECIPES = 30  # 最大评估食谱数量
    
    # 输入输出
    OUTPUT_FILE = os.path.join(_project_root, "data", "synergy_param_optimization_results.csv")
    
    # 扰动类型过滤
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
        HAVING COUNT(*) >= 2
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
                                ingredient_info: pd.DataFrame) -> Optional[List[Dict]]:
    """
    生成 synergy 相关的扰动
    """
    # 获取原始食谱的原料
    original_ingredients = get_recipe_ingredients(recipe_id, ingredients_df)
    if len(original_ingredients) < 3:
        return None
    
    # 随机选择扰动类型
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
    
    return perturbed_ingredients

# =========================================================
# 参数优化函数
# =========================================================

def generate_weight_combinations() -> List[Tuple[float, float, float]]:
    """
    生成权重组合
    """
    weight_combinations = []
    
    # 固定网格搜索 - 使用更密集的关键区域
    print(f"[INFO] 生成 {Config.NUM_GRID_SAMPLES} 组网格搜索权重...")
    for i in range(Config.NUM_GRID_SAMPLES):
        # 生成更有针对性的权重组合
        alpha1 = 0.1 + (i % 5) * 0.2  # 0.1, 0.3, 0.5, 0.7, 0.9
        alpha2 = 0.1 + ((i // 5) % 4) * 0.2  # 0.1, 0.3, 0.5, 0.7
        # 计算 alpha3 并确保总和为1
        alpha3 = 1 - alpha1 - alpha2
        # 如果 alpha3 小于 0.1，重新分配权重
        if alpha3 < 0.1:
            # 计算需要调整的量
            adjustment = 0.1 - alpha3
            # 按比例调整 alpha1 和 alpha2
            total = alpha1 + alpha2
            alpha1 -= adjustment * (alpha1 / total)
            alpha2 -= adjustment * (alpha2 / total)
            alpha3 = 0.1
        weight_combinations.append((alpha1, alpha2, alpha3))
    
    # Dirichlet 分布采样 - 集中在合理范围内
    print(f"[INFO] 生成 {Config.NUM_DIRICHLET_SAMPLES} 组 Dirichlet 分布权重...")
    # 使用参数 [2, 2, 2] 生成更集中的分布
    dirichlet_weights = dirichlet.rvs([2, 2, 2], size=Config.NUM_DIRICHLET_SAMPLES)
    for w in dirichlet_weights:
        # 确保权重都大于 0.1
        w = [max(0.1, x) for x in w]
        # 重新归一化
        total = sum(w)
        w = [x / total for x in w]
        weight_combinations.append((w[0], w[1], w[2]))
    
    return weight_combinations

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

def evaluate_weight_combination(weights: Tuple[float, float, float], 
                             recipe_id: int, 
                             original_ingredients: List[Dict],
                             perturbed_ingredients: List[Dict]) -> Dict:
    """
    评估权重组合的性能
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
    print("Synergy 评分器参数优化...")
    
    # 加载数据
    print("[INFO] 加载数据...")
    recipe_ids = load_recipe_ids()
    ingredients_df = load_recipe_ingredients()
    ingredient_info = load_ingredient_info()
    
    # 生成权重组合
    weight_combinations = generate_weight_combinations()
    print(f"[INFO] 共生成 {len(weight_combinations)} 组权重组合")
    
    # 准备评估数据
    print("[INFO] 准备评估数据...")
    eval_data = []
    
    # 随机选择部分食谱进行评估
    if len(recipe_ids) > Config.MAX_RECIPES:
        recipe_ids = np.random.choice(recipe_ids, Config.MAX_RECIPES, replace=False)
    
    # 为每个食谱生成扰动
    for recipe_id in tqdm(recipe_ids, desc="生成扰动"):
        original_ingredients = get_recipe_ingredients(recipe_id, ingredients_df)
        if len(original_ingredients) >= 2:
            perturbed_ingredients = generate_synergy_perturbation(recipe_id, ingredients_df, ingredient_info)
            if perturbed_ingredients and len(perturbed_ingredients) >= 2:
                eval_data.append((recipe_id, original_ingredients, perturbed_ingredients))
    
    print(f"[INFO] 准备了 {len(eval_data)} 个食谱用于评估")
    
    # 评估权重组合
    print("[INFO] 评估权重组合...")
    results = []
    
    for weights in tqdm(weight_combinations, desc="评估权重"):
        total_correct = 0
        total_margin = 0.0
        total_evaluations = 0
        
        for recipe_id, original_ingredients, perturbed_ingredients in eval_data:
            try:
                eval_result = evaluate_weight_combination(weights, recipe_id, original_ingredients, perturbed_ingredients)
                total_correct += eval_result["correct"]
                total_margin += eval_result["margin"]
                total_evaluations += 1
            except Exception as e:
                # 跳过失败的评估
                continue
        
        if total_evaluations > 0:
            accuracy = total_correct / total_evaluations
            avg_margin = total_margin / total_evaluations
            
            results.append({
                "weights": weights,
                "accuracy": accuracy,
                "average_margin": avg_margin,
                "evaluations": total_evaluations
            })
    
    # 按 accuracy 排序
    results.sort(key=lambda x: x["accuracy"], reverse=True)
    
    # 提取 top-k 结果
    top_results = results[:Config.TOP_K]
    
    # 准备输出数据
    output_data = []
    for i, result in enumerate(top_results):
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
        output_data.append(row)
    
    # 转换为 DataFrame
    output_df = pd.DataFrame(output_data)
    
    # 保存结果
    os.makedirs(os.path.dirname(Config.OUTPUT_FILE), exist_ok=True)
    output_df.to_csv(Config.OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"[INFO] 优化结果已保存到: {Config.OUTPUT_FILE}")
    
    # 打印最优权重
    print("\n[INFO] 最优权重组合:")
    best_result = top_results[0]
    alpha1, alpha2, alpha3 = best_result["weights"]
    print(f"[INFO] Alpha1 (Flavor): {alpha1:.4f}")
    print(f"[INFO] Alpha2 (Cooccur): {alpha2:.4f}")
    print(f"[INFO] Alpha3 (Anchor): {alpha3:.4f}")
    print(f"[INFO] Accuracy: {best_result['accuracy']:.4f}")
    print(f"[INFO] Average Margin: {best_result['average_margin']:.4f}")

if __name__ == "__main__":
    main()
