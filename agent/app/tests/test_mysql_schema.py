#!/usr/bin/env python3
"""
测试 MySQL 数据库表结构
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.db.mysql import get_mysql_connection

def test_mysql_schema():
    """测试 MySQL 数据库表结构"""
    print("开始测试 MySQL 数据库表结构...")
    print("=" * 80)
    
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # 检查 ingredient 表结构
        print("\ningredient 表结构:")
        cursor.execute("DESCRIBE ingredient")
        ingredient_columns = cursor.fetchall()
        for column in ingredient_columns:
            column_name = column[0]
            column_type = column[1]
            is_null = column[2]
            key = column[3]
            default = column[4]
            extra = column[5]
            print(f"  - {column_name} ({column_type}, {is_null}, {key}, {default}, {extra})")
        
        # 检查 recipe 表结构
        print("\nrecipe 表结构:")
        cursor.execute("DESCRIBE recipe")
        recipe_columns = cursor.fetchall()
        for column in recipe_columns:
            column_name = column[0]
            column_type = column[1]
            is_null = column[2]
            key = column[3]
            default = column[4]
            extra = column[5]
            print(f"  - {column_name} ({column_type}, {is_null}, {key}, {default}, {extra})")
        
        # 检查 ingredient_alias 表结构
        print("\ningredient_alias 表结构:")
        cursor.execute("DESCRIBE ingredient_alias")
        alias_columns = cursor.fetchall()
        for column in alias_columns:
            column_name = column[0]
            column_type = column[1]
            is_null = column[2]
            key = column[3]
            default = column[4]
            extra = column[5]
            print(f"  - {column_name} ({column_type}, {is_null}, {key}, {default}, {extra})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"查询失败: {e}")
    
    print("\n" + "=" * 80)
    print("测试完成！")

if __name__ == "__main__":
    test_mysql_schema()
