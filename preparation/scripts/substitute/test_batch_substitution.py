# -*- coding: utf-8 -*-
"""
批量替代分析测试脚本

功能：
1. 测试批量替代分析的核心功能
2. 处理少量配方和原料
3. 将结果插入到数据库的 recipe_substitute_result 表中
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from sqlalchemy import text
from decimal import Decimal

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.db import get_engine
from scripts.sqe.phase_A.phaseA_baseline_v2 import set_sqe_weights
from scripts.sqe.phase_A.sqe_scorer_conflict_v2 import calculate_conflict_score_from_ingredients
from scripts.sqe.phase_A.sqe_scorer_balance import calculate_balance_score_from_ingredients
from scripts.sqe.phase_A.sqe_scorer_synergy import score_recipe_from_ingredients

class Config:
    """配置类"""
    # 输入文件
    PHASE_C_PARAMS_FILE = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseC", "optimal_params.json")

def load_optimal_params() -> dict:
    """
    加载最优参数
    """
    with open(Config.PHASE_C_PARAMS_FILE, 'r', encoding='utf-8') as f:
        params = json.load(f)
    return params

def set_optimal_weights():
    """
    设置最优权重
    """
    params = load_optimal_params()
    sqe_params = params.get('sqe', {})
    
    lambda_synergy = sqe_params.get('lambda_synergy', 0.4)
    lambda_conflict = sqe_params.get('lambda_conflict', 0.3)
    lambda_balance = sqe_params.get('lambda_balance', 0.3)
    
    set_sqe_weights(lambda_synergy, lambda_conflict, lambda_balance)
    
    print(f"[INFO] 设置最优权重: synergy={lambda_synergy}, conflict={lambda_conflict}, balance={lambda_balance}")

def load_recipe_ingredients(recipe_id: int) -> list:
    """
    加载配方的原料列表
    """
    engine = get_engine()
    sql = text("""
    SELECT ri.ingredient_id, i.name_norm, ri.amount, ri.unit, ri.role, ri.line_no, ri.raw_text
    FROM recipe_ingredient ri
    JOIN ingredient i ON ri.ingredient_id = i.ingredient_id
    WHERE ri.recipe_id = :recipe_id
    ORDER BY ri.line_no
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql, {'recipe_id': recipe_id})
        ingredients = []
        for row in result:
            ingredient = {
                'ingredient_id': row.ingredient_id,
                'ingredient_name': row.name_norm,
                'amount': float(row.amount) if row.amount is not None else None,
                'unit': row.unit,
                'role': row.role,
                'line_no': row.line_no,
                'raw_text': row.raw_text
            }
            ingredients.append(ingredient)
    
    return ingredients

def load_canonical_mapping() -> dict:
    """
    加载 canonical 映射信息
    """
    engine = get_engine()
    sql = text("""
    SELECT src_ingredient_id, canonical_id, canonical_name
    FROM llm_canonical_map
    WHERE status = 'ok'
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql)
        canonical_map = {}
        for row in result:
            canonical_map[row.src_ingredient_id] = {
                'canonical_id': row.canonical_id,
                'canonical_name': row.canonical_name
            }
    
    return canonical_map

def load_candidate_ingredients(target_ingredient_id: int, target_role: str, canonical_map: dict) -> list:
    """
    加载候选替代原料，参考风味互补和共现信息
    """
    engine = get_engine()
    
    # 获取目标原料的 canonical 信息
    target_canonical = canonical_map.get(target_ingredient_id, {})
    target_canonical_id = target_canonical.get('canonical_id')
    
    # 查找与目标原料同角色的其他原料，且 canonical 不同
    sql = text("""
    SELECT DISTINCT i.ingredient_id, i.name_norm, ri.role
    FROM ingredient i
    JOIN recipe_ingredient ri ON i.ingredient_id = ri.ingredient_id
    LEFT JOIN llm_canonical_map lcm ON i.ingredient_id = lcm.src_ingredient_id AND lcm.status = 'ok'
    WHERE ri.role = :target_role 
    AND i.ingredient_id != :target_ingredient_id
    AND (lcm.canonical_id != :target_canonical_id OR lcm.canonical_id IS NULL)
    GROUP BY i.ingredient_id, i.name_norm, ri.role
    ORDER BY COUNT(*) DESC
    LIMIT 10
    """)
    
    with engine.begin() as conn:
        result = conn.execute(sql, {
            'target_role': target_role, 
            'target_ingredient_id': target_ingredient_id,
            'target_canonical_id': target_canonical_id
        })
        candidates = []
        for row in result:
            candidate = {
                'ingredient_id': row.ingredient_id,
                'ingredient_name': row.name_norm,
                'role': row.role
            }
            # 添加 canonical 信息
            if row.ingredient_id in canonical_map:
                candidate['canonical_id'] = canonical_map[row.ingredient_id]['canonical_id']
                candidate['canonical_name'] = canonical_map[row.ingredient_id]['canonical_name']
            else:
                candidate['canonical_id'] = None
                candidate['canonical_name'] = row.name_norm
            candidates.append(candidate)
    
    # 过滤掉没有 canonical 映射的候选原料
    candidates = [c for c in candidates if c.get('canonical_id') is not None]
    
    return candidates

def calculate_sqe_score(ingredients: list) -> dict:
    """
    计算配方的 SQE 分数
    """
    try:
        # 计算各维度分数
        synergy_result = score_recipe_from_ingredients(ingredients)
        syn_score = synergy_result.get("synergy_score", 0.0)
        
        conflict_result = calculate_conflict_score_from_ingredients(ingredients)
        conf_score = conflict_result.get("conflict_score", 0.0)
        conf_norm = conflict_result.get("conflict_normalized", 0.0)
        
        balance_result = calculate_balance_score_from_ingredients(ingredients)
        bal_score = balance_result.get("final_balance_score", 0.0)
        
        # 加载基线统计信息
        baseline_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseA_baseline_v2.csv")
        if not os.path.exists(baseline_file):
            raise FileNotFoundError(f"Phase A 基线评分表不存在: {baseline_file}")
        
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
        
        # 加载最优权重
        params = load_optimal_params()
        sqe_params = params.get('sqe', {})
        lambda_synergy = sqe_params.get('lambda_synergy', 0.4)
        lambda_conflict = sqe_params.get('lambda_conflict', 0.3)
        lambda_balance = sqe_params.get('lambda_balance', 0.3)
        
        # 计算 SQE 总分
        sqe_total = (
            lambda_synergy * syn_norm +
            lambda_conflict * conf_good +
            lambda_balance * bal_norm
        )
        
        return {
            "synergy_score": syn_score,
            "conflict_score": conf_score,
            "final_balance_score": bal_score,
            "synergy_normalized": syn_norm,
            "conflict_normalized": conf_norm,
            "balance_normalized": bal_norm,
            "conflict_good": conf_good,
            "sqe_total": sqe_total
        }
    except Exception as e:
        print(f"[ERROR] 计算 SQE 分数时出错: {e}")
        return {
            "synergy_score": 0.0,
            "conflict_score": 0.0,
            "final_balance_score": 0.0,
            "synergy_normalized": 0.0,
            "conflict_normalized": 0.0,
            "balance_normalized": 0.0,
            "conflict_good": 1.0,
            "sqe_total": 0.0
        }

def determine_acceptance(delta_sqe: float, threshold: float = 0.05) -> bool:
    """
    确定替代是否可接受
    """
    return delta_sqe > -threshold

def generate_reason_code(delta_sqe: float) -> str:
    """
    生成替代判断原因代码
    """
    if delta_sqe > 0:
        return "accepted_improvement"
    elif delta_sqe > -0.05:
        return "accepted_small_loss"
    else:
        return "rejected_large_loss"

def generate_explanation(original_score, new_score, target_ingredient, candidate_ingredient, ingredients) -> dict:
    """
    生成替代解释
    """
    delta_sqe = new_score['sqe_total'] - original_score['sqe_total']
    
    explanation = {
        "summary": "",
        "delta_sqe": delta_sqe,
        "delta_synergy": new_score['synergy_normalized'] - original_score['synergy_normalized'],
        "delta_conflict": new_score['conflict_good'] - original_score['conflict_good'],
        "delta_balance": new_score['balance_normalized'] - original_score['balance_normalized'],
        "role_match": target_ingredient['role'] == candidate_ingredient['role'],
        "canonical_diff": target_ingredient.get('canonical_name', target_ingredient['ingredient_name']) != candidate_ingredient.get('canonical_name', candidate_ingredient['ingredient_name']),
        "compatibility_score": candidate_ingredient.get('compatibility_score', 0)
    }
    
    # 整体变化
    if delta_sqe > 0:
        explanation["summary"] = f"替代后整体结构质量提升，SQE 总分增加了 {delta_sqe:.4f}"
    elif delta_sqe > -0.05:
        explanation["summary"] = f"替代后整体结构质量基本保持稳定，SQE 总分变化不大 ({delta_sqe:.4f})"
    else:
        explanation["summary"] = f"替代后整体结构质量下降，SQE 总分减少了 {abs(delta_sqe):.4f}"
    
    return explanation

def insert_substitution_result(engine, result):
    """
    将替代结果插入到数据库，如果存在则更新
    """
    # 检查记录是否存在
    check_sql = text("""
    SELECT COUNT(*) as count
    FROM recipe_substitute_result
    WHERE snapshot_id = :snapshot_id
    AND recipe_id = :recipe_id
    AND target_canonical_id = :target_canonical_id
    AND candidate_canonical_id = :candidate_canonical_id
    """)
    
    with engine.begin() as conn:
        check_result = conn.execute(check_sql, {
            'snapshot_id': result['snapshot_id'],
            'recipe_id': result['recipe_id'],
            'target_canonical_id': result['target_canonical_id'],
            'candidate_canonical_id': result['candidate_canonical_id']
        }).scalar()
        
        if check_result > 0:
            # 记录存在，执行更新
            update_sql = text("""
            UPDATE recipe_substitute_result
            SET target_role = :target_role,
                candidate_role = :candidate_role,
                old_sqe_total = :old_sqe_total,
                new_sqe_total = :new_sqe_total,
                delta_sqe = :delta_sqe,
                old_synergy_score = :old_synergy_score,
                new_synergy_score = :new_synergy_score,
                delta_synergy = :delta_synergy,
                old_conflict_score = :old_conflict_score,
                new_conflict_score = :new_conflict_score,
                delta_conflict = :delta_conflict,
                old_balance_score = :old_balance_score,
                new_balance_score = :new_balance_score,
                delta_balance = :delta_balance,
                accept_flag = :accept_flag,
                rank_no = :rank_no,
                reason_code = :reason_code,
                explanation = :explanation,
                model_version = :model_version,
                updated_at = CURRENT_TIMESTAMP
            WHERE snapshot_id = :snapshot_id
            AND recipe_id = :recipe_id
            AND target_canonical_id = :target_canonical_id
            AND candidate_canonical_id = :candidate_canonical_id
            """)
            conn.execute(update_sql, result)
            print(f"[INFO] 更新了替代结果: recipe_id={result['recipe_id']}, target_canonical_id={result['target_canonical_id']}, candidate_canonical_id={result['candidate_canonical_id']}")
        else:
            # 记录不存在，执行插入
            insert_sql = text("""
            INSERT INTO recipe_substitute_result (
                snapshot_id, recipe_id, target_canonical_id, candidate_canonical_id,
                target_role, candidate_role, old_sqe_total, new_sqe_total, delta_sqe,
                old_synergy_score, new_synergy_score, delta_synergy,
                old_conflict_score, new_conflict_score, delta_conflict,
                old_balance_score, new_balance_score, delta_balance,
                accept_flag, rank_no, reason_code, explanation, model_version
            ) VALUES (
                :snapshot_id, :recipe_id, :target_canonical_id, :candidate_canonical_id,
                :target_role, :candidate_role, :old_sqe_total, :new_sqe_total, :delta_sqe,
                :old_synergy_score, :new_synergy_score, :delta_synergy,
                :old_conflict_score, :new_conflict_score, :delta_conflict,
                :old_balance_score, :new_balance_score, :delta_balance,
                :accept_flag, :rank_no, :reason_code, :explanation, :model_version
            )
            """)
            conn.execute(insert_sql, result)
            print(f"[INFO] 插入了替代结果: recipe_id={result['recipe_id']}, target_canonical_id={result['target_canonical_id']}, candidate_canonical_id={result['candidate_canonical_id']}")

def process_recipe(recipe_id: int, canonical_map: dict, snapshot_id: str = 's0'):
    """
    处理单个配方的所有原料
    """
    print(f"[INFO] 处理配方 {recipe_id}")
    
    # 加载配方原料
    ingredients = load_recipe_ingredients(recipe_id)
    print(f"[INFO] 加载了 {len(ingredients)} 个原料")
    
    # 为每个原料生成替代结果
    for i, target_ingredient in enumerate(ingredients):
        print(f"[INFO] 处理原料 {i+1}/{len(ingredients)}: {target_ingredient['ingredient_name']}")
        
        # 添加 canonical 信息到目标原料
        if target_ingredient['ingredient_id'] in canonical_map:
            target_ingredient['canonical_id'] = canonical_map[target_ingredient['ingredient_id']]['canonical_id']
            target_ingredient['canonical_name'] = canonical_map[target_ingredient['ingredient_id']]['canonical_name']
        else:
            target_ingredient['canonical_id'] = None
            target_ingredient['canonical_name'] = target_ingredient['ingredient_name']
        
        # 跳过没有 canonical 映射的目标原料
        if target_ingredient['canonical_id'] is None:
            print(f"[INFO] 跳过没有 canonical 映射的原料: {target_ingredient['ingredient_name']}")
            continue
        
        # 加载候选替代原料
        candidate_ingredients = load_candidate_ingredients(
            target_ingredient['ingredient_id'], 
            target_ingredient['role'], 
            canonical_map
        )
        
        print(f"[INFO] 加载了 {len(candidate_ingredients)} 个候选替代原料")
        
        # 计算原始配方的 SQE 分数
        original_score = calculate_sqe_score(ingredients)
        print(f"[INFO] 原始配方 SQE 分数: {original_score['sqe_total']:.4f}")
        
        # 执行替代并计算新分数
        for rank_no, candidate in enumerate(candidate_ingredients, 1):
            # 创建新的原料列表，替换目标原料
            new_ingredients = []
            for ing in ingredients:
                if ing['ingredient_id'] == target_ingredient['ingredient_id']:
                    # 替换为候选原料，保持其他属性不变
                    new_ing = ing.copy()
                    new_ing['ingredient_id'] = candidate['ingredient_id']
                    new_ing['ingredient_name'] = candidate['ingredient_name']
                    # 添加 canonical 信息
                    if 'canonical_id' in candidate:
                        new_ing['canonical_id'] = candidate['canonical_id']
                        new_ing['canonical_name'] = candidate['canonical_name']
                    new_ingredients.append(new_ing)
                else:
                    new_ingredients.append(ing)
            
            # 计算新配方的 SQE 分数
            new_score = calculate_sqe_score(new_ingredients)
            delta_sqe = new_score['sqe_total'] - original_score['sqe_total']
            
            # 确定是否接受
            accept_flag = 1 if determine_acceptance(delta_sqe) else 0
            
            # 生成原因代码
            reason_code = generate_reason_code(delta_sqe)
            
            # 生成解释
            explanation = generate_explanation(original_score, new_score, target_ingredient, candidate, ingredients)
            
            # 准备插入数据
            result = {
                'snapshot_id': snapshot_id,
                'recipe_id': recipe_id,
                'target_canonical_id': target_ingredient['canonical_id'],
                'candidate_canonical_id': candidate.get('canonical_id'),
                'target_role': target_ingredient['role'],
                'candidate_role': candidate['role'],
                'old_sqe_total': original_score['sqe_total'],
                'new_sqe_total': new_score['sqe_total'],
                'delta_sqe': delta_sqe,
                'old_synergy_score': original_score['synergy_score'],
                'new_synergy_score': new_score['synergy_score'],
                'delta_synergy': new_score['synergy_score'] - original_score['synergy_score'],
                'old_conflict_score': original_score['conflict_score'],
                'new_conflict_score': new_score['conflict_score'],
                'delta_conflict': new_score['conflict_score'] - original_score['conflict_score'],
                'old_balance_score': original_score['final_balance_score'],
                'new_balance_score': new_score['final_balance_score'],
                'delta_balance': new_score['final_balance_score'] - original_score['final_balance_score'],
                'accept_flag': accept_flag,
                'rank_no': rank_no,
                'reason_code': reason_code,
                'explanation': json.dumps(explanation, ensure_ascii=False),
                'model_version': 'phaseD_v1'
            }
            
            # 插入到数据库
            insert_substitution_result(get_engine(), result)
            
            # 每处理 5 个候选原料后打印进度
            if rank_no % 5 == 0:
                print(f"[INFO] 已处理 {rank_no}/{len(candidate_ingredients)} 个候选原料")

def main():
    """
    主函数
    """
    print("开始批量替代分析测试...")
    
    # 设置最优权重
    set_optimal_weights()
    
    # 加载 canonical 映射
    canonical_map = load_canonical_mapping()
    print(f"[INFO] 加载了 {len(canonical_map)} 个 canonical 映射")
    
    # 测试处理前 3 个配方
    test_recipes = [1, 2, 3]
    
    # 处理每个配方
    for i, recipe_id in enumerate(test_recipes):
        print(f"[INFO] 处理配方 {i+1}/{len(test_recipes)}: {recipe_id}")
        try:
            process_recipe(recipe_id, canonical_map)
        except Exception as e:
            print(f"[ERROR] 处理配方 {recipe_id} 时出错: {e}")
            continue

if __name__ == "__main__":
    main()
