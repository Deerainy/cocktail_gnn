import csv
import json
from collections import defaultdict

# 读取llm_cache_canonical.jsonl，构建name_norm到canonical_name的映射
canonical_map = {}
with open('d:\\items\\cocktail_gnn\\preparation\\data\\ingredient\\llm_cache_canonical.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line.strip())
        name_norm = data['name_norm']
        canonical_name = data['canonical_name']
        canonical_map[name_norm] = canonical_name

# 读取ingredient_roles.csv，获取recipe_id、raw_text和用量信息
recipe_ingredients = []
with open('d:\\items\\cocktail_gnn\\preparation\\data\\ingredient\\ingredient_roles.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        recipe_id = row['recipe_id']
        raw_text = row['raw_text']
        # 获取用量信息
        amount = row['amount']
        unit = row['unit']
        amount_value = row['amount_value']
        amount_ratio_all = row['amount_ratio_all']
        amount_rank_all = row['amount_rank_all']
        
        # 将raw_text转换为小写，用于匹配
        raw_text_lower = raw_text.lower()
        
        # 遍历所有name_norm，检查是否出现在raw_text中
        # 为了提高准确性，我们选择最长的匹配
        best_match = None
        max_length = 0
        for name_norm in canonical_map:
            if name_norm in raw_text_lower:
                if len(name_norm) > max_length:
                    max_length = len(name_norm)
                    best_match = name_norm
        
        if best_match:
            # 使用匹配到的name_norm对应的canonical_name
            canonical_name = canonical_map[best_match]
        else:
            # 如果没有匹配到，提取raw_text中的成分名称
            # 例如："1.5 oz Mezcal" -> "Mezcal"
            parts = raw_text.split(' ')
            ingredient_name = ''
            for i, part in enumerate(parts):
                # 如果是数字或单位，跳过
                if part.replace('.', '', 1).isdigit() or part in ['oz', 'ml', 'dash', 'bsp', 'c', 'tbsp', 'count', 'drop']:
                    continue
                # 如果是"top"、"mist"、"float"等前缀，跳过
                if part in ['top', 'mist', 'float', 'splash']:
                    continue
                # 否则，将后面的部分拼接成成分名称
                ingredient_name = ' '.join(parts[i:])
                break
            canonical_name = ingredient_name
        
        # 保存recipe_id、canonical_name和用量信息
        recipe_ingredients.append({
            'recipe_id': recipe_id,
            'canonical_name': canonical_name,
            'amount': amount,
            'unit': unit,
            'amount_value': amount_value,
            'amount_ratio_all': amount_ratio_all,
            'amount_rank_all': amount_rank_all
        })

# 生成输出csv
output_file = 'd:\\items\\cocktail_gnn\\preparation\\data\\ingredient\\recipe_canonical.csv'
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    # 添加用量相关的列名
    writer.writerow([
        'recipe_id', 'canonical_name', 'amount', 'unit', 
        'amount_value', 'amount_ratio_all', 'amount_rank_all'
    ])
    
    for item in recipe_ingredients:
        writer.writerow([
            item['recipe_id'],
            item['canonical_name'],
            item['amount'],
            item['unit'],
            item['amount_value'],
            item['amount_ratio_all'],
            item['amount_rank_all']
        ])

print(f"Output file generated: {output_file}")