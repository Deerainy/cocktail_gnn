#!/usr/bin/env python3
"""
Neo4j 数据库连接模块

提供 Neo4j 图数据库连接功能
"""

from neo4j import GraphDatabase
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入配置
try:
    from agent.app.config import settings
except ImportError:
    print("警告: 无法导入配置，使用默认配置")
    class Settings:
        NEO4J_URI = "bolt://localhost:7687"
        NEO4J_USER = "neo4j"
        NEO4J_PASSWORD = "Lyx040410"
    settings = Settings()

def get_neo4j_driver():
    """获取 Neo4j 数据库驱动
    
    Returns:
        GraphDatabase.driver: Neo4j 数据库驱动
    """
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        return driver
    except Exception as e:
        print(f"连接 Neo4j 数据库失败: {str(e)}")
        raise
