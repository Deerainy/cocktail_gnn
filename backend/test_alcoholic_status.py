#!/usr/bin/env python3
"""
测试脚本：根据ingredient_type判断配方是否含有酒精
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from cocktail.models_recipe import Recipe, RecipeIngredient, IngredientType

# 模拟数据
mock_ingredient_types = [
    {'ingredient_id': '1', 'type_tag': 'spirit', 'source': 'rule', 'confidence': 0.9},
    {'ingredient_id': '2', 'type_tag': 'liqueur', 'source': 'rule', 'confidence': 0.95},
    {'ingredient_id': '3', 'type_tag': 'juice', 'source': 'rule', 'confidence': 0.85},
    {'ingredient_id': '4', 'type_tag': 'syrup', 'source': 'rule', 'confidence': 0.8},
    {'ingredient_id': '5', 'type_tag': 'fortified_wine', 'source': 'rule', 'confidence': 0.9},
    {'ingredient_id': '6', 'type_tag': 'bitters', 'source': 'rule', 'confidence': 0.85},
    {'ingredient_id': '7', 'type_tag': 'other', 'source': 'rule', 'confidence': 0.7},
]

def setup_test_data():
    """设置测试数据"""
    print("设置测试数据...")
    
    # 创建IngredientType记录
    for item in mock_ingredient_types:
        ingredient_type, created = IngredientType.objects.get_or_create(
            ingredient_id=item['ingredient_id'],
            defaults={
                'type_tag': item['type_tag'],
                'source': item['source'],
                'confidence': item['confidence']
            }
        )
        if created:
            print(f"创建 IngredientType: {item['ingredient_id']} - {item['type_tag']}")
        else:
            print(f"更新 IngredientType: {item['ingredient_id']} - {item['type_tag']}")

def test_recipe_alcoholic_status():
    """测试配方酒精状态判断"""
    print("\n测试配方酒精状态判断...")
    
    # 定义酒精类型
    alcoholic_types = {'spirit', 'liqueur', 'fortified_wine'}
    
    # 获取所有配方
    recipes = Recipe.objects.all()
    
    if not recipes:
        print("没有找到配方数据")
        return
    
    print(f"找到 {recipes.count()} 个配方")
    
    for recipe in recipes:
        # 获取配方的所有原料
        recipe_ingredients = RecipeIngredient.objects.filter(recipe_id=recipe.recipe_id)
        has_alcohol = False
        
        print(f"\n配方: {recipe.name}")
        print(f"当前 is_alcoholic: {recipe.is_alcoholic}")
        print("原料:")
        
        for ri in recipe_ingredients:
            # 查找原料类型
            try:
                ingredient_type = IngredientType.objects.get(ingredient_id=ri.ingredient_id)
                print(f"  - {ri.ingredient_id}: {ingredient_type.type_tag}")
                if ingredient_type.type_tag in alcoholic_types:
                    has_alcohol = True
            except IngredientType.DoesNotExist:
                print(f"  - {ri.ingredient_id}: 无类型信息")
        
        print(f"判断结果: {has_alcohol}")
        
        # 如果状态发生变化，更新配方
        if recipe.is_alcoholic != has_alcohol:
            recipe.is_alcoholic = has_alcohol
            recipe.save()
            print(f"已更新 is_alcoholic 为: {has_alcohol}")

def main():
    """主函数"""
    try:
        setup_test_data()
        test_recipe_alcoholic_status()
        print("\n测试完成！")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()