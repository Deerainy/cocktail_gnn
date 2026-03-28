# -*- coding: utf-8 -*-
"""
将生成的角色推断结果更新到数据库的 recipe_ingredient 表中
"""

import os
import sys
import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

# 加载环境变量
load_dotenv()

from src.db import get_engine

# 数据库引擎
engine = get_engine()

def update_recipe_ingredient_role(recipe_id, ingredient_id, line_no, role):
    """
    更新 recipe_ingredient.role 字段
    """
    sql = text("""
    UPDATE recipe_ingredient
    SET role = :role
    WHERE recipe_id = :recipe_id
      AND ingredient_id = :ingredient_id
      AND line_no = :line_no
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {
            "role": role,
            "recipe_id": recipe_id,
            "ingredient_id": ingredient_id,
            "line_no": line_no
        })

def batch_update_roles(csv_file):
    """
    批量更新角色
    """
    # 读取 CSV 文件
    df = pd.read_csv(csv_file)
    print(f"读取到 {len(df)} 条记录")
    
    total = len(df)
    success_count = 0
    error_count = 0
    
    for i, row in df.iterrows():
        if i % 100 == 0:
            print(f"更新进度: {i}/{total}")
        
        try:
            recipe_id = int(row['recipe_id'])
            ingredient_id = int(row['ingredient_id'])
            line_no = int(row['line_no'])
            role = row['role_rule']
            
            update_recipe_ingredient_role(recipe_id, ingredient_id, line_no, role)
            success_count += 1
        except Exception as e:
            print(f"更新失败: recipe_id={row.get('recipe_id')}, ingredient_id={row.get('ingredient_id')}, error={e}")
            error_count += 1
    
    print(f"更新完成，成功 {success_count} 条，失败 {error_count} 条")

def main():
    """
    主函数
    """
    # CSV 文件路径
    csv_file = os.path.join(_root, "data", "ingredient_roles.csv")
    
    if not os.path.exists(csv_file):
        print(f"CSV 文件不存在: {csv_file}")
        return
    
    print(f"开始更新数据库，读取文件: {csv_file}")
    batch_update_roles(csv_file)
    print("更新完成！")


if __name__ == "__main__":
    main()
