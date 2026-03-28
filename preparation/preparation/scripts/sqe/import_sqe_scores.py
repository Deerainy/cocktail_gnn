# -*- coding: utf-8 -*-
"""
SQE 分数导入脚本

功能：
1. 加载 phaseA 的 SQE 数据
2. 对 phaseA 的 conflict 数据进行归一化
3. 加载 phaseC 的数据
4. 对 phaseC 的数据进行归一化
5. 将数据插入到数据库的 sqe_recipe_score 表中
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from sqlalchemy import text

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.db import get_engine

def min_max_normalize(series):
    """
    Min-Max 归一化
    """
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series([0.0] * len(series), index=series.index)
    return (series - min_val) / (max_val - min_val)

def winsorize_and_normalize(series, lower_percentile=0.01, upper_percentile=0.99):
    """
    对数据进行 winsorization 处理后再进行 Min-Max 归一化
    """
    # 计算分位数
    lower_bound = series.quantile(lower_percentile)
    upper_bound = series.quantile(upper_percentile)
    
    # 对极端值进行 Winsorization 处理
    series_winsorized = series.clip(lower=lower_bound, upper=upper_bound)
    
    # 对处理后的数据进行 Min-Max 归一化
    return min_max_normalize(series_winsorized)

def load_phaseA_data():
    """
    加载 phaseA 的 SQE 数据
    """
    phaseA_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseA", "phaseA_baseline_v2.csv")
    if not os.path.exists(phaseA_file):
        raise FileNotFoundError(f"Phase A 数据文件不存在: {phaseA_file}")
    
    df = pd.read_csv(phaseA_file)
    print(f"[INFO] 加载了 {len(df)} 条 Phase A 数据")
    
    # 对 conflict 数据进行 winsorization 处理后再归一化
    if 'conflict_score' in df.columns:
        df['phaseA_conflict_norm'] = winsorize_and_normalize(df['conflict_score'])
    
    # 对 synergy 和 balance 数据进行归一化
    if 'synergy_score' in df.columns:
        df['phaseA_synergy_norm'] = min_max_normalize(df['synergy_score'])
    
    if 'final_balance_score' in df.columns:
        df['phaseA_balance_norm'] = min_max_normalize(df['final_balance_score'])
    
    return df

def load_phaseC_data():
    """
    加载 phaseC 的数据
    """
    phaseC_file = os.path.join(str(Path(__file__).resolve().parents[2]), "scripts", "sqe", "phase_C", "outputs", "phaseC", "recipes_data_with_sqe_c.jsonl")
    if not os.path.exists(phaseC_file):
        raise FileNotFoundError(f"Phase C 数据文件不存在: {phaseC_file}")
    
    data = []
    with open(phaseC_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    data.append(obj)
                except json.JSONDecodeError:
                    print(f"[WARNING] 跳过无效的 JSON 行: {line[:100]}...")
    
    df = pd.DataFrame(data)
    print(f"[INFO] 加载了 {len(df)} 条 Phase C 数据")
    
    # 对数据进行归一化
    if 'syn_B' in df.columns:
        df['phaseB_synergy_score'] = min_max_normalize(df['syn_B'])
    
    if 'conf_B' in df.columns:
        df['phaseB_conflict_score'] = min_max_normalize(df['conf_B'])
    
    if 'bal_B' in df.columns:
        df['phaseB_balance_score'] = min_max_normalize(df['bal_B'])
    
    if 'sqe_B' in df.columns:
        df['phaseB_total'] = min_max_normalize(df['sqe_B'])
    
    if 'sqe_c' in df.columns:
        df['phaseC_final_sqe'] = min_max_normalize(df['sqe_c'])
    
    return df

def insert_into_database(phaseA_df, phaseC_df):
    """
    将数据插入到数据库中
    """
    engine = get_engine()
    
    # 合并 phaseA 和 phaseC 的数据
    merged_df = pd.merge(phaseA_df, phaseC_df, on='recipe_id', how='outer')
    print(f"[INFO] 合并后的数据行数: {len(merged_df)}")
    
    # 插入数据
    for _, row in merged_df.iterrows():
        recipe_id = row.get('recipe_id', None)
        
        # 过滤掉非整数的 recipe_id
        if recipe_id is not None:
            try:
                # 尝试转换为整数
                int(recipe_id)
            except (ValueError, TypeError):
                print(f"[WARNING] 跳过非整数 recipe_id: {recipe_id}")
                continue
        
        # 准备插入数据
        data = {
            'snapshot_id': 's0',
            'recipe_id': recipe_id,
            'param_version': 'phaseB_v3',
            'model_version': 'phaseC_v1',
            'phaseA_synergy_raw': row.get('synergy_score', None),
            'phaseA_conflict_raw': row.get('conflict_score', None),
            'phaseA_balance_raw': row.get('final_balance_score', None),
            'phaseA_synergy_norm': row.get('phaseA_synergy_norm', None),
            'phaseA_conflict_norm': row.get('phaseA_conflict_norm', None),
            'phaseA_balance_norm': row.get('phaseA_balance_norm', None),
            'phaseA_total': row.get('sqe_total', None),
            'phaseB_synergy_score': row.get('phaseB_synergy_score', None),
            'phaseB_conflict_score': row.get('phaseB_conflict_score', None),
            'phaseB_balance_score': row.get('phaseB_balance_score', None),
            'phaseB_total': row.get('phaseB_total', None),
            'phaseC_base_score': row.get('phaseB_total', None),
            'phaseC_residual': row.get('hat_syn', None),
            'phaseC_pred_score': row.get('sqe_c', None),
            'final_sqe_total': row.get('phaseC_final_sqe', None),
            'is_valid': 1
        }
        
        # 处理 nan 值，替换为 None
        import math
        for key, value in data.items():
            if isinstance(value, float) and math.isnan(value):
                data[key] = None
        
        # 检查记录是否存在
        check_sql = text("""
        SELECT COUNT(*) as count
        FROM sqe_recipe_score
        WHERE snapshot_id = :snapshot_id
        AND recipe_id = :recipe_id
        """)
        
        with engine.begin() as conn:
            check_result = conn.execute(check_sql, {
                'snapshot_id': data['snapshot_id'],
                'recipe_id': data['recipe_id']
            }).scalar()
            
            if check_result > 0:
                # 记录存在，执行更新
                update_sql = text("""
                UPDATE sqe_recipe_score
                SET param_version = :param_version,
                    model_version = :model_version,
                    phaseA_synergy_raw = :phaseA_synergy_raw,
                    phaseA_conflict_raw = :phaseA_conflict_raw,
                    phaseA_balance_raw = :phaseA_balance_raw,
                    phaseA_synergy_norm = :phaseA_synergy_norm,
                    phaseA_conflict_norm = :phaseA_conflict_norm,
                    phaseA_balance_norm = :phaseA_balance_norm,
                    phaseA_total = :phaseA_total,
                    phaseB_synergy_score = :phaseB_synergy_score,
                    phaseB_conflict_score = :phaseB_conflict_score,
                    phaseB_balance_score = :phaseB_balance_score,
                    phaseB_total = :phaseB_total,
                    phaseC_base_score = :phaseC_base_score,
                    phaseC_residual = :phaseC_residual,
                    phaseC_pred_score = :phaseC_pred_score,
                    final_sqe_total = :final_sqe_total,
                    is_valid = :is_valid,
                    updated_at = CURRENT_TIMESTAMP
                WHERE snapshot_id = :snapshot_id
                AND recipe_id = :recipe_id
                """)
                conn.execute(update_sql, data)
                print(f"[INFO] 更新了配方 {data['recipe_id']} 的 SQE 分数")
            else:
                # 记录不存在，执行插入
                insert_sql = text("""
                INSERT INTO sqe_recipe_score (
                    snapshot_id, recipe_id, param_version, model_version,
                    phaseA_synergy_raw, phaseA_conflict_raw, phaseA_balance_raw,
                    phaseA_synergy_norm, phaseA_conflict_norm, phaseA_balance_norm,
                    phaseA_total, phaseB_synergy_score, phaseB_conflict_score,
                    phaseB_balance_score, phaseB_total, phaseC_base_score,
                    phaseC_residual, phaseC_pred_score, final_sqe_total,
                    is_valid
                ) VALUES (
                    :snapshot_id, :recipe_id, :param_version, :model_version,
                    :phaseA_synergy_raw, :phaseA_conflict_raw, :phaseA_balance_raw,
                    :phaseA_synergy_norm, :phaseA_conflict_norm, :phaseA_balance_norm,
                    :phaseA_total, :phaseB_synergy_score, :phaseB_conflict_score,
                    :phaseB_balance_score, :phaseB_total, :phaseC_base_score,
                    :phaseC_residual, :phaseC_pred_score, :final_sqe_total,
                    :is_valid
                )
                """)
                conn.execute(insert_sql, data)
                print(f"[INFO] 插入了配方 {data['recipe_id']} 的 SQE 分数")

def main():
    """
    主函数
    """
    print("开始导入 SQE 分数...")
    
    # 加载 phaseA 数据
    phaseA_df = load_phaseA_data()
    
    # 加载 phaseC 数据
    phaseC_df = load_phaseC_data()
    
    # 插入到数据库
    insert_into_database(phaseA_df, phaseC_df)
    
    print("SQE 分数导入完成！")

if __name__ == "__main__":
    main()
