# -*- coding: utf-8 -*-
"""
全局关键风味汇总脚本 (v3)

功能：
1. 汇总所有配方中的节点重要性结果
2. 先将每条记录映射到 canonical_id
3. 再映射到 flavor anchor 进行更高级别的归一化
4. 在 recipe 内部按 flavor anchor 合并
5. 利用数据库中的支撑度信息
6. 计算支持度修正后的全局得分（加强支持度惩罚）
7. 生成多张不同角色的全局关键风味元素排行榜
8. 将结果输送给 LLM 进行分析总结
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.db import get_conn, get_engine
from sqlalchemy import text

class Config:
    """配置类"""
    # 输入文件
    NODE_IMPORTANCE_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "node_importance_scores.csv")
    
    # 输出文件
    GLOBAL_SUMMARY_OVERALL_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "global_key_flavor_summary_overall_v3.csv")
    GLOBAL_SUMMARY_BASE_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "global_key_flavor_summary_base_v3.csv")
    GLOBAL_SUMMARY_MODIFIER_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "global_key_flavor_summary_modifier_v3.csv")
    GLOBAL_SUMMARY_SWEETENER_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "global_key_flavor_summary_sweetener_v3.csv")
    GLOBAL_SUMMARY_ACID_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "global_key_flavor_summary_acid_v3.csv")
    GLOBAL_SUMMARY_BITTERS_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "global_key_flavor_summary_bitters_v3.csv")
    GLOBAL_SUMMARY_GARNISH_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "global_key_flavor_summary_garnish_v3.csv")
    GLOBAL_SUMMARY_DILUTION_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "global_key_flavor_summary_dilution_v3.csv")
    GLOBAL_SUMMARY_OTHER_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "global_key_flavor_summary_other_v3.csv")
    LLM_INPUT_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "llm_input_v3.json")

def load_node_importance_data() -> pd.DataFrame:
    """
    加载节点重要性数据
    """
    if not os.path.exists(Config.NODE_IMPORTANCE_FILE):
        raise FileNotFoundError(f"节点重要性文件不存在: {Config.NODE_IMPORTANCE_FILE}")
    
    df = pd.read_csv(Config.NODE_IMPORTANCE_FILE)
    print(f"[INFO] 加载了 {len(df)} 条节点重要性数据")
    return df

def load_canonical_mapping() -> pd.DataFrame:
    """
    加载 canonical 映射信息
    """
    engine = get_engine()
    # 只取每个 src_ingredient_id 最新且状态为 ok 的一条记录
    sql = text("""
    SELECT src_ingredient_id, canonical_id, canonical_name, confidence
    FROM (
        SELECT 
            src_ingredient_id, 
            canonical_id, 
            canonical_name, 
            confidence,
            ROW_NUMBER() OVER (PARTITION BY src_ingredient_id ORDER BY updated_at DESC) as rn
        FROM llm_canonical_map
        WHERE status = 'ok'
    ) t
    WHERE rn = 1
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条 canonical 映射数据")
    return df

def load_flavor_anchor_mapping() -> pd.DataFrame:
    """
    加载 flavor anchor 映射信息
    """
    engine = get_engine()
    # 只取每个 ingredient_id 最新的一条记录，只使用 approved 状态
    sql = text("""
    SELECT ingredient_id, canonical_id, anchor_name, anchor_form, match_confidence
    FROM (
        SELECT 
            ingredient_id, 
            canonical_id, 
            anchor_name, 
            anchor_form, 
            match_confidence,
            ROW_NUMBER() OVER (PARTITION BY ingredient_id ORDER BY updated_at DESC) as rn
        FROM ingredient_flavor_anchor
        WHERE review_status = 'approved'
    ) t
    WHERE rn = 1
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条 flavor anchor 映射数据")
    return df

def load_canonical_freq() -> pd.DataFrame:
    """
    加载 canonical 频率信息
    """
    engine = get_engine()
    sql = text("""
    SELECT canonical_id, freq
    FROM canonical_freq_v2
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条 canonical 频率数据")
    return df

def load_ingredient_roles() -> pd.DataFrame:
    """
    加载原料角色数据
    """
    engine = get_engine()
    sql = text("""
    SELECT recipe_id, ingredient_id, role
    FROM recipe_ingredient
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条原料角色数据")
    return df

def load_ingredient_types() -> pd.DataFrame:
    """
    加载原料类型数据
    """
    engine = get_engine()
    sql = text("""
    SELECT ingredient_id, type_tag
    FROM ingredient_type
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    print(f"[INFO] 加载了 {len(df)} 条原料类型数据")
    return df

def map_to_canonical(node_importance_df: pd.DataFrame, canonical_df: pd.DataFrame) -> pd.DataFrame:
    """
    将节点重要性数据映射到 canonical
    """
    # 合并 canonical 映射信息
    merged_df = node_importance_df.merge(
        canonical_df, 
        left_on='ingredient_id', 
        right_on='src_ingredient_id', 
        how='left'
    )
    
    # 填充缺失的 canonical 信息（如果没有 canonical 映射，使用自身的 ingredient_id 和名称）
    merged_df['canonical_id'] = merged_df['canonical_id'].fillna(merged_df['ingredient_id'])
    merged_df['canonical_name'] = merged_df['canonical_name'].fillna(merged_df['ingredient_name'])
    
    return merged_df

def map_to_flavor_anchor(canonical_df: pd.DataFrame, flavor_anchor_df: pd.DataFrame) -> pd.DataFrame:
    """
    将 canonical 数据映射到 flavor anchor
    """
    # 合并 flavor anchor 映射信息
    merged_df = canonical_df.merge(
        flavor_anchor_df, 
        left_on='ingredient_id', 
        right_on='ingredient_id', 
        how='left'
    )
    
    # 填充缺失的 flavor anchor 信息（如果没有 anchor 映射，使用 canonical 信息）
    merged_df['anchor_name'] = merged_df['anchor_name'].fillna(merged_df['canonical_name'])
    merged_df['anchor_form'] = merged_df['anchor_form'].fillna('unknown')
    merged_df['match_confidence'] = merged_df['match_confidence'].fillna(0.5)
    
    return merged_df

def merge_with_roles(canonical_df: pd.DataFrame, roles_df: pd.DataFrame) -> pd.DataFrame:
    """
    合并角色信息
    """
    # 合并角色信息
    merged_df = canonical_df.merge(
        roles_df, 
        on=['recipe_id', 'ingredient_id'], 
        how='left'
    )
    
    # 填充缺失的角色
    merged_df['role'] = merged_df['role'].fillna('unknown')
    
    return merged_df

def merge_with_types(canonical_df: pd.DataFrame, types_df: pd.DataFrame) -> pd.DataFrame:
    """
    合并类型信息
    """
    # 合并类型信息
    merged_df = canonical_df.merge(
        types_df, 
        on='ingredient_id', 
        how='left'
    )
    
    # 填充缺失的类型
    merged_df['type_tag'] = merged_df['type_tag'].fillna('unknown')
    
    # 标记可疑节点
    suspect_keywords = ['grated', 'sliced', 'wedge', 'peel', 'fresh', 'chopped', 'diced', 'minced']
    merged_df['is_suspect_node'] = False
    
    # 检查是否为可疑节点
    for keyword in suspect_keywords:
        merged_df['is_suspect_node'] = merged_df['is_suspect_node'] | merged_df['ingredient_name'].str.contains(keyword, case=False, na=False)
    
    # 检查类型是否为 other
    merged_df['is_suspect_node'] = merged_df['is_suspect_node'] | (merged_df['type_tag'] == 'other')
    
    return merged_df

def merge_with_freq(canonical_df: pd.DataFrame, freq_df: pd.DataFrame) -> pd.DataFrame:
    """
    合并频率信息
    """
    # 检查是否存在 canonical_id 字段
    if 'canonical_id' not in canonical_df.columns:
        # 如果不存在，使用 ingredient_id 作为替代
        merged_df = canonical_df.merge(
            freq_df, 
            left_on='ingredient_id', 
            right_on='canonical_id', 
            how='left'
        )
    else:
        # 合并频率信息
        merged_df = canonical_df.merge(
            freq_df, 
            on='canonical_id', 
            how='left'
        )
    
    # 填充缺失的频率
    merged_df['freq'] = merged_df['freq'].fillna(0)
    
    return merged_df

def aggregate_within_recipe(canonical_df: pd.DataFrame) -> pd.DataFrame:
    """
    在 recipe 内部按 flavor anchor 合并
    """
    # 定义一个函数来获取每个组内重要性最大的角色
    def get_dominant_role(group):
        if len(group) == 0:
            return 'unknown'
        return group.loc[group['importance_score'].idxmax(), 'role']
    
    # 按 recipe_id 和 anchor_name 聚合
    aggregated = canonical_df.groupby(['recipe_id', 'anchor_name', 'anchor_form']).apply(
        lambda group: pd.Series({
            'max_importance': group['importance_score'].max(),
            'min_rank': group['rank'].min(),
            'role': get_dominant_role(group),
            'is_suspect_node': group['is_suspect_node'].any(),
            'freq': group['freq'].max() if 'freq' in group.columns else 0
        })
    ).reset_index()
    
    return aggregated

def calculate_global_statistics(aggregated_df: pd.DataFrame) -> pd.DataFrame:
    """
    计算全局统计信息
    """
    # 按 anchor_name 聚合
    global_stats = aggregated_df.groupby(['anchor_name', 'anchor_form']).agg(
        recipe_count=('recipe_id', 'nunique'),
        total_importance=('max_importance', 'sum'),
        avg_importance=('max_importance', 'mean'),
        median_importance=('max_importance', 'median'),
        top1_count=('min_rank', lambda x: (x == 1).sum()),
        top3_count=('min_rank', lambda x: (x <= 3).sum()),
        top5_count=('min_rank', lambda x: (x <= 5).sum()),
        # 角色分布
        role_base_spirit_count=('role', lambda x: (x == 'base_spirit').sum()),
        role_modifier_count=('role', lambda x: (x == 'modifier').sum()),
        role_acid_count=('role', lambda x: (x == 'acid').sum()),
        role_sweetener_count=('role', lambda x: (x == 'sweetener').sum()),
        role_bitters_count=('role', lambda x: (x == 'bitters').sum()),
        role_garnish_count=('role', lambda x: (x == 'garnish').sum()),
        role_dilution_count=('role', lambda x: (x == 'dilution').sum()),
        role_other_count=('role', lambda x: (x == 'other').sum()),
        is_suspect_node=('is_suspect_node', 'any'),
        # 频率信息
        avg_freq=('freq', 'mean'),
        max_freq=('freq', 'max')
    ).reset_index()
    
    # 计算派生统计量
    global_stats['top1_rate'] = global_stats['top1_count'] / global_stats['recipe_count']
    global_stats['top3_rate'] = global_stats['top3_count'] / global_stats['recipe_count']
    global_stats['top5_rate'] = global_stats['top5_count'] / global_stats['recipe_count']
    
    # 计算主要角色
    role_columns = ['role_base_spirit_count', 'role_modifier_count', 'role_acid_count', 
                   'role_sweetener_count', 'role_bitters_count', 'role_garnish_count', 
                   'role_dilution_count', 'role_other_count']
    
    global_stats['dominant_role'] = global_stats[role_columns].idxmax(axis=1).str.replace('role_', '').str.replace('_count', '')
    global_stats['dominant_role_ratio'] = global_stats[role_columns].max(axis=1) / global_stats['recipe_count']
    
    return global_stats

def calculate_shrunk_importance(global_stats: pd.DataFrame, aggregated_df: pd.DataFrame, m: int = 8) -> pd.DataFrame:
    """
    计算收缩后的重要性（加强支持度惩罚）
    """
    # 计算 recipe-anchor 事件层的全局均值
    global_mean = aggregated_df['max_importance'].mean()
    
    # 计算收缩后的重要性（加强 m 值，增加惩罚）
    global_stats['shrunk_importance'] = (
        (global_stats['recipe_count'] * global_stats['avg_importance'] + m * global_mean) / 
        (global_stats['recipe_count'] + m)
    )
    
    return global_stats

def calculate_global_key_score(global_stats: pd.DataFrame) -> pd.DataFrame:
    """
    计算全局关键得分
    """
    # 计算 topk 得分
    global_stats['topk_score'] = (
        1.0 * global_stats['top1_rate'] +
        0.6 * global_stats['top3_rate'] +
        0.3 * global_stats['top5_rate']
    ) / 1.9
    
    # 计算覆盖度得分（使用数据库中的 freq 信息）
    if 'max_freq' in global_stats.columns:
        global_max_freq = global_stats['max_freq'].max()
        if global_max_freq > 0:
            # 使用每个 anchor 自身的频率作为分子，全局最大频率作为分母
            global_stats['coverage_score'] = np.log1p(global_stats['max_freq']) / np.log1p(global_max_freq)
        else:
            max_recipe_count = global_stats['recipe_count'].max()
            global_stats['coverage_score'] = np.log1p(global_stats['recipe_count']) / np.log1p(max_recipe_count)
    else:
        max_recipe_count = global_stats['recipe_count'].max()
        global_stats['coverage_score'] = np.log1p(global_stats['recipe_count']) / np.log1p(max_recipe_count)
    
    # 计算全局关键得分（调整权重，增加覆盖度权重）
    global_stats['global_key_score'] = (
        0.55 * global_stats['shrunk_importance'] +  # 降低重要性权重
        0.25 * global_stats['topk_score'] +
        0.20 * global_stats['coverage_score']  # 增加覆盖度权重
    )
    
    return global_stats

def filter_by_role(global_stats: pd.DataFrame, role: str) -> pd.DataFrame:
    """
    根据角色过滤数据
    """
    if role == 'base':
        return global_stats[global_stats['dominant_role'] == 'base_spirit']
    elif role == 'modifier':
        return global_stats[global_stats['dominant_role'] == 'modifier']
    elif role == 'sweetener':
        return global_stats[global_stats['dominant_role'] == 'sweetener']
    elif role == 'acid':
        return global_stats[global_stats['dominant_role'] == 'acid']
    elif role == 'bitters':
        return global_stats[global_stats['dominant_role'] == 'bitters']
    elif role == 'garnish':
        return global_stats[global_stats['dominant_role'] == 'garnish']
    elif role == 'dilution':
        return global_stats[global_stats['dominant_role'] == 'dilution']
    elif role == 'other':
        return global_stats[global_stats['dominant_role'] == 'other']
    elif role == 'acid_sweet':
        return global_stats[global_stats['dominant_role'].isin(['acid', 'sweetener'])]
    else:
        return global_stats

def generate_llm_input(global_summary: pd.DataFrame, total_recipes: int) -> dict:
    """
    生成 LLM 输入数据
    """
    # 获取前 20 个关键风味原料
    top_20_flavors = global_summary.head(20)
    
    # 准备 LLM 输入
    llm_input = {
        "task": "分析全局关键风味元素",
        "description": "基于对所有配方的节点重要性分析，汇总出的全局关键风味元素排行榜。请分析这些原料的特点、在不同角色中的分布，以及它们对配方结构的影响。",
        "top_flavors": [],
        "key_statistics": {
            "total_ingredients": len(global_summary),
            "total_recipes": total_recipes
        }
    }
    
    # 添加前 20 个风味原料的详细信息
    for _, row in top_20_flavors.iterrows():
        flavor_info = {
            "rank": int(row['global_rank']),
            "name": str(row['anchor_name']),
            "form": str(row['anchor_form']),
            "avg_importance": float(row['avg_importance']),
            "shrunk_importance": float(row['shrunk_importance']),
            "total_importance": float(row['total_importance']),
            "recipe_count": int(row['recipe_count']),
            "top1_count": int(row['top1_count']),
            "top3_count": int(row['top3_count']),
            "top5_count": int(row['top5_count']),
            "top1_rate": float(row['top1_rate']),
            "top3_rate": float(row['top3_rate']),
            "top5_rate": float(row['top5_rate']),
            "dominant_role": str(row['dominant_role']),
            "dominant_role_ratio": float(row['dominant_role_ratio']),
            "global_key_score": float(row['global_key_score']),
            "is_suspect_node": bool(row['is_suspect_node'])
        }
        llm_input['top_flavors'].append(flavor_info)
    
    return llm_input

def main():
    """
    主函数
    """
    print("开始汇总全局关键风味 (v3)...")
    
    # 加载数据
    node_importance_df = load_node_importance_data()
    canonical_df = load_canonical_mapping()
    flavor_anchor_df = load_flavor_anchor_mapping()
    freq_df = load_canonical_freq()
    roles_df = load_ingredient_roles()
    types_df = load_ingredient_types()
    
    # 计算总配方数
    total_recipes = node_importance_df['recipe_id'].nunique()
    print(f"[INFO] 总配方数: {total_recipes}")
    
    # 映射到 canonical
    canonical_mapped = map_to_canonical(node_importance_df, canonical_df)
    
    # 映射到 flavor anchor
    anchor_mapped = map_to_flavor_anchor(canonical_mapped, flavor_anchor_df)
    
    # 合并角色信息
    anchor_with_roles = merge_with_roles(anchor_mapped, roles_df)
    
    # 合并类型信息
    anchor_with_types = merge_with_types(anchor_with_roles, types_df)
    
    # 合并频率信息
    anchor_with_freq = merge_with_freq(anchor_with_types, freq_df)
    
    # 在 recipe 内部按 flavor anchor 合并
    aggregated_within_recipe = aggregate_within_recipe(anchor_with_freq)
    
    # 计算全局统计信息
    global_stats = calculate_global_statistics(aggregated_within_recipe)
    
    # 计算收缩后的重要性
    global_stats = calculate_shrunk_importance(global_stats, aggregated_within_recipe)
    
    # 计算全局关键得分
    global_stats = calculate_global_key_score(global_stats)
    
    # 生成总体榜
    global_summary_overall = global_stats.sort_values('global_key_score', ascending=False)
    global_summary_overall['global_rank'] = range(1, len(global_summary_overall) + 1)
    
    # 生成 base 榜
    global_summary_base = filter_by_role(global_stats, 'base').sort_values('global_key_score', ascending=False)
    global_summary_base['global_rank'] = range(1, len(global_summary_base) + 1)
    
    # 生成 modifier 榜
    global_summary_modifier = filter_by_role(global_stats, 'modifier').sort_values('global_key_score', ascending=False)
    global_summary_modifier['global_rank'] = range(1, len(global_summary_modifier) + 1)
    
    # 生成 acid/sweet 榜
    global_summary_acid_sweet = filter_by_role(global_stats, 'acid_sweet').sort_values('global_key_score', ascending=False)
    global_summary_acid_sweet['global_rank'] = range(1, len(global_summary_acid_sweet) + 1)
    
    # 生成 sweetener 榜
    global_summary_sweetener = filter_by_role(global_stats, 'sweetener').sort_values('global_key_score', ascending=False)
    global_summary_sweetener['global_rank'] = range(1, len(global_summary_sweetener) + 1)
    
    # 生成 acid 榜
    global_summary_acid = filter_by_role(global_stats, 'acid').sort_values('global_key_score', ascending=False)
    global_summary_acid['global_rank'] = range(1, len(global_summary_acid) + 1)
    
    # 生成 bitters 榜
    global_summary_bitters = filter_by_role(global_stats, 'bitters').sort_values('global_key_score', ascending=False)
    global_summary_bitters['global_rank'] = range(1, len(global_summary_bitters) + 1)
    
    # 生成 garnish 榜
    global_summary_garnish = filter_by_role(global_stats, 'garnish').sort_values('global_key_score', ascending=False)
    global_summary_garnish['global_rank'] = range(1, len(global_summary_garnish) + 1)
    
    # 生成 dilution 榜
    global_summary_dilution = filter_by_role(global_stats, 'dilution').sort_values('global_key_score', ascending=False)
    global_summary_dilution['global_rank'] = range(1, len(global_summary_dilution) + 1)
    
    # 生成 other 榜
    global_summary_other = filter_by_role(global_stats, 'other').sort_values('global_key_score', ascending=False)
    global_summary_other['global_rank'] = range(1, len(global_summary_other) + 1)
    
    # 保存结果
    output_columns = [
        'global_rank', 'anchor_name', 'anchor_form', 'global_key_score',
        'avg_importance', 'shrunk_importance', 'total_importance', 'recipe_count',
        'top1_count', 'top3_count', 'top5_count', 'top1_rate', 'top3_rate', 'top5_rate',
        'role_base_spirit_count', 'role_modifier_count', 'role_acid_count', 'role_sweetener_count',
        'role_bitters_count', 'role_garnish_count', 'role_dilution_count', 'role_other_count',
        'avg_freq', 'max_freq',
        'dominant_role', 'dominant_role_ratio', 'is_suspect_node'
    ]
    
    global_summary_overall[output_columns].to_csv(Config.GLOBAL_SUMMARY_OVERALL_FILE, index=False, encoding='utf-8')
    global_summary_base[output_columns].to_csv(Config.GLOBAL_SUMMARY_BASE_FILE, index=False, encoding='utf-8')
    global_summary_modifier[output_columns].to_csv(Config.GLOBAL_SUMMARY_MODIFIER_FILE, index=False, encoding='utf-8')
    global_summary_sweetener[output_columns].to_csv(Config.GLOBAL_SUMMARY_SWEETENER_FILE, index=False, encoding='utf-8')
    global_summary_acid[output_columns].to_csv(Config.GLOBAL_SUMMARY_ACID_FILE, index=False, encoding='utf-8')
    global_summary_bitters[output_columns].to_csv(Config.GLOBAL_SUMMARY_BITTERS_FILE, index=False, encoding='utf-8')
    global_summary_garnish[output_columns].to_csv(Config.GLOBAL_SUMMARY_GARNISH_FILE, index=False, encoding='utf-8')
    global_summary_dilution[output_columns].to_csv(Config.GLOBAL_SUMMARY_DILUTION_FILE, index=False, encoding='utf-8')
    global_summary_other[output_columns].to_csv(Config.GLOBAL_SUMMARY_OTHER_FILE, index=False, encoding='utf-8')
    
    print(f"[INFO] 总体榜已保存到: {Config.GLOBAL_SUMMARY_OVERALL_FILE}")
    print(f"[INFO] Base 榜已保存到: {Config.GLOBAL_SUMMARY_BASE_FILE}")
    print(f"[INFO] Modifier 榜已保存到: {Config.GLOBAL_SUMMARY_MODIFIER_FILE}")
    print(f"[INFO] Sweetener 榜已保存到: {Config.GLOBAL_SUMMARY_SWEETENER_FILE}")
    print(f"[INFO] Acid 榜已保存到: {Config.GLOBAL_SUMMARY_ACID_FILE}")
    print(f"[INFO] Bitters 榜已保存到: {Config.GLOBAL_SUMMARY_BITTERS_FILE}")
    print(f"[INFO] Garnish 榜已保存到: {Config.GLOBAL_SUMMARY_GARNISH_FILE}")
    print(f"[INFO] Dilution 榜已保存到: {Config.GLOBAL_SUMMARY_DILUTION_FILE}")
    print(f"[INFO] Other 榜已保存到: {Config.GLOBAL_SUMMARY_OTHER_FILE}")
    print(f"[INFO] 共分析了 {len(global_summary_overall)} 种 flavor anchor")
    
    # 生成 LLM 输入
    llm_input = generate_llm_input(global_summary_overall, total_recipes)
    
    # 保存 LLM 输入
    with open(Config.LLM_INPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(llm_input, f, ensure_ascii=False, indent=2)
    
    print(f"[INFO] LLM 输入数据已保存到: {Config.LLM_INPUT_FILE}")
    
    # 显示前 10 个关键风味原料（总体榜）
    print("\n[INFO] 前 10 个关键风味原料 (总体榜):")
    top_10_overall = global_summary_overall.head(10)
    for _, row in top_10_overall.iterrows():
        print(f"{int(row['global_rank'])}. {row['anchor_name']} (全局关键得分: {row['global_key_score']:.4f}, 配方数: {int(row['recipe_count'])}, 主要角色: {row['dominant_role']})")
    
    # 显示前 10 个关键风味原料（base 榜）
    print("\n[INFO] 前 10 个关键风味原料 (Base 榜):")
    top_10_base = global_summary_base.head(10)
    for _, row in top_10_base.iterrows():
        print(f"{int(row['global_rank'])}. {row['anchor_name']} (全局关键得分: {row['global_key_score']:.4f}, 配方数: {int(row['recipe_count'])})")
    
    # 显示前 10 个关键风味原料（modifier 榜）
    print("\n[INFO] 前 10 个关键风味原料 (Modifier 榜):")
    top_10_modifier = global_summary_modifier.head(10)
    for _, row in top_10_modifier.iterrows():
        print(f"{int(row['global_rank'])}. {row['anchor_name']} (全局关键得分: {row['global_key_score']:.4f}, 配方数: {int(row['recipe_count'])})")
    
    # 显示前 10 个关键风味原料（sweetener 榜）
    print("\n[INFO] 前 10 个关键风味原料 (Sweetener 榜):")
    top_10_sweetener = global_summary_sweetener.head(10)
    for _, row in top_10_sweetener.iterrows():
        print(f"{int(row['global_rank'])}. {row['anchor_name']} (全局关键得分: {row['global_key_score']:.4f}, 配方数: {int(row['recipe_count'])})")
    
    # 显示前 10 个关键风味原料（acid 榜）
    print("\n[INFO] 前 10 个关键风味原料 (Acid 榜):")
    top_10_acid = global_summary_acid.head(10)
    for _, row in top_10_acid.iterrows():
        print(f"{int(row['global_rank'])}. {row['anchor_name']} (全局关键得分: {row['global_key_score']:.4f}, 配方数: {int(row['recipe_count'])})")
    
    # 显示前 10 个关键风味原料（bitters 榜）
    print("\n[INFO] 前 10 个关键风味原料 (Bitters 榜):")
    top_10_bitters = global_summary_bitters.head(10)
    for _, row in top_10_bitters.iterrows():
        print(f"{int(row['global_rank'])}. {row['anchor_name']} (全局关键得分: {row['global_key_score']:.4f}, 配方数: {int(row['recipe_count'])})")
    
    # 显示前 10 个关键风味原料（garnish 榜）
    print("\n[INFO] 前 10 个关键风味原料 (Garnish 榜):")
    top_10_garnish = global_summary_garnish.head(10)
    for _, row in top_10_garnish.iterrows():
        print(f"{int(row['global_rank'])}. {row['anchor_name']} (全局关键得分: {row['global_key_score']:.4f}, 配方数: {int(row['recipe_count'])})")
    
    # 显示前 10 个关键风味原料（dilution 榜）
    print("\n[INFO] 前 10 个关键风味原料 (Dilution 榜):")
    top_10_dilution = global_summary_dilution.head(10)
    for _, row in top_10_dilution.iterrows():
        print(f"{int(row['global_rank'])}. {row['anchor_name']} (全局关键得分: {row['global_key_score']:.4f}, 配方数: {int(row['recipe_count'])})")
    
    # 显示前 10 个关键风味原料（other 榜）
    print("\n[INFO] 前 10 个关键风味原料 (Other 榜):")
    top_10_other = global_summary_other.head(10)
    for _, row in top_10_other.iterrows():
        print(f"{int(row['global_rank'])}. {row['anchor_name']} (全局关键得分: {row['global_key_score']:.4f}, 配方数: {int(row['recipe_count'])})")
    
    # 显示前 10 个关键风味原料（acid/sweet 榜）
    print("\n[INFO] 前 10 个关键风味原料 (Acid/Sweet 榜):")
    top_10_acid_sweet = global_summary_acid_sweet.head(10)
    for _, row in top_10_acid_sweet.iterrows():
        print(f"{int(row['global_rank'])}. {row['anchor_name']} (全局关键得分: {row['global_key_score']:.4f}, 配方数: {int(row['recipe_count'])})")

if __name__ == "__main__":
    main()
