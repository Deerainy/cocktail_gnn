import sys
import os
import traceback

# 添加项目根目录到路径
sys.path.insert(0, 'd:/items/cocktail_gnn')

print('Testing generate_recipe_images.py...')

from preparation.scripts.generate_recipe_images import call_llm_for_prompts

# 测试调用LLM函数
recipe_name = "Test Recipe"
recipe_instructions = "Test instructions"
recipe_ingredients = "vodka, tonic water"

print(f"Testing with: name={recipe_name}, instructions={recipe_instructions}, ingredients={recipe_ingredients}")

try:
    result = call_llm_for_prompts(recipe_name, recipe_instructions, recipe_ingredients)
    print("Success!")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Traceback: {traceback.format_exc()}")
