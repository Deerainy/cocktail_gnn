# -*- coding: utf-8 -*-

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import get_conn

def test_db_connection():
    """测试数据库连接和recipe表"""
    print("Testing database connection...")
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            # 测试连接
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"Connection test: {result}")
            
            # 检查recipe表是否存在
            cursor.execute("SHOW TABLES LIKE 'recipe'")
            tables = cursor.fetchall()
            if tables:
                print("Recipe table exists")
                
                # 检查表结构
                cursor.execute("DESCRIBE recipe")
                print("\nRecipe table structure:")
                for row in cursor.fetchall():
                    print(row)
                
                # 检查数据量
                cursor.execute("SELECT COUNT(*) as count FROM recipe")
                count = cursor.fetchone()
                print(f"\nTotal recipes: {count['count']}")
                
                # 检查有instructions的记录
                cursor.execute("SELECT COUNT(*) as count FROM recipe WHERE instructions IS NOT NULL AND instructions != ''")
                count_with_instructions = cursor.fetchone()
                print(f"Recipes with instructions: {count_with_instructions['count']}")
                
                # 查看前5条记录
                cursor.execute("SELECT id, name, instructions FROM recipe WHERE instructions IS NOT NULL AND instructions != '' LIMIT 5")
                print("\nSample recipes:")
                for row in cursor.fetchall():
                    print(f"ID: {row['id']}, Name: {row['name']}")
                    print(f"Instructions: {row['instructions'][:100]}...")
                    print("---")
            else:
                print("Recipe table does not exist")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_db_connection()
