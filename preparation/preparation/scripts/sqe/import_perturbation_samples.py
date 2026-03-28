# -*- coding: utf-8 -*-
"""
导入 Phase B 扰动样本数据到数据库

功能：
1. 读取 Phase B 生成的扰动样本数据文件
2. 将数据转换为适合数据库的格式
3. 插入到 sqe_perturbation_sample 表中
"""

import os
import sys
import csv
import json
from pathlib import Path
from sqlalchemy import text

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.db import get_engine

def parse_perturb_detail(detail):
    """
    解析扰动详情字符串，转换为操作 JSON
    """
    if not detail:
        return None
    
    try:
        # 解析扰动详情
        parts = detail.split(':')
        if len(parts) < 2:
            return None
        
        op_type = parts[0]
        op_details = parts[1].split(',')
        
        operation = {'op': op_type}
        
        for part in op_details:
            if '=' in part:
                key, value = part.split('=', 1)
                operation[key.strip()] = value.strip()
            elif 'from:' in part:
                operation['from'] = part.split('from:', 1)[1].strip()
            elif 'to:' in part:
                operation['to'] = part.split('to:', 1)[1].strip()
            elif 'line_no:' in part:
                operation['line_no'] = int(part.split('line_no:', 1)[1].strip())
            elif 'factor:' in part:
                operation['factor'] = float(part.split('factor:', 1)[1].strip())
            elif 'type:' in part:
                operation['type'] = part.split('type:', 1)[1].strip()
            elif 'current=' in part:
                operation['current'] = int(part.split('current=', 1)[1].strip())
            else:
                # 对于 replace_with_different_anchor 等操作，处理多个ID
                if op_type in ['replace_with_different_anchor', 'replace_with_different_type']:
                    if 'old' not in operation:
                        operation['old'] = part.strip()
                    else:
                        operation['new'] = part.strip()
                elif op_type in ['add_extra_base_spirit', 'acid_sweetener_ratio_break']:
                    operation['ingredient_id'] = part.strip()
        
        return operation
    except Exception as e:
        print(f"解析扰动详情失败: {detail}, 错误: {e}")
        return None

def import_perturbation_samples():
    """
    导入扰动样本数据到数据库
    """
    engine = get_engine()
    
    # 数据文件路径
    data_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseB", "phaseB_pairwise_train.csv")
    
    if not os.path.exists(data_file):
        print(f"数据文件不存在: {data_file}")
        return
    
    # 开始事务
    with engine.begin() as conn:
        total_rows = 0
        success_rows = 0
        
        with open(data_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_rows += 1
                
                try:
                    # 解析扰动详情
                    operation_json = parse_perturb_detail(row['perturb_detail'])
                    
                    # 构建数据字典
                    sample_data = {
                        'snapshot_id': 's0',
                        'sample_version': 'v3',
                        'source_recipe_id': int(row['recipe_id_pos']),
                        'variant_recipe_id': None,  # 扰动后的配方ID，这里使用扰动标识
                        'pair_group_id': row['pair_id'],
                        'sample_type': 'pairwise',
                        'perturb_type_id': row['perturb_type'],
                        'target_canonical_id': None,  # 需要从扰动详情中提取
                        'candidate_canonical_id': None,  # 需要从扰动详情中提取
                        'target_role': None,  # 需要从扰动详情中提取
                        'candidate_role': None,  # 需要从扰动详情中提取
                        'perturb_position': None,  # 需要从扰动详情中提取
                        'perturb_strength': None,  # 需要从扰动详情中提取
                        'before_state': None,  # 扰动前状态
                        'after_state': None,  # 扰动后状态
                        'operation_json': json.dumps(operation_json) if operation_json else None,
                        'label': 1 if row['is_hard_negative'] == 'False' else 0,
                        'preference_direction': 'source_better' if row['is_hard_negative'] == 'False' else 'variant_better',
                        'expected_margin': float(row['overall_margin']),
                        'actual_margin': float(row['overall_margin']),
                        'source_sqe_total': float(row['syn_pos']) + float(row['conf_pos']) + float(row['bal_pos']),
                        'variant_sqe_total': float(row['syn_neg']) + float(row['conf_neg']) + float(row['bal_neg']),
                        'delta_sqe': float(row['delta_syn']) + float(row['delta_conf']) + float(row['delta_bal']),
                        'split_set': 'train',
                        'is_valid': 1 if row['validity_flag'] == 'True' else 0,
                        'reject_reason': row['drop_reason'] if row['drop_reason'] else None
                    }
                    
                    # 从扰动详情中提取更多信息
                    if operation_json:
                        # 提取目标和候选原料ID
                        if 'old' in operation_json:
                            sample_data['target_canonical_id'] = int(operation_json['old'])
                        if 'new' in operation_json:
                            sample_data['candidate_canonical_id'] = int(operation_json['new'])
                        # 提取角色信息
                        if 'role' in operation_json:
                            sample_data['target_role'] = operation_json['role']
                        # 提取位置信息
                        if 'line_no' in operation_json:
                            sample_data['perturb_position'] = operation_json['line_no']
                        # 提取强度信息
                        if 'factor' in operation_json:
                            sample_data['perturb_strength'] = operation_json['factor']
                    
                    # 插入数据
                    insert_sql = text("""
                    INSERT INTO sqe_perturbation_sample (
                        snapshot_id, sample_version, source_recipe_id, variant_recipe_id, pair_group_id,
                        sample_type, perturb_type_id, target_canonical_id, candidate_canonical_id,
                        target_role, candidate_role, perturb_position, perturb_strength, before_state,
                        after_state, operation_json, label, preference_direction, expected_margin,
                        actual_margin, source_sqe_total, variant_sqe_total, delta_sqe, split_set,
                        is_valid, reject_reason
                    ) VALUES (
                        :snapshot_id, :sample_version, :source_recipe_id, :variant_recipe_id, :pair_group_id,
                        :sample_type, :perturb_type_id, :target_canonical_id, :candidate_canonical_id,
                        :target_role, :candidate_role, :perturb_position, :perturb_strength, :before_state,
                        :after_state, :operation_json, :label, :preference_direction, :expected_margin,
                        :actual_margin, :source_sqe_total, :variant_sqe_total, :delta_sqe, :split_set,
                        :is_valid, :reject_reason
                    )
                    """)
                    
                    conn.execute(insert_sql, sample_data)
                    success_rows += 1
                    
                    if total_rows % 100 == 0:
                        print(f"处理进度: {total_rows} 行, 成功: {success_rows} 行")
                        
                except Exception as e:
                    print(f"处理行失败: {row['pair_id']}, 错误: {e}")
                    continue
        
        print(f"导入完成: 总计 {total_rows} 行, 成功 {success_rows} 行")

if __name__ == "__main__":
    print("开始导入 Phase B 扰动样本数据...")
    import_perturbation_samples()
    print("扰动样本数据导入完成！")
