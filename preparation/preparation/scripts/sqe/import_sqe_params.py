# -*- coding: utf-8 -*-
"""
导入 SQE 参数到数据库

功能：
1. 加载 phaseA 和 phaseB 的 SQE 参数
2. 将参数插入到数据库的 sqe_param_snapshot 表中
"""

import os
import sys
import json
from pathlib import Path
from sqlalchemy import text

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.db import get_engine

def import_sqe_params():
    """
    导入 SQE 参数到数据库
    """
    engine = get_engine()
    
    # 开始事务
    with engine.begin() as conn:
        # 1. 导入 phaseA 的 balance 参数
        balance_params = [
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'balance',
                'param_key': 'MU_FLAVOR',
                'param_value': 0.5,
                'note': '风味平衡权重',
                'phase': 'A'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'balance',
                'param_key': 'MU_ROLE',
                'param_value': 0.5,
                'note': '角色平衡权重',
                'phase': 'A'
            }
        ]
        
        # 2. 导入 phaseA 的 conflict 参数
        conflict_params = [
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'conflict',
                'param_key': 'ETA_FLAVOR',
                'param_value': 1.0,
                'note': '风味冲突权重',
                'phase': 'A'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'conflict',
                'param_key': 'ETA_ROLE',
                'param_value': 1.2,
                'note': '角色冲突权重',
                'phase': 'A'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'conflict',
                'param_key': 'ETA_TYPE',
                'param_value': 0.8,
                'note': '类型冲突权重',
                'phase': 'A'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'conflict',
                'param_key': 'ETA_RATIO',
                'param_value': 0.8,
                'note': '比例冲突权重',
                'phase': 'A'
            }
        ]
        
        # 3. 导入 phaseA 的 synergy 参数
        synergy_params = [
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'synergy',
                'param_key': 'LAMBDA_FLAVOR',
                'param_value': 0.4,
                'note': '风味权重 lambda1',
                'phase': 'A'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'synergy',
                'param_key': 'LAMBDA_COOCCUR',
                'param_value': 0.3,
                'note': '共现权重 lambda2',
                'phase': 'A'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'synergy',
                'param_key': 'LAMBDA_ANCHOR',
                'param_value': 0.3,
                'note': '锚点相似度权重 lambda3',
                'phase': 'A'
            }
        ]
        
        # 4. 导入 phaseA 的整体 SQE 权重
        sqe_params = [
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'sqe',
                'param_key': 'LAMBDA_SYNERGY',
                'param_value': 0.4,
                'note': '协同权重',
                'phase': 'A'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'sqe',
                'param_key': 'LAMBDA_CONFLICT',
                'param_value': 0.3,
                'note': '冲突权重',
                'phase': 'A'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseA_v1',
                'param_group': 'sqe',
                'param_key': 'LAMBDA_BALANCE',
                'param_value': 0.3,
                'note': '平衡权重',
                'phase': 'A'
            }
        ]
        
        # 5. 导入 phaseB 的参数（从 optimal_params.json 中获取）
        phaseB_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "phaseC", "optimal_params.json")
        with open(phaseB_file, 'r', encoding='utf-8') as f:
            phaseB_data = json.load(f)
        
        phaseB_params = [
            # synergy 参数
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'synergy',
                'param_key': 'alpha1',
                'param_value': phaseB_data['synergy']['alpha1'],
                'note': '风味兼容度权重',
                'phase': 'B'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'synergy',
                'param_key': 'alpha2',
                'param_value': phaseB_data['synergy']['alpha2'],
                'note': '共现权重',
                'phase': 'B'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'synergy',
                'param_key': 'alpha3',
                'param_value': phaseB_data['synergy']['alpha3'],
                'note': '锚点相似度权重',
                'phase': 'B'
            },
            # conflict 参数
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'conflict',
                'param_key': 'eta1',
                'param_value': phaseB_data['conflict']['eta1'],
                'note': '风味冲突权重',
                'phase': 'B'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'conflict',
                'param_key': 'eta2',
                'param_value': phaseB_data['conflict']['eta2'],
                'note': '角色冲突权重',
                'phase': 'B'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'conflict',
                'param_key': 'eta3',
                'param_value': phaseB_data['conflict']['eta3'],
                'note': '类型冲突权重',
                'phase': 'B'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'conflict',
                'param_key': 'eta4',
                'param_value': phaseB_data['conflict']['eta4'],
                'note': '比例冲突权重',
                'phase': 'B'
            },
            # balance 参数
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'balance',
                'param_key': 'mu1',
                'param_value': phaseB_data['balance']['mu1'],
                'note': '风味平衡权重',
                'phase': 'B'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'balance',
                'param_key': 'mu2',
                'param_value': phaseB_data['balance']['mu2'],
                'note': '角色平衡权重',
                'phase': 'B'
            },
            # sqe 参数
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'sqe',
                'param_key': 'lambda_synergy',
                'param_value': phaseB_data['sqe']['lambda_synergy'],
                'note': '协同权重',
                'phase': 'B'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'sqe',
                'param_key': 'lambda_conflict',
                'param_value': phaseB_data['sqe']['lambda_conflict'],
                'note': '冲突权重',
                'phase': 'B'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseB_v1',
                'param_group': 'sqe',
                'param_key': 'lambda_balance',
                'param_value': phaseB_data['sqe']['lambda_balance'],
                'note': '平衡权重',
                'phase': 'B'
            }
        ]
        
        # 6. 导入 phaseC 的参数
        phaseC_params = [
            # 模型配置
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'model',
                'param_key': 'HIDDEN_DIM',
                'param_value': 64,
                'note': '隐藏维度',
                'phase': 'C'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'model',
                'param_key': 'DROPOUT',
                'param_value': 0.2,
                'note': 'Dropout 率',
                'phase': 'C'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'model',
                'param_key': 'NUM_LAYERS',
                'param_value': 2,
                'note': 'GINE 层数',
                'phase': 'C'
            },
            # 训练配置
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'training',
                'param_key': 'BATCH_SIZE',
                'param_value': 32,
                'note': '批次大小',
                'phase': 'C'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'training',
                'param_key': 'LEARNING_RATE',
                'param_value': 0.001,
                'note': '学习率',
                'phase': 'C'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'training',
                'param_key': 'EPOCHS',
                'param_value': 5,
                'note': '训练轮数',
                'phase': 'C'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'training',
                'param_key': 'LAMBDA_RES',
                'param_value': 0.01,
                'note': '残差正则化权重',
                'phase': 'C'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'training',
                'param_key': 'LAMBDA_REG',
                'param_value': 0.001,
                'note': '参数正则化权重',
                'phase': 'C'
            },
            # 外层权重
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'sqe',
                'param_key': 'ALPHA',
                'param_value': 0.3521,
                'note': '协同权重',
                'phase': 'C'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'sqe',
                'param_key': 'BETA',
                'param_value': 0.3067,
                'note': '冲突权重',
                'phase': 'C'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'sqe',
                'param_key': 'GAMMA',
                'param_value': 0.3412,
                'note': '平衡权重',
                'phase': 'C'
            },
            # 其他配置
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'other',
                'param_key': 'SEED',
                'param_value': 42,
                'note': '随机种子',
                'phase': 'C'
            },
            {
                'snapshot_id': 's0',
                'param_version': 'phaseC_v1',
                'param_group': 'other',
                'param_key': 'EARLY_STOP',
                'param_value': 20,
                'note': '早停轮数',
                'phase': 'C'
            }
        ]
        
        # 合并所有参数
        all_params = balance_params + conflict_params + synergy_params + sqe_params + phaseB_params + phaseC_params
        
        # 插入参数到数据库
        insert_sql = text("""
        INSERT INTO sqe_param_snapshot (
            snapshot_id, param_version, param_group, param_key, param_value, note, phase
        ) VALUES (
            :snapshot_id, :param_version, :param_group, :param_key, :param_value, :note, :phase
        )
        ON DUPLICATE KEY UPDATE
            param_value = :param_value,
            note = :note,
            phase = :phase
        """)
        
        for param in all_params:
            conn.execute(insert_sql, param)
            print(f"[INFO] 插入/更新参数: {param['param_group']}.{param['param_key']} = {param['param_value']}")
        
        print(f"[INFO] 成功插入/更新 {len(all_params)} 个 SQE 参数")

if __name__ == "__main__":
    print("开始导入 SQE 参数...")
    import_sqe_params()
    print("SQE 参数导入完成！")
