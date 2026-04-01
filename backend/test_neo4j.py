"""
测试 Neo4j 数据库连接和数据
"""

import os
import django

# 配置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from neo4j import GraphDatabase
from django.conf import settings

# 连接到 Neo4j 数据库
driver = GraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
)

print("连接到 Neo4j 数据库成功！")

# 测试查询食谱数据
with driver.session() as session:
    # 查询所有食谱
    result = session.run("MATCH (r:Recipe) RETURN r LIMIT 10")
    recipes = [record["r"] for record in result]
    
    print(f"找到 {len(recipes)} 个食谱：")
    for i, recipe in enumerate(recipes):
        print(f"食谱 {i+1}: ID={recipe.get('id')}, 名称={recipe.get('name')}")
    
    # 测试特定 ID 的食谱
    recipe_id = "1"
    result = session.run("MATCH (r:Recipe {id: $id}) RETURN r", id=recipe_id)
    recipe = result.single()
    
    if recipe:
        print(f"\n找到 ID 为 {recipe_id} 的食谱：")
        print(f"ID: {recipe['r'].get('id')}")
        print(f"名称: {recipe['r'].get('name')}")
    else:
        print(f"\n未找到 ID 为 {recipe_id} 的食谱")

# 关闭连接
driver.close()
print("\n测试完成，连接已关闭")
