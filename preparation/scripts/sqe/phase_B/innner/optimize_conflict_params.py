# -*- coding: utf-8 -*-
"""
Conflict 评分器参数优化脚本

功能：
1. 专门优化 conflict 评分器的内部参数（η1, η2, η3, η4）
2. 使用 "原配方 > 扰动配方" 的 pairwise preference
3. 优先使用 conflict 相关扰动集，如添加额外的 base spirit、创建不兼容类型对、破坏酸甜比例等
4. 采用网格搜索和 Dirichlet 分布采样相结合的方法
5. 评估参数组合的 pairwise accuracy 和平均 margin
"""

import os
import sys
import random
import numpy as np
import pandas as pd
from scipy.stats import dirichlet
from typing import List, Dict, Tuple, Optional, Any
from tqdm import tqdm

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_script_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 数据库导入
from src.db import get_engine
from sqlalchemy import text

# 导入 conflict 评分器
from scripts.SQE.sqe_scorer_conflict_v2 import calculate_conflict_score_from_ingredients

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 搜索参数
    NUM_GRID_SAMPLES = 100  # 网格搜索样本数
    NUM_DIRICHLET_SAMPLES = 400  # Dirichlet 分布采样数
    TOP_K = 10  # 输出 top-k 最优权重
    MAX_RECIPES = 50  # 最大评估食谱数量
    
    # 输入输出
    OUTPUT_FILE = os.path.join(_project_root, "data", "conflict_param_optimization_results.csv")
    
    # 扰动类型
    CONFLICT_PERTURB_TYPES = [
        "conflict_add_extra_base_spirit",
        "conflict_create_incompatible_type_pair",
        "conflict_acid_sweetener_ratio_break",
        "conflict_modifier_overload"
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

def safe_parse_amount(amount: Any) -> float:
    """
    安全解析 amount 字段
    """
    if amount is None:
        return 1.0
    
    try:
        # 处理字符串类型
        if isinstance(amount, str):
            cleaned_amount = amount.strip()
            # 处理分数形式
            # 处理带整数的分数，如 "1 1/2"
            import re
            mixed_fraction_pattern = r'^\s*(\d+)\s+(\d+)/(\d+)\s*$'
            match = re.match(mixed_fraction_pattern, cleaned_amount)
            if match:
                integer_part = int(match.group(1))
                numerator = int(match.group(2))
                denominator = int(match.group(3))
                if denominator != 0:
                    return integer_part + (numerator / denominator)
            # 处理纯分数，如 "1/2"
            fraction_pattern = r'^\s*(\d+)/(\d+)\s*$'
            match = re.match(fraction_pattern, cleaned_amount)
            if match:
                numerator = int(match.group(1))
                denominator = int(match.group(2))
                if denominator != 0:
                    return numerator / denominator
            # 清理非数字字符后尝试转换
            cleaned_amount = re.sub(r'[^0-9.]', '', cleaned_amount)
            if cleaned_amount:
                return float(cleaned_amount)
        # 处理数字类型
        elif isinstance(amount, (int, float)):
            return float(amount)
    except Exception as e:
        pass
    
    return 1.0

def generate_conflict_perturbation(recipe_id: int, ingredients_df: pd.DataFrame, 
                                ingredient_info: pd.DataFrame) -> Optional[Tuple[List[Dict], str]]:
    """
    生成 conflict 相关的扰动
    """
    # 获取原始食谱的原料
    original_ingredients = get_recipe_ingredients(recipe_id, ingredients_df)
    if len(original_ingredients) < 3:
        return None
    
    # 随机选择扰动类型
    perturb_type = random.choice(Config.CONFLICT_PERTURB_TYPES)
    perturbed_ingredients = [ing.copy() for ing in original_ingredients]
    
    if perturb_type == "conflict_add_extra_base_spirit":
        # 添加额外的 base spirit，可能导致 base 过多
        # 选择一个 base spirit 类型的原料
        base_ingredients = ingredient_info[ingredient_info['type_tag'] == 'spirit']
        if len(base_ingredients) > 0:
            new_ingredient = base_ingredients.sample(1).iloc[0]
            # 插入原料
            new_ingredient_dict = {
                "recipe_id": recipe_id,
                "ingredient_id": new_ingredient['ingredient_id'],
                "line_no": len(perturbed_ingredients) + 1,
                "amount": "1",
                "unit": "oz",
                "role": "base_spirit",
                "raw_text": f"1 oz Ingredient {new_ingredient['ingredient_id']}"
            }
            perturbed_ingredients.append(new_ingredient_dict)
        else:
            return None
    
    elif perturb_type == "conflict_create_incompatible_type_pair":
        # 创建不兼容类型对，如 cream 和 acid
        # 选择一个 cream 类型的原料
        cream_ingredients = ingredient_info[ingredient_info['type_tag'] == 'cream']
        if len(cream_ingredients) > 0:
            new_ingredient = cream_ingredients.sample(1).iloc[0]
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
    
    elif perturb_type == "conflict_acid_sweetener_ratio_break":
        # 破坏酸甜比例
        acid_sweet_ingredients = [ing for ing in perturbed_ingredients if 'acid' in ing['role'].lower() or 'sweet' in ing['role'].lower()]
        if len(acid_sweet_ingredients) > 0:
            ingredient_to_change = random.choice(acid_sweet_ingredients)
            # 根据角色选择不同的系数
            if 'acid' in ingredient_to_change['role'].lower():
                # 酸乘以 3.0
                factor = 3.0
            else:
                # 甜乘以 0.3
                factor = 0.3
            # 计算新的数值量
            original_amount = safe_parse_amount(ingredient_to_change['amount'])
            new_amount = original_amount * factor
            # 更新原料量
            for ing in perturbed_ingredients:
                if ing['line_no'] == ingredient_to_change['line_no']:
                    ing['amount'] = new_amount
                    break
        else:
            return None
    
    else:  # conflict_modifier_overload
        # 添加过多的 modifier
        # 选择一个 modifier 类型的原料
        modifier_ingredients = ingredient_info[ingredient_info['type_tag'] == 'modifier']
        if len(modifier_ingredients) > 0:
            # 添加多个 modifier
            for i in range(3):  # 添加 3 个 modifier
                if len(modifier_ingredients) > 0:
                    new_ingredient = modifier_ingredients.sample(1).iloc[0]
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
# 参数优化函数
# =========================================================

def generate_weight_combinations() -> List[Tuple[float, float, float, float]]:
    """
    生成权重组合
    """
    weight_combinations = []
    
    # 网格搜索
    print(f"[INFO] 生成 {Config.NUM_GRID_SAMPLES} 组网格搜索权重...")
    for i in range(Config.NUM_GRID_SAMPLES):
        # 生成均匀分布的权重
        eta1 = random.uniform(0.5, 1.5)  # ETA_FLAVOR
        eta2 = random.uniform(0.5, 1.5)  # ETA_ROLE
        eta3 = random.uniform(0.5, 1.5)  # ETA_TYPE
        eta4 = random.uniform(0.5, 1.5)  # ETA_RATIO
        
        # 归一化权重
        total = eta1 + eta2 + eta3 + eta4
        eta1 /= total
        eta2 /= total
        eta3 /= total
        eta4 /= total
        
        weight_combinations.append((eta1, eta2, eta3, eta4))
    
    # Dirichlet 分布采样
    print(f"[INFO] 生成 {Config.NUM_DIRICHLET_SAMPLES} 组 Dirichlet 分布权重...")
    # 使用参数 [2, 2, 2, 2] 生成更集中的分布
    dirichlet_weights = dirichlet.rvs([2, 2, 2, 2], size=Config.NUM_DIRICHLET_SAMPLES)
    for w in dirichlet_weights:
        weight_combinations.append((w[0], w[1], w[2], w[3]))
    
    return weight_combinations

def calculate_conflict_score(ingredients: List[Dict], eta1: float, eta2: float, eta3: float, eta4: float) -> float:
    """
    计算 conflict 评分，使用指定的权重
    """
    # 临时修改全局参数
    import scripts.SQE.sqe_scorer_conflict_v2 as conflict_scorer
    original_eta_flavor = conflict_scorer.ETA_FLAVOR
    original_eta_role = conflict_scorer.ETA_ROLE
    original_eta_type = conflict_scorer.ETA_TYPE
    original_eta_ratio = conflict_scorer.ETA_RATIO
    
    try:
        # 设置新的权重
        conflict_scorer.ETA_FLAVOR = eta1
        conflict_scorer.ETA_ROLE = eta2
        conflict_scorer.ETA_TYPE = eta3
        conflict_scorer.ETA_RATIO = eta4
        
        # 计算评分
        result = calculate_conflict_score_from_ingredients(ingredients)
        return result.get("conflict_score", 0.0)
    finally:
        # 恢复原始参数
        conflict_scorer.ETA_FLAVOR = original_eta_flavor
        conflict_scorer.ETA_ROLE = original_eta_role
        conflict_scorer.ETA_TYPE = original_eta_type
        conflict_scorer.ETA_RATIO = original_eta_ratio

def evaluate_weight_combination(weights: Tuple[float, float, float, float], 
                             recipe_id: int, 
                             original_ingredients: List[Dict],
                             perturbed_ingredients: List[Dict],
                             perturb_type: str) -> Dict:
    """
    评估权重组合的性能
    """
    eta1, eta2, eta3, eta4 = weights
    
    # 计算原始配方和扰动配方的评分
    original_score = calculate_conflict_score(original_ingredients, eta1, eta2, eta3, eta4)
    perturbed_score = calculate_conflict_score(perturbed_ingredients, eta1, eta2, eta3, eta4)
    
    # 计算指标（冲突分数越大越差，所以原始配方的分数应该小于扰动配方）
    correct = 1 if original_score < perturbed_score else 0
    margin = perturbed_score - original_score  # 扰动配方分数减去原始配方分数，越大越好
    
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
    print("Conflict 评分器参数优化...")
    
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
        if len(original_ingredients) >= 3:
            result = generate_conflict_perturbation(recipe_id, ingredients_df, ingredient_info)
            if result:
                perturbed_ingredients, perturb_type = result
                if len(perturbed_ingredients) >= 2:
                    eval_data.append((recipe_id, original_ingredients, perturbed_ingredients, perturb_type))
    
    print(f"[INFO] 准备了 {len(eval_data)} 个食谱用于评估")
    
    # 评估权重组合
    print("[INFO] 评估权重组合...")
    results = []
    
    for weights in tqdm(weight_combinations, desc="评估权重"):
        total_correct = 0
        total_margin = 0.0
        total_evaluations = 0
        
        for recipe_id, original_ingredients, perturbed_ingredients, perturb_type in eval_data:
            try:
                eval_result = evaluate_weight_combination(weights, recipe_id, original_ingredients, perturbed_ingredients, perturb_type)
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
        eta1, eta2, eta3, eta4 = result["weights"]
        row = {
            "rank": i + 1,
            "eta1_flavor": eta1,
            "eta2_role": eta2,
            "eta3_type": eta3,
            "eta4_ratio": eta4,
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
    eta1, eta2, eta3, eta4 = best_result["weights"]
    print(f"[INFO] Eta1 (Flavor): {eta1:.4f}")
    print(f"[INFO] Eta2 (Role): {eta2:.4f}")
    print(f"[INFO] Eta3 (Type): {eta3:.4f}")
    print(f"[INFO] Eta4 (Ratio): {eta4:.4f}")
    print(f"[INFO] Accuracy: {best_result['accuracy']:.4f}")
    print(f"[INFO] Average Margin: {best_result['average_margin']:.4f}")

if __name__ == "__main__":
    main()
