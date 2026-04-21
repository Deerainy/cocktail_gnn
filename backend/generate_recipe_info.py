#!/usr/bin/env python3
"""
脚本：使用LLM为recipe表生成glass、tags、is_alcoholic字段
"""

import os
import json
import django
import requests

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from cocktail.models_recipe import Recipe, RecipeIngredient, Ingredient, RecipeBalanceFeature

# DeepSeek API配置
DEEPSEEK_API_KEY = "sk-ede8258f75cd47aa90248b99bb1c6a6f"  # 请替换为实际的DeepSeek API密钥
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

def get_recipe_data(recipe):
    """获取配方的相关数据"""
    # 获取原料信息
    recipe_ingredients = RecipeIngredient.objects.filter(recipe_id=recipe.recipe_id)
    ingredients = []
    for ri in recipe_ingredients:
        try:
            ingredient = Ingredient.objects.get(ingredient_id=ri.ingredient_id)
            ingredients.append({
                'name': ingredient.name_norm,
                'category': ingredient.category,
                'is_alcoholic': ingredient.is_alcoholic
            })
        except Ingredient.DoesNotExist:
            pass
    
    # 获取balance feature信息
    balance_feature = RecipeBalanceFeature.objects.filter(
        recipe_id=recipe.recipe_id
    ).order_by('-computed_at').first()
    
    balance_data = {}
    if balance_feature:
        balance_data = {
            'family': balance_feature.family,
            'flavor': {
                'sour': float(balance_feature.f_sour),
                'sweet': float(balance_feature.f_sweet),
                'bitter': float(balance_feature.f_bitter),
                'aroma': float(balance_feature.f_aroma),
                'fruity': float(balance_feature.f_fruity),
                'body': float(balance_feature.f_body)
            },
            'role': {
                'base': float(balance_feature.r_base),
                'acid': float(balance_feature.r_acid),
                'sweetener': float(balance_feature.r_sweetener),
                'modifier': float(balance_feature.r_modifier),
                'bitters': float(balance_feature.r_bitters),
                'garnish': float(balance_feature.r_garnish),
                'dilution': float(balance_feature.r_dilution),
                'other': float(balance_feature.r_other)
            }
        }
    
    return {
        'name': recipe.name,
        'instructions': recipe.instructions,
        'ingredients': ingredients,
        'balance_data': balance_data
    }

def generate_recipe_info(recipe_data):
    """使用DeepSeek生成配方信息"""
    prompt = f"""
    请根据以下配方信息，生成规范的glass、tags和is_alcoholic字段内容：
    
    配方名称：{recipe_data['name']}
    
    制作步骤：
    {recipe_data['instructions']}
    
    原料列表：
    {json.dumps(recipe_data['ingredients'], ensure_ascii=False, indent=2)}
    
    风味和角色分布：
    {json.dumps(recipe_data['balance_data'], ensure_ascii=False, indent=2)}
    
    要求：
    1. glass：生成一个适合该配方的酒杯类型，如 coupe、margarita glass、highball 等
    2. tags：生成一个JSON数组，包含多个标签，分为以下几类：
       - 酒精类型（如 spirit、liqueur、wine 等）
       - 风味特征（如 sweet、sour、bitter 等）
       - 适合场合（如 party、casual、formal 等）
       - 其他特征（如 classic、modern、refreshing 等）
    3. is_alcoholic：根据原料和角色分布判断是否含酒精，返回 true 或 false
    
    请以JSON格式返回，键名为 glass、tags、is_alcoholic
    """
    
    print(f"\n=== 调用DeepSeek API ===")
    print(f"配方名称: {recipe_data['name']}")
    print(f"API密钥: {DEEPSEEK_API_KEY[:10]}...")
    print(f"API URL: {DEEPSEEK_API_URL}")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的鸡尾酒配方分析师，擅长根据配方信息生成规范的分类和标签。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    try:
        print("发送请求...")
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        print(f"响应状态码: {response.status_code}")
        
        response_data = response.json()
        print(f"响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        if 'choices' in response_data and response_data['choices']:
            content = response_data['choices'][0]['message']['content']
            print(f"生成内容: {content}")
            # 提取JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
                print(f"提取的JSON: {json_str}")
                result = json.loads(json_str)
                print(f"解析结果: {result}")
                return result
            else:
                print("未找到JSON部分")
        else:
            print("响应中没有choices字段")
    except Exception as e:
        print(f"API调用错误: {e}")
    
    # 如果解析失败，返回默认值
    print("使用默认值")
    return {
        "glass": "cocktail glass",
        "tags": ["other"],
        "is_alcoholic": False
    }

def update_recipe(recipe, generated_info):
    """更新配方信息"""
    recipe.glass = generated_info.get('glass', '')
    recipe.tags = generated_info.get('tags', [])
    recipe.is_alcoholic = generated_info.get('is_alcoholic', False)
    recipe.save()
    return True

def main():
    """主函数"""
    # 获取所有配方
    recipes = Recipe.objects.all()
    total = recipes.count()
    processed = 0
    updated = 0
    
    print(f"Processing {total} recipes...")
    
    for recipe in recipes:
        # 检查是否需要更新
        if not recipe.glass or not recipe.tags or recipe.is_alcoholic is None:
            try:
                # 获取配方数据
                recipe_data = get_recipe_data(recipe)
                
                # 生成配方信息
                generated_info = generate_recipe_info(recipe_data)
                
                # 更新配方
                if update_recipe(recipe, generated_info):
                    updated += 1
                
                processed += 1
                print(f"Processed {processed}/{total} recipes, updated: {updated}")
                
            except Exception as e:
                print(f"Error processing recipe {recipe.recipe_id}: {e}")
        else:
            processed += 1
            print(f"Recipe {recipe.recipe_id} already has complete info, skipping")
    
    print(f"\nCompleted! Processed {processed} recipes, updated {updated}")

if __name__ == "__main__":
    main()