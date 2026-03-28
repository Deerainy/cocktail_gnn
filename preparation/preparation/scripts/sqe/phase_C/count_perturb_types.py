# -*- coding: utf-8 -*-
"""
统计 pairs_phaseC.csv 文件中的扰动类型数量
"""

import csv
import os

# 数据文件路径
pairs_file = os.path.join('..', '..', '..', 'data', 'phaseC', 'pairs_phaseC.csv')

# 读取文件并收集扰动类型
perturb_types = set()

with open(pairs_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        perturb_type = row.get('perturb_type', 'unknown')
        perturb_types.add(perturb_type)

# 打印结果
print(f"扰动类型数量: {len(perturb_types)}")
print("\n扰动类型列表:")
for perturb_type in sorted(perturb_types):
    print(f"  - {perturb_type}")
