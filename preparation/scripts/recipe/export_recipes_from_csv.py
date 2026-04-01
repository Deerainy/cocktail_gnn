# -*- coding: utf-8 -*-

import json
import csv
import os


def export_recipes_from_csv():
    """从hotaling_cocktails.csv导出recipe数据"""
    csv_path = 'data/ingredient/hotaling_cocktails.csv'
    
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return
    
    recipes = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            recipe = {
                'id': idx,
                'name': row.get('Cocktail Name', ''),
                'instructions': row.get('Preparation', '')
            }
            # 过滤掉空的做法
            if recipe['instructions']:
                recipes.append(recipe)
    
    print(f"Found {len(recipes)} recipes with instructions")
    
    # 确保data目录存在
    os.makedirs('data', exist_ok=True)
    
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


if __name__ == "__main__":
    export_recipes_from_csv()
