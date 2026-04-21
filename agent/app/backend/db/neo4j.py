#!/usr/bin/env python3
"""
Neo4j数据库连接模块

用于创建和管理Neo4j数据库连接
"""

from neo4j import GraphDatabase

# 导入配置
from app.config import settings

# Neo4j连接配置
NEO4J_CONFIG = {
    'uri': settings.NEO4J_URI,
    'user': settings.NEO4J_USER,
    'password': settings.NEO4J_PASSWORD
}

# 全局驱动实例
NEO4J_DRIVER = None

def initialize_neo4j_driver():
    """初始化Neo4j驱动
    
    Returns:
        neo4j.GraphDatabase.driver: Neo4j数据库驱动对象
    
    Raises:
        Exception: 数据库连接失败
    """
    global NEO4J_DRIVER
    if NEO4J_DRIVER is None:
        try:
            # 尝试创建Neo4j驱动
            NEO4J_DRIVER = GraphDatabase.driver(
                NEO4J_CONFIG['uri'],
                auth=(NEO4J_CONFIG['user'], NEO4J_CONFIG['password']),
                max_connection_pool_size=5,  # 连接池大小
                connection_acquisition_timeout=30  # 连接获取超时
            )
            # 测试连接
            with NEO4J_DRIVER.session() as session:
                session.run("RETURN 1")
            print("成功连接到Neo4j数据库")
        except Exception as e:
            print(f"Neo4j数据库连接失败: {str(e)}")
            raise
    return NEO4J_DRIVER

def get_neo4j_driver():
    """获取Neo4j数据库驱动
    
    Returns:
        neo4j.GraphDatabase.driver: Neo4j数据库驱动对象
    
    Raises:
        Exception: 数据库连接失败
    """
    return initialize_neo4j_driver()

def close_neo4j_driver():
    """关闭Neo4j驱动
    """
    global NEO4J_DRIVER
    if NEO4J_DRIVER is not None:
        try:
            NEO4J_DRIVER.close()
            print("Neo4j驱动已关闭")
        except Exception as e:
            print(f"关闭Neo4j驱动失败: {e}")
        finally:
            NEO4J_DRIVER = None
