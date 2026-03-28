# -*- coding: utf-8 -*-
"""
批量组合调整处理
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.substitute.combo_adjustment_planner import ComboAdjustmentPlanner
from scripts.substitute.combo_adjustment_database import ComboAdjustmentDatabase

def get_all_recipes() -> List[int]:
    """
    获取所有配方 ID
    """
    from src.db import get_engine
    from sqlalchemy import text
    
    engine = get_engine()
    sql = text("SELECT recipe_id FROM recipe ORDER BY recipe_id")
    
    with engine.begin() as conn:
        result = conn.execute(sql)
        recipes = [row.recipe_id for row in result]
    
    print(f"[INFO] 从数据库获取了 {len(recipes)} 个配方")
    return recipes

def process_recipe(recipe_id: int, db: ComboAdjustmentDatabase):
    """
    处理单个配方
    """
    # 创建计划生成器
    planner = ComboAdjustmentPlanner()
    
    # 获取配方的所有原料
    from scripts.substitute.combo_adjustment_utils import load_recipe_ingredients
    ingredients = load_recipe_ingredients(recipe_id)
    
    # 对每个原料作为目标原料进行处理
    for ingredient in ingredients:
        target_ingredient_id = ingredient['ingredient_id']
        
        # 生成组合调整计划
        plans = planner.generate_plans_for_recipe(recipe_id, target_ingredient_id)
        
        # 候选生成阶段去重
        unique_plans = {}
        for p in plans:
            # 构建唯一键
            key = (
                "phaseD_combo_v1",  # snapshot_id
                p.get('recipe_id', 0),
                # 从 plan 中获取 target_canonical_id 和 candidate_canonical_id
                # 这里需要根据实际的 plan 结构进行调整
                p['step1'].get('target_ingredient_id', 0),
                p['step1'].get('replacement_id', 0),
                p['step2'].get('ingredient_id', 0),
                round(float(p['step2'].get('alpha', 1.0)), 4)
            )
            unique_plans[key] = p
        
        # 去重后的计划列表
        unique_plans_list = list(unique_plans.values())
        
        # 保存计划到数据库
        for plan in unique_plans_list:
            plan_id = db.save_plan(plan)

def main():
    """
    主函数
    """
    print("开始批量处理组合调整...")
    
    # 创建数据库实例
    db = ComboAdjustmentDatabase()
    
    try:
        # 连接数据库
        db.connect()
        
        # 获取所有配方
        recipes = get_all_recipes()
        print(f"[INFO] 共找到 {len(recipes)} 个配方")
        
        # 使用进度条处理每个配方
        with tqdm(total=len(recipes), desc="处理配方", unit="个") as pbar:
            for recipe_id in recipes:
                process_recipe(recipe_id, db)
                pbar.update(1)
                pbar.set_postfix_str(f"当前配方: {recipe_id}")
            
    finally:
        # 断开数据库连接
        db.disconnect()

if __name__ == "__main__":
    main()
