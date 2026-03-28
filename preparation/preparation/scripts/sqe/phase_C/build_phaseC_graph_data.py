# -*- coding: utf-8 -*-
"""
Phase C 图数据构建脚本

功能：
1. 读取 Phase A/Phase B 结果数据
2. 为每个 recipe 构建标准图样本
3. 整理 pairwise 训练对
4. 按原始 recipe_id 进行分组划分
5. 保存图数据和配对数据
"""

import os
import sys
import json
import pickle
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from sklearn.preprocessing import StandardScaler, LabelEncoder

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 输入文件
    RECIPE_INGREDIENT_FILE = os.path.join(_project_root, "data", "ingredient", "hotaling_cocktails.csv")
    PHASE_A_BASELINE_FILE = os.path.join(_project_root, "data", "phaseA", "phaseA_baseline_v2.csv")
    PHASE_B_PAIRS_FILE = os.path.join(_project_root, "data", "phaseB", "phaseB_pairwise_dataset_v3_valid.csv")
    PHASE_C_RECIPES_FILE = os.path.join(_project_root, "data", "phaseC", "recipes_data.jsonl")
    PHASE_C_PAIRS_FILE = os.path.join(_project_root, "data", "phaseC", "pairs_data.jsonl")
    
    # 输出文件
    GRAPHS_OUTPUT_FILE = os.path.join(_project_root, "data", "phaseC", "graphs_phaseC.pt")
    PAIRS_OUTPUT_FILE = os.path.join(_project_root, "data", "phaseC", "pairs_phaseC.csv")
    
    # 划分比例
    TRAIN_RATIO = 0.6
    VALID_RATIO = 0.2
    TEST_RATIO = 0.2

# =========================================================
# 数据加载函数
# =========================================================

def load_recipe_ingredients() -> pd.DataFrame:
    """
    加载 recipe 原料数据
    """
    from src.db import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    sql = text("""
    SELECT recipe_id, ingredient_id, amount, unit, role, line_no, raw_text
    FROM recipe_ingredient
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条原料数据")
    return df

def load_ingredients() -> pd.DataFrame:
    """
    加载原料信息
    """
    from src.db import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    sql = text("""
    SELECT i.ingredient_id, i.name_norm, i.category, i.is_alcoholic, i.abv,
           it.type_tag
    FROM ingredient i
    LEFT JOIN ingredient_type it ON i.ingredient_id = it.ingredient_id
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条原料信息")
    return df

def load_canonical_ingredients() -> pd.DataFrame:
    """
    加载 canonical ingredient 信息
    """
    from src.db import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    sql = text("""
    SELECT ingredient_id, canonical_id, canonical_name, anchor_name
    FROM ingredient_flavor_anchor
    WHERE canonical_id IS NOT NULL
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条 canonical ingredient 信息")
    return df

def load_edge_features() -> Dict:
    """
    加载边特征
    """
    from src.db import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    edge_features = {}
    
    # 加载共现强度
    print("[INFO] 加载共现强度边特征...")
    sql = text("""
    SELECT i_id, j_id, weight as cooccur
    FROM graph_edge_stats_v2
    WHERE snapshot_id = (SELECT MAX(snapshot_id) FROM graph_edge_stats_v2)
    """)
    
    with engine.begin() as conn:
        cooccur_df = pd.read_sql(sql, conn)
    
    for _, row in cooccur_df.iterrows():
        key = (row['i_id'], row['j_id'])
        if key not in edge_features:
            edge_features[key] = {}
        edge_features[key]['cooccur'] = float(row['cooccur'])
    
    # 加载风味兼容性
    print("[INFO] 加载风味兼容性边特征...")
    sql = text("""
    SELECT i_canonical_id, j_canonical_id, compat_score as flavor, role_bonus as role
    FROM graph_flavor_compat_edge_stats
    WHERE snapshot_id = (SELECT MAX(snapshot_id) FROM graph_flavor_compat_edge_stats)
    """)
    
    with engine.begin() as conn:
        flavor_df = pd.read_sql(sql, conn)
    
    for _, row in flavor_df.iterrows():
        key = (row['i_canonical_id'], row['j_canonical_id'])
        if key not in edge_features:
            edge_features[key] = {}
        edge_features[key]['flavor'] = float(row['flavor'])
        edge_features[key]['role'] = float(row['role'])
    
    print(f"[INFO] 加载了 {len(edge_features)} 条边特征")
    return edge_features

def load_phaseA_baseline() -> pd.DataFrame:
    """
    加载 Phase A 基线数据
    """
    if not os.path.exists(Config.PHASE_A_BASELINE_FILE):
        raise FileNotFoundError(f"Phase A 基线文件不存在: {Config.PHASE_A_BASELINE_FILE}")
    
    df = pd.read_csv(Config.PHASE_A_BASELINE_FILE)
    print(f"[INFO] 加载了 {len(df)} 条 Phase A 基线数据")
    return df

def load_phaseB_pairs() -> pd.DataFrame:
    """
    加载 Phase B 配对数据
    """
    if not os.path.exists(Config.PHASE_B_PAIRS_FILE):
        raise FileNotFoundError(f"Phase B 配对文件不存在: {Config.PHASE_B_PAIRS_FILE}")
    
    df = pd.read_csv(Config.PHASE_B_PAIRS_FILE)
    print(f"[INFO] 加载了 {len(df)} 条 Phase B 配对数据")
    return df

def generate_perturbed_recipe(original_recipe: Dict, perturb_type: str, hard_negative=False) -> Dict:
    """
    根据扰动类型生成扰动后的配方
    
    参数:
    original_recipe: 原始配方数据
    perturb_type: 扰动类型
    hard_negative: 是否生成 hard negative 样本
    
    返回:
    扰动后的配方数据
    """
    # 导入必要的模块
    import hashlib
    import random
    import copy
    
    # 深度复制原始配方数据，避免修改原始数据
    perturbed_recipe = copy.deepcopy(original_recipe)
    
    # 生成新的 recipe_id
    perturb_id = hashlib.md5((str(original_recipe['recipe_id']) + perturb_type + ('_hard' if hard_negative else '')).encode()).hexdigest()
    perturbed_recipe['recipe_id'] = f"perturbed_{perturb_id}"
    
    # 获取原始原料
    nodes = perturbed_recipe.get('nodes', [])
    
    # 根据扰动类型进行扰动
    if perturb_type == 'balance_change_role':
        # 改变原料角色
        if nodes:
            # 随机选择一个非关键原料改变其角色
            non_critical_nodes = [i for i, node in enumerate(nodes) if 'base' not in node.get('role', '').lower()]
            if non_critical_nodes:
                idx = random.choice(non_critical_nodes)
                node = nodes[idx]
                # 改变角色为相似的角色
                current_role = node.get('role', 'other')
                role_groups = {
                    'base': ['base', 'base_spirit'],
                    'modifier': ['modifier', 'liqueur'],
                    'sweetener': ['sweetener', 'syrup'],
                    'acid': ['acid', 'juice'],
                    'bitters': ['bitters'],
                    'garnish': ['garnish'],
                    'dilution': ['dilution']
                }
                # 找到当前角色所属的组
                current_group = None
                for group, roles in role_groups.items():
                    if any(r in current_role.lower() for r in roles):
                        current_group = group
                        break
                
                # 选择同一组内的其他角色或相似组
                if current_group:
                    # 同一组内的其他角色
                    same_group_roles = [r for r in role_groups[current_group] if r not in current_role.lower()]
                    if same_group_roles:
                        new_role = random.choice(same_group_roles)
                    else:
                        # 选择相似组
                        similar_groups = {'modifier': ['base'], 'base': ['modifier'], 'sweetener': ['acid'], 'acid': ['sweetener']}
                        if current_group in similar_groups:
                            similar_group = similar_groups[current_group]
                            new_role = random.choice(role_groups[similar_group[0]])
                        else:
                            new_role = current_role
                    node['role'] = new_role
    elif perturb_type == 'balance_remove_key_ingredient':
        # 移除关键原料
        if nodes and len(nodes) > 2:  # 确保至少保留 2 个原料
            # 移除非关键原料
            non_base_nodes = [i for i, node in enumerate(nodes) if 'base' not in node.get('role', '').lower()]
            if non_base_nodes:
                # 移除用量最小的非关键原料
                non_base_nodes.sort(key=lambda i: float(nodes[i].get('amount', 1.0)))
                nodes.pop(non_base_nodes[0])
    elif perturb_type == 'synergy_insert_different_type':
        # 插入不同类型的原料
        # 这里简化处理，实际上应该从数据库中选择合适的原料
        if nodes:
            # 插入用量很小的原料
            new_ingredient = {
                "id": random.randint(1000, 9999),  # 随机原料 ID
                "amount": 0.2 if hard_negative else 0.5,  # 使用更小的用量
                "unit": "oz",
                "role": "modifier",
                "line_no": len(nodes) + 1,
                "raw_text": "Perturbed Ingredient"
            }
            nodes.append(new_ingredient)
    elif perturb_type == 'synergy_replace_with_different_type':
        # 替换为不同类型的原料
        if nodes:
            # 随机选择一个非关键原料进行替换
            non_base_nodes = [i for i, node in enumerate(nodes) if 'base' not in node.get('role', '').lower()]
            if non_base_nodes:
                idx = random.choice(non_base_nodes)
                # 替换为相似类型的原料
                nodes[idx]['id'] = random.randint(1000, 9999)  # 随机原料 ID
                nodes[idx]['raw_text'] = "Similar Ingredient"
    elif perturb_type == 'conflict_acid_sweetener_ratio_break':
        # 破坏酸甜比例
        if nodes:
            # 轻微调整甜味剂或酸味剂的用量
            sweet_acid_nodes = [i for i, node in enumerate(nodes) if 'sweet' in node.get('role', '').lower() or 'acid' in node.get('role', '').lower()]
            if sweet_acid_nodes:
                idx = random.choice(sweet_acid_nodes)
                # 轻微调整用量
                multiplier = random.uniform(1.1, 1.3) if hard_negative else random.uniform(1.2, 1.5)
                nodes[idx]['amount'] = float(nodes[idx].get('amount', 1.0)) * multiplier
    elif perturb_type == 'conflict_create_incompatible_type_pair':
        # 创建不兼容的类型对
        # 这里简化处理，实际上应该插入不兼容的原料
        if nodes:
            # 插入用量很小的不兼容原料
            new_ingredient = {
                "id": random.randint(1000, 9999),  # 随机原料 ID
                "amount": 0.1 if hard_negative else 0.25,  # 使用更小的用量
                "unit": "oz",
                "role": "acid",
                "line_no": len(nodes) + 1,
                "raw_text": "Incompatible Ingredient"
            }
            nodes.append(new_ingredient)
    # 新增：轻微调整用量比例（hard negative 专用）
    elif perturb_type == 'balance_minor_amount_adjustment' and hard_negative:
        # 轻微调整原料用量
        if nodes:
            # 选择 1-2 个原料进行轻微调整
            num_adjust = min(2, len(nodes))
            adjust_indices = random.sample(range(len(nodes)), num_adjust)
            for idx in adjust_indices:
                node = nodes[idx]
                # 更轻微的调整 0.9-1.1 倍
                adjustment = random.uniform(0.9, 1.1)
                node['amount'] = float(node.get('amount', 1.0)) * adjustment
    # 新增：替换为功能相似的原料（hard negative 专用）
    elif perturb_type == 'synergy_similar_ingredient_replacement' and hard_negative:
        # 替换为功能相似但效果稍差的原料
        if nodes:
            # 选择非关键原料
            non_base_nodes = [i for i, node in enumerate(nodes) if 'base' not in node.get('role', '').lower()]
            if non_base_nodes:
                idx = random.choice(non_base_nodes)
                # 替换为相似但不同的原料
                nodes[idx]['id'] = random.randint(1000, 9999)  # 随机原料 ID
                nodes[idx]['raw_text'] = "Similar Ingredient"
    
    # 更新节点
    perturbed_recipe['nodes'] = nodes
    
    # 重新计算图级特征
    # 这里简化处理，实际上应该重新计算
    perturbed_recipe['graph_level_features']['n_ingredients'] = len(nodes)
    
    # 保持原始 base_scores（syn_B, conf_B, bal_B）
    # 不再手工调整分数，让模型通过学习图结构残差来区分正负样本
    perturbed_recipe['syn_B'] = original_recipe.get('syn_B', 0.0)
    perturbed_recipe['conf_B'] = original_recipe.get('conf_B', 0.0)
    perturbed_recipe['bal_B'] = original_recipe.get('bal_B', 0.0)
    
    return perturbed_recipe

def load_phaseC_data() -> Tuple[List[Dict], List[Dict]]:
    """
    加载 Phase C 数据
    """
    # 加载 recipes 数据
    recipes_data = []
    with open(Config.PHASE_C_RECIPES_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            recipes_data.append(data)
    
    # 加载 pairs 数据
    pairs_data = []
    with open(Config.PHASE_C_PAIRS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            pairs_data.append(data)
    
    print(f"[INFO] 加载了 {len(recipes_data)} 条 Phase C recipes 数据")
    print(f"[INFO] 加载了 {len(pairs_data)} 条 Phase C pairs 数据")
    
    # 生成扰动后的配方数据
    print("[INFO] 生成扰动后的配方数据...")
    recipe_dict = {r['recipe_id']: r for r in recipes_data}
    perturbed_recipes = []
    
    # 为每个 pair 生成扰动配方并更新 neg_recipe_id
    for pair in pairs_data:
        pos_recipe_id = pair.get('pos_recipe_id')
        perturb_type = pair.get('perturb_type')
        
        if pos_recipe_id in recipe_dict:
            original_recipe = recipe_dict[pos_recipe_id]
            perturbed_recipe = generate_perturbed_recipe(original_recipe, perturb_type)
            perturbed_recipes.append(perturbed_recipe)
            # 更新 pair 中的 neg_recipe_id 为生成的扰动配方的 recipe_id
            pair['neg_recipe_id'] = perturbed_recipe['recipe_id']
    
    # 生成 hard negative 样本
    print("[INFO] 生成 hard negative 样本...")
    hard_negative_pairs = []
    hard_negative_perturb_types = [
        'balance_minor_amount_adjustment',
        'synergy_similar_ingredient_replacement'
    ]
    
    # 为每个原始 recipe 生成 hard negative 样本
    for recipe_data in recipes_data:
        if 'perturbed_' not in str(recipe_data['recipe_id']):  # 只对原始 recipe 生成
            for perturb_type in hard_negative_perturb_types:
                # 生成 hard negative 样本
                hard_perturbed_recipe = generate_perturbed_recipe(recipe_data, perturb_type, hard_negative=True)
                perturbed_recipes.append(hard_perturbed_recipe)
                
                # 创建对应的 pair 数据
                hard_pair = {
                    'pos_recipe_id': recipe_data['recipe_id'],
                    'neg_recipe_id': hard_perturbed_recipe['recipe_id'],
                    'perturb_type': f"{perturb_type}_hard",
                    'group_id': str(recipe_data['recipe_id'])
                }
                hard_negative_pairs.append(hard_pair)
    
    # 将 hard negative pairs 添加到 pairs_data 中
    pairs_data.extend(hard_negative_pairs)
    
    # 将扰动后的配方数据添加到 recipes_data 中
    recipes_data.extend(perturbed_recipes)
    print(f"[INFO] 生成了 {len(perturbed_recipes)} 条扰动后的配方数据")
    print(f"[INFO] 生成了 {len(hard_negative_pairs)} 条 hard negative 样本")
    print(f"[INFO] 总配方数据数: {len(recipes_data)}")
    print(f"[INFO] 总配对数据数: {len(pairs_data)}")
    
    return recipes_data, pairs_data

# =========================================================
# 特征处理函数
# =========================================================

def standardize_amount(amount: float, unit: str) -> float:
    """
    标准化原料用量，转换为毫升
    
    参数:
    amount: 原料用量
    unit: 单位
    
    返回:
    标准化后的用量（毫升）
    """
    # 体积单位转换为毫升
    volume_conversion = {
        'ml': 1.0,
        'cl': 10.0,
        'l': 1000.0,
        'oz': 29.5735,
        'cup': 236.588,
        'c': 236.588,
        'tbsp': 14.7868,
        'tsp': 4.92892,
        'bsp': 4.92892,  # 假设 bsp 是 teaspoon 的变体
        'spg': 4.92892,  # 假设 spg 是 teaspoon 的变体
        'dash': 0.929292,  # 约 1/8 茶匙
        'splash': 5.0,  # 估计值
        'fill': 50.0,  # 估计值
        'top': 10.0,  # 估计值
    }
    
    # 数量单位转换为毫升（估计值）
    count_conversion = {
        'piece': 10.0,  # 估计值
        'pc': 10.0,  # 估计值
        'count': 10.0,  # 估计值
        'cube': 5.0,  # 估计值
        'cubes': 5.0,  # 估计值
        'drop': 0.05,  # 约 0.05 毫升
        'drops': 0.05,  # 约 0.05 毫升
        'microdrops': 0.01,  # 估计值
        'pinch': 0.5,  # 估计值
        'stick': 10.0,  # 估计值
        'strip': 5.0,  # 估计值
        'wedge': 10.0,  # 估计值
        'whole': 15.0,  # 估计值
        'berry': 5.0,  # 估计值
        'berries': 5.0,  # 估计值
        'leaf': 2.0,  # 估计值
        'leaves': 2.0,  # 估计值
        'sprig': 3.0,  # 估计值
        'sprigs': 3.0,  # 估计值
        'stalk': 5.0,  # 估计值
        'peel': 8.0,  # 估计值
        'disc': 3.0,  # 估计值
        'float': 10.0,  # 估计值
    }
    
    # 其他单位转换为毫升（估计值）
    other_conversion = {
        'bag': 50.0,  # 估计值
        'package': 100.0,  # 估计值
        'pkg': 100.0,  # 估计值
        'handful': 30.0,  # 估计值
        'scoop': 20.0,  # 估计值
        'part': 30.0,  # 估计值
        'tincture': 5.0,  # 估计值
        'coffee spoon': 5.0,  # 估计值
        'spoon': 10.0,  # 估计值
        'in': 1.0,  # 英寸，这里作为估计值
        'inch': 1.0,  # 英寸，这里作为估计值
        'bottle': 750.0,  # 标准酒瓶容量
        'bottles': 750.0,  # 标准酒瓶容量
        'beans': 0.5,  # 估计值
        'berry': 5.0,  # 估计值
        'berries': 5.0,  # 估计值
        'cube': 5.0,  # 估计值
        'cubes': 5.0,  # 估计值
        'microdrops': 0.01,  # 估计值
        'packages': 100.0,  # 估计值
        'peel': 8.0,  # 估计值
        'peels': 8.0,  # 估计值
        'slice': 5.0,  # 估计值
        'slices': 5.0,  # 估计值
        'stick': 10.0,  # 估计值
        'sticks': 10.0,  # 估计值
        'wedge': 10.0,  # 估计值
        'wedges': 10.0,  # 估计值
    }
    
    # 转换单位
    if unit is None:
        # 单位为 None，返回原始值
        return amount
    
    unit_lower = unit.lower()
    if unit_lower in volume_conversion:
        return amount * volume_conversion[unit_lower]
    elif unit_lower in count_conversion:
        return amount * count_conversion[unit_lower]
    elif unit_lower in other_conversion:
        return amount * other_conversion[unit_lower]
    else:
        # 未知单位，返回原始值
        return amount

def process_node_features(ingredient_id: int, ingredient_info: Dict, amount: float, unit: str, role: str, frequency_dict: Dict) -> List[float]:
    """
    处理节点特征
    
    参数:
    ingredient_id: 原料 ID
    ingredient_info: 原料信息
    amount: 原料用量
    unit: 原料单位
    role: 原料角色
    frequency_dict: 原料频率字典
    
    返回:
    节点特征向量
    """
    # 原料出现频率
    freq = frequency_dict.get(ingredient_id, 0)
    
    # 归一化频率
    max_freq = 1000  # 假设最大频率为 1000
    frequency = min(freq / max_freq, 1.0)
    
    # 原料类型（one-hot 编码）
    type_encoding = [0.0] * 7  # 7 种原料类型
    type_mapping = {'juice': 0, 'syrup': 1, 'liqueur': 2, 'spirit': 3, 'bitters': 4, 'fortified_wine': 5, 'other': 6}
    ingredient_type = ingredient_info.get('type_tag', 'other')
    type_idx = type_mapping.get(ingredient_type, 6)
    type_encoding[type_idx] = 1.0
    
    # 原料形态（one-hot 编码）
    form_encoding = [0.0] * 3  # 简化处理
    form_mapping = {'liquid': 0, 'solid': 1, 'other': 2}
    # 基于原料类型推断形态
    liquid_types = ['juice', 'syrup', 'liqueur', 'spirit', 'bitters', 'fortified_wine']
    if ingredient_type in liquid_types:
        form = 'liquid'
    else:
        form = 'other'
    form_idx = form_mapping.get(form, 2)
    form_encoding[form_idx] = 1.0
    
    # 原料角色（one-hot 编码）
    role_encoding = [0.0] * 8  # 8 种原料角色
    role_mapping = {
        'base': 0, 'base_spirit': 0,  # base 和 base_spirit 都映射到同一个索引
        'modifier': 1,
        'sweetener': 2,
        'acid': 3,
        'bitters': 4,
        'garnish': 5,
        'dilution': 6,
        'other': 7
    }
    role_lower = role.lower()
    if 'base' in role_lower:
        role_key = 'base'
    elif 'modifier' in role_lower:
        role_key = 'modifier'
    elif 'sweet' in role_lower:
        role_key = 'sweetener'
    elif 'acid' in role_lower:
        role_key = 'acid'
    elif 'bitter' in role_lower:
        role_key = 'bitters'
    elif 'garnish' in role_lower:
        role_key = 'garnish'
    elif 'dilution' in role_lower:
        role_key = 'dilution'
    else:
        role_key = 'other'
    role_idx = role_mapping.get(role_key, 7)
    role_encoding[role_idx] = 1.0
    
    # 标准化原料用量
    standardized_amount = standardize_amount(amount, unit)
    
    # 归一化用量
    max_amount = 1000.0  # 假设最大用量为 1000 毫升
    normalized_amount = min(standardized_amount / max_amount, 1.0)
    normalized_amount = max(0.0, normalized_amount)
    
    # 是否含酒精
    alcohol = 1.0 if ingredient_info.get('is_alcoholic', False) else 0.0
    
    # 酒精度（如果是酒精原料）
    abv_value = ingredient_info.get('abv', 0.0)
    abv = abv_value / 100.0 if abv_value is not None else 0.0  # 转换为 0-1 范围
    abv = max(0.0, min(1.0, abv))
    
    # 组合特征
    features = [frequency]
    features.extend(type_encoding)
    features.extend(form_encoding)
    features.extend(role_encoding)
    features.append(normalized_amount)
    features.append(alcohol)
    features.append(abv)
    
    return features

def process_edge_features(ingredient1_id: int, ingredient2_id: int, edge_features: Dict, canonical_df: pd.DataFrame) -> List[float]:
    """
    处理边特征
    
    参数:
    ingredient1_id: 原料 1 ID
    ingredient2_id: 原料 2 ID
    edge_features: 边特征字典
    canonical_df: 规范原料数据框
    
    返回:
    边特征向量
    """
    # 构建原料 ID 到规范 ID 的映射
    id_to_canonical = dict(zip(canonical_df['ingredient_id'], canonical_df['canonical_id']))
    
    # 获取规范 ID
    canonical1 = id_to_canonical.get(ingredient1_id, ingredient1_id)
    canonical2 = id_to_canonical.get(ingredient2_id, ingredient2_id)
    
    # 尝试使用原料 ID 查询
    flavor_compat = edge_features.get((ingredient1_id, ingredient2_id), {}).get('flavor', 0.5)
    cooccur = edge_features.get((ingredient1_id, ingredient2_id), {}).get('cooccur', 0.5)
    anchor_similarity = edge_features.get((ingredient1_id, ingredient2_id), {}).get('anchor', 0.5)
    role_compat = edge_features.get((ingredient1_id, ingredient2_id), {}).get('role', 0.5)
    
    # 如果风味兼容性或角色兼容性未找到，尝试使用规范 ID 查询
    if flavor_compat == 0.5 or role_compat == 0.5:
        flavor_compat = edge_features.get((canonical1, canonical2), {}).get('flavor', flavor_compat)
        role_compat = edge_features.get((canonical1, canonical2), {}).get('role', role_compat)
    
    # 如果共现强度未找到，尝试使用规范 ID 查询
    if cooccur == 0.5:
        cooccur = edge_features.get((canonical1, canonical2), {}).get('cooccur', cooccur)
    
    return [flavor_compat, cooccur, anchor_similarity, role_compat]

def process_graph_features(recipe_data: Dict, recipe_balance_dict: Dict) -> List[float]:
    """
    处理图级特征
    
    参数:
    recipe_data: 食谱数据
    recipe_balance_dict: 食谱平衡特征字典
    
    返回:
    图级特征向量
    """
    nodes = recipe_data.get('nodes', [])
    n_ingredients = len(nodes)
    recipe_id = recipe_data.get('recipe_id')
    
    # 从数据库中获取真实的角色占比
    balance_data = recipe_balance_dict.get(recipe_id, {})
    
    # 各角色的数量分布
    role_counts = {'base': 0, 'acid': 0, 'sweetener': 0, 'modifier': 0, 'bitters': 0, 'garnish': 0, 'dilution': 0, 'other': 0}
    for node in nodes:
        role = node.get('role', 'other').lower()
        if 'base' in role:
            role_counts['base'] += 1
        elif 'acid' in role:
            role_counts['acid'] += 1
        elif 'sweet' in role:
            role_counts['sweetener'] += 1
        elif 'modifier' in role:
            role_counts['modifier'] += 1
        elif 'bitter' in role:
            role_counts['bitters'] += 1
        elif 'garnish' in role:
            role_counts['garnish'] += 1
        elif 'dilution' in role:
            role_counts['dilution'] += 1
        else:
            role_counts['other'] += 1
    
    # 各角色的用量占比（从数据库中获取）
    role_ratios = [
        balance_data.get('r_base', 0.0),
        balance_data.get('r_acid', 0.0),
        balance_data.get('r_sweetener', 0.0),
        balance_data.get('r_modifier', 0.0),
        balance_data.get('r_bitters', 0.0),
        balance_data.get('r_garnish', 0.0),
        balance_data.get('r_dilution', 0.0),
        balance_data.get('r_other', 0.0)
    ]
    
    # 酒精原料占比
    alcohol_count = 0
    for node in nodes:
        ingredient_id = node.get('id')
        # 从原料信息中获取是否含酒精
        # 注意：这里需要根据实际情况调整，可能需要从数据库中查询
        # 简化处理，假设酒精原料的 role 包含 'base' 或 'liqueur'
        role = node.get('role', '').lower()
        if 'base' in role or 'liqueur' in role:
            alcohol_count += 1
    alcohol_ratio = alcohol_count / n_ingredients if n_ingredients > 0 else 0.0
    
    # 酸甜比
    acid_ratio = balance_data.get('r_acid', 0.0)
    sweet_ratio = balance_data.get('r_sweetener', 0.0)
    if acid_ratio > 0:
        sweet_sour_ratio = sweet_ratio / acid_ratio
    else:
        sweet_sour_ratio = 1.0  # 避免除以零
    sweet_sour_ratio = min(sweet_sour_ratio, 5.0)  # 限制最大值
    
    # base/modifier 比
    base_ratio = balance_data.get('r_base', 0.0)
    modifier_ratio = balance_data.get('r_modifier', 0.0)
    if modifier_ratio > 0:
        base_modifier_ratio = base_ratio / modifier_ratio
    else:
        base_modifier_ratio = 1.0  # 避免除以零
    base_modifier_ratio = min(base_modifier_ratio, 5.0)  # 限制最大值
    
    # 配方整体的组成均衡度指标（从数据库中获取）
    balance_score = balance_data.get('final_balance_score', 0.0)
    flavor_balance = balance_data.get('flavor_balance_score', 0.0)
    role_balance = balance_data.get('role_balance_score', 0.0)
    
    # 组合特征
    features = [n_ingredients]
    features.extend(list(role_counts.values()))
    features.extend(role_ratios)
    features.append(alcohol_ratio)
    features.append(sweet_sour_ratio)
    features.append(base_modifier_ratio)
    features.append(balance_score)
    features.append(flavor_balance)
    features.append(role_balance)
    
    return features

# =========================================================
# 图构建函数
# =========================================================

def build_graph(recipe_data: Dict, ingredient_info_dict: Dict, edge_features: Dict, frequency_dict: Dict, recipe_balance_dict: Dict, canonical_df: pd.DataFrame) -> Dict:
    """
    为单个食谱构建图
    
    参数:
    recipe_data: 食谱数据
    ingredient_info_dict: 原料信息字典
    edge_features: 边特征字典
    frequency_dict: 原料频率字典
    recipe_balance_dict: 食谱平衡特征字典
    canonical_df: 规范原料数据框
    
    返回:
    图数据字典
    """
    nodes = recipe_data.get('nodes', [])
    n_nodes = len(nodes)
    
    # 构建节点特征矩阵
    x = []
    for node in nodes:
        ingredient_id = node.get('id')
        amount = float(node.get('amount', 0))
        unit = node.get('unit', '')
        role = node.get('role', 'other')
        ingredient_info = ingredient_info_dict.get(ingredient_id, {})
        node_features = process_node_features(ingredient_id, ingredient_info, amount, unit, role, frequency_dict)
        x.append(node_features)
    x = np.array(x, dtype=np.float32)
    
    # 构建边索引和边特征
    edge_index = []
    edge_attr = []
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            edge_index.append([i, j])
            edge_index.append([j, i])  # 无向图
            
            ingredient1_id = nodes[i].get('id')
            ingredient2_id = nodes[j].get('id')
            edge_feature = process_edge_features(ingredient1_id, ingredient2_id, edge_features, canonical_df)
            edge_attr.append(edge_feature)
            edge_attr.append(edge_feature)  # 无向图
    
    edge_index = np.array(edge_index, dtype=np.int64).T if edge_index else np.empty((2, 0), dtype=np.int64)
    edge_attr = np.array(edge_attr, dtype=np.float32) if edge_attr else np.empty((0, 4), dtype=np.float32)
    
    # 构建图级特征
    z_graph = process_graph_features(recipe_data, recipe_balance_dict)
    z_graph = np.array(z_graph, dtype=np.float32)
    
    # 获取基础分数
    base_scores = [
        recipe_data.get('syn_B', 0.0),
        recipe_data.get('conf_B', 0.0),
        recipe_data.get('bal_B', 0.0)
    ]
    
    # 构建元数据
    meta = {
        'recipe_id': recipe_data.get('recipe_id'),
        'n_ingredients': n_nodes,
        'roles': recipe_data.get('graph_level_features', {}).get('roles', [])
    }
    
    return {
        'x': x,
        'edge_index': edge_index,
        'edge_attr': edge_attr,
        'z_graph': z_graph,
        'base_scores': base_scores,
        'meta': meta
    }

# =========================================================
# 数据划分函数
# =========================================================

def group_by_original_recipe(pairs_data: List[Dict]) -> Dict:
    """
    按原始 recipe_id 分组
    
    参数:
    pairs_data: 配对数据列表
    
    返回:
    分组字典
    """
    groups = {}
    
    for pair in pairs_data:
        pos_recipe_id = pair.get('pos_recipe_id')
        # 提取原始 recipe_id（去掉 'perturbed_' 前缀）
        if isinstance(pos_recipe_id, str) and 'perturbed_' in pos_recipe_id:
            original_recipe_id = pos_recipe_id.replace('perturbed_', '')
        else:
            original_recipe_id = str(pos_recipe_id)
        
        if original_recipe_id not in groups:
            groups[original_recipe_id] = []
        groups[original_recipe_id].append(pair)
    
    return groups

def split_groups(groups: Dict) -> Tuple[List[str], List[str], List[str]]:
    """
    划分训练、验证和测试组
    
    参数:
    groups: 分组字典
    
    返回:
    训练组、验证组和测试组的 keys
    """
    group_keys = list(groups.keys())
    np.random.shuffle(group_keys)
    
    n_groups = len(group_keys)
    n_train = int(n_groups * Config.TRAIN_RATIO)
    n_valid = int(n_groups * Config.VALID_RATIO)
    
    train_groups = group_keys[:n_train]
    valid_groups = group_keys[n_train:n_train + n_valid]
    test_groups = group_keys[n_train + n_valid:]
    
    return train_groups, valid_groups, test_groups

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("构建 Phase C 图数据...")
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(Config.GRAPHS_OUTPUT_FILE), exist_ok=True)
    
    # 加载数据
    print("[INFO] 加载数据...")
    recipes_data, pairs_data = load_phaseC_data()
    ingredients_df = load_ingredients()
    canonical_df = load_canonical_ingredients()
    edge_features = load_edge_features()
    
    # 构建原料信息字典
    ingredient_info_dict = {}
    for _, row in ingredients_df.iterrows():
        ingredient_info_dict[row['ingredient_id']] = {
            'name_norm': row.get('name_norm', 'Unknown'),
            'category': row.get('category', 'other'),
            'type_tag': row.get('type_tag', 'other'),
            'is_alcoholic': row.get('is_alcoholic', False),
            'abv': row.get('abv', 0.0)
        }
    
    # 预计算所有原料的频率
    print("[INFO] 预计算原料频率...")
    from src.db import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    sql = text("""
    SELECT ingredient_id, COUNT(*) as freq
    FROM recipe_ingredient
    GROUP BY ingredient_id
    """)
    
    with engine.begin() as conn:
        freq_df = pd.read_sql(sql, conn)
    
    frequency_dict = {}
    for _, row in freq_df.iterrows():
        frequency_dict[row['ingredient_id']] = row['freq']
    
    # 加载 recipe_balance_feature 表数据
    print("[INFO] 加载 recipe_balance_feature 数据...")
    sql = text("""
    SELECT recipe_id, r_base, r_acid, r_sweetener, r_modifier, r_bitters, r_garnish, r_dilution, r_other,
           flavor_balance_score, role_balance_score, final_balance_score
    FROM recipe_balance_feature
    """)
    
    with engine.begin() as conn:
        balance_df = pd.read_sql(sql, conn)
    
    recipe_balance_dict = {}
    for _, row in balance_df.iterrows():
        recipe_id = row['recipe_id']
        recipe_balance_dict[recipe_id] = {
            'r_base': float(row.get('r_base', 0.0)),
            'r_acid': float(row.get('r_acid', 0.0)),
            'r_sweetener': float(row.get('r_sweetener', 0.0)),
            'r_modifier': float(row.get('r_modifier', 0.0)),
            'r_bitters': float(row.get('r_bitters', 0.0)),
            'r_garnish': float(row.get('r_garnish', 0.0)),
            'r_dilution': float(row.get('r_dilution', 0.0)),
            'r_other': float(row.get('r_other', 0.0)),
            'flavor_balance_score': float(row.get('flavor_balance_score', 0.0)),
            'role_balance_score': float(row.get('role_balance_score', 0.0)),
            'final_balance_score': float(row.get('final_balance_score', 0.0))
        }
    
    # 构建图数据
    print("[INFO] 构建图数据...")
    graphs = {}
    for recipe_data in recipes_data:
        recipe_id = recipe_data.get('recipe_id')
        graph = build_graph(recipe_data, ingredient_info_dict, edge_features, frequency_dict, recipe_balance_dict, canonical_df)
        graphs[recipe_id] = graph
    
    # 按原始 recipe_id 分组
    print("[INFO] 按原始 recipe_id 分组...")
    groups = group_by_original_recipe(pairs_data)
    
    # 划分训练、验证和测试组
    print("[INFO] 划分训练、验证和测试组...")
    train_groups, valid_groups, test_groups = split_groups(groups)
    
    # 构建配对数据
    print("[INFO] 构建配对数据...")
    pairs_rows = []
    pair_id = 0
    
    for group_id, group_pairs in groups.items():
        # 确定分组所属的 split
        if group_id in train_groups:
            split = 'train'
        elif group_id in valid_groups:
            split = 'valid'
        else:
            split = 'test'
        
        for pair in group_pairs:
            pairs_rows.append({
                'pair_id': pair_id,
                'group_id': group_id,
                'pos_recipe_id': pair.get('pos_recipe_id'),
                'neg_recipe_id': pair.get('neg_recipe_id'),
                'perturb_type': pair.get('perturb_type'),
                'split': split
            })
            pair_id += 1
    
    # 保存图数据
    print("[INFO] 保存图数据...")
    with open(Config.GRAPHS_OUTPUT_FILE, 'wb') as f:
        pickle.dump(graphs, f)
    
    # 保存配对数据
    print("[INFO] 保存配对数据...")
    pairs_df = pd.DataFrame(pairs_rows)
    pairs_df.to_csv(Config.PAIRS_OUTPUT_FILE, index=False, encoding='utf-8')
    
    print(f"[INFO] 保存了 {len(graphs)} 个图样本到 {Config.GRAPHS_OUTPUT_FILE}")
    print(f"[INFO] 保存了 {len(pairs_rows)} 条配对数据到 {Config.PAIRS_OUTPUT_FILE}")
    print(f"[INFO] 训练组: {len(train_groups)} 个组")
    print(f"[INFO] 验证组: {len(valid_groups)} 个组")
    print(f"[INFO] 测试组: {len(test_groups)} 个组")
    print("[INFO] Phase C 图数据构建完成！")

def build_graph_from_recipe(ingredients: List[Dict]) -> Optional[Any]:
    """
    从原料列表构建图数据
    
    参数:
    ingredients: 原料列表，每个原料包含以下字段:
        - ingredient_id: 原料 ID
        - amount: 原料用量
        - unit: 单位
        - role: 角色
        - line_no: 行号
        - raw_text: 原始文本
    
    返回:
    PyTorch Geometric Data 对象
    """
    try:
        import torch
        from torch_geometric.data import Data
        
        # 加载必要的数据
        ingredients_df = load_ingredients()
        canonical_df = load_canonical_ingredients()
        edge_features = load_edge_features()
        
        # 构建原料信息字典
        ingredient_info_dict = {}
        for _, row in ingredients_df.iterrows():
            ingredient_info_dict[row['ingredient_id']] = {
                'name_norm': row.get('name_norm', 'Unknown'),
                'category': row.get('category', 'other'),
                'type_tag': row.get('type_tag', 'other'),
                'is_alcoholic': row.get('is_alcoholic', False),
                'abv': float(row.get('abv', 0.0)) if row.get('abv') is not None else 0.0
            }
        
        # 预计算所有原料的频率
        from src.db import get_engine
        from sqlalchemy import text
        
        engine = get_engine()
        sql = text("""
        SELECT ingredient_id, COUNT(*) as freq
        FROM recipe_ingredient
        GROUP BY ingredient_id
        """)
        
        with engine.begin() as conn:
            freq_df = pd.read_sql(sql, conn)
        
        frequency_dict = {}
        for _, row in freq_df.iterrows():
            frequency_dict[row['ingredient_id']] = row['freq']
        
        # 加载 recipe_balance_feature 表数据
        sql = text("""
        SELECT recipe_id, r_base, r_acid, r_sweetener, r_modifier, r_bitters, r_garnish, r_dilution, r_other,
               flavor_balance_score, role_balance_score, final_balance_score
        FROM recipe_balance_feature
        """)
        
        with engine.begin() as conn:
            balance_df = pd.read_sql(sql, conn)
        
        recipe_balance_dict = {}
        for _, row in balance_df.iterrows():
            recipe_id = row['recipe_id']
            recipe_balance_dict[recipe_id] = {
                'r_base': float(row.get('r_base', 0.0)) if row.get('r_base') is not None else 0.0,
                'r_acid': float(row.get('r_acid', 0.0)) if row.get('r_acid') is not None else 0.0,
                'r_sweetener': float(row.get('r_sweetener', 0.0)) if row.get('r_sweetener') is not None else 0.0,
                'r_modifier': float(row.get('r_modifier', 0.0)) if row.get('r_modifier') is not None else 0.0,
                'r_bitters': float(row.get('r_bitters', 0.0)) if row.get('r_bitters') is not None else 0.0,
                'r_garnish': float(row.get('r_garnish', 0.0)) if row.get('r_garnish') is not None else 0.0,
                'r_dilution': float(row.get('r_dilution', 0.0)) if row.get('r_dilution') is not None else 0.0,
                'r_other': float(row.get('r_other', 0.0)) if row.get('r_other') is not None else 0.0,
                'flavor_balance_score': float(row.get('flavor_balance_score', 0.0)) if row.get('flavor_balance_score') is not None else 0.0,
                'role_balance_score': float(row.get('role_balance_score', 0.0)) if row.get('role_balance_score') is not None else 0.0,
                'final_balance_score': float(row.get('final_balance_score', 0.0)) if row.get('final_balance_score') is not None else 0.0
            }
        
        # 构建 recipe_data 字典
        recipe_data = {
            'recipe_id': 'custom',
            'nodes': [
                {
                    'id': int(ing['ingredient_id']),
                    'amount': float(ing['amount']) if ing['amount'] is not None else 0.0,
                    'unit': ing['unit'] if ing['unit'] is not None else '',
                    'role': ing['role'] if ing['role'] is not None else 'other',
                    'line_no': int(ing['line_no']) if ing['line_no'] is not None else 0,
                    'raw_text': ing['raw_text'] if ing['raw_text'] is not None else ''
                }
                for ing in ingredients
            ],
            'graph_level_features': {
                'n_ingredients': len(ingredients),
                'roles': [ing['role'] if ing['role'] is not None else 'other' for ing in ingredients]
            },
            'syn_B': 0.0,  # 这些值会在 SQE 计算器中被覆盖
            'conf_B': 0.0,
            'bal_B': 0.0
        }
        
        # 构建图数据
        graph_dict = build_graph(recipe_data, ingredient_info_dict, edge_features, frequency_dict, recipe_balance_dict, canonical_df)
        
        # 转换为 PyTorch Geometric Data 对象
        data = Data(
            x=torch.tensor(graph_dict['x'], dtype=torch.float32),
            edge_index=torch.tensor(graph_dict['edge_index'], dtype=torch.long),
            edge_attr=torch.tensor(graph_dict['edge_attr'], dtype=torch.float32),
            z_graph=torch.tensor(graph_dict['z_graph'], dtype=torch.float32)
        )
        
        return data
    except Exception as e:
        print(f"[ERROR] 构建图数据失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
