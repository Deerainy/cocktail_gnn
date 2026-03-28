# -*- coding: utf-8 -*-
"""
计算 SQE 的 balance 项目

功能：
1. 读取 recipe_balance_feature 表中的数据
2. 判定每个 recipe 的 family
3. 计算整体风味平衡和角色结构平衡
4. 生成包含 family 信息和 balance 分数的 CSV 文件
"""

import os
import sys
import math
import csv
from typing import Dict, List, Tuple

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.db import get_engine
import pandas as pd
from sqlalchemy import text

# 数据库引擎
engine = get_engine()

# 权重配置
# MU_FLAVOR = 0.5  # 风味平衡权重
# MU_ROLE = 0.5    # 角色平衡权重
MU_FLAVOR = 0.6521  # 风味平衡权重
MU_ROLE = 0.3479    # 角色平衡权重

# 配置参数接口
def set_balance_weights(flavor_weight=0.6521, role_weight=0.3479):
    """
    设置 balance 评分器的权重参数
    
    参数:
    flavor_weight: 风味平衡权重
    role_weight: 角色平衡权重
    """
    global MU_FLAVOR, MU_ROLE
    MU_FLAVOR = flavor_weight
    MU_ROLE = role_weight

# 风味特征维度
FLAVOR_DIMENSIONS = ["sour", "sweet", "bitter", "aroma", "fruity", "body"]

# 角色类型
ROLE_TYPES = ["base", "acid", "sweetener", "modifier", "bitters", "garnish", "dilution", "other"]

# Family 定义
FAMILIES = {
    "cluster_0": {
        "flavor_template": {
            "sour": 0.33, "sweet": 0.51, "bitter": 0.36, "aroma": 0.70, "fruity": 0.54, "body": 0.52
        },
        "role_template": {
            "base": 0.37, "acid": 0.22, "sweetener": 0.14, "modifier": 0.17, "bitters": 0.04, "garnish": 0.01, "dilution": 0.02, "other": 0.02
        }
    },
    "cluster_1": {
        "flavor_template": {
            "sour": 0.19, "sweet": 0.37, "bitter": 0.60, "aroma": 0.78, "fruity": 0.38, "body": 0.41
        },
        "role_template": {
            "base": 0.27, "acid": 0.03, "sweetener": 0.07, "modifier": 0.16, "bitters": 0.42, "garnish": 0.01, "dilution": 0.02, "other": 0.02
        }
    },
    "cluster_3": {
        "flavor_template": {
            "sour": 0.20, "sweet": 0.52, "bitter": 0.38, "aroma": 0.75, "fruity": 0.47, "body": 0.62
        },
        "role_template": {
            "base": 0.47, "acid": 0.03, "sweetener": 0.11, "modifier": 0.31, "bitters": 0.04, "garnish": 0.0, "dilution": 0.01, "other": 0.03
        }
    },
    "cluster_2": {
        "flavor_template": {
            "sour": 0.23, "sweet": 0.42, "bitter": 0.38, "aroma": 0.60, "fruity": 0.39, "body": 0.41
        },
        "role_template": {
            "base": 0.20, "acid": 0.07, "sweetener": 0.07, "modifier": 0.09, "bitters": 0.05, "garnish": 0.17, "dilution": 0.34, "other": 0.01
        }
    },
    "cluster_4": {
        "flavor_template": {
            "sour": 0.24, "sweet": 0.49, "bitter": 0.35, "aroma": 0.66, "fruity": 0.45, "body": 0.50
        },
        "role_template": {
            "base": 0.23, "acid": 0.08, "sweetener": 0.10, "modifier": 0.14, "bitters": 0.03, "garnish": 0.03, "dilution": 0.04, "other": 0.35
        }
    }
}


def load_recipe_balance_features() -> pd.DataFrame:
    """
    从数据库中加载 recipe_balance_feature 表的数据
    """
    sql = text("""
    SELECT * FROM recipe_balance_feature
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条 recipe 平衡特征数据")
    return df


def calculate_euclidean_distance(vec1: Dict[str, float], vec2: Dict[str, float], dimensions: List[str]) -> float:
    """
    计算两个向量之间的欧氏距离
    """
    distance = 0.0
    for dim in dimensions:
        distance += (vec1.get(dim, 0.0) - vec2.get(dim, 0.0)) ** 2
    return math.sqrt(distance)


def determine_family(flavor_vector: Dict[str, float], role_distribution: Dict[str, float]) -> str:
    """
    根据风味向量和角色分布判定 recipe 的 family
    """
    min_distance = float('inf')
    best_family = "sour"  # 默认 family
    
    for family, templates in FAMILIES.items():
        # 计算风味距离
        flavor_distance = calculate_euclidean_distance(
            flavor_vector, templates["flavor_template"], FLAVOR_DIMENSIONS
        )
        
        # 计算角色距离
        role_distance = calculate_euclidean_distance(
            role_distribution, templates["role_template"], ROLE_TYPES
        )
        
        # 综合距离（权重可以调整）
        total_distance = 0.6 * flavor_distance + 0.4 * role_distance
        
        if total_distance < min_distance:
            min_distance = total_distance
            best_family = family
    
    return best_family


def calculate_balance_scores(df: pd.DataFrame) -> List[Dict]:
    """
    计算 balance 分数并判定 family
    """
    results = []
    
    for _, row in df.iterrows():
        recipe_id = row["recipe_id"]
        
        # 构建风味向量
        flavor_vector = {
            "sour": float(row.get("f_sour", 0.0)),
            "sweet": float(row.get("f_sweet", 0.0)),
            "bitter": float(row.get("f_bitter", 0.0)),
            "aroma": float(row.get("f_aroma", 0.0)),
            "fruity": float(row.get("f_fruity", 0.0)),
            "body": float(row.get("f_body", 0.0))
        }
        
        # 构建角色分布
        role_distribution = {
            "base": float(row.get("r_base", 0.0)),
            "acid": float(row.get("r_acid", 0.0)),
            "sweetener": float(row.get("r_sweetener", 0.0)),
            "modifier": float(row.get("r_modifier", 0.0)),
            "bitters": float(row.get("r_bitters", 0.0)),
            "garnish": float(row.get("r_garnish", 0.0)),
            "dilution": float(row.get("r_dilution", 0.0)),
            "other": float(row.get("r_other", 0.0))
        }
        
        # 判定 family
        family = determine_family(flavor_vector, role_distribution)
        
        # 获取 family 模板
        family_template = FAMILIES[family]
        flavor_template = family_template["flavor_template"]
        role_template = family_template["role_template"]
        
        # 计算整体风味平衡分数 (L2 距离的负值)
        flavor_distance = calculate_euclidean_distance(flavor_vector, flavor_template, FLAVOR_DIMENSIONS)
        flavor_balance_score = -flavor_distance
        
        # 计算角色结构平衡分数 (L2 距离的负值)
        role_distance = calculate_euclidean_distance(role_distribution, role_template, ROLE_TYPES)
        role_balance_score = -role_distance
        
        # 计算最终 balance 分数
        final_balance_score = MU_FLAVOR * flavor_balance_score + MU_ROLE * role_balance_score
        
        # 保存结果
        results.append({
            "recipe_id": recipe_id,
            "family": family,
            "flavor_balance_score": flavor_balance_score,
            "role_balance_score": role_balance_score,
            "final_balance_score": final_balance_score,
            "f_sour": flavor_vector["sour"],
            "f_sweet": flavor_vector["sweet"],
            "f_bitter": flavor_vector["bitter"],
            "f_aroma": flavor_vector["aroma"],
            "f_fruity": flavor_vector["fruity"],
            "f_body": flavor_vector["body"],
            "r_base": role_distribution["base"],
            "r_acid": role_distribution["acid"],
            "r_sweetener": role_distribution["sweetener"],
            "r_modifier": role_distribution["modifier"],
            "r_bitters": role_distribution["bitters"],
            "r_garnish": role_distribution["garnish"],
            "r_dilution": role_distribution["dilution"],
            "r_other": role_distribution["other"]
        })
    
    return results


def save_to_csv(results: List[Dict], output_file: str):
    """
    将结果保存到 CSV 文件
    """
    if not results:
        print("[WARN] 没有结果可保存")
        return
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 定义 CSV 列名
    fieldnames = [
        "recipe_id", "family", "flavor_balance_score", "role_balance_score", "final_balance_score",
        "f_sour", "f_sweet", "f_bitter", "f_aroma", "f_fruity", "f_body",
        "r_base", "r_acid", "r_sweetener", "r_modifier", "r_bitters", "r_garnish", "r_dilution", "r_other"
    ]
    
    # 写入 CSV 文件
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"[INFO] 结果已保存到: {output_file}")


def calculate_balance_score_from_ingredients(ingredients: List[Dict]) -> Dict:
    """
    计算给定配方的平衡分数
    
    参数:
    ingredients: 原料列表，每个原料是一个字典，包含以下字段:
        - ingredient_id: 原料 ID
        - amount: 原料用量
        - unit: 单位
        - role: 角色
        - line_no: 行号
        - raw_text: 原始文本
    
    返回:
    包含平衡分数的字典
    """
    try:
        if not ingredients:
            return {
                "recipe_id": "custom",
                "family": "sour",
                "flavor_balance_score": 0.0,
                "role_balance_score": 0.0,
                "final_balance_score": 0.0
            }
        
        # 提取 ingredient_ids
        ingredient_ids = [ing["ingredient_id"] for ing in ingredients]
        
        # 从数据库加载原料的风味特征
        flavor_vector = {
            "sour": 0.0,
            "sweet": 0.0,
            "bitter": 0.0,
            "aroma": 0.0,
            "fruity": 0.0,
            "body": 0.0
        }
        
        total_amount = 0.0
        for ing in ingredients:
            amount = ing.get("amount", 0.0)
            if amount is not None:
                total_amount += amount
        
        # 从数据库加载每个原料的风味特征，并根据用量加权计算
        sql = text("""
        SELECT ingredient_id, sour, sweet, bitter, aroma, fruity, body
        FROM ingredient_flavor_feature
        WHERE ingredient_id IN :ingredient_ids
        """)
        
        with engine.begin() as conn:
            result = conn.execute(sql, {"ingredient_ids": ingredient_ids})
            flavor_features = {row.ingredient_id: {
                "sour": float(row.sour),
                "sweet": float(row.sweet),
                "bitter": float(row.bitter),
                "aroma": float(row.aroma),
                "fruity": float(row.fruity),
                "body": float(row.body)
            } for row in result}
        
        # 计算加权风味向量
        for ing in ingredients:
            ingredient_id = ing["ingredient_id"]
            amount = ing.get("amount", 0.0)
            if amount is not None and ingredient_id in flavor_features:
                features = flavor_features[ingredient_id]
                weight = amount / total_amount if total_amount > 0 else 1.0 / len(ingredients)
                for dim in FLAVOR_DIMENSIONS:
                    flavor_vector[dim] += features.get(dim, 0.0) * weight
        
        # 构建角色分布（根据原料用量加权）
        role_amounts = {
            "base": 0.0,
            "acid": 0.0,
            "sweetener": 0.0,
            "modifier": 0.0,
            "bitters": 0.0,
            "garnish": 0.0,
            "dilution": 0.0,
            "other": 0.0
        }
        
        total_amount = 0.0
        for ing in ingredients:
            amount = ing.get("amount", 0.0)
            if amount is not None:
                total_amount += amount
        
        for ing in ingredients:
            role = ing["role"].lower()
            amount = ing.get("amount", 0.0)
            if amount is not None:
                if "base" in role:
                    role_amounts["base"] += amount
                elif "acid" in role:
                    role_amounts["acid"] += amount
                elif "sweet" in role:
                    role_amounts["sweetener"] += amount
                elif "modifier" in role:
                    role_amounts["modifier"] += amount
                elif "bitter" in role:
                    role_amounts["bitters"] += amount
                elif "garnish" in role:
                    role_amounts["garnish"] += amount
                elif "dilution" in role:
                    role_amounts["dilution"] += amount
                else:
                    role_amounts["other"] += amount
        
        # 计算角色分布比例
        role_distribution = {}
        for role, amount in role_amounts.items():
            role_distribution[role] = amount / total_amount if total_amount > 0 else 0.0
        
        # 判定 family
        family = determine_family(flavor_vector, role_distribution)
        
        # 获取 family 模板
        family_template = FAMILIES[family]
        flavor_template = family_template["flavor_template"]
        role_template = family_template["role_template"]
        
        # 计算整体风味平衡分数 (L2 距离的负值)
        flavor_distance = calculate_euclidean_distance(flavor_vector, flavor_template, FLAVOR_DIMENSIONS)
        flavor_balance_score = -flavor_distance
        
        # 计算角色结构平衡分数 (L2 距离的负值)
        role_distance = calculate_euclidean_distance(role_distribution, role_template, ROLE_TYPES)
        role_balance_score = -role_distance
        
        # 计算最终 balance 分数
        final_balance_score = MU_FLAVOR * flavor_balance_score + MU_ROLE * role_balance_score
        
        return {
            "recipe_id": "custom",
            "family": family,
            "flavor_balance_score": flavor_balance_score,
            "role_balance_score": role_balance_score,
            "final_balance_score": final_balance_score
        }
    except Exception as e:
        print(f"[ERROR] 处理自定义配方时出错: {e}")
        # 记录错误但返回默认值
        return {
            "recipe_id": "custom",
            "family": "sour",
            "flavor_balance_score": 0.0,
            "role_balance_score": 0.0,
            "final_balance_score": 0.0
        }

def main():
    """
    主函数
    """
    # 加载数据
    df = load_recipe_balance_features()
    
    # 计算 balance 分数并判定 family
    results = calculate_balance_scores(df)
    
    # 保存结果到 CSV 文件
    output_file = os.path.join(_root, "data", "sqe_balance_results.csv")
    save_to_csv(results, output_file)
    
    # 统计 family 分布
    family_counts = {}
    for result in results:
        family = result["family"]
        family_counts[family] = family_counts.get(family, 0) + 1
    
    print("\n[INFO] Family 分布:")
    for family, count in family_counts.items():
        print(f"[INFO]   {family}: {count}")
    
    # 统计平衡分数
    total_flavor_score = sum(r["flavor_balance_score"] for r in results)
    total_role_score = sum(r["role_balance_score"] for r in results)
    total_final_score = sum(r["final_balance_score"] for r in results)
    
    avg_flavor_score = total_flavor_score / len(results)
    avg_role_score = total_role_score / len(results)
    avg_final_score = total_final_score / len(results)
    
    print("\n[INFO] 平均平衡分数:")
    print(f"[INFO]   风味平衡: {avg_flavor_score:.4f}")
    print(f"[INFO]   角色平衡: {avg_role_score:.4f}")
    print(f"[INFO]   最终平衡: {avg_final_score:.4f}")


if __name__ == "__main__":
    main()
