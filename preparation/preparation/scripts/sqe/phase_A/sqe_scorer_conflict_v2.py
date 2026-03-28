# -*- coding: utf-8 -*-
"""
计算 SQE 的 conflict 项目 (v4)

功能：
1. 基于原始计算公式计算冲突分数
2. 先标准化子项，再加权求和
3. 处理极端值和长尾分布
4. 修复 None 值和除零错误
5. 生成包含冲突分数的 CSV 文件
"""

import os
import sys
import math
import csv
import re
from typing import Dict, List, Tuple, Optional, Any

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_script_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from src.db import get_engine
import pandas as pd
from sqlalchemy import text

# 数据库引擎
engine = get_engine()

# 配置参数
# ETA_FLAVOR = 1.0    # 风味冲突权重
# ETA_ROLE = 1.2      # 角色冲突权重
# ETA_TYPE = 0.8      # 类型冲突权重
# ETA_RATIO = 0.8     # 比例冲突权重
ETA_FLAVOR = 1.1525
ETA_ROLE   = 0.8797
ETA_TYPE   = 1.1886
ETA_RATIO  = 0.5787
# 配置参数接口
def set_conflict_weights(flavor_weight=1.1525, role_weight=0.8797, type_weight=1.1886, ratio_weight=0.5787):
    """
    设置 conflict 评分器的权重参数
    
    参数:
    flavor_weight: 风味冲突权重
    role_weight: 角色冲突权重
    type_weight: 类型冲突权重
    ratio_weight: 比例冲突权重
    """
    global ETA_FLAVOR, ETA_ROLE, ETA_TYPE, ETA_RATIO
    ETA_FLAVOR = flavor_weight
    ETA_ROLE = role_weight
    ETA_TYPE = type_weight
    ETA_RATIO = ratio_weight

ALPHA_1 = 0.8       # base 过多惩罚权重
ALPHA_2 = 1.0       # 缺少 backbone 惩罚权重
ALPHA_3 = 1.2       # 酸甜失衡惩罚权重
ALPHA_4 = 0.6       # modifier 过多惩罚权重


TAU_Q = 0.35        # 单一原料占比阈值
base_max = 2        # 最多 base spirit 数量

# =========================================================
# 工具函数
# =========================================================
def safe_float(value: Any, default: float = 0.0) -> float:
    """
    安全转换为 float
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_parse_amount(amount: Any) -> float:
    """
    安全解析 amount 字段
    """
    if amount is None:
        return 0.0
    
    try:
        # 处理 Decimal 类型
        if hasattr(amount, 'as_tuple'):
            return float(amount)
        # 处理字符串类型
        elif isinstance(amount, str):
            cleaned_amount = amount.strip()
            # 处理分数形式
            # 处理带整数的分数，如 "1 1/2"
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
        pass
    
    return 0.0

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    安全除法
    """
    if denominator == 0:
        return default
    return numerator / denominator

def normalize_score(score: float, max_possible: float = 10.0) -> float:
    """
    标准化得分到 [0, 1] 区间
    """
    if max_possible <= 0:
        return 0.0
    return max(0.0, min(1.0, score / max_possible))

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
    
    with engine.begin() as conn:
        anchor_rows = conn.execute(anchor_sql, {"ids": ingredient_ids}).mappings().all()
        type_rows = conn.execute(type_sql, {"ids": ingredient_ids}).mappings().all()
        feature_rows = conn.execute(feature_sql, {"ids": ingredient_ids}).mappings().all()
    
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
            "feature_confidence": None
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
    
    return result

def load_edge_weights(ingredient_ids: List[int]) -> Dict[Tuple[int, int], Dict[str, float]]:
    """
    加载原料对的边权重信息
    """
    if not ingredient_ids or len(ingredient_ids) < 2:
        return {}
    
    # 加载共现边权重
    cooccur_sql = text("""
    SELECT
        i_id,
        j_id,
        weight
    FROM graph_edge_stats_v2
    WHERE (i_id IN :ingredient_ids AND j_id IN :ingredient_ids)
    """)
    
    with engine.begin() as conn:
        cooccur_rows = conn.execute(cooccur_sql, {"ingredient_ids": ingredient_ids}).mappings().all()
    
    # 构建结果字典，使用排序后的 (i,j) 作为键
    result = {}
    for row in cooccur_rows:
        i, j = sorted([row["i_id"], row["j_id"]])
        edge_key = (i, j)
        if edge_key not in result:
            result[edge_key] = {"cooccur_raw": 0.0, "cooccur_used": 0.0}
        result[edge_key]["cooccur_raw"] = float(row["weight"])
        result[edge_key]["cooccur_used"] = max(0.0, float(row["weight"]))
    
    return result

# =========================================================
# 规则函数
# =========================================================
def calc_flavor_conflict(node_i: Dict, node_j: Dict, cooccur_weight: float) -> float:
    """
    计算风味差异冲突
    """
    # 检查是否有 dilution 角色
    if "dilution" in node_i["role"].lower() or "dilution" in node_j["role"].lower():
        return 0.0
    
    # 计算风味特征距离
    flavor_features = ["sour", "sweet", "bitter", "aroma", "fruity", "body"]
    dist = 0.0
    valid_features = 0
    
    for feature in flavor_features:
        val_i = node_i.get(feature)
        val_j = node_j.get(feature)
        if val_i is not None and val_j is not None:
            dist += (safe_float(val_i) - safe_float(val_j)) ** 2
            valid_features += 1
    
    if valid_features > 0:
        dist = math.sqrt(safe_divide(dist, valid_features))
    else:
        dist = 0.0
    
    # 计算共现支持
    normalized_cooccur = max(0.0, min(1.0, cooccur_weight))
    
    # 计算冲突分数
    tau_f = 0.3  # 风味距离阈值
    c_flavor = max(0.0, dist - tau_f) * (1 - normalized_cooccur)
    
    return c_flavor

def calc_type_conflict(node1: Dict, node2: Dict, total_amount: float) -> float:
    """
    计算类型冲突
    """
    # 检查双强 base 冲突
    if "base" in node1["role"].lower() and "base" in node2["role"].lower():
        amount1 = node1.get("parsed_amount", 0.0)
        amount2 = node2.get("parsed_amount", 0.0)
        if total_amount > 0:
            share1 = safe_divide(amount1, total_amount)
            share2 = safe_divide(amount2, total_amount)
            if share1 > 0.25 and share2 > 0.25:
                return 1.0
    
    # 检查 cream × acid 冲突
    form1 = node1.get("anchor_form", "").lower()
    form2 = node2.get("anchor_form", "").lower()
    role1 = node1["role"].lower()
    role2 = node2["role"].lower()
    
    is_cream1 = "cream" in form1 or "dairy" in form1
    is_acid1 = "acid" in role1 or "citrus" in form1 or "juice" in form1
    is_cream2 = "cream" in form2 or "dairy" in form2
    is_acid2 = "acid" in role2 or "citrus" in form2 or "juice" in form2
    
    if (is_cream1 and is_acid2) or (is_cream2 and is_acid1):
        return 1.0
    
    # 检查明显 form 不兼容
    incompatible_pairs = [
        ("spirit", "cream"),
        ("cream", "spirit"),
        ("syrup", "bitters"),
        ("bitters", "syrup")
    ]
    
    if (form1, form2) in incompatible_pairs:
        return 0.6
    
    return 0.0

def calc_role_conflict(recipe_id: int, nodes: List[Dict]) -> Dict:
    """
    计算角色冲突
    """
    # 统计 base spirit 数量
    base_count = 0
    for node in nodes:
        if "base" in node["role"].lower():
            base_count += 1
    
    # R1: base 过多惩罚
    # 改进：当 base 数量超过 1 时就开始惩罚，惩罚值随 base 数量增加而增加
    c_base_over = max(0, base_count - 1) * 2.0  # 每多一个 base 惩罚 2.0
    
    # R2: 缺少 backbone 惩罚
    c_no_backbone = 1 if base_count == 0 else 0
    
    # R3: 酸甜失衡惩罚
    acid_total = 0.0
    sweet_total = 0.0
    for node in nodes:
        if "acid" in node["role"].lower():
            amount = node.get("parsed_amount", 0.0)
            acid_total += safe_float(amount)
        elif "sweet" in node["role"].lower():
            amount = node.get("parsed_amount", 0.0)
            sweet_total += safe_float(amount)
    
    epsilon = 1e-6
    p_r = safe_divide(acid_total + epsilon, sweet_total + epsilon)
    las = 0.6  # 酸甜比例下界
    uas = 1.4  # 酸甜比例上界
    
    if p_r < las:
        c_acid_sweet = las - p_r
    elif p_r > uas:
        c_acid_sweet = p_r - uas
    else:
        c_acid_sweet = 0.0
    
    # 限制酸甜失衡惩罚
    c_acid_sweet = min(c_acid_sweet, 2.0)  # 上限 2.0
    
    # R4: modifier 过多惩罚
    modifier_count = 0
    main_count = 0
    for node in nodes:
        role = node["role"].lower()
        if "modifier" in role:
            modifier_count += 1
        elif any(r in role for r in ["base", "acid", "sweet"]):
            main_count += 1
    
    K = 1.5
    # 避免除零错误
    if main_count == 0:
        c_modifier_over = 0.0
    else:
        c_modifier_over = max(0, modifier_count - K * main_count)
    
    # 限制 modifier 过多惩罚
    c_modifier_over = min(c_modifier_over, 5.0)  # 上限 5.0
    
    # 计算总角色冲突
    c_role = ALPHA_1 * c_base_over + ALPHA_2 * c_no_backbone + ALPHA_3 * c_acid_sweet + ALPHA_4 * c_modifier_over
    
    return {
        "c_base_over": c_base_over,
        "c_no_backbone": c_no_backbone,
        "c_acid_sweet": c_acid_sweet,
        "c_modifier_over": c_modifier_over,
        "c_role": c_role
    }

def calc_ratio_conflict(nodes: List[Dict]) -> float:
    """
    计算比例冲突
    """
    total_amount = 0.0
    for node in nodes:
        amount = node.get("parsed_amount", 0.0)
        total_amount += safe_float(amount)
    
    if total_amount <= 0:
        return 0.0
    
    c_ratio = 0.0
    for node in nodes:
        amount = node.get("parsed_amount", 0.0)
        if amount is not None:
            q_i = safe_divide(safe_float(amount), total_amount)
            # 计算极端风味强度
            sour = node.get("sour", 0.0)
            bitter = node.get("bitter", 0.0)
            e_i = max(safe_float(sour), safe_float(bitter))
            # 计算比例冲突
            c_i = max(0.0, q_i - TAU_Q) * e_i
            c_ratio += c_i
    
    # 限制比例冲突
    c_ratio = min(c_ratio, 5.0)  # 上限 5.0
    
    return c_ratio

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
    
    return nodes, ingredient_info, edge_weights

# =========================================================
# Pair 冲突计算函数
# =========================================================
def score_conflict_pair(node_i: Dict, node_j: Dict, edge_weights: Dict[Tuple[int, int], Dict[str, float]], total_amount: float) -> Dict:
    """
    计算原料对的冲突分数
    """
    i_id = node_i["ingredient_id"]
    j_id = node_j["ingredient_id"]
    
    # 获取边权重
    edge_key = tuple(sorted([i_id, j_id]))
    weights = edge_weights.get(edge_key, {"cooccur_raw": 0.0, "cooccur_used": 0.0})
    w_cooccur_raw = weights.get("cooccur_raw", 0.0)
    
    # 计算风味冲突
    c_flavor = calc_flavor_conflict(node_i, node_j, w_cooccur_raw)
    
    # 计算类型冲突
    c_type = calc_type_conflict(node_i, node_j, total_amount)
    
    return {
        "i_id": i_id,
        "j_id": j_id,
        "i_role": node_i["role"],
        "j_role": node_j["role"],
        "i_amount": node_i["parsed_amount"],
        "j_amount": node_j["parsed_amount"],
        "w_cooccur_raw": w_cooccur_raw,
        "c_flavor": c_flavor,
        "c_type": c_type,
        "total_conflict": c_flavor + c_type
    }

# =========================================================
# Recipe 冲突计算函数
# =========================================================
def calculate_conflict_score(recipe_id: int) -> Dict:
    """
    计算冲突分数
    """
    try:
        # 构建 recipe graph
        nodes, ingredient_info, edge_weights = build_recipe_graph(recipe_id)
        
        if not nodes:
            return {
                "recipe_id": recipe_id,
                "num_nodes": 0,
                "pair_count": 0,
                "C_flavor": 0.0,
                "C_role": 0.0,
                "C_type": 0.0,
                "C_ratio": 0.0,
                "C_flavor_norm": 0.0,
                "C_role_norm": 0.0,
                "C_type_norm": 0.0,
                "C_ratio_norm": 0.0,
                "conflict_score": 0.0,
                "conflict_normalized": 0.0
            }
        
        # 计算总用量
        total_amount = 0.0
        for node in nodes:
            amount = node.get("parsed_amount", 0.0)
            total_amount += safe_float(amount)
        
        # 计算所有原料对的冲突
        pair_conflicts = []
        c_flavor_total = 0.0
        c_type_total = 0.0
        
        # 遍历所有两两组合
        n = len(nodes)
        for i in range(n):
            for j in range(i + 1, n):
                node_i = nodes[i]
                node_j = nodes[j]
                
                # 计算冲突
                conflict = score_conflict_pair(node_i, node_j, edge_weights, total_amount)
                pair_conflicts.append(conflict)
                
                # 累计冲突分数
                c_flavor_total += conflict["c_flavor"]
                c_type_total += conflict["c_type"]
        
        # 计算角色冲突
        role_conflict = calc_role_conflict(recipe_id, nodes)
        c_role = role_conflict["c_role"]
        
        # 计算比例冲突
        c_ratio = calc_ratio_conflict(nodes)
        
        # 标准化各子项
        # 估计最大可能值
        max_flavor = n * (n - 1) / 2 * 1.0  # 每对最大 1.0
        max_role = ALPHA_1 * 5 + ALPHA_2 * 1 + ALPHA_3 * 2 + ALPHA_4 * 5  # 估计最大值
        max_type = n * (n - 1) / 2 * 1.0  # 每对最大 1.0
        max_ratio = 5.0  # 最大 5.0
        
        # 标准化
        C_flavor_norm = normalize_score(c_flavor_total, max_flavor)
        C_role_norm = normalize_score(c_role, max_role)
        C_type_norm = normalize_score(c_type_total, max_type)
        C_ratio_norm = normalize_score(c_ratio, max_ratio)
        
        # 加权求和计算总冲突分数
        conflict_score = (ETA_FLAVOR * C_flavor_norm +
                         ETA_ROLE * C_role_norm +
                         ETA_TYPE * C_type_norm +
                         ETA_RATIO * C_ratio_norm) / (ETA_FLAVOR + ETA_ROLE + ETA_TYPE + ETA_RATIO)
        
        # 最终标准化
        conflict_normalized = normalize_score(conflict_score, 1.0)
        
        return {
            "recipe_id": recipe_id,
            "num_nodes": n,
            "pair_count": len(pair_conflicts),
            "C_flavor": c_flavor_total,
            "C_role": c_role,
            "C_type": c_type_total,
            "C_ratio": c_ratio,
            "C_flavor_norm": C_flavor_norm,
            "C_role_norm": C_role_norm,
            "C_type_norm": C_type_norm,
            "C_ratio_norm": C_ratio_norm,
            "conflict_score": conflict_score,
            "conflict_normalized": conflict_normalized
        }
    except Exception as e:
        print(f"[ERROR] 处理 recipe {recipe_id} 时出错: {e}")
        # 记录错误但返回默认值
        return {
            "recipe_id": recipe_id,
            "num_nodes": 0,
            "pair_count": 0,
            "C_flavor": 0.0,
            "C_role": 0.0,
            "C_type": 0.0,
            "C_ratio": 0.0,
            "C_flavor_norm": 0.0,
            "C_role_norm": 0.0,
            "C_type_norm": 0.0,
            "C_ratio_norm": 0.0,
            "conflict_score": 0.0,
            "conflict_normalized": 0.0
        }

def calculate_conflict_score_from_ingredients(ingredients: List[Dict]) -> Dict:
    """
    计算给定配方的冲突分数
    
    参数:
    ingredients: 原料列表，每个原料是一个字典，包含以下字段:
        - ingredient_id: 原料 ID
        - amount: 原料用量
        - unit: 单位
        - role: 角色
        - line_no: 行号
        - raw_text: 原始文本
    
    返回:
    包含冲突分数的字典
    """
    try:
        if not ingredients:
            return {
                "recipe_id": "custom",
                "num_nodes": 0,
                "pair_count": 0,
                "C_flavor": 0.0,
                "C_role": 0.0,
                "C_type": 0.0,
                "C_ratio": 0.0,
                "C_flavor_norm": 0.0,
                "C_role_norm": 0.0,
                "C_type_norm": 0.0,
                "C_ratio_norm": 0.0,
                "conflict_score": 0.0,
                "conflict_normalized": 0.0
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
        
        # 计算总用量
        total_amount = 0.0
        for node in nodes:
            amount = node.get("parsed_amount", 0.0)
            total_amount += safe_float(amount)
        
        # 计算所有原料对的冲突
        pair_conflicts = []
        c_flavor_total = 0.0
        c_type_total = 0.0
        
        # 遍历所有两两组合
        n = len(nodes)
        for i in range(n):
            for j in range(i + 1, n):
                node_i = nodes[i]
                node_j = nodes[j]
                
                # 计算冲突
                conflict = score_conflict_pair(node_i, node_j, edge_weights, total_amount)
                pair_conflicts.append(conflict)
                
                # 累计冲突分数
                c_flavor_total += conflict["c_flavor"]
                c_type_total += conflict["c_type"]
        
        # 计算角色冲突
        role_conflict = calc_role_conflict(0, nodes)  # 使用 0 作为虚拟 recipe_id
        c_role = role_conflict["c_role"]
        
        # 计算比例冲突
        c_ratio = calc_ratio_conflict(nodes)
        
        # 标准化各子项
        # 估计最大可能值
        max_flavor = n * (n - 1) / 2 * 1.0  # 每对最大 1.0
        max_role = ALPHA_1 * 5 + ALPHA_2 * 1 + ALPHA_3 * 2 + ALPHA_4 * 5  # 估计最大值
        max_type = n * (n - 1) / 2 * 1.0  # 每对最大 1.0
        max_ratio = 5.0  # 最大 5.0
        
        # 标准化
        C_flavor_norm = normalize_score(c_flavor_total, max_flavor)
        C_role_norm = normalize_score(c_role, max_role)
        C_type_norm = normalize_score(c_type_total, max_type)
        C_ratio_norm = normalize_score(c_ratio, max_ratio)
        
        # 加权求和计算总冲突分数
        conflict_score = (ETA_FLAVOR * C_flavor_norm +
                         ETA_ROLE * C_role_norm +
                         ETA_TYPE * C_type_norm +
                         ETA_RATIO * C_ratio_norm) / (ETA_FLAVOR + ETA_ROLE + ETA_TYPE + ETA_RATIO)
        
        # 最终标准化
        conflict_normalized = normalize_score(conflict_score, 1.0)
        
        return {
            "recipe_id": "custom",
            "num_nodes": n,
            "pair_count": len(pair_conflicts),
            "C_flavor": c_flavor_total,
            "C_role": c_role,
            "C_type": c_type_total,
            "C_ratio": c_ratio,
            "C_flavor_norm": C_flavor_norm,
            "C_role_norm": C_role_norm,
            "C_type_norm": C_type_norm,
            "C_ratio_norm": C_ratio_norm,
            "conflict_score": conflict_score,
            "conflict_normalized": conflict_normalized
        }
    except Exception as e:
        print(f"[ERROR] 处理自定义配方时出错: {e}")
        # 记录错误但返回默认值
        return {
            "recipe_id": "custom",
            "num_nodes": 0,
            "pair_count": 0,
            "C_flavor": 0.0,
            "C_role": 0.0,
            "C_type": 0.0,
            "C_ratio": 0.0,
            "C_flavor_norm": 0.0,
            "C_role_norm": 0.0,
            "C_type_norm": 0.0,
            "C_ratio_norm": 0.0,
            "conflict_score": 0.0,
            "conflict_normalized": 0.0
        }

# =========================================================
# 批量处理函数
# =========================================================
def score_conflict_all_recipes() -> List[Dict]:
    """
    计算所有食谱的冲突分数
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
    total = len(recipe_ids)
    
    for i, recipe_id in enumerate(recipe_ids):
        if (i + 1) % 100 == 0:
            print(f"[INFO] 处理中: {i + 1}/{total}")
        
        # 计算冲突分数
        result = calculate_conflict_score(recipe_id)
        results.append(result)
    
    return results

# =========================================================
# 保存函数
# =========================================================
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
        "recipe_id", "num_nodes", "pair_count",
        "C_flavor", "C_role", "C_type", "C_ratio",
        "C_flavor_norm", "C_role_norm", "C_type_norm", "C_ratio_norm",
        "conflict_score", "conflict_normalized"
    ]
    
    # 写入 CSV 文件
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
    
    print(f"[INFO] 结果已保存到: {output_file}")

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("计算 SQE 的 conflict 项目 (v2)...")
    
    # 计算所有食谱的冲突分数
    results = score_conflict_all_recipes()
    
    # 保存结果到 CSV 文件
    output_file = os.path.join(_project_root, "data", "sqe_conflict_results_v2.csv")
    save_to_csv(results, output_file)
    
    # 统计冲突分数
    valid_results = [r for r in results if r.get("conflict_score") is not None]
    
    if valid_results:
        total_conflict = sum(r["conflict_score"] for r in valid_results)
        total_normalized = sum(r["conflict_normalized"] for r in valid_results)
        
        avg_conflict = total_conflict / len(valid_results)
        avg_normalized = total_normalized / len(valid_results)
        
        print("\n[INFO] 平均冲突分数:")
        print(f"[INFO]   原始冲突分数: {avg_conflict:.4f}")
        print(f"[INFO]   标准化冲突分数: {avg_normalized:.4f}")
        
        # 统计子项分数
        total_flavor = sum(r["C_flavor"] for r in valid_results)
        total_role = sum(r["C_role"] for r in valid_results)
        total_type = sum(r["C_type"] for r in valid_results)
        total_ratio = sum(r["C_ratio"] for r in valid_results)
        
        avg_flavor = total_flavor / len(valid_results)
        avg_role = total_role / len(valid_results)
        avg_type = total_type / len(valid_results)
        avg_ratio = total_ratio / len(valid_results)
        
        print("\n[INFO] 平均子项分数:")
        print(f"[INFO]   风味冲突: {avg_flavor:.4f}")
        print(f"[INFO]   角色冲突: {avg_role:.4f}")
        print(f"[INFO]   类型冲突: {avg_type:.4f}")
        print(f"[INFO]   比例冲突: {avg_ratio:.4f}")
    else:
        print("\n[INFO] 没有有效结果")

if __name__ == "__main__":
    main()
