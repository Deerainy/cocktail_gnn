import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from cocktail.models_recipe import Ingredient, LlmCanonicalMap

# 测试查询逻辑
print("=== 测试查询逻辑 ===")
ingredient = Ingredient.objects.filter(ingredient_id='1').first()
print(f"Ingredient: {ingredient.ingredient_id}, name_norm: {ingredient.name_norm}")

# 测试1: 直接查询
print("\n=== 测试1: 直接查询 ===")
mapping = LlmCanonicalMap.objects.filter(src_ingredient_id=1, status='ok').first()
if mapping:
    print(f"找到映射: canonical_id={mapping.canonical_id}, canonical_name={mapping.canonical_name}, canonical_name_zh={mapping.canonical_name_zh}")
else:
    print("未找到映射")

# 测试2: 使用int转换
print("\n=== 测试2: 使用int转换 ===")
try:
    src_ingredient_id = int(ingredient.ingredient_id)
    mapping = LlmCanonicalMap.objects.filter(src_ingredient_id=src_ingredient_id, status='ok').first()
    if mapping:
        print(f"找到映射: canonical_id={mapping.canonical_id}, canonical_name={mapping.canonical_name}, canonical_name_zh={mapping.canonical_name_zh}")
    else:
        print("未找到映射")
except Exception as e:
    print(f"错误: {e}")

# 测试3: 查看所有映射
print("\n=== 测试3: 查看所有映射 ===")
all_mappings = LlmCanonicalMap.objects.filter(status='ok')[:5]
for m in all_mappings:
    print(f"src_ingredient_id={m.src_ingredient_id}, canonical_name_zh={m.canonical_name_zh}")
