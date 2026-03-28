# -*- coding: utf-8 -*-
"""
关键风味节点识别脚本

功能：
1. 使用节点删除法识别每个配方中的关键风味节点
2. 计算每个原料的重要性分数
3. 为每个配方生成节点重要性表
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
    PHASE_C_RECIPES_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseC", "recipes_data.jsonl")
    
    # 输出文件
    OUTPUT_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "flavor", "node_importance_scores.csv")

def load_recipes_data() -> list:
    """
    加载 Phase C 配方数据
    """
    recipes_data = []
    with open(Config.PHASE_C_RECIPES_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            recipes_data.append(data)
    
    print(f"[INFO] 加载了 {len(recipes_data)} 条配方数据")
    return recipes_data

def load_ingredient_names() -> dict:
    """
    加载原料名称
    """
    engine = get_engine()
    sql = text("""
    SELECT ingredient_id, name_norm
    FROM ingredient
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    ingredient_names = dict(zip(df['ingredient_id'], df['name_norm']))
    print(f"[INFO] 加载了 {len(ingredient_names)} 条原料名称")
    return ingredient_names

# 全局变量，用于存储最优参数和评分数据
_optimal_params = None
_recipe_ingredients = None
_sqe_scores = None

# 导入评分函数
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.sqe.phase_A.phaseA_baseline_v2 import set_sqe_weights
from scripts.sqe.phase_A.sqe_scorer_conflict_v2 import calculate_conflict_score_from_ingredients
from scripts.sqe.phase_A.sqe_scorer_balance import calculate_balance_score_from_ingredients
from scripts.sqe.phase_A.sqe_scorer_synergy import score_recipe_from_ingredients

def load_optimal_params():
    """
    加载最优参数
    """
    global _optimal_params
    
    params_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseC", "optimal_params.json")
    if os.path.exists(params_file):
        with open(params_file, 'r', encoding='utf-8') as f:
            _optimal_params = json.load(f)
        
        # 设置 SQE 权重
        sqe_params = _optimal_params.get('sqe', {})
        lambda_synergy = sqe_params.get('lambda_synergy', 0.4)
        lambda_conflict = sqe_params.get('lambda_conflict', 0.3)
        lambda_balance = sqe_params.get('lambda_balance', 0.3)
        
        set_sqe_weights(lambda_synergy, lambda_conflict, lambda_balance)
        print(f"[INFO] 加载了最优参数: lambda_synergy={lambda_synergy}, lambda_conflict={lambda_conflict}, lambda_balance={lambda_balance}")
    else:
        _optimal_params = {}
        print("[WARNING] 最优参数文件不存在")

def load_recipe_ingredients():
    """
    加载配方原料数据
    """
    global _recipe_ingredients
    
    # 从数据库加载配方原料
    engine = get_engine()
    sql = text("""
    SELECT recipe_id, ingredient_id, amount, unit, role, line_no, raw_text
    FROM recipe_ingredient
    ORDER BY recipe_id, line_no
    """)
    
    with engine.begin() as conn:
        df = pd.read_sql(sql, conn)
    
    # 按配方 ID 分组
    _recipe_ingredients = {}
    for recipe_id, group in df.groupby('recipe_id'):
        ingredients = []
        for _, row in group.iterrows():
            ingredients.append({
                'ingredient_id': row['ingredient_id'],
                'amount': row['amount'],
                'unit': row['unit'],
                'role': row['role'],
                'line_no': row['line_no'],
                'raw_text': row['raw_text']
            })
        _recipe_ingredients[recipe_id] = ingredients
    
    print(f"[INFO] 加载了 {len(_recipe_ingredients)} 个配方的原料数据")

def calculate_sqe_score(recipe_id: int) -> float:
    """
    计算配方的 SQE 分数
    
    参数:
    recipe_id: 配方 ID
    
    返回:
    SQE 分数
    """
    # 检查是否已缓存分数
    global _sqe_scores
    if _sqe_scores is not None and recipe_id in _sqe_scores:
        return _sqe_scores[recipe_id]
    
    # 获取配方原料
    ingredients = _recipe_ingredients.get(recipe_id, [])
    if not ingredients:
        return 0.0
    
    try:
        # 计算协同分数
        synergy_result = score_recipe_from_ingredients(ingredients)
        syn_score = synergy_result.get("synergy_score", 0.0)
        
        # 计算冲突分数
        conflict_result = calculate_conflict_score_from_ingredients(ingredients)
        conf_score = conflict_result.get("conflict_score", 0.0)
        conf_norm = conflict_result.get("conflict_normalized", 0.0)
        
        # 计算平衡分数
        balance_result = calculate_balance_score_from_ingredients(ingredients)
        bal_score = balance_result.get("final_balance_score", 0.0)
        
        # 加载基线统计信息用于标准化
        baseline_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseA_baseline_v2.csv")
        if not os.path.exists(baseline_file):
            return 0.0
        
        df = pd.read_csv(baseline_file)
        
        # 计算各维度的 min/max
        syn_min = df['synergy_score'].min()
        syn_max = df['synergy_score'].max()
        bal_min = df['final_balance_score'].min()
        bal_max = df['final_balance_score'].max()
        
        # 标准化分数
        def normalize(score, min_val, max_val):
            if max_val == min_val:
                return 0.5
            return max(0.0, min(1.0, (score - min_val) / (max_val - min_val)))
        
        syn_norm = normalize(syn_score, syn_min, syn_max)
        bal_norm = normalize(bal_score, bal_min, bal_max)
        
        # 转换冲突分数为越大越好的形式
        conf_good = 1 - conf_norm
        
        # 获取 SQE 权重
        sqe_params = _optimal_params.get('sqe', {})
        lambda_synergy = sqe_params.get('lambda_synergy', 0.4)
        lambda_conflict = sqe_params.get('lambda_conflict', 0.3)
        lambda_balance = sqe_params.get('lambda_balance', 0.3)
        
        # 计算 SQE 总分
        sqe_total = (
            lambda_synergy * syn_norm +
            lambda_conflict * conf_good +
            lambda_balance * bal_norm
        )
        
        # 缓存分数
        if _sqe_scores is None:
            _sqe_scores = {}
        _sqe_scores[recipe_id] = sqe_total
        
        return sqe_total
    except Exception as e:
        print(f"[ERROR] 计算配方 {recipe_id} 的 SQE 分数时出错: {e}")
        return 0.0

def calculate_ingredient_importance(recipe_data: dict, ingredient_names: dict) -> list:
    """
    计算配方中每个原料的重要性
    
    参数:
    recipe_data: 配方数据
    ingredient_names: 原料名称字典
    
    返回:
    原料重要性列表
    """
    recipe_id = recipe_data.get('recipe_id')
    nodes = recipe_data.get('nodes', [])
    
    if not nodes:
        print(f"[DEBUG] 配方 {recipe_id} 没有节点")
        return []
    
    # 计算原始配方的 SQE 分数
    original_score = calculate_sqe_score(recipe_id)
    print(f"[DEBUG] 配方 {recipe_id} 的原始 SQE 分数: {original_score}")
    
    # 获取原始原料列表
    original_ingredients = _recipe_ingredients.get(recipe_id, [])
    if not original_ingredients:
        print(f"[DEBUG] 配方 {recipe_id} 没有原料数据")
        return []
    
    print(f"[DEBUG] 配方 {recipe_id} 有 {len(original_ingredients)} 个原料")
    
    importance_list = []
    
    # 依次删除每个节点，计算重要性
    for i, node in enumerate(nodes):
        ingredient_id = node.get('id')
        ingredient_name = ingredient_names.get(ingredient_id, f"Unknown_{ingredient_id}")
        
        try:
            print(f"[DEBUG] 处理配方 {recipe_id} 的原料 {ingredient_id} ({ingredient_name})")
        except UnicodeEncodeError:
            print(f"[DEBUG] 处理配方 {recipe_id} 的原料 {ingredient_id}")
        
        # 创建删除该原料后的新原料列表
        perturbed_ingredients = [ing for ing in original_ingredients if ing['ingredient_id'] != ingredient_id]
        
        # 如果删除后没有原料，跳过
        if not perturbed_ingredients:
            print(f"[DEBUG] 删除原料 {ingredient_id} 后没有剩余原料，跳过")
            continue
        
        print(f"[DEBUG] 删除原料 {ingredient_id} 后剩余 {len(perturbed_ingredients)} 个原料")
        
        try:
            # 计算协同分数
            print(f"[DEBUG] 计算协同分数...")
            synergy_result = score_recipe_from_ingredients(perturbed_ingredients)
            syn_score = synergy_result.get("synergy_score", 0.0)
            print(f"[DEBUG] 协同分数: {syn_score}")
            
            # 计算冲突分数
            print(f"[DEBUG] 计算冲突分数...")
            conflict_result = calculate_conflict_score_from_ingredients(perturbed_ingredients)
            conf_score = conflict_result.get("conflict_score", 0.0)
            conf_norm = conflict_result.get("conflict_normalized", 0.0)
            print(f"[DEBUG] 冲突分数: {conf_score}, 标准化: {conf_norm}")
            
            # 计算平衡分数
            print(f"[DEBUG] 计算平衡分数...")
            balance_result = calculate_balance_score_from_ingredients(perturbed_ingredients)
            bal_score = balance_result.get("final_balance_score", 0.0)
            print(f"[DEBUG] 平衡分数: {bal_score}")
            
            # 加载基线统计信息用于标准化
            baseline_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseA_baseline_v2.csv")
            if not os.path.exists(baseline_file):
                print(f"[DEBUG] 基线文件不存在: {baseline_file}")
                continue
            
            df = pd.read_csv(baseline_file)
            
            # 计算各维度的 min/max
            syn_min = df['synergy_score'].min()
            syn_max = df['synergy_score'].max()
            bal_min = df['final_balance_score'].min()
            bal_max = df['final_balance_score'].max()
            
            # 标准化分数
            def normalize(score, min_val, max_val):
                if max_val == min_val:
                    return 0.5
                return max(0.0, min(1.0, (score - min_val) / (max_val - min_val)))
            
            syn_norm = normalize(syn_score, syn_min, syn_max)
            bal_norm = normalize(bal_score, bal_min, bal_max)
            
            # 转换冲突分数为越大越好的形式
            conf_good = 1 - conf_norm
            
            # 获取 SQE 权重
            sqe_params = _optimal_params.get('sqe', {})
            lambda_synergy = sqe_params.get('lambda_synergy', 0.4)
            lambda_conflict = sqe_params.get('lambda_conflict', 0.3)
            lambda_balance = sqe_params.get('lambda_balance', 0.3)
            
            # 计算 SQE 总分
            perturbed_score = (
                lambda_synergy * syn_norm +
                lambda_conflict * conf_good +
                lambda_balance * bal_norm
            )
            
            # 计算重要性分数
            importance_score = original_score - perturbed_score
            
            print(f"[DEBUG] 扰动后 SQE 分数: {perturbed_score}, 重要性分数: {importance_score}")
            
            importance_list.append({
                'recipe_id': recipe_id,
                'ingredient_id': ingredient_id,
                'ingredient_name': ingredient_name,
                'importance_score': importance_score
            })
        except Exception as e:
            print(f"[ERROR] 计算配方 {recipe_id} 中原料 {ingredient_id} 的重要性时出错: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 排序并添加排名
    importance_list.sort(key=lambda x: x['importance_score'], reverse=True)
    for rank, item in enumerate(importance_list, 1):
        item['rank'] = rank
    
    print(f"[DEBUG] 配方 {recipe_id} 计算了 {len(importance_list)} 个原料的重要性")
    return importance_list

def main():
    """
    主函数
    """
    print("开始识别关键风味节点...")
    
    # 加载最优参数
    load_optimal_params()
    
    # 加载配方原料数据
    load_recipe_ingredients()
    
    # 加载数据
    recipes_data = load_recipes_data()
    ingredient_names = load_ingredient_names()
    
    # 计算每个配方的原料重要性
    all_importance = []
    for i, recipe_data in enumerate(recipes_data):
        if i % 100 == 0:
            print(f"[INFO] 处理第 {i} 个配方")
        
        try:
            importance_list = calculate_ingredient_importance(recipe_data, ingredient_names)
            all_importance.extend(importance_list)
        except Exception as e:
            print(f"[ERROR] 处理配方 {recipe_data.get('recipe_id')} 时出错: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # 保存结果
    try:
        df = pd.DataFrame(all_importance)
        df.to_csv(Config.OUTPUT_FILE, index=False, encoding='utf-8')
        
        print(f"[INFO] 结果已保存到: {Config.OUTPUT_FILE}")
        print(f"[INFO] 共处理了 {len(recipes_data)} 个配方")
        print(f"[INFO] 共计算了 {len(all_importance)} 个原料的重要性")
    except Exception as e:
        print(f"[ERROR] 保存结果时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
