# -*- coding: utf-8 -*-

import os
import sys
import json
import csv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.db import get_conn


def export_recipes():
    """导出recipe表中的name、instructions和id字段"""
    conn = get_conn()
    try:
        with conn.cursor() as cursor:
            # 先查看recipe表的结构
            cursor.execute("DESCRIBE recipe")
            print("Recipe table structure:")
            for row in cursor.fetchall():
                print(row)
            
            # 查询所有recipe数据
            cursor.execute("SELECT id, name, instructions FROM recipe WHERE instructions IS NOT NULL AND instructions != ''")
            recipes = cursor.fetchall()
            
            print(f"\nFound {len(recipes)} recipes with instructions")
            
            # 导出为JSON文件
            with open('data/recipes_export.json', 'w', encoding='utf-8') as f:
                json.dump(recipes, f, ensure_ascii=False, indent=2)
            print("\nExported to data/recipes_export.json")
            
            # 导出为CSV文件
            with open('data/recipes_export.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'name', 'instructions'])
                for recipe in recipes:
                    writer.writerow([recipe['id'], recipe['name'], recipe['instructions']])
            print("Exported to data/recipes_export.csv")
            
            # 导出为JSONL文件（每行一个JSON对象）
            with open('data/recipes_export.jsonl', 'w', encoding='utf-8') as f:
                for recipe in recipes:
                    json.dump(recipe, f, ensure_ascii=False)
                    f.write('\n')
            print("Exported to data/recipes_export.jsonl")
            
    finally:
        conn.close()


if __name__ == "__main__":
    export_recipes()
