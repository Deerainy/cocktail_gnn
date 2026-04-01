"""
测试 Neo4j 数据库连接和数据
"""

import os
import django

# 配置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from neo4j import GraphDatabase

# 直接硬编码连接信息
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "12345678")

# 连接到 Neo4j 数据库
driver = GraphDatabase.driver(URI, auth=AUTH)

print("连接到 Neo4j 数据库成功！")

# 测试查询食谱数据
with driver.session() as session:
    # 查询所有食谱
    result = session.run("MATCH (r:Recipe) RETURN r LIMIT 10")
    recipes = [record["r"] for record in result]
    
    print(f"找到 {len(recipes)} 个食谱：")
    for i, recipe in enumerate(recipes):
        print(f"食谱 {i+1}: ID={recipe