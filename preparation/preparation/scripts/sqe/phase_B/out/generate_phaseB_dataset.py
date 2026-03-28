# -*- coding: utf-8 -*-
"""
Phase B 成对训练数据集生成脚本 (v3)

功能：
1. 生成候选负样本（recipe 变体）
2. 对变体进行真实重评分
3. 构建 pairwise 训练数据
4. 增加有效性过滤
5. 输出完整的分析字段
"""

import os
import sys
import uuid
import random
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_script_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 数据库导入
from src.db import get_engine
from sqlalchemy import text

# =========================================================
# 数据结构定义
# =========================================================

@dataclass #装饰器。此处封装扰动方案
class PerturbationProposal:
    """扰动方案"""
    perturb_type: str
    perturb_detail: str
    recipe_id: int
    ingredient_changes: List[Dict]  # 原料变化列表

@dataclass #装饰器。此处封装重评分后的样本信息
class RescoredSample:
    """
    重评分后的样本
    注意：所有分数都是"越大越好"的口径
    """
    recipe_id: str
    syn_score: float
    conf_score: float  # 原始冲突分数（越大越差）
    bal_score: float  # 原始平衡分数（越大越好）
    syn_norm: float
    conf_norm: float  # 标准化冲突分数（越大越差）
    bal_norm: float
    conf_good: float  # 冲突转换为越大越好的形式

@dataclass #装饰器。此处封装成对记录信息
class PairRecord:
    """
    成对记录
    所有分数都是"越大越好"的口径
    """
    pair_id: str
    recipe_id_pos: int
    recipe_id_neg: str
    perturb_type: str
    perturb_detail: str
    syn_pos: float
    conf_pos: float  # 原始冲突分数（越大越差）
    bal_pos: float
    syn_neg: float
    conf_neg: float  # 原始冲突分数（越大越差）
    bal_neg: float
    syn_pos_norm: float
    conf_pos_norm: float  # 标准化冲突分数（越大越差）
    bal_pos_norm: float
    syn_neg_norm: float
    conf_neg_norm: float  # 标准化冲突分数（越大越差）
    bal_neg_norm: float
    conf_pos_good: float  # 冲突转换为越大越好的形式
    conf_neg_good: float  # 冲突转换为越大越好的形式
    delta_syn: float
    delta_conf: float  # 冲突变化（越大越好，表示冲突减少）
    delta_bal: float
    delta_conf_good: float
    overall_margin: Optional[float] = None
    is_hard_negative: bool = False
    validity_flag: bool = True
    drop_reason: Optional[str] = None

# =========================================================
# 配置参数
# =========================================================
# 主要配置了生成数据的参数，包括：
# NUM_PAIRS: 成对数量
# MAX_RETRY: 最大重试次数
# ENABLE_BALANCED_SAMPLING: 是否启用平衡采样（分成了两个样本库）
# MIN_DELTA_THRESHOLD: 最小分数变化阈值
# MAX_DELTA_THRESHOLD: 最大分数变化阈值
# VALIDITY_THRESHOLD: 有效性阈值
class Config:
    """配置类"""
    NUM_PAIRS = 3000
    MAX_RETRY = 5
    ENABLE_BALANCED_SAMPLING = True
    MIN_DELTA_THRESHOLD = 0.01  # 最小分数变化阈值
    MAX_DELTA_THRESHOLD = 0.8   # 最大分数变化阈值
    VALIDITY_THRESHOLD = 0.5     # 有效性阈值

# =========================================================
# 数据加载函数
# =========================================================

def load_phaseA_baseline() -> pd.DataFrame:
    """
    加载 Phase A 基线评分表
    """
    baseline_file = os.path.join(_project_root, "data", "phaseA_baseline_v2.csv")
    if not os.path.exists(baseline_file):
        raise FileNotFoundError(f"Phase A 基线评分表不存在: {baseline_file}")
    
    df = pd.read_csv(baseline_file)
    print(f"[INFO] 加载了 {len(df)} 条 Phase A 基线数据")
    return df

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

def get_recipe_ingredients(recipe_id: int, ingredients_df: pd.DataFrame) -> pd.DataFrame:
    """
    获取指定食谱的原料
    """
    return ingredients_df[ingredients_df['recipe_id'] == recipe_id]

def load_ingredient_info() -> pd.DataFrame:
    """
    加载原料信息，用于 replace 和 insert 扰动
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
# 工具函数
# =========================================================

def safe_parse_amount(amount: Any) -> float:
    """
    安全解析 amount 字段
    """
    if amount is None:
        return 1.0
    
    try:
        # 处理 NaN
        if pd.isna(amount):
            return 1.0
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

# =========================================================
# 扰动生成函数
# =========================================================

def generate_perturbation_proposal(recipe_id: int, ingredients_df: pd.DataFrame, 
                                   baseline_df: pd.DataFrame, ingredient_info: pd.DataFrame) -> Optional[PerturbationProposal]:
    """
    生成扰动方案
    """
    # 获取原始食谱的原料
    recipe_ingredients = get_recipe_ingredients(recipe_id, ingredients_df)
    if len(recipe_ingredients) < 2:
        return None
    
    # 选择扰动类型
    perturb_types = [
        "synergy_replace_with_different_type",
        "synergy_replace_with_different_anchor",
        "synergy_insert_different_type",
        "conflict_add_extra_base_spirit",
        "conflict_create_incompatible_type_pair",
        "conflict_acid_sweetener_ratio_break",
        "balance_remove_key_ingredient",
        "balance_change_role",
        "balance_change_amount"
    ]
    
    # 随机选择一个扰动类型
    perturb_type = random.choice(perturb_types)
    ingredient_changes = []
    perturb_detail = ""
    
    if perturb_type.startswith("synergy"):
        # 协同性扰动
        if perturb_type == "synergy_replace_with_different_type":
            # 替换为不同类型的原料
            ingredient_to_replace = recipe_ingredients.sample(1).iloc[0]
            # 选择一个不同类型的原料作为替换
            available_ingredients = ingredient_info[ingredient_info['type_tag'] != ingredient_info.loc[
                ingredient_info['ingredient_id'] == ingredient_to_replace['ingredient_id'], 'type_tag'].values[0]]
            if len(available_ingredients) > 0:
                new_ingredient = available_ingredients.sample(1).iloc[0]
                perturb_detail = f"replace_with_different_type:{ingredient_to_replace['ingredient_id']},{new_ingredient['ingredient_id']},role:{ingredient_to_replace['role']},line_no:{ingredient_to_replace['line_no']}"
                ingredient_changes.append({
                    "type": "replace",
                    "ingredient_id": ingredient_to_replace['ingredient_id'],
                    "line_no": ingredient_to_replace['line_no'],
                    "new_ingredient_id": new_ingredient['ingredient_id'],
                    "reason": "different_type"
                })
            else:
                return None
        
        elif perturb_type == "synergy_replace_with_different_anchor":
            # 替换为不同锚点的原料
            ingredient_to_replace = recipe_ingredients.sample(1).iloc[0]
            # 选择一个不同锚点的原料作为替换
            available_ingredients = ingredient_info[ingredient_info['anchor_name'] != ingredient_info.loc[
                ingredient_info['ingredient_id'] == ingredient_to_replace['ingredient_id'], 'anchor_name'].values[0]]
            if len(available_ingredients) > 0:
                new_ingredient = available_ingredients.sample(1).iloc[0]
                perturb_detail = f"replace_with_different_anchor:{ingredient_to_replace['ingredient_id']},{new_ingredient['ingredient_id']},role:{ingredient_to_replace['role']},line_no:{ingredient_to_replace['line_no']}"
                ingredient_changes.append({
                    "type": "replace",
                    "ingredient_id": ingredient_to_replace['ingredient_id'],
                    "line_no": ingredient_to_replace['line_no'],
                    "new_ingredient_id": new_ingredient['ingredient_id'],
                    "reason": "different_anchor"
                })
            else:
                return None
        
        else:  # synergy_insert_different_type
            # 插入不同类型的原料
            # 选择一个与现有原料不同类型的原料
            existing_types = set(ingredient_info[ingredient_info['ingredient_id'].isin(
                recipe_ingredients['ingredient_id'])].type_tag.unique())
            available_ingredients = ingredient_info[~ingredient_info['type_tag'].isin(existing_types)]
            if len(available_ingredients) > 0:
                new_ingredient = available_ingredients.sample(1).iloc[0]
                perturb_detail = f"insert_different_type:{new_ingredient['ingredient_id']},type:{new_ingredient['type_tag']}"
                ingredient_changes.append({
                    "type": "insert",
                    "ingredient_id": new_ingredient['ingredient_id'],
                    "amount": 1.0,
                    "unit": "oz",
                    "role": "modifier",
                    "reason": "different_type"
                })
            else:
                return None
    
    elif perturb_type.startswith("conflict"):
        # 冲突扰动
        if perturb_type == "conflict_add_extra_base_spirit":
            # 添加额外的 base spirit
            base_count = len(recipe_ingredients[recipe_ingredients['role'] == 'base_spirit'])
            # 选择一个 base spirit 类型的原料
            base_ingredients = ingredient_info[ingredient_info['type_tag'] == 'spirit']
            if len(base_ingredients) > 0:
                new_ingredient = base_ingredients.sample(1).iloc[0]
                perturb_detail = f"add_extra_base_spirit:{new_ingredient['ingredient_id']},current={base_count}"
                ingredient_changes.append({
                    "type": "insert",
                    "ingredient_id": new_ingredient['ingredient_id'],
                    "amount": 1.0,
                    "unit": "oz",
                    "role": "base_spirit",
                    "reason": "extra_base"
                })
            else:
                return None
        
        elif perturb_type == "conflict_create_incompatible_type_pair":
            # 创建不兼容类型对
            # 选择一个与现有原料类型不兼容的原料
            existing_types = set(ingredient_info[ingredient_info['ingredient_id'].isin(
                recipe_ingredients['ingredient_id'])].type_tag.unique())
            # 假设 cream 和 spirit 不兼容
            incompatible_types = ['cream'] if 'spirit' in existing_types else ['spirit']
            available_ingredients = ingredient_info[ingredient_info['type_tag'].isin(incompatible_types)]
            if len(available_ingredients) > 0:
                new_ingredient = available_ingredients.sample(1).iloc[0]
                perturb_detail = f"create_incompatible_type_pair:{new_ingredient['ingredient_id']},type:{new_ingredient['type_tag']}"
                ingredient_changes.append({
                    "type": "insert",
                    "ingredient_id": new_ingredient['ingredient_id'],
                    "amount": 1.0,
                    "unit": "oz",
                    "role": "modifier",
                    "reason": "incompatible_type"
                })
            else:
                return None
        
        else:  # conflict_acid_sweetener_ratio_break
            # 破坏酸甜比例
            perturb_detail = "acid_sweetener_ratio_break"
            # 选择一个酸甜原料
            acid_sweet_ingredients = recipe_ingredients[
                recipe_ingredients['role'].isin(['acid', 'sweetener'])
            ]
            if len(acid_sweet_ingredients) > 0:
                ingredient_to_change = acid_sweet_ingredients.sample(1).iloc[0]
                # 根据角色选择不同的系数
                if ingredient_to_change['role'] == 'acid':
                    # 酸乘以 2.0
                    factor = 2.0
                else:
                    # 甜乘以 0.5
                    factor = 0.5
                # 计算新的数值量
                original_amount = safe_parse_amount(ingredient_to_change['amount'])
                new_amount = original_amount * factor
                perturb_detail = f"acid_sweetener_ratio_break:{ingredient_to_change['ingredient_id']},role:{ingredient_to_change['role']},factor:{factor},line_no:{ingredient_to_change['line_no']}"
                ingredient_changes.append({
                    "type": "change_amount",
                    "ingredient_id": ingredient_to_change['ingredient_id'],
                    "line_no": ingredient_to_change['line_no'],
                    "new_amount": new_amount,
                    "reason": "ratio_break"
                })
            else:
                return None
    
    else:  # balance 扰动
        if perturb_type == "balance_remove_key_ingredient":
            # 移除关键原料
            key_ingredients = recipe_ingredients[
                recipe_ingredients['role'].isin(['acid', 'sweetener', 'base_spirit'])
            ]
            if len(key_ingredients) > 0:
                ingredient_to_remove = key_ingredients.sample(1).iloc[0]
                perturb_detail = f"remove_key:{ingredient_to_remove['ingredient_id']},role:{ingredient_to_remove['role']},line_no:{ingredient_to_remove['line_no']}"
                ingredient_changes.append({
                    "type": "remove",
                    "ingredient_id": ingredient_to_remove['ingredient_id'],
                    "line_no": ingredient_to_remove['line_no'],
                    "reason": "key_ingredient"
                })
            else:
                return None
        
        elif perturb_type == "balance_change_role":
            # 改变角色
            ingredient_to_change = recipe_ingredients.sample(1).iloc[0]
            # 随机选择一个不同的角色
            new_role = random.choice(["base_spirit", "modifier", "acid", "sweetener"])
            while new_role == ingredient_to_change['role']:
                new_role = random.choice(["base_spirit", "modifier", "acid", "sweetener"])
            perturb_detail = f"change_role:{ingredient_to_change['ingredient_id']},from:{ingredient_to_change['role']},to:{new_role},line_no:{ingredient_to_change['line_no']}"
            ingredient_changes.append({
                "type": "change_role",
                "ingredient_id": ingredient_to_change['ingredient_id'],
                "line_no": ingredient_to_change['line_no'],
                "new_role": new_role,
                "reason": "role_change"
            })
        
        else:  # balance_change_amount
            # 改变原料量
            ingredient_to_change = recipe_ingredients.sample(1).iloc[0]
            # 随机增加或减少量
            factor = random.choice([0.5, 2.0])
            # 计算新的数值量
            original_amount = safe_parse_amount(ingredient_to_change['amount'])
            new_amount = original_amount * factor
            perturb_detail = f"change_amount:{ingredient_to_change['ingredient_id']},factor:{factor},line_no:{ingredient_to_change['line_no']}"
            ingredient_changes.append({
                "type": "change_amount",
                "ingredient_id": ingredient_to_change['ingredient_id'],
                "line_no": ingredient_to_change['line_no'],
                "new_amount": new_amount,
                "reason": "amount_change"
            })
    
    return PerturbationProposal(
        perturb_type=perturb_type,
        perturb_detail=perturb_detail,
        recipe_id=recipe_id,
        ingredient_changes=ingredient_changes
    )

# =========================================================
# 扰动应用函数
# =========================================================

def apply_perturbation_to_recipe(recipe_id: int, proposal: PerturbationProposal, 
                               ingredients_df: pd.DataFrame) -> List[Dict]:
    """
    应用扰动到食谱
    真正实现 replace 和 insert 扰动
    """
    # 获取原始食谱的原料
    original_ingredients = get_recipe_ingredients(recipe_id, ingredients_df)
    perturbed_ingredients = []
    
    # 转换为字典列表
    for _, row in original_ingredients.iterrows():
        perturbed_ingredients.append({
            "recipe_id": row['recipe_id'],
            "ingredient_id": row['ingredient_id'],
            "line_no": row['line_no'],
            "amount": row['amount'],
            "unit": row['unit'],
            "role": row['role'],
            "raw_text": row['raw_text']
        })
    
    # 应用扰动
    for change in proposal.ingredient_changes:
        if change["type"] == "remove":
            # 移除原料（使用 line_no 精确定位）
            if "line_no" in change:
                perturbed_ingredients = [ing for ing in perturbed_ingredients 
                                      if ing["line_no"] != change["line_no"]]
            else:
                # 向后兼容：如果没有 line_no，使用 ingredient_id
                perturbed_ingredients = [ing for ing in perturbed_ingredients 
                                      if ing["ingredient_id"] != change["ingredient_id"]]
        
        elif change["type"] == "change_role":
            # 改变角色（使用 line_no 精确定位）
            for ing in perturbed_ingredients:
                if "line_no" in change:
                    if ing["line_no"] == change["line_no"]:
                        ing["role"] = change.get("new_role", ing["role"])
                else:
                    # 向后兼容：如果没有 line_no，使用 ingredient_id
                    if ing["ingredient_id"] == change["ingredient_id"]:
                        ing["role"] = change.get("new_role", ing["role"])
        
        elif change["type"] == "change_amount":
            # 改变用量（使用 line_no 精确定位）
            for ing in perturbed_ingredients:
                if "line_no" in change:
                    if ing["line_no"] == change["line_no"]:
                        ing["amount"] = change.get("new_amount", ing["amount"])
                        if "new_unit" in change:
                            ing["unit"] = change["new_unit"]
                else:
                    # 向后兼容：如果没有 line_no，使用 ingredient_id
                    if ing["ingredient_id"] == change["ingredient_id"]:
                        ing["amount"] = change.get("new_amount", ing["amount"])
                        if "new_unit" in change:
                            ing["unit"] = change["new_unit"]
        
        elif change["type"] == "replace":
            # 替换原料（使用 line_no 精确定位）
            new_ingredient_id = change.get("new_ingredient_id")
            if new_ingredient_id:
                for ing in perturbed_ingredients:
                    if "line_no" in change:
                        if ing["line_no"] == change["line_no"]:
                            ing["ingredient_id"] = new_ingredient_id
                            # 更新 raw_text
                            ing["raw_text"] = f"1 oz Ingredient {new_ingredient_id}"
                    else:
                        # 向后兼容：如果没有 line_no，使用 ingredient_id
                        if ing["ingredient_id"] == change["ingredient_id"]:
                            ing["ingredient_id"] = new_ingredient_id
                            # 更新 raw_text
                            ing["raw_text"] = f"1 oz Ingredient {new_ingredient_id}"
        
        elif change["type"] == "insert":
            # 插入原料
            amount = float(change.get("amount", "1"))
            unit = change.get("unit", "oz")
            new_ingredient = {
                "recipe_id": recipe_id,
                "ingredient_id": change["ingredient_id"],
                "line_no": len(perturbed_ingredients) + 1,
                "amount": amount,
                "unit": unit,
                "role": change.get("role", "modifier"),
                "raw_text": f"{amount} {unit} Ingredient {change['ingredient_id']}"
            }
            perturbed_ingredients.append(new_ingredient)
    
    return perturbed_ingredients

# =========================================================
# 重评分函数（真实实现）
# =========================================================

def normalize_score(score: float, min_val: float, max_val: float) -> float:
    """
    标准化分数到 [0, 1] 区间
    """
    if max_val == min_val:
        return 0.5
    return max(0.0, min(1.0, (score - min_val) / (max_val - min_val)))

def rescore_perturbed_recipe(original_ingredients: List[Dict], 
                            perturbed_ingredients: List[Dict]) -> Optional[RescoredSample]:
    """
    对扰动后的食谱进行真实重评分
    
    调用现有的 Phase A 评分逻辑
    """
    # 生成虚拟的 recipe_id
    perturbed_recipe_id = f"perturbed_{uuid.uuid4().hex[:8]}"
    
    # 导入评分接口函数
    from scripts.SQE.phaseA_baseline_v2 import calculate_baseline_scores_from_ingredients
    
    # 计算扰动后食谱的分数
    baseline_result = calculate_baseline_scores_from_ingredients(perturbed_ingredients)
    
    # 提取分数
    syn_score = baseline_result["synergy_score"]
    conf_score = baseline_result["conflict_score"]
    bal_score = baseline_result["final_balance_score"]
    syn_norm = baseline_result["synergy_normalized"]
    conf_norm = baseline_result["conflict_normalized"]
    bal_norm = baseline_result["balance_normalized"]
    conf_good = baseline_result["conflict_good"]
    
    return RescoredSample(
        recipe_id=perturbed_recipe_id,
        syn_score=syn_score,
        conf_score=conf_score,
        bal_score=bal_score,
        syn_norm=syn_norm,
        conf_norm=conf_norm,
        bal_norm=bal_norm,
        conf_good=conf_good
    )

# =========================================================
# 样本验证函数
# =========================================================
def validate_negative_sample(pos_row: pd.Series, neg_sample: RescoredSample) -> Tuple[bool, Optional[str]]:
    """
    验证负样本的有效性
    使用统一的"越大越好"口径
    """
    # 计算分数变化（越大越好）
    delta_syn = pos_row['synergy_normalized'] - neg_sample.syn_norm  # 协同性应该降低
    delta_conf = (1 - pos_row['conflict_normalized']) - neg_sample.conf_good  # 冲突应该增加（conf_good 降低）
    delta_bal = pos_row['balance_normalized'] - neg_sample.bal_norm  # 平衡性应该降低
    
    # 检查是否至少有一个核心维度显著变差
    has_significant_change = (
        delta_syn > Config.MIN_DELTA_THRESHOLD or
        delta_conf > Config.MIN_DELTA_THRESHOLD or
        delta_bal > Config.MIN_DELTA_THRESHOLD
    )
    
    if not has_significant_change:
        return False, "No significant score change"
    
    # 检查是否坏到完全失真
    if delta_syn > Config.MAX_DELTA_THRESHOLD or \
       delta_conf > Config.MAX_DELTA_THRESHOLD or \
       delta_bal > Config.MAX_DELTA_THRESHOLD:
        return False, "Score change too large"
    
    # 检查正样本总分是否高于负样本
    # 使用统一的"越大越好"口径计算总分（都使用归一化分数）
    pos_total = pos_row['synergy_normalized'] + (1 - pos_row['conflict_normalized']) + pos_row['balance_normalized']
    neg_total = neg_sample.syn_norm + neg_sample.conf_good + neg_sample.bal_norm
    
    if pos_total <= neg_total:
        return False, "Positive sample score not higher than negative"
    
    return True, None

# =========================================================
# 构建成对记录函数
# =========================================================
def build_pair_record(pos_row: pd.Series, proposal: PerturbationProposal, 
                    neg_sample: RescoredSample, validity: bool, 
                    drop_reason: Optional[str]) -> PairRecord:
    """
    构建成对记录
    使用统一的"越大越好"口径
    """
    # 计算差值（越大越好）
    delta_syn = pos_row['synergy_score'] - neg_sample.syn_score  # 协同性应该降低
    delta_conf = (1 - pos_row['conflict_normalized']) - neg_sample.conf_good  # 冲突应该增加（conf_good 降低）
    delta_bal = pos_row['final_balance_score'] - neg_sample.bal_score  # 平衡性应该降低
    delta_conf_good = delta_conf  # 与 delta_conf 相同
    
    # 计算整体 margin（使用统一的"越大越好"口径）
    pos_total = pos_row['synergy_normalized'] + (1 - pos_row['conflict_normalized']) + pos_row['balance_normalized']
    neg_total = neg_sample.syn_norm + neg_sample.conf_good + neg_sample.bal_norm
    overall_margin = pos_total - neg_total
    
    # 判断是否为 hard negative
    is_hard = overall_margin < 0.1
    
    return PairRecord(
        pair_id=str(uuid.uuid4()),
        recipe_id_pos=pos_row['recipe_id'],
        recipe_id_neg=neg_sample.recipe_id,
        perturb_type=proposal.perturb_type,
        perturb_detail=proposal.perturb_detail,
        syn_pos=pos_row['synergy_score'],
        conf_pos=pos_row['conflict_score'],
        bal_pos=pos_row['final_balance_score'],
        syn_neg=neg_sample.syn_score,
        conf_neg=neg_sample.conf_score,
        bal_neg=neg_sample.bal_score,
        syn_pos_norm=pos_row['synergy_normalized'],
        conf_pos_norm=pos_row['conflict_normalized'],
        bal_pos_norm=pos_row['balance_normalized'],
        syn_neg_norm=neg_sample.syn_norm,
        conf_neg_norm=neg_sample.conf_norm,
        bal_neg_norm=neg_sample.bal_norm,
        conf_pos_good=1 - pos_row['conflict_normalized'],
        conf_neg_good=neg_sample.conf_good,
        delta_syn=delta_syn,
        delta_conf=delta_conf,
        delta_bal=delta_bal,
        delta_conf_good=delta_conf_good,
        overall_margin=overall_margin,
        is_hard_negative=is_hard,
        validity_flag=validity,
        drop_reason=drop_reason
    )

# =========================================================
# 生成数据集函数
# =========================================================
def generate_pairwise_dataset(num_pairs: int = Config.NUM_PAIRS) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    生成成对训练数据集
    返回：(有效样本数据集, 无效样本数据集)
    """
    # 加载数据
    baseline_df = load_phaseA_baseline()
    ingredients_df = load_recipe_ingredients()
    ingredient_info = load_ingredient_info()
    
    valid_pairs = []
    invalid_pairs = []
    total_recipes = len(baseline_df)
    perturb_type_counts = {}
    
    while len(valid_pairs) < num_pairs:
        # 选择一个正样本
        pos_idx = random.randint(0, total_recipes - 1)
        pos_row = baseline_df.iloc[pos_idx]
        recipe_id = pos_row['recipe_id']
        
        # 生成扰动方案
        for _ in range(Config.MAX_RETRY):
            proposal = generate_perturbation_proposal(recipe_id, ingredients_df, baseline_df, ingredient_info)
            if proposal:
                break
        else:
            continue
        
        # 应用扰动
        original_ingredients = get_recipe_ingredients(recipe_id, ingredients_df).to_dict('records')
        perturbed_ingredients = apply_perturbation_to_recipe(recipe_id, proposal, ingredients_df)
        
        # 重评分
        neg_sample = rescore_perturbed_recipe(original_ingredients, perturbed_ingredients)
        if not neg_sample:
            continue
        
        # 验证负样本
        validity, drop_reason = validate_negative_sample(pos_row, neg_sample)
        
        # 构建成对记录
        pair_record = build_pair_record(pos_row, proposal, neg_sample, validity, drop_reason)
        
        # 统计扰动类型
        perturb_type = proposal.perturb_type
        perturb_type_counts[perturb_type] = perturb_type_counts.get(perturb_type, 0) + 1
        
        # 根据有效性添加到不同列表
        if validity:
            valid_pairs.append(pair_record)
            # 打印进度
            if len(valid_pairs) % 100 == 0:
                print(f"[INFO] 生成中: {len(valid_pairs)}/{num_pairs}")
        else:
            invalid_pairs.append(pair_record)
    
    # 转换为 DataFrame
    def convert_to_df(pairs):
        pair_dicts = []
        for pair in pairs:
            pair_dicts.append({
                "pair_id": pair.pair_id,
                "recipe_id_pos": pair.recipe_id_pos,
                "recipe_id_neg": pair.recipe_id_neg,
                "perturb_type": pair.perturb_type,
                "perturb_detail": pair.perturb_detail,
                "syn_pos": pair.syn_pos,
                "conf_pos": pair.conf_pos,
                "bal_pos": pair.bal_pos,
                "syn_neg": pair.syn_neg,
                "conf_neg": pair.conf_neg,
                "bal_neg": pair.bal_neg,
                "syn_pos_norm": pair.syn_pos_norm,
                "conf_pos_norm": pair.conf_pos_norm,
                "bal_pos_norm": pair.bal_pos_norm,
                "syn_neg_norm": pair.syn_neg_norm,
                "conf_neg_norm": pair.conf_neg_norm,
                "bal_neg_norm": pair.bal_neg_norm,
                "conf_pos_good": pair.conf_pos_good,
                "conf_neg_good": pair.conf_neg_good,
                "delta_syn": pair.delta_syn,
                "delta_conf": pair.delta_conf,
                "delta_bal": pair.delta_bal,
                "delta_conf_good": pair.delta_conf_good,
                "overall_margin": pair.overall_margin,
                "is_hard_negative": pair.is_hard_negative,
                "validity_flag": pair.validity_flag,
                "drop_reason": pair.drop_reason
            })
        return pd.DataFrame(pair_dicts)
    
    valid_df = convert_to_df(valid_pairs)
    invalid_df = convert_to_df(invalid_pairs)
    
    return valid_df, invalid_df, perturb_type_counts

# =========================================================
# 保存函数
# =========================================================
def save_pairwise_dataset(valid_df: pd.DataFrame, invalid_df: pd.DataFrame):
    """
    保存成对训练数据集
    有效样本保存到主文件，无效样本保存到分析文件
    """
    # 确保输出目录存在
    output_dir = os.path.join(_project_root, "data")
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存有效样本
    valid_file = os.path.join(output_dir, "phaseB_pairwise_dataset_valid.csv")
    valid_df.to_csv(valid_file, index=False, encoding="utf-8")
    print(f"[INFO] 有效样本已保存到: {valid_file}")
    
    # 保存所有样本用于分析（debug）
    all_df = pd.concat([valid_df, invalid_df], ignore_index=True)
    debug_file = os.path.join(output_dir, "phaseB_pairwise_dataset_debug.csv")
    all_df.to_csv(debug_file, index=False, encoding="utf-8")
    print(f"[INFO] 所有样本（包括无效）已保存到: {debug_file}")

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("生成改进的 Phase B 成对训练数据集 (v3)...")
    
    # 生成数据集
    valid_df, invalid_df, perturb_type_counts = generate_pairwise_dataset()
    
    # 保存结果
    save_pairwise_dataset(valid_df, invalid_df)
    
    # 统计信息
    print(f"\n[INFO] 生成的有效样本对数量: {len(valid_df)}")
    print(f"[INFO] 生成的无效样本对数量: {len(invalid_df)}")
    
    # 详细统计各扰动类型的表现
    print("\n[INFO] 各扰动类型的表现:")
    all_df = pd.concat([valid_df, invalid_df], ignore_index=True)
    for perturb_type in sorted(perturb_type_counts.keys()):
        type_df = all_df[all_df['perturb_type'] == perturb_type]
        type_valid_df = valid_df[valid_df['perturb_type'] == perturb_type]
        total_count = len(type_df)
        valid_count = len(type_valid_df)
        valid_rate = valid_count / total_count if total_count > 0 else 0
        avg_margin = type_valid_df['overall_margin'].mean() if valid_count > 0 else 0
        print(f"[INFO]   {perturb_type}: 总数={total_count}, 有效={valid_count}, 有效率={valid_rate:.4f}, 平均 margin={avg_margin:.4f}")
    
    # 统计整体有效性
    total_samples = len(valid_df) + len(invalid_df)
    valid_rate = len(valid_df) / total_samples if total_samples > 0 else 0
    print(f"\n[INFO] 整体统计:")
    print(f"[INFO]   总样本数: {total_samples}")
    print(f"[INFO]   有效样本数: {len(valid_df)}")
    print(f"[INFO]   无效样本数: {len(invalid_df)}")
    print(f"[INFO]   有效率: {valid_rate:.4f}")

if __name__ == "__main__":
    main()
