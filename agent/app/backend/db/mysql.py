#!/usr/bin/env python3
"""
MySQL数据库连接模块

用于创建和管理MySQL数据库连接
"""

import mysql.connector
from mysql.connector import errors
from mysql.connector.pooling import MySQLConnectionPool

# 导入配置
from app.config import settings

# 数据库连接配置
DB_CONFIG = {
    'host': settings.MYSQL_HOST,
    'user': settings.MYSQL_USER,
    'password': settings.MYSQL_PASSWORD,
    'database': settings.MYSQL_DATABASE,
    'charset': 'utf8mb4'
}

# 创建连接池
try:
    DB_POOL = MySQLConnectionPool(
        pool_name="mysql_pool",
        pool_size=5,  # 连接池大小
        pool_reset_session=True,
        **DB_CONFIG
    )
    print("MySQL连接池创建成功")
except Exception as e:
    print(f"创建MySQL连接池失败: {e}")
    DB_POOL = None

def get_mysql_connection():
    """获取MySQL数据库连接
    
    Returns:
        mysql.connector.connection.MySQLConnection: MySQL数据库连接对象
    
    Raises:
        mysql.connector.errors.ProgrammingError: 数据库连接失败
    """
    try:
        # 优先使用连接池
        if DB_POOL:
            conn = DB_POOL.get_connection()
            return conn
        else:
            # 回退到直接连接
            conn = mysql.connector.connect(**DB_CONFIG)
            return conn
    except errors.ProgrammingError as e:
        print(f"MySQL数据库连接失败: {str(e)}")
        raise
    except Exception as e:
        print(f"数据库连接异常: {str(e)}")
        raise
