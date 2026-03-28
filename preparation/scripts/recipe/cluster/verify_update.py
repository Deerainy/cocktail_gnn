import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db import get_conn

def verify_update():
    """
    验证 recipe_balance_feature 表中的 family 字段是否已更新
    """
    conn = get_conn()
    
    try:
        with conn.cursor() as cursor:
            # 查询前10条记录
            cursor.execute("SELECT recipe_id, family FROM recipe_balance_feature LIMIT 10")
            print("前10条记录:")
            for row in cursor.fetchall():
                print(row)
            
            # 统计各家族的数量
            cursor.execute("SELECT family, COUNT(*) FROM recipe_balance_feature GROUP BY family")
            print("\n各家族数量:")
            for row in cursor.fetchall():
                print(row)
                
    finally:
        conn.close()

if __name__ == "__main__":
    verify_update()
