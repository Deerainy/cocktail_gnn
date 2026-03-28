# -*- coding: utf-8 -*-
"""
组合调整数据库入库

功能：
1. 将组合调整方案存入数据库
2. 插入 recipe_combo_adjust_result 表
3. 插入 recipe_combo_adjust_step 表
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Optional
from sqlalchemy import text

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.db import get_engine

class ComboAdjustmentDatabase:
    """
    组合调整数据库操作类
    """
    
    def __init__(self):
        """
        初始化数据库连接
        """
        self.engine = None
    
    def connect(self):
        """
        连接数据库
        """
        try:
            self.engine = get_engine()
            print("[INFO] 数据库连接成功")
        except Exception as e:
            print(f"[ERROR] 数据库连接失败: {e}")
    
    def disconnect(self):
        """
        断开数据库连接
        """
        if self.engine:
            self.engine.dispose()
            print("[INFO] 数据库连接已断开")
    
    def insert_combo_adjust_result(self, plan: Dict) -> Optional[int]:
        """
        插入组合调整结果到 recipe_combo_adjust_result 表
        
        参数:
        plan: 组合调整计划
        
        返回:
        plan_id: 插入的计划 ID
        """
        if not self.engine:
            self.connect()
        
        if not self.engine:
            print("[ERROR] 数据库连接失败，跳过入库")
            return None
        
        try:
            # 准备参数
            snapshot_id = "phaseD_combo_v1"
            recipe_id = plan.get('recipe_id', 0)
            
            # 获取 target_canonical_id
            target_ingredient_id = plan['step1']['target_ingredient_id']
            target_canonical_id = self._get_canonical_id(target_ingredient_id)
            
            # 获取 candidate_canonical_id
            candidate_ingredient_id = plan['step1']['replacement_id']
            candidate_canonical_id = self._get_canonical_id(candidate_ingredient_id)
            
            # 获取 repair_ingredient_id
            repair_ingredient_id = plan['step2']['ingredient_id']
            repair_canonical_id = self._get_canonical_id(repair_ingredient_id)
            
            # 获取 repair_role
            repair_role = self._get_ingredient_role(repair_ingredient_id)
            
            # 检查必要字段是否为空
            if target_canonical_id is None or candidate_canonical_id is None:
                print("[ERROR] 缺少必要的 canonical_id，跳过入库")
                return None
            
            # 其他参数
            repair_factor = plan['step2']['alpha']
            old_sqe_total = plan['original_score']
            single_sqe_total = plan['single_score']
            combo_sqe_total = plan['combo_score']
            delta_sqe_single = plan['single_delta_sqe']
            delta_sqe_combo = plan['final_delta_sqe']
            
            # 获取各维度的变化量
            delta_synergy_combo = plan['details'].get('delta_synergy', 0)
            delta_conflict_combo = plan['details'].get('delta_conflict', 0)
            delta_balance_combo = plan['details'].get('delta_balance', 0)
            
            accept_flag = 1 if plan['accept'] else 0
            
            # 计算 rank_no：同目标原料下，按 delta_sqe_combo 降序排序
            rank_no_sql = text("""
            SELECT COUNT(*) + 1 as rank_no
            FROM recipe_combo_adjust_result
            WHERE snapshot_id = :snapshot_id
              AND recipe_id = :recipe_id
              AND target_canonical_id = :target_canonical_id
              AND delta_sqe_combo > :delta_sqe_combo
            """)
            
            with self.engine.connect() as conn:
                rank_result = conn.execute(rank_no_sql, {
                    'snapshot_id': snapshot_id,
                    'recipe_id': recipe_id,
                    'target_canonical_id': target_canonical_id,
                    'delta_sqe_combo': delta_sqe_combo
                }).fetchone()
                rank_no = rank_result[0] if rank_result else 1
            
            reason_code = "ACCEPT" if plan['accept'] else "REJECT"
            explanation = f"组合调整方案: {plan['step1']['target_ingredient']} -> {plan['step1']['replacement']}, 调整 {plan['step2']['ingredient']} × {plan['step2']['alpha']}"
            plan_json = json.dumps(plan, ensure_ascii=False)
            model_version = "phaseD_combo_v1"
            
            # 准备 SQL 语句
            sql = text("""
            INSERT INTO recipe_combo_adjust_result (
                snapshot_id, recipe_id, target_canonical_id, candidate_canonical_id,
                repair_ingredient_id, repair_canonical_id, repair_role, repair_factor,
                old_sqe_total, single_sqe_total, combo_sqe_total,
                delta_sqe_single, delta_sqe_combo, delta_synergy_combo, delta_conflict_combo, delta_balance_combo,
                accept_flag, rank_no, reason_code, explanation, plan_json, model_version
            ) VALUES (
                :snapshot_id, :recipe_id, :target_canonical_id, :candidate_canonical_id,
                :repair_ingredient_id, :repair_canonical_id, :repair_role, :repair_factor,
                :old_sqe_total, :single_sqe_total, :combo_sqe_total,
                :delta_sqe_single, :delta_sqe_combo, :delta_synergy_combo, :delta_conflict_combo, :delta_balance_combo,
                :accept_flag, :rank_no, :reason_code, :explanation, :plan_json, :model_version
            )
            """)
            
            # 执行 SQL
            params = {
                'snapshot_id': snapshot_id,
                'recipe_id': recipe_id,
                'target_canonical_id': target_canonical_id,
                'candidate_canonical_id': candidate_canonical_id,
                'repair_ingredient_id': repair_ingredient_id,
                'repair_canonical_id': repair_canonical_id,
                'repair_role': repair_role,
                'repair_factor': repair_factor,
                'old_sqe_total': old_sqe_total,
                'single_sqe_total': single_sqe_total,
                'combo_sqe_total': combo_sqe_total,
                'delta_sqe_single': delta_sqe_single,
                'delta_sqe_combo': delta_sqe_combo,
                'delta_synergy_combo': delta_synergy_combo,
                'delta_conflict_combo': delta_conflict_combo,
                'delta_balance_combo': delta_balance_combo,
                'accept_flag': accept_flag,
                'rank_no': rank_no,
                'reason_code': reason_code,
                'explanation': explanation,
                'plan_json': plan_json,
                'model_version': model_version
            }
            
            # 插入前先查重
            check_sql = text("""
            SELECT 1
            FROM recipe_combo_adjust_result
            WHERE snapshot_id = :snapshot_id
              AND recipe_id = :recipe_id
              AND target_canonical_id = :target_canonical_id
              AND candidate_canonical_id = :candidate_canonical_id
              AND repair_ingredient_id = :repair_ingredient_id
              AND repair_factor = :repair_factor
            LIMIT 1
            """)
            
            with self.engine.begin() as conn:
                exists = conn.execute(check_sql, params).fetchone()
                if not exists:
                    result = conn.execute(sql, params)
                    # 获取插入的 plan_id
                    plan_id = conn.execute(text("SELECT LAST_INSERT_ID()")).scalar()
                    print(f"[INFO] 插入组合调整结果成功，plan_id: {plan_id}")
                else:
                    print("[INFO] 组合调整方案已存在，跳过插入")
                    plan_id = None
            
            return plan_id
            
        except Exception as e:
            print(f"[ERROR] 插入组合调整结果失败: {e}")
            return None
    
    def insert_combo_adjust_steps(self, plan_id: int, plan: Dict):
        """
        插入组合调整步骤到 recipe_combo_adjust_step 表
        
        参数:
        plan_id: 组合调整计划 ID
        plan: 组合调整计划
        """
        if not self.engine:
            self.connect()
        
        if not self.engine:
            print("[ERROR] 数据库连接失败，跳过入库")
            return
        
        try:
            # 步骤 1: replace
            step1_sql = text("""
            INSERT INTO recipe_combo_adjust_step (
                plan_id, step_no, op_type, target_ingredient_id, target_canonical_id,
                candidate_ingredient_id, candidate_canonical_id, amount_factor, role_info,
                before_sqe_total, after_sqe_total, delta_sqe, note
            ) VALUES (
                :plan_id, :step_no, :op_type, :target_ingredient_id, :target_canonical_id,
                :candidate_ingredient_id, :candidate_canonical_id, :amount_factor, :role_info,
                :before_sqe_total, :after_sqe_total, :delta_sqe, :note
            )
            """)
            
            target_ingredient_id = plan['step1']['target_ingredient_id']
            target_canonical_id = self._get_canonical_id(target_ingredient_id)
            candidate_ingredient_id = plan['step1']['replacement_id']
            candidate_canonical_id = self._get_canonical_id(candidate_ingredient_id)
            
            step1_params = {
                'plan_id': plan_id,
                'step_no': 1,
                'op_type': 'replace',
                'target_ingredient_id': target_ingredient_id,
                'target_canonical_id': target_canonical_id,
                'candidate_ingredient_id': candidate_ingredient_id,
                'candidate_canonical_id': candidate_canonical_id,
                'amount_factor': None,
                'role_info': None,
                'before_sqe_total': plan['original_score'],
                'after_sqe_total': plan['single_score'],
                'delta_sqe': plan['single_delta_sqe'],
                'note': f"Step 1: {plan['step1']['target_ingredient']} -> {plan['step1']['replacement']}"
            }
            
            # 步骤 2: adjust_amount
            step2_sql = text("""
            INSERT INTO recipe_combo_adjust_step (
                plan_id, step_no, op_type, target_ingredient_id, target_canonical_id,
                candidate_ingredient_id, candidate_canonical_id, amount_factor, role_info,
                before_sqe_total, after_sqe_total, delta_sqe, note
            ) VALUES (
                :plan_id, :step_no, :op_type, :target_ingredient_id, :target_canonical_id,
                :candidate_ingredient_id, :candidate_canonical_id, :amount_factor, :role_info,
                :before_sqe_total, :after_sqe_total, :delta_sqe, :note
            )
            """)
            
            repair_ingredient_id = plan['step2']['ingredient_id']
            repair_canonical_id = self._get_canonical_id(repair_ingredient_id)
            repair_role = self._get_ingredient_role(repair_ingredient_id)
            
            step2_params = {
                'plan_id': plan_id,
                'step_no': 2,
                'op_type': 'adjust_amount',
                'target_ingredient_id': repair_ingredient_id,
                'target_canonical_id': repair_canonical_id,
                'candidate_ingredient_id': None,
                'candidate_canonical_id': None,
                'amount_factor': plan['step2']['alpha'],
                'role_info': repair_role,
                'before_sqe_total': plan['single_score'],
                'after_sqe_total': plan['combo_score'],
                'delta_sqe': plan['final_delta_sqe'] - plan['single_delta_sqe'],
                'note': f"Step 2: {plan['step2']['ingredient']} amount × {plan['step2']['alpha']}"
            }
            
            with self.engine.begin() as conn:
                conn.execute(step1_sql, step1_params)
                conn.execute(step2_sql, step2_params)
                print(f"[INFO] 插入组合调整步骤成功，plan_id: {plan_id}")
            
        except Exception as e:
            print(f"[ERROR] 插入组合调整步骤失败: {e}")
    
    def _get_canonical_id(self, ingredient_id: int) -> Optional[int]:
        """
        获取原料的 canonical_id
        
        参数:
        ingredient_id: 原料 ID
        
        返回:
        canonical_id: 原料的 canonical_id
        """
        try:
            if not self.engine:
                self.connect()
            
            if not self.engine:
                return None
            
            # 尝试从 llm_canonical_map 表获取 canonical_id，使用 src_ingredient_id 作为查询条件
            sql = text("SELECT canonical_id FROM llm_canonical_map WHERE src_ingredient_id = :ingredient_id LIMIT 1")
            with self.engine.connect() as conn:
                result = conn.execute(sql, {'ingredient_id': ingredient_id}).fetchone()
                if result:
                    return result[0]
            
            # 如果 llm_canonical_map 表没有，返回 ingredient_id 作为 canonical_id
            return ingredient_id
        except Exception as e:
            print(f"[ERROR] 获取 canonical_id 失败: {e}")
            # 出错时返回 ingredient_id 作为 canonical_id
            return ingredient_id
    
    def _get_ingredient_role(self, ingredient_id: int) -> Optional[str]:
        """
        获取原料的角色
        
        参数:
        ingredient_id: 原料 ID
        
        返回:
        role: 原料的角色
        """
        try:
            if not self.engine:
                self.connect()
            
            if not self.engine:
                return None
            
            # 尝试从 recipe_ingredient 表获取 role
            sql = text("SELECT role FROM recipe_ingredient WHERE ingredient_id = :ingredient_id LIMIT 1")
            with self.engine.connect() as conn:
                result = conn.execute(sql, {'ingredient_id': ingredient_id}).fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"[ERROR] 获取原料角色失败: {e}")
            return None
    
    def save_plan(self, plan: Dict) -> Optional[int]:
        """
        保存组合调整计划到数据库
        
        参数:
        plan: 组合调整计划
        
        返回:
        plan_id: 保存的计划 ID
        """
        # 插入组合调整结果
        plan_id = self.insert_combo_adjust_result(plan)
        
        if plan_id:
            # 插入组合调整步骤
            self.insert_combo_adjust_steps(plan_id, plan)
        
        return plan_id

def main():
    """
    主函数
    """
    print("开始测试组合调整数据库入库...")
    
    # 加载示例计划
    plan_file = os.path.join(str(Path(__file__).resolve().parents[2]), "data", "substitute", "combo_adjustment_plan.json")
    with open(plan_file, 'r', encoding='utf-8') as f:
        plans = json.load(f)
    
    if not plans:
        print("[ERROR] 未找到组合调整计划")
        return
    
    plan = plans[0]
    # 添加 recipe_id
    plan['recipe_id'] = 1
    
    # 创建数据库实例
    db = ComboAdjustmentDatabase()
    
    try:
        # 连接数据库
        db.connect()
        
        # 保存计划
        plan_id = db.save_plan(plan)
        
        if plan_id:
            print(f"[INFO] 组合调整计划保存成功，plan_id: {plan_id}")
        else:
            print("[ERROR] 组合调整计划保存失败")
            
    finally:
        # 断开数据库连接
        db.disconnect()

if __name__ == "__main__":
    main()
