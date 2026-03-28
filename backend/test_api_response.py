import requests
import json

# 测试API响应
response = requests.get('http://127.0.0.1:8000/api/recipes/1/ingredients')
data = response.json()

print("=== API响应 ===")
print(json.dumps(data, ensure_ascii=False, indent=2))

# 检查第一个原料的canonical_name_zh
if data['code'] == 0 and len(data['data']) > 0:
    first_ingredient = data['data'][0]['ingredient']
    print(f"\n=== 第一个原料的中文 ===")
    print(f"canonical_name: {first_ingredient['canonical_name']}")
    print(f"canonical_name_zh: {first_ingredient['canonical_name_zh']}")
    print(f"canonical_name_zh类型: {type(first_ingredient['canonical_name_zh'])}")
