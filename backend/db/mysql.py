#!/usr/bin/env python3
"""
MySQL 数据库连接模块

提供 MySQL 数据库连接功能
"""

import pymysql
from pymysql.cursors import DictCursor
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
        MYSQL_HOST = "localhost"
        MYSQL_PORT = 3306
        MYSQL_USER = "root"
        MYSQL_PASSWORD = "123456"
        MYSQL_DATABASE = "cocktail_graph"
    settings = Settings()

def get_mysql_connection():
    """获取 MySQL 数据库连接
    
    Returns:
        pymysql.Connection: MySQL 数据库连接
    """
    try:
        connection = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        return connection
    except Exception as e:
        print(f"连接 MySQL 数据库失败: {str(e)}")
        raise
