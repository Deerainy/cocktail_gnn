# -*- coding: utf-8 -*-
"""
Conflict 评分器参数验证脚本

功能：
1. 验证优化得到的 conflict 评分器参数
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

# 导入 conflict 评分器
from scripts.SQE.sqe_scorer_conflict_v2 import calculate_conflict_score_from_ingredients

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 验证参数
    MAX_RECIPES = 100  # 最大评估食谱数量
    
    # 输入输出
    OUTPUT_FILE = os.path.join(_project_root, "data", "conflict_param_validation_results.csv")
    
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
    import random
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
# 验证函数
# =========================================================

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

def validate_weight_combination(weights: Tuple[float, float, float, float], 
                             recipe_id: int, 
                             original_ingredients: List[Dict],
                             perturbed_ingredients: List[Dict],
                             perturb_type: str) -> Dict:
    """
    验证权重组合的性能
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
    print("Conflict 评分器参数验证...")
    
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
            result = generate_conflict_perturbation(recipe_id, ingredients_df, ingredient_info)
            if result:
                perturbed_ingredients, perturb_type = result
                if len(perturbed_ingredients) >= 2:
                    eval_data.append((recipe_id, original_ingredients, perturbed_ingredients, perturb_type))
    
    print(f"[INFO] 准备了 {len(eval_data)} 个食谱用于评估")
    
    # 验证不同的权重组合
    print("[INFO] 验证权重组合...")
    weight_combinations = [
        (0.3066, 0.1888, 0.3556, 0.1490),  # 最优权重
        (0.25, 0.25, 0.25, 0.25),           # 均衡权重
        (0.4, 0.2, 0.3, 0.1),               # 强调 flavor
        (0.2, 0.4, 0.2, 0.2),               # 强调 role
        (0.2, 0.2, 0.4, 0.2),               # 强调 type
        (0.2, 0.2, 0.2, 0.4),               # 强调 ratio
        (1.0, 1.2, 0.8, 0.8),               # 原始权重（未归一化）
    ]
    
    # 归一化权重
    normalized_weight_combinations = []
    for weights in weight_combinations:
        if sum(weights) != 1.0:
            total = sum(weights)
            normalized_weights = tuple(w / total for w in weights)
            normalized_weight_combinations.append(normalized_weights)
        else:
            normalized_weight_combinations.append(weights)
    
    results = []
    for weights in tqdm(normalized_weight_combinations, desc="验证权重"):
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
        eta1, eta2, eta3, eta4 = result["weights"]
        print(f"[INFO] 排名 {i+1}:")
        print(f"[INFO] Eta1 (Flavor): {eta1:.4f}")
        print(f"[INFO] Eta2 (Role): {eta2:.4f}")
        print(f"[INFO] Eta3 (Type): {eta3:.4f}")
        print(f"[INFO] Eta4 (Ratio): {eta4:.4f}")
        print(f"[INFO] Accuracy: {result['accuracy']:.4f}")
        print(f"[INFO] Average Margin: {result['average_margin']:.4f}")
        print(f"[INFO] 各扰动类型准确率:")
        for perturb_type, accuracy in result["perturb_type_accuracies"].items():
            print(f"[INFO]   {perturb_type}: {accuracy:.4f}")
        print()

if __name__ == "__main__":
    main()
