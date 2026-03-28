# -*- coding: utf-8 -*-

import pymysql


def test_simple_connection():
    """简单测试数据库连接"""
    print("Testing simple database connection...")
    try:
        conn = pymysql.connect(
            host="127.0.0.1",
            port=3306,
            user="root",
            password="123456",
            database="cocktail_graph",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        print("Connection successful!")
        
        with conn.cursor() as cursor:
            # 检查recipe表
            cursor.execute("SHOW TABLES LIKE 'recipe'")
            result = cursor.fetchall()
            print(f"Recipe table exists: {len(result) > 0}")
            
            if len(result) > 0:
                # 查看数据
                cursor.execute("SELECT COUNT(*) as count FROM recipe")
                count = cursor.fetchone()
                print(f"Total recipes: {count['count']}")
        
        conn.close()
        print("Connection closed")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_simple_connection()
