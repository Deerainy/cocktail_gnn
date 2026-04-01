# -*- coding: utf-8 -*-

import json
import csv


def read_recipes_from_json(json_path):
    """从JSON文件读取recipe数据"""
    with open(json_path, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
    return recipes


def read_recipes_from_csv(csv_path):
    """从CSV文件读取recipe数据"""
    recipes = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            recipe = {
                'id': int(row['id']),
                'name': row['name'],
                'instructions': row['instructions']
            }
            recipes.append(recipe)
    return recipes


def read_recipes_from_jsonl(jsonl_path):
    """从JSONL文件读取recipe数据"""
    recipes = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                recipe = json.loads(line)
                recipes.append(recipe)
    return recipes


def process_recipes(recipes):
    """处理recipe数据，示例函数"""
    print(f"Found {len(recipes)} recipes")
    
    # 示例：逐个处理每个recipe
    for i, recipe in enumerate(recipes, 1):
        print(f"\nProcessing recipe {i}/{len(recipes)}")
        print(f"ID: {recipe['id']}")
        print(f"Name: {recipe['name']}")
        print(f"Instructions: {recipe['instructions'][:100]}...")
        
        # 这里可以添加生成图片的代码
        # generate_image(recipe['name'], recipe['instructions'])


if __name__ == "__main__":
    # 选择一种读取方式
    # recipes = read_recipes_from_json('data/recipes_export.json')
    # recipes = read_recipes_from_csv('data/recipes_export.csv')
    recipes = read_recipes_from_jsonl('data/recipes_export.jsonl')
    
    process_recipes(recipes)
