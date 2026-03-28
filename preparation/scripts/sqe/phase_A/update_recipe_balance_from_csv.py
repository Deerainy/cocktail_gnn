# -*- coding: utf-8 -*-
"""
将 CSV 中的平衡分数数据更新到 recipe_balance_feature 表

功能：
1. 读取 sqe_balance_results.csv 文件
2. 将 family 和平衡分数更新到 recipe_balance_feature 表中
"""

import os
import sys
import csv
from typing import Dict

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.db import get_engine
from sqlalchemy import text

# 数据库引擎
engine = get_engine()


def load_csv_data(csv_file: str) -> Dict[int, Dict]:
    """
    从 CSV 文件加载数据
    """
    data = {}
    
    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            recipe_id = int(row["recipe_id"])
            data[recipe_id] = {
                "family": row["family"],
                "flavor_balance_score": float(row["flavor_balance_score"]),
                "role_balance_score": float(row["role_balance_score"]),
                "final_balance_score": float(row["final_balance_score"])
            }
    
    print(f"[INFO] 从 CSV 文件加载了 {len(data)} 条数据")
    return data


def update_database(data: Dict[int, Dict]):
    """
    将数据更新到数据库
    """
    total = len(data)
    success_count = 0
    error_count = 0
    
    for recipe_id, values in data.items():
        try:
            # 构建 SQL 语句
            sql = text("""
            UPDATE recipe_balance_feature
            SET 
                family = :family,
                flavor_balance_score = :flavor_balance_score,
                role_balance_score = :role_balance_score,
                final_balance_score = :final_balance_score
            WHERE recipe_id = :recipe_id
            """)
            
            # 执行更新
            with engine.begin() as conn:
                result = conn.execute(
                    sql,
                    {
                        "recipe_id": recipe_id,
                        "family": values["family"],
                        "flavor_balance_score": values["flavor_balance_score"],
                        "role_balance_score": values["role_balance_score"],
                        "final_balance_score": values["final_balance_score"]
                    }
                )
            
            if result.rowcount > 0:
                success_count += 1
            else:
                error_count += 1
                print(f"[WARN] 未找到 recipe_id = {recipe_id} 的记录")
                
        except Exception as e:
            error_count += 1
            print(f"[ERROR] 更新 recipe_id = {recipe_id} 时出错: {e}")
    
    print(f"\n[INFO] 更新完成: 成功 {success_count}, 失败 {error_count}, 总计 {total}")


def main():
    """
    主函数
    """
    # CSV 文件路径
    csv_file = os.path.join(_root, "data", "sqe_balance_results.csv")
    
    if not os.path.exists(csv_file):
        print(f"[ERROR] CSV 文件不存在: {csv_file}")
        return
    
    # 加载 CSV 数据
    data = load_csv_data(csv_file)
    
    if not data:
        print("[WARN] 没有数据可更新")
        return
    
    # 更新数据库
    update_database(data)


if __name__ == "__main__":
    main()
