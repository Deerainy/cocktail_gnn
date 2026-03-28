# -*- coding: utf-8 -*-
"""
计算 recipe 的整体风味向量 F(G_r) 并保存到 recipe_balance_feature 表

功能：
1. 从数据库中读取每个 recipe 的原料信息
2. 读取每个原料的风味特征向量
3. 基于用量计算每个原料的权重
4. 计算加权和得到 recipe 的整体风味向量
5. 计算 role 分布占比
6. 确保风味向量的每维都在统一范围内
7. 将结果插入到 recipe_balance_feature 表
"""

import os
import sys
import math
from typing import Dict, List, Tuple, Optional

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.db import get_engine
import pandas as pd
from sqlalchemy import text
from datetime import datetime

# 数据库引擎
engine = get_engine()

# 风味特征维度
FLAVOR_DIMENSIONS = ["sour", "sweet", "bitter", "aroma", "fruity", "body"]

# 角色类型
ROLE_TYPES = ["base", "acid", "sweetener", "modifier", "bitters", "garnish", "dilution", "other"]


def safe_parse_amount(amount: Optional[any]) -> Optional[float]:
    """
    安全解析 amount 字段
    """
    if amount is None:
        return None
    
    try:
        # 处理 Decimal 类型
        if hasattr(amount, 'as_tuple'):  # 检查是否为 Decimal 类型
            return float(amount)
        # 处理字符串类型
        elif isinstance(amount, str):
            # 清理字符串
            cleaned_amount = amount.strip()
            
            # 先处理分数形式
            # 处理带整数的分数，如 "1 1/2"
            import re
            mixed_fraction_pattern = r'^\s*(\d+)\s+(\d+)/(\d+)\s*$'
            match = re.match(mixed_fraction_pattern, cleaned_amount)
            if match:
                integer_part = int(match.group(1))
                numerator = int(match.group(2))
                denominator = int(match.group(3))
                return integer_part + (numerator / denominator)
            
            # 处理纯分数，如 "1/2"
            fraction_pattern = r'^\s*(\d+)/(\d+)\s*$'
            match = re.match(fraction_pattern, cleaned_amount)
            if match:
                numerator = int(match.group(1))
                denominator = int(match.group(2))
                return numerator / denominator
            
            # 尝试直接转换为 float
            try:
                return float(cleaned_amount)
            except:
                # 清理非数字字符后尝试转换
                cleaned_amount = re.sub(r'[^0-9.]', '', cleaned_amount)
                if cleaned_amount:
                    return float(cleaned_amount)
        # 处理数字类型
        elif isinstance(amount, (int, float)):
            return float(amount)
    except Exception as e:
        # 打印调试信息
        if isinstance(amount, str):
            print(f"[DEBUG] 解析 amount 失败: '{amount}', 错误: {e}")
        pass
    
    return None


def create_recipe_balance_feature_table():
    """
    创建 recipe_balance_feature 表
    """
    sql = text("""
    CREATE TABLE IF NOT EXISTS recipe_balance_feature (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        recipe_id BIGINT NOT NULL,
        snapshot_id VARCHAR(50) NOT NULL,
        family VARCHAR(50),
        f_sour DECIMAL(10,6),
        f_sweet DECIMAL(10,6),
        f_bitter DECIMAL(10,6),
        f_aroma DECIMAL(10,6),
        f_fruity DECIMAL(10,6),
        f_body DECIMAL(10,6),
        r_base DECIMAL(10,6),
        r_acid DECIMAL(10,6),
        r_sweetener DECIMAL(10,6),
        r_modifier DECIMAL(10,6),
        r_bitters DECIMAL(10,6),
        r_garnish DECIMAL(10,6),
        r_dilution DECIMAL(10,6),
        r_other DECIMAL(10,6),
        flavor_dist DECIMAL(12,6),
        role_dist DECIMAL(12,6),
        flavor_balance_score DECIMAL(12,6),
        role_balance_score DECIMAL(12,6),
        final_balance_score DECIMAL(12,6),
        computed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uk_recipe_snapshot (recipe_id, snapshot_id),
        KEY idx_snapshot (snapshot_id),
        KEY idx_family (family)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    
    with engine.begin() as conn:
        conn.execute(sql)
    
    print("[INFO] recipe_balance_feature 表创建成功")


def load_recipe_ingredients(recipe_id: int) -> List[Dict]:
    """
    加载指定 recipe 的原料信息
    """
    sql = text("""
    SELECT
        recipe_id,
        ingredient_id,
        amount,
        unit,
        role,
        raw_text
    FROM recipe_ingredient
    WHERE recipe_id = :recipe_id
    ORDER BY line_no
    """)
    
    with engine.begin() as conn:
        rows = conn.execute(sql, {"recipe_id": recipe_id}).mappings().all()
    
    ingredients = []
    for row in rows:
        ingredient = dict(row)
        # 解析 amount
        ingredient["parsed_amount"] = safe_parse_amount(ingredient["amount"])
        ingredients.append(ingredient)
    
    return ingredients


def load_ingredient_flavor_features(ingredient_ids: List[int]) -> Dict[int, Dict]:
    """
    加载指定原料的风味特征
    """
    if not ingredient_ids:
        return {}
    
    sql = text("""
    SELECT
        ingredient_id,
        sour,
        sweet,
        bitter,
        aroma,
        fruity,
        body
    FROM ingredient_flavor_feature
    WHERE ingredient_id IN :ids
    """)
    
    with engine.begin() as conn:
        rows = conn.execute(sql, {"ids": ingredient_ids}).mappings().all()
    
    # 构建结果字典
    result = {}
    for row in rows:
        ingredient_id = row["ingredient_id"]
        result[ingredient_id] = {
            "sour": row["sour"],
            "sweet": row["sweet"],
            "bitter": row["bitter"],
            "aroma": row["aroma"],
            "fruity": row["fruity"],
            "body": row["body"]
        }
    
    return result


def calculate_recipe_features(recipe_id: int, snapshot_id: str = "s0") -> Optional[Dict]:
    """
    计算 recipe 的整体风味向量和角色分布
    """
    # 加载 recipe 原料
    ingredients = load_recipe_ingredients(recipe_id)
    if not ingredients:
        return None
    
    # 提取 ingredient_ids
    ingredient_ids = [ing["ingredient_id"] for ing in ingredients]
    
    # 加载原料风味特征
    flavor_features = load_ingredient_flavor_features(ingredient_ids)
    
    # 计算总用量
    total_amount = 0.0
    valid_ingredients = []
    
    for ing in ingredients:
        amount = ing.get("parsed_amount")
        if amount is not None and amount > 0:
            total_amount += amount
            valid_ingredients.append(ing)
    
    if total_amount == 0:
        return None
    
    # Step 3: 计算 recipe 的整体风味向量 F(G_r) = Σ α_i f_i
    # α_i 是基于用量的权重
    flavor_vector = {dim: 0.0 for dim in FLAVOR_DIMENSIONS}
    
    for ing in valid_ingredients:
        ingredient_id = ing["ingredient_id"]
        amount = ing["parsed_amount"]
        
        # 计算权重 α_i = amount / total_amount
        alpha_i = amount / total_amount
        
        # 获取风味特征 f_i
        features = flavor_features.get(ingredient_id)
        if features:
            # 加权累加
            for dim in FLAVOR_DIMENSIONS:
                value = features.get(dim, 0.0)
                # 确保 f_i 每维都在 [0, 1] 范围内
                # 处理 Decimal 类型
                if hasattr(value, 'as_tuple'):  # 检查是否为 Decimal 类型
                    value = float(value)
                value = max(0.0, min(1.0, value))
                flavor_vector[dim] += alpha_i * value
    
    # 确保最终向量的每维都在 [0, 1] 范围内
    for dim in FLAVOR_DIMENSIONS:
        flavor_vector[dim] = max(0.0, min(1.0, flavor_vector[dim]))
    
    # Step 4: 计算 role 分布 R(G_r)
    # 按用量聚合，p_k = (Σ_{i:role(i)=k} u_i) / (Σ_j u_j)
    role_distribution = {role: 0.0 for role in ROLE_TYPES}
    
    # 计算所有原料的总用量（分母）
    total_u = total_amount
    
    for ing in valid_ingredients:
        role = ing.get("role", "").lower().replace('_', ' ')
        u_i = ing["parsed_amount"]  # u_i 是原料 i 的用量
        
        # 映射角色到标准类型
        if "base" in role:
            role_distribution["base"] += u_i
        elif "acid" in role:
            role_distribution["acid"] += u_i
        elif "sweet" in role:
            role_distribution["sweetener"] += u_i
        elif "modifier" in role:
            role_distribution["modifier"] += u_i
        elif "bitter" in role:
            role_distribution["bitters"] += u_i
        elif "garnish" in role:
            role_distribution["garnish"] += u_i
        elif "dilution" in role:
            role_distribution["dilution"] += u_i
        elif "other" in role:
            role_distribution["other"] += u_i
    
    # 计算各角色的占比 p_k
    for role in ROLE_TYPES:
        if total_u > 0:
            role_distribution[role] = role_distribution[role] / total_u
        else:
            role_distribution[role] = 0.0
    
    # 计算与目标模板的距离（简单实现，使用默认模板）
    # 这里使用一个默认的平衡模板
    default_flavor_template = {"sour": 0.3, "sweet": 0.3, "bitter": 0.2, "aroma": 0.4, "fruity": 0.3, "body": 0.5}
    default_role_template = {"base": 0.4, "acid": 0.2, "sweetener": 0.2, "modifier": 0.05, "bitters": 0.03, "garnish": 0.02, "dilution": 0.05, "other": 0.05}
    
    # 计算风味距离
    flavor_dist = 0.0
    for dim in FLAVOR_DIMENSIONS:
        flavor_dist += (flavor_vector[dim] - default_flavor_template[dim]) ** 2
    flavor_dist = math.sqrt(flavor_dist)
    
    # 计算角色距离
    role_dist = 0.0
    for role in ROLE_TYPES:
        role_dist += (role_distribution[role] - default_role_template[role]) ** 2
    role_dist = math.sqrt(role_dist)
    
    # 计算平衡分数
    flavor_balance_score = -flavor_dist  # 距离越小，分数越高
    role_balance_score = -role_dist      # 距离越小，分数越高
    final_balance_score = 0.5 * flavor_balance_score + 0.5 * role_balance_score
    
    return {
        "recipe_id": recipe_id,
        "snapshot_id": snapshot_id,
        "family": "sour",  # 暂时默认 family 为 sour
        "flavor_vector": flavor_vector,
        "role_distribution": role_distribution,
        "flavor_dist": flavor_dist,
        "role_dist": role_dist,
        "flavor_balance_score": flavor_balance_score,
        "role_balance_score": role_balance_score,
        "final_balance_score": final_balance_score,
        "num_ingredients": len(valid_ingredients),
        "total_amount": total_amount
    }


def insert_recipe_balance_feature(result: Dict):
    """
    将计算结果插入到 recipe_balance_feature 表
    """
    sql = text("""
    INSERT INTO recipe_balance_feature (
        recipe_id,
        snapshot_id,
        family,
        f_sour,
        f_sweet,
        f_bitter,
        f_aroma,
        f_fruity,
        f_body,
        r_base,
        r_acid,
        r_sweetener,
        r_modifier,
        r_bitters,
        r_garnish,
        r_dilution,
        r_other,
        flavor_dist,
        role_dist,
        flavor_balance_score,
        role_balance_score,
        final_balance_score,
        computed_at
    ) VALUES (
        :recipe_id,
        :snapshot_id,
        :family,
        :f_sour,
        :f_sweet,
        :f_bitter,
        :f_aroma,
        :f_fruity,
        :f_body,
        :r_base,
        :r_acid,
        :r_sweetener,
        :r_modifier,
        :r_bitters,
        :r_garnish,
        :r_dilution,
        :r_other,
        :flavor_dist,
        :role_dist,
        :flavor_balance_score,
        :role_balance_score,
        :final_balance_score,
        :computed_at
    ) ON DUPLICATE KEY UPDATE
        family = VALUES(family),
        f_sour = VALUES(f_sour),
        f_sweet = VALUES(f_sweet),
        f_bitter = VALUES(f_bitter),
        f_aroma = VALUES(f_aroma),
        f_fruity = VALUES(f_fruity),
        f_body = VALUES(f_body),
        r_base = VALUES(r_base),
        r_acid = VALUES(r_acid),
        r_sweetener = VALUES(r_sweetener),
        r_modifier = VALUES(r_modifier),
        r_bitters = VALUES(r_bitters),
        r_garnish = VALUES(r_garnish),
        r_dilution = VALUES(r_dilution),
        r_other = VALUES(r_other),
        flavor_dist = VALUES(flavor_dist),
        role_dist = VALUES(role_dist),
        flavor_balance_score = VALUES(flavor_balance_score),
        role_balance_score = VALUES(role_balance_score),
        final_balance_score = VALUES(final_balance_score),
        computed_at = VALUES(computed_at)
    """)
    
    params = {
        "recipe_id": result["recipe_id"],
        "snapshot_id": result["snapshot_id"],
        "family": result["family"],
        "f_sour": result["flavor_vector"]["sour"],
        "f_sweet": result["flavor_vector"]["sweet"],
        "f_bitter": result["flavor_vector"]["bitter"],
        "f_aroma": result["flavor_vector"]["aroma"],
        "f_fruity": result["flavor_vector"]["fruity"],
        "f_body": result["flavor_vector"]["body"],
        "r_base": result["role_distribution"]["base"],
        "r_acid": result["role_distribution"]["acid"],
        "r_sweetener": result["role_distribution"]["sweetener"],
        "r_modifier": result["role_distribution"]["modifier"],
        "r_bitters": result["role_distribution"]["bitters"],
        "r_garnish": result["role_distribution"]["garnish"],
        "r_dilution": result["role_distribution"]["dilution"],
        "r_other": result["role_distribution"]["other"],
        "flavor_dist": result["flavor_dist"],
        "role_dist": result["role_dist"],
        "flavor_balance_score": result["flavor_balance_score"],
        "role_balance_score": result["role_balance_score"],
        "final_balance_score": result["final_balance_score"],
        "computed_at": datetime.now()
    }
    
    with engine.begin() as conn:
        conn.execute(sql, params)
    
    print(f"[INFO] 已插入 recipe {result['recipe_id']} 的平衡特征")


def process_all_recipes(limit: int = 100, snapshot_id: str = "s0"):
    """
    处理所有 recipe 并将结果插入到数据库
    """
    # 创建表
    create_recipe_balance_feature_table()
    
    # 获取 recipe_id 列表
    sql = text("""
    SELECT DISTINCT recipe_id
    FROM recipe_ingredient
    LIMIT :limit
    """)
    
    with engine.begin() as conn:
        rows = conn.execute(sql, {"limit": limit}).mappings().all()
    
    recipe_ids = [row["recipe_id"] for row in rows]
    
    # 处理每个 recipe
    for i, recipe_id in enumerate(recipe_ids, 1):
        print(f"处理 recipe {i}/{len(recipe_ids)}: {recipe_id}")
        try:
            result = calculate_recipe_features(recipe_id, snapshot_id)
            if result:
                insert_recipe_balance_feature(result)
        except Exception as e:
            print(f"处理 recipe {recipe_id} 时出错: {e}")


def main():
    """
    主函数
    """
    import json
    
    # 先创建表
    create_recipe_balance_feature_table()
    
    # 测试单个 recipe
    test_recipe_id = 1
    print(f"测试 recipe {test_recipe_id}...")
    result = calculate_recipe_features(test_recipe_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 插入到数据库
    if result:
        insert_recipe_balance_feature(result)
    
    # 批量处理所有 recipes
    print("\n批量处理所有 recipes...")
    process_all_recipes(limit=10000)  # 设置一个足够大的值来处理所有 recipe


if __name__ == "__main__":
    main()
