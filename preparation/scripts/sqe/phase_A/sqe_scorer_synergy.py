# -*- coding: utf-8 -*-
"""
鸡尾酒配方的 Phase A 规则版图评分器（SQE v1）

功能：
1. 对数据库中的每个 recipe_id，构建一个 recipe graph
2. 计算可解释的结构分数，先实现协同项 S_synergy
3. 输出每个 recipe 的：
   - 总分 sqe_score
   - pair 级别贡献明细
   - top 正贡献 pair
   - 缺失边统计
   - 各子项统计

当前阶段只做规则版 Phase A，不使用训练模型，不使用 GNN。
"""

import os
import sys
import re
from typing import Dict, List, Tuple, Optional, Any

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
# 向上两级到项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.db import get_engine
import pandas as pd
from sqlalchemy import text

# 数据库引擎
engine = get_engine()

# 配置参数
# LAMBDA_FLAVOR = 0.4  # 风味权重 lambda1
# LAMBDA_COOCCUR = 0.3  # 共现权重 lamda2
# LAMBDA_ANCHOR = 0.3  # 锚点相似度权重 lambda3
LAMBDA_FLAVOR = 0.45  # 风味权重 lambda1
LAMBDA_COOCCUR = 0.45  # 共现权重 lamda2
LAMBDA_ANCHOR = 0.1  # 锚点相似度权重 lambda3

# 配置参数接口
def set_synergy_weights(flavor_weight=0.45, cooccur_weight=0.45, anchor_weight=0.1):
    """
    设置 synergy 评分器的权重参数
    
    参数:
    flavor_weight: 风味兼容度权重
    cooccur_weight: 共现权重
    anchor_weight: 锚点相似度权重
    """
    global LAMBDA_FLAVOR, LAMBDA_COOCCUR, LAMBDA_ANCHOR
    LAMBDA_FLAVOR = flavor_weight
    LAMBDA_COOCCUR = cooccur_weight
    LAMBDA_ANCHOR = anchor_weight

# 全局统计变量
flavor_edge_total_loaded = 0
flavor_edge_hit_count = 0
flavor_edge_miss_count = 0
cooccur_edge_total_loaded = 0
cooccur_edge_hit_count = 0
cooccur_edge_miss_count = 0


# =========================================================
# 数据加载函数
# =========================================================
def load_recipe_ingredients(recipe_id: int) -> List[Dict]:
    """
    加载指定 recipe 的原料信息
    """
    sql = text("""
    SELECT
        recipe_id,
        ingredient_id,
        line_no,
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
    
    # 打印调试信息
    if recipe_id == 1:  # 只在测试 recipe 时打印
        print("\n===== Recipe Ingredient 调试信息 =====")
        print(f"Recipe {recipe_id} 的原料数量: {len(rows)}")
        for i, row in enumerate(rows[:3]):  # 打印前 3 个原料
            print(f"原料 {i+1}: id={row['ingredient_id']}, amount={row['amount']}, unit={row['unit']}, raw_text={row['raw_text']}")
        print("====================================\n")
    
    return [dict(row) for row in rows]


def load_ingredient_info(ingredient_ids: List[int]) -> Dict[int, Dict]:
    """
    加载指定原料的详细信息
    """
    if not ingredient_ids:
        return {}
    
    # 加载 flavor anchor 信息
    anchor_sql = text("""
    SELECT
        ingredient_id,
        anchor_name,
        anchor_form,
        match_confidence
    FROM ingredient_flavor_anchor
    WHERE ingredient_id IN :ids
    """)
    
    # 加载 type 信息
    type_sql = text("""
    SELECT
        ingredient_id,
        type_tag,
        confidence
    FROM ingredient_type
    WHERE ingredient_id IN :ids
    """)
    
    # 加载 flavor feature 信息
    feature_sql = text("""
    SELECT
        ingredient_id,
        anchor_name,
        sour,
        sweet,
        bitter,
        aroma,
        fruity,
        body,
        feature_confidence
    FROM ingredient_flavor_feature
    WHERE ingredient_id IN :ids
    """)
    
    # 加载 canonical id 信息
    canonical_sql = text("""
    SELECT
        src_ingredient_id,
        canonical_id
    FROM llm_canonical_map
    WHERE src_ingredient_id IN :ids
    """)
    
    with engine.begin() as conn:
        anchor_rows = conn.execute(anchor_sql, {"ids": ingredient_ids}).mappings().all()
        type_rows = conn.execute(type_sql, {"ids": ingredient_ids}).mappings().all()
        feature_rows = conn.execute(feature_sql, {"ids": ingredient_ids}).mappings().all()
        canonical_rows = conn.execute(canonical_sql, {"ids": ingredient_ids}).mappings().all()
    
    # 构建结果字典
    result = {}
    for ingredient_id in ingredient_ids:
        result[ingredient_id] = {
            "anchor_name": None,
            "anchor_form": None,
            "match_confidence": None,
            "type_tag": None,
            "type_confidence": None,
            "sour": None,
            "sweet": None,
            "bitter": None,
            "aroma": None,
            "fruity": None,
            "body": None,
            "feature_confidence": None,
            "canonical_id": None
        }
    
    # 填充 anchor 信息
    for row in anchor_rows:
        ingredient_id = row["ingredient_id"]
        result[ingredient_id]["anchor_name"] = row["anchor_name"]
        result[ingredient_id]["anchor_form"] = row["anchor_form"]
        result[ingredient_id]["match_confidence"] = row["match_confidence"]
    
    # 填充 type 信息
    for row in type_rows:
        ingredient_id = row["ingredient_id"]
        result[ingredient_id]["type_tag"] = row["type_tag"]
        result[ingredient_id]["type_confidence"] = row["confidence"]
    
    # 填充 feature 信息
    for row in feature_rows:
        ingredient_id = row["ingredient_id"]
        result[ingredient_id]["sour"] = row["sour"]
        result[ingredient_id]["sweet"] = row["sweet"]
        result[ingredient_id]["bitter"] = row["bitter"]
        result[ingredient_id]["aroma"] = row["aroma"]
        result[ingredient_id]["fruity"] = row["fruity"]
        result[ingredient_id]["body"] = row["body"]
        result[ingredient_id]["feature_confidence"] = row["feature_confidence"]
    
    # 填充 canonical id 信息
    for row in canonical_rows:
        ingredient_id = row["src_ingredient_id"]
        result[ingredient_id]["canonical_id"] = row["canonical_id"]
    
    return result


def load_edge_weights(ingredient_ids: List[int], snapshot_id: Optional[str] = None) -> Dict[Tuple[int, int], Dict[str, float]]:
    """
    加载原料对的边权重信息
    """
    global flavor_edge_total_loaded, flavor_edge_hit_count, flavor_edge_miss_count
    global cooccur_edge_total_loaded, cooccur_edge_hit_count, cooccur_edge_miss_count
    
    if not ingredient_ids or len(ingredient_ids) < 2:
        return {}
    
    # 加载 canonical id 映射
    canonical_sql = text("""
    SELECT
        src_ingredient_id,
        canonical_id
    FROM llm_canonical_map
    WHERE src_ingredient_id IN :ids
    """)
    
    with engine.begin() as conn:
        canonical_rows = conn.execute(canonical_sql, {"ids": ingredient_ids}).mappings().all()
        
        # 构建 ingredient_id 到 canonical_id 的映射
        id_map = {row["src_ingredient_id"]: row["canonical_id"] for row in canonical_rows}
        canonical_ids = list(id_map.values())
    
    # 加载共现边权重（使用 canonical_id）
    cooccur_sql = text("""
    SELECT
        i_id,
        j_id,
        weight
    FROM graph_edge_stats_v2
    WHERE (i_id IN :canonical_ids AND j_id IN :canonical_ids)
    """)
    
    # 加载风味兼容度边权重（使用 canonical_id）
    compat_sql = text("""
    SELECT
        i_canonical_id,
        j_canonical_id,
        weight
    FROM graph_flavor_compat_edge_stats
    WHERE (i_canonical_id IN :canonical_ids AND j_canonical_id IN :canonical_ids)
    """)
    
    with engine.begin() as conn:
        cooccur_rows = conn.execute(cooccur_sql, {"canonical_ids": canonical_ids}).mappings().all()
        compat_rows = conn.execute(compat_sql, {"canonical_ids": canonical_ids}).mappings().all()
    
    # 构建结果字典，使用排序后的 (i,j) 作为键
    result = {}
    
    # 处理共现边
    cooccur_edge_total_loaded += len(cooccur_rows)
    for row in cooccur_rows:
        # 找到对应的原始 ingredient_id
        i_canonical = row["i_id"]
        j_canonical = row["j_id"]
        
        # 反向查找 ingredient_id
        i_ingredient = None
        j_ingredient = None
        for ing_id, can_id in id_map.items():
            if can_id == i_canonical:
                i_ingredient = ing_id
            if can_id == j_canonical:
                j_ingredient = ing_id
            if i_ingredient and j_ingredient:
                break
        
        if i_ingredient and j_ingredient:
            i, j = sorted([i_ingredient, j_ingredient])
            edge_key = (i, j)
            if edge_key not in result:
                result[edge_key] = {"cooccur_raw": 0.0, "cooccur_used": 0.0, "flavor": 0.0}
            result[edge_key]["cooccur_raw"] = float(row["weight"])
            result[edge_key]["cooccur_used"] = max(0.0, float(row["weight"]))
    
    # 处理风味兼容度边
    flavor_edge_total_loaded += len(compat_rows)
    for row in compat_rows:
        # 找到对应的原始 ingredient_id
        i_canonical = row["i_canonical_id"]
        j_canonical = row["j_canonical_id"]
        
        # 反向查找 ingredient_id
        i_ingredient = None
        j_ingredient = None
        for ing_id, can_id in id_map.items():
            if can_id == i_canonical:
                i_ingredient = ing_id
            if can_id == j_canonical:
                j_ingredient = ing_id
            if i_ingredient and j_ingredient:
                break
        
        if i_ingredient and j_ingredient:
            i, j = sorted([i_ingredient, j_ingredient])
            edge_key = (i, j)
            if edge_key not in result:
                result[edge_key] = {"cooccur_raw": 0.0, "cooccur_used": 0.0, "flavor": 0.0}
            result[edge_key]["flavor"] = float(row["weight"])
    
    # 打印调试信息
    # if ingredient_ids and len(ingredient_ids) <= 10:  # 只在测试时打印
    #     print("\n===== Edge Weights 调试信息 =====")
    #     print(f"Recipe 原料 ID: {ingredient_ids}")
    #     print(f"Canonical ID 映射: {id_map}")
    #     print(f"Flavor compat edge 匹配数量: {len(compat_rows)}")
    #     print(f"Cooccur edge 匹配数量: {len(cooccur_rows)}")
    #     print("====================================\n")
    
    return result


# =========================================================
# 规则函数
# =========================================================
def safe_parse_amount(amount: Any) -> Optional[float]:
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

# 求sim，主要是本身的（风味）属性
def calc_anchor_similarity(anchor_info_i: Dict, anchor_info_j: Dict) -> float:
    """
    计算两个原料的锚点相似度
    """
    # 检查是否有缺失的 anchor 信息
    if not anchor_info_i.get("anchor_name") or not anchor_info_j.get("anchor_name"):
        return 0.0
    
    # 若 anchor_name 完全相同
    if anchor_info_i["anchor_name"] == anchor_info_j["anchor_name"]:
        return 1.0
    # 若 anchor_name 不同，但 anchor_form 相同
    elif anchor_info_i.get("anchor_form") and anchor_info_j.get("anchor_form") and \
         anchor_info_i["anchor_form"] == anchor_info_j["anchor_form"]:
        return 0.5
    # 否则
    else:
        return 0.0

# 现阶段，此处的角色兼容规则是自定义的
def calc_role_compatibility(role_i: str, role_j: str) -> float:
    """
    计算两个原料的角色兼容度
    """
    # 统一转小写并标准化（替换下划线为空格）
    role_i = role_i.lower().replace('_', ' ') if role_i else ""
    role_j = role_j.lower().replace('_', ' ') if role_j else ""
    
    # 定义角色兼容规则
    rules = [
        # (role1, role2, score)
        ("base spirit", "sweetener", 1.2),
        ("sweetener", "base spirit", 1.2),
        ("base spirit", "modifier", 1.1),
        ("modifier", "base spirit", 1.1),
        ("base spirit", "acid", 1.2),
        ("acid", "base spirit", 1.2),
        ("sweetener", "acid", 1.1),
        ("acid", "sweetener", 1.1),
        ("modifier", "modifier", 0.9),
    ]
    
    # 检查是否有 garnish
    if "garnish" in role_i or "garnish" in role_j:
        return 0.6
    
    # 检查规则
    for r1, r2, score in rules:
        if (r1 in role_i and r2 in role_j) or (r2 in role_i and r1 in role_j):
            return score
    
    # 都为空或无法识别，或其他组合
    return 1.0


def calc_amount_modifier(amount_i: Optional[float], amount_j: Optional[float], 
                        role_i: str, role_j: str) -> float:
    """
    计算 amount 权重修正项
    """
    # 如果双方 amount 都存在
    if amount_i is not None and amount_j is not None:
        if amount_i >= 1.0 and amount_j >= 1.0:
            return 1.2
        elif (amount_i >= 1.0 and amount_j < 1.0) or (amount_i < 1.0 and amount_j >= 1.0):
            return 1.0
        else:  # 双方都 < 1.0
            return 0.8
    else:  # amount 缺失，基于 role 的简化规则
        # 定义主成分角色
        main_roles = ["base spirit", "sweetener", "acid"]
        role_i = role_i.lower().replace('_', ' ') if role_i else ""
        role_j = role_j.lower().replace('_', ' ') if role_j else ""
        
        # 检查是否两个都是主成分
        i_is_main = any(role in role_i for role in main_roles)
        j_is_main = any(role in role_j for role in main_roles)
        
        if i_is_main and j_is_main:
            return 1.1
        else:
            return 1.0


# =========================================================
# Recipe Graph 构建函数
# =========================================================
def build_recipe_graph(recipe_id: int) -> Tuple[List[Dict], Dict[int, Dict], Dict[Tuple[int, int], Dict[str, float]]]:
    """
    构建 recipe graph
    
    返回：
    - 节点列表
    - 原料信息字典
    - 边权重字典
    """
    # 加载 recipe 原料
    ingredients = load_recipe_ingredients(recipe_id)
    if not ingredients:
        return [], {}, {}
    
    # 提取 ingredient_ids
    ingredient_ids = [ing["ingredient_id"] for ing in ingredients]
    
    # 加载原料详细信息
    ingredient_info = load_ingredient_info(ingredient_ids)
    
    # 构建节点列表
    nodes = []
    amount_non_empty_count = 0
    
    for ing in ingredients:
        ingredient_id = ing["ingredient_id"]
        info = ingredient_info.get(ingredient_id, {})
        
        # 解析 amount
        original_amount = ing["amount"]
        parsed_amount = safe_parse_amount(original_amount)
        if original_amount is not None and original_amount != '':
            amount_non_empty_count += 1
        
        node = {
            "ingredient_id": ingredient_id,
            "amount": original_amount,
            "parsed_amount": parsed_amount,
            "unit": ing["unit"],
            "role": ing["role"],
            "line_no": ing["line_no"],
            "raw_text": ing["raw_text"],
            "type_tag": info.get("type_tag"),
            "anchor_name": info.get("anchor_name"),
            "anchor_form": info.get("anchor_form"),
            "sour": info.get("sour"),
            "sweet": info.get("sweet"),
            "bitter": info.get("bitter"),
            "aroma": info.get("aroma"),
            "fruity": info.get("fruity"),
            "body": info.get("body")
        }
        nodes.append(node)
    
    # 打印调试信息
    if recipe_id == 1:  # 只在测试 recipe 时打印
        print("\n===== Amount 和 Anchor 调试信息 =====")
        print(f"Amount 非空记录数: {amount_non_empty_count}/{len(ingredients)}")
        
        # 打印 amount 解析情况
        print("\nAmount 解析情况:")
        for i, node in enumerate(nodes[:3]):  # 打印前 3 个节点
            print(f"原料 {i+1}: 原始 amount={node['amount']}, 解析后={node['parsed_amount']}")
        
        # 打印 anchor 信息
        print("\nAnchor 信息示例:")
        for i, node in enumerate(nodes[:3]):  # 打印前 3 个节点
            print(f"原料 {i+1}: anchor_name={node['anchor_name']}, anchor_form={node['anchor_form']}")
        print("====================================\n")
    
    # 加载边权重
    edge_weights = load_edge_weights(ingredient_ids)
    
    return nodes, ingredient_info, edge_weights


# =========================================================
# Pair 打分函数
# =========================================================
def score_pair(node_i: Dict, node_j: Dict, edge_weights: Dict[Tuple[int, int], Dict[str, float]]) -> Dict:
    """
    对原料对进行打分
    """
    global flavor_edge_hit_count, flavor_edge_miss_count
    global cooccur_edge_hit_count, cooccur_edge_miss_count
    
    i_id = node_i["ingredient_id"]
    j_id = node_j["ingredient_id"]
    
    # 获取边权重
    edge_key = tuple(sorted([i_id, j_id]))
    weights = edge_weights.get(edge_key, {"cooccur_raw": 0.0, "cooccur_used": 0.0, "flavor": 0.0})
    w_flavor = weights.get("flavor", 0.0)
    w_cooccur_raw = weights.get("cooccur_raw", 0.0)
    w_cooccur_used = weights.get("cooccur_used", 0.0)
    
    # 统计命中情况
    if w_flavor > 0:
        flavor_edge_hit_count += 1
    else:
        flavor_edge_miss_count += 1
    
    if w_cooccur_raw != 0:
        cooccur_edge_hit_count += 1
    else:
        cooccur_edge_miss_count += 1
    
    # 计算 anchor 相似度
    anchor_info_i = {
        "anchor_name": node_i["anchor_name"],
        "anchor_form": node_i["anchor_form"]
    }
    anchor_info_j = {
        "anchor_name": node_j["anchor_name"],
        "anchor_form": node_j["anchor_form"]
    }
    sim_anchor = calc_anchor_similarity(anchor_info_i, anchor_info_j)
    
    # 计算角色兼容度
    c_role = calc_role_compatibility(node_i["role"], node_j["role"])
    
    # 计算 amount 修正项
    u_ij = calc_amount_modifier(node_i["parsed_amount"], node_j["parsed_amount"], 
                               node_i["role"], node_j["role"])
    
    # 计算 m_ij
    m_ij = u_ij * c_role
    
    # 计算各子项贡献
    flavor_term = m_ij * LAMBDA_FLAVOR * w_flavor
    cooccur_term = m_ij * LAMBDA_COOCCUR * w_cooccur_used
    anchor_term = m_ij * LAMBDA_ANCHOR * sim_anchor
    
    # 计算总贡献
    pair_score = flavor_term + cooccur_term + anchor_term
    
    return {
        "i_id": i_id,
        "j_id": j_id,
        "i_role": node_i["role"],
        "j_role": node_j["role"],
        "i_amount": node_i["parsed_amount"],
        "j_amount": node_j["parsed_amount"],
        "w_flavor": w_flavor,
        "w_cooccur_raw": w_cooccur_raw,
        "w_cooccur_used": w_cooccur_used,
        "sim_anchor": sim_anchor,
        "role_compat": c_role,
        "amount_modifier": u_ij,
        "m_ij": m_ij,
        "flavor_term": flavor_term,
        "cooccur_term": cooccur_term,
        "anchor_term": anchor_term,
        "pair_score": pair_score,
        "flavor_edge_found": w_flavor > 0,
        "cooccur_edge_found": w_cooccur_raw != 0,
        "anchor_info_found": node_i["anchor_name"] is not None and node_j["anchor_name"] is not None
    }


# =========================================================
# Recipe 打分函数
# =========================================================
def score_recipe(recipe_id: int) -> Dict:
    """
    对 recipe 进行打分
    """
    # 构建 recipe graph
    nodes, ingredient_info, edge_weights = build_recipe_graph(recipe_id)
    
    if not nodes:
        return {
            "recipe_id": recipe_id,
            "num_nodes": 0,
            "pair_count": 0,
            "missing_edges": 0,
            "missing_flavor_edges": 0,
            "missing_cooccur_edges": 0,
            "edge_coverage": 0.0,
            "score_confidence": "low",
            "sum_flavor_term": 0.0,
            "sum_cooccur_term": 0.0,
            "sum_anchor_term": 0.0,
            "synergy_score": 0.0,
            "sqe_score": 0.0,
            "pair_contributions": [],
            "top_positive_pairs": []
        }
    
    # 计算所有原料对的贡献
    pair_contributions = []
    missing_edges = 0
    missing_flavor_edges = 0
    missing_cooccur_edges = 0
    sum_flavor_term = 0.0
    sum_cooccur_term = 0.0
    sum_anchor_term = 0.0
    
    # 遍历所有两两组合
    n = len(nodes)
    for i in range(n):
        for j in range(i + 1, n):
            node_i = nodes[i]
            node_j = nodes[j]
            
            # 打分
            contrib = score_pair(node_i, node_j, edge_weights)
            pair_contributions.append(contrib)
            
            # 统计缺失边
            edge_key = tuple(sorted([node_i["ingredient_id"], node_j["ingredient_id"]]))
            if edge_key not in edge_weights:
                missing_edges += 1
            
            # 统计缺失的 flavor edges
            if contrib["w_flavor"] == 0:
                missing_flavor_edges += 1
            
            # 统计缺失的 cooccur edges
            if contrib["w_cooccur_raw"] == 0:
                missing_cooccur_edges += 1
            
            # 累计子项贡献
            sum_flavor_term += contrib["flavor_term"]
            sum_cooccur_term += contrib["cooccur_term"]
            sum_anchor_term += contrib["anchor_term"]
    
    # 计算总分
    synergy_score = sum(contrib["pair_score"] for contrib in pair_contributions)
    sqe_score = synergy_score
    
    # 计算 top 正贡献 pair
    top_positive_pairs = sorted(
        pair_contributions,
        key=lambda x: x["pair_score"],
        reverse=True
    )[:5]  # 取前 5 个
    
    # 计算统计信息
    pair_count = len(pair_contributions)
    edge_coverage = 0.0
    if pair_count > 0:
        edge_coverage = 1 - (missing_edges / pair_count)
    
    # 计算 score_confidence
    score_confidence = "low"
    if edge_coverage >= 0.7:
        score_confidence = "high"
    elif edge_coverage >= 0.4:
        score_confidence = "medium"
    
    return {
        "recipe_id": recipe_id,
        "num_nodes": n,
        "pair_count": pair_count,
        "missing_edges": missing_edges,
        "missing_flavor_edges": missing_flavor_edges,
        "missing_cooccur_edges": missing_cooccur_edges,
        "edge_coverage": edge_coverage,
        "score_confidence": score_confidence,
        "sum_flavor_term": sum_flavor_term,
        "sum_cooccur_term": sum_cooccur_term,
        "sum_anchor_term": sum_anchor_term,
        "synergy_score": synergy_score,
        "sqe_score": sqe_score,
        "pair_contributions": pair_contributions,
        "top_positive_pairs": top_positive_pairs
    }


# =========================================================
# 批量处理函数
# =========================================================
def score_all_recipes() -> Tuple[List[Dict], pd.DataFrame, pd.DataFrame]:
    """
    批量处理所有 recipe
    """
    # 获取 recipe_id 列表
    sql = text("""
    SELECT DISTINCT recipe_id
    FROM recipe_ingredient
    """)
    
    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()
    
    recipe_ids = [row["recipe_id"] for row in rows]
    results = []
    pair_details = []
    
    # 处理每个 recipe
    for i, recipe_id in enumerate(recipe_ids, 1):
        print(f"处理 recipe {i}/{len(recipe_ids)}: {recipe_id}")
        try:
            result = score_recipe(recipe_id)
            results.append(result)
            
            # 收集 pair 级别的详细信息
            for contrib in result.get("pair_contributions", []):
                pair_detail = {
                    "recipe_id": recipe_id,
                    "i_id": contrib["i_id"],
                    "j_id": contrib["j_id"],
                    "i_role": contrib["i_role"],
                    "j_role": contrib["j_role"],
                    "i_amount": contrib["i_amount"],
                    "j_amount": contrib["j_amount"],
                    "w_flavor": contrib["w_flavor"],
                    "w_cooccur_raw": contrib["w_cooccur_raw"],
                    "w_cooccur_used": contrib["w_cooccur_used"],
                    "sim_anchor": contrib["sim_anchor"],
                    "role_compat": contrib["role_compat"],
                    "amount_modifier": contrib["amount_modifier"],
                    "m_ij": contrib["m_ij"],
                    "flavor_term": contrib["flavor_term"],
                    "cooccur_term": contrib["cooccur_term"],
                    "anchor_term": contrib["anchor_term"],
                    "pair_score": contrib["pair_score"],
                    "flavor_edge_found": contrib["flavor_edge_found"],
                    "cooccur_edge_found": contrib["cooccur_edge_found"],
                    "anchor_info_found": contrib["anchor_info_found"]
                }
                pair_details.append(pair_detail)
        except Exception as e:
            print(f"处理 recipe {recipe_id} 时出错: {e}")
            # 记录错误但继续处理
            results.append({
                "recipe_id": recipe_id,
                "num_nodes": 0,
                "pair_count": 0,
                "missing_edges": 0,
                "missing_flavor_edges": 0,
                "missing_cooccur_edges": 0,
                "edge_coverage": 0.0,
                "score_confidence": "low",
                "sum_flavor_term": 0.0,
                "sum_cooccur_term": 0.0,
                "sum_anchor_term": 0.0,
                "synergy_score": 0.0,
                "sqe_score": 0.0,
                "error": str(e)
            })
    
    # 构建 DataFrames
    recipe_score_df = pd.DataFrame(results)
    pair_detail_df = pd.DataFrame(pair_details)
    
    return results, recipe_score_df, pair_detail_df


# =========================================================
# 主函数
# =========================================================
def score_recipe_from_ingredients(ingredients: List[Dict]) -> Dict:
    """
    计算给定配方的协同分数
    
    参数:
    ingredients: 原料列表，每个原料是一个字典，包含以下字段:
        - ingredient_id: 原料 ID
        - amount: 原料用量
        - unit: 单位
        - role: 角色
        - line_no: 行号
        - raw_text: 原始文本
    
    返回:
    包含协同分数的字典
    """
    try:
        if not ingredients:
            return {
                "recipe_id": "custom",
                "num_nodes": 0,
                "pair_count": 0,
                "missing_edges": 0,
                "missing_flavor_edges": 0,
                "missing_cooccur_edges": 0,
                "edge_coverage": 0.0,
                "score_confidence": "low",
                "sum_flavor_term": 0.0,
                "sum_cooccur_term": 0.0,
                "sum_anchor_term": 0.0,
                "synergy_score": 0.0,
                "sqe_score": 0.0,
                "pair_contributions": [],
                "top_positive_pairs": []
            }
        
        # 提取 ingredient_ids
        ingredient_ids = [ing["ingredient_id"] for ing in ingredients]
        
        # 加载原料详细信息
        ingredient_info = load_ingredient_info(ingredient_ids)
        
        # 构建节点列表
        nodes = []
        for ing in ingredients:
            ingredient_id = ing["ingredient_id"]
            info = ingredient_info.get(ingredient_id, {})
            
            # 解析 amount
            original_amount = ing["amount"]
            parsed_amount = safe_parse_amount(original_amount)
            
            node = {
                "ingredient_id": ingredient_id,
                "amount": original_amount,
                "parsed_amount": parsed_amount,
                "unit": ing["unit"],
                "role": ing["role"],
                "line_no": ing["line_no"],
                "raw_text": ing["raw_text"],
                "type_tag": info.get("type_tag"),
                "anchor_name": info.get("anchor_name"),
                "anchor_form": info.get("anchor_form"),
                "sour": info.get("sour"),
                "sweet": info.get("sweet"),
                "bitter": info.get("bitter"),
                "aroma": info.get("aroma"),
                "fruity": info.get("fruity"),
                "body": info.get("body")
            }
            nodes.append(node)
        
        # 加载边权重
        edge_weights = load_edge_weights(ingredient_ids)
        
        # 计算所有原料对的贡献
        pair_contributions = []
        missing_edges = 0
        missing_flavor_edges = 0
        missing_cooccur_edges = 0
        sum_flavor_term = 0.0
        sum_cooccur_term = 0.0
        sum_anchor_term = 0.0
        
        # 遍历所有两两组合
        n = len(nodes)
        for i in range(n):
            for j in range(i + 1, n):
                node_i = nodes[i]
                node_j = nodes[j]
                
                # 打分
                contrib = score_pair(node_i, node_j, edge_weights)
                pair_contributions.append(contrib)
                
                # 统计缺失边
                edge_key = tuple(sorted([node_i["ingredient_id"], node_j["ingredient_id"]]))
                if edge_key not in edge_weights:
                    missing_edges += 1
                
                # 统计缺失的 flavor edges
                if contrib["w_flavor"] == 0:
                    missing_flavor_edges += 1
                
                # 统计缺失的 cooccur edges
                if contrib["w_cooccur_raw"] == 0:
                    missing_cooccur_edges += 1
                
                # 累计子项贡献
                sum_flavor_term += contrib["flavor_term"]
                sum_cooccur_term += contrib["cooccur_term"]
                sum_anchor_term += contrib["anchor_term"]
        
        # 计算总分
        synergy_score = sum(contrib["pair_score"] for contrib in pair_contributions)
        sqe_score = synergy_score
        
        # 计算 top 正贡献 pair
        top_positive_pairs = sorted(
            pair_contributions,
            key=lambda x: x["pair_score"],
            reverse=True
        )[:5]  # 取前 5 个
        
        # 计算统计信息
        pair_count = len(pair_contributions)
        edge_coverage = 0.0
        if pair_count > 0:
            edge_coverage = 1 - (missing_edges / pair_count)
        
        # 计算 score_confidence
        score_confidence = "low"
        if edge_coverage >= 0.7:
            score_confidence = "high"
        elif edge_coverage >= 0.4:
            score_confidence = "medium"
        
        return {
            "recipe_id": "custom",
            "num_nodes": n,
            "pair_count": pair_count,
            "missing_edges": missing_edges,
            "missing_flavor_edges": missing_flavor_edges,
            "missing_cooccur_edges": missing_cooccur_edges,
            "edge_coverage": edge_coverage,
            "score_confidence": score_confidence,
            "sum_flavor_term": sum_flavor_term,
            "sum_cooccur_term": sum_cooccur_term,
            "sum_anchor_term": sum_anchor_term,
            "synergy_score": synergy_score,
            "sqe_score": sqe_score,
            "pair_contributions": pair_contributions,
            "top_positive_pairs": top_positive_pairs
        }
    except Exception as e:
        print(f"[ERROR] 处理自定义配方时出错: {e}")
        # 记录错误但返回默认值
        return {
            "recipe_id": "custom",
            "num_nodes": 0,
            "pair_count": 0,
            "missing_edges": 0,
            "missing_flavor_edges": 0,
            "missing_cooccur_edges": 0,
            "edge_coverage": 0.0,
            "score_confidence": "low",
            "sum_flavor_term": 0.0,
            "sum_cooccur_term": 0.0,
            "sum_anchor_term": 0.0,
            "synergy_score": 0.0,
            "sqe_score": 0.0,
            "pair_contributions": [],
            "top_positive_pairs": []
        }

def main():
    """
    主函数
    """
    import json
    
    # 重置全局统计变量
    global flavor_edge_total_loaded, flavor_edge_hit_count, flavor_edge_miss_count
    global cooccur_edge_total_loaded, cooccur_edge_hit_count, cooccur_edge_miss_count
    flavor_edge_total_loaded = 0
    flavor_edge_hit_count = 0
    flavor_edge_miss_count = 0
    cooccur_edge_total_loaded = 0
    cooccur_edge_hit_count = 0
    cooccur_edge_miss_count = 0
    
    # 测试单个 recipe
    test_recipe_id = 1
    print(f"测试 recipe {test_recipe_id}...")
    result = score_recipe(test_recipe_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 批量处理所有 recipes
    print("\n批量处理所有 recipes...")
    results, recipe_score_df, pair_detail_df = score_all_recipes()
    
    # 保存结果
    output_file = os.path.join(_project_root, "data", "sqe_scores.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 保存 DataFrames
    recipe_score_csv = os.path.join(_project_root, "data", "recipe_scores.csv")
    pair_detail_csv = os.path.join(_project_root, "data", "pair_details.csv")
    recipe_score_df.to_csv(recipe_score_csv, index=False, encoding="utf-8")
    pair_detail_df.to_csv(pair_detail_csv, index=False, encoding="utf-8")
    
    # 计算调试统计信息
    total_recipes = len(results)
    total_pairs = len(pair_detail_df)
    flavor_edge_hit_rate = flavor_edge_hit_count / (flavor_edge_hit_count + flavor_edge_miss_count) if (flavor_edge_hit_count + flavor_edge_miss_count) > 0 else 0
    cooccur_edge_hit_rate = cooccur_edge_hit_count / (cooccur_edge_hit_count + cooccur_edge_miss_count) if (cooccur_edge_hit_count + cooccur_edge_miss_count) > 0 else 0
    avg_edge_coverage = recipe_score_df["edge_coverage"].mean() if not recipe_score_df.empty else 0
    negative_synergy_count = len(recipe_score_df[recipe_score_df["synergy_score"] < 0]) if not recipe_score_df.empty else 0
    
    # 打印调试信息
    print("\n===== 调试统计信息 =====")
    print(f"总 recipe 数: {total_recipes}")
    print(f"总 pair 数: {total_pairs}")
    print(f"Flavor edge 命中率: {flavor_edge_hit_rate:.2%} ({flavor_edge_hit_count}/{flavor_edge_hit_count + flavor_edge_miss_count})")
    print(f"Cooccur edge 命中率: {cooccur_edge_hit_rate:.2%} ({cooccur_edge_hit_count}/{cooccur_edge_hit_count + cooccur_edge_miss_count})")
    print(f"平均 edge coverage: {avg_edge_coverage:.2%}")
    print(f"Synergy score 为负的 recipe 数量: {negative_synergy_count}")
    print("====================")
    
    print(f"\n结果保存到:")
    print(f"- JSON 文件: {output_file}")
    print(f"- Recipe 分数 CSV: {recipe_score_csv}")
    print(f"- Pair 详情 CSV: {pair_detail_csv}")


if __name__ == "__main__":
    main()
