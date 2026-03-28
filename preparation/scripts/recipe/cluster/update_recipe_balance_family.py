import csv
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db import get_conn

def update_recipe_balance_family(csv_path: str):
    """
    更新 recipe_balance_feature 表中的 family 字段
    """
    # 家族映射
    family_map = {
        'cluster_0': 'Margarita-like',
        'cluster_1': 'Old Fashioned-like',
        'cluster_2': 'Daiquiri-like',
        'cluster_3': 'Martini-like',
        'cluster_4': 'Sour-like'
    }
    
    # 连接数据库
    conn = get_conn()
    
    try:
        with conn.cursor() as cursor:
            # 读取 CSV 文件
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    recipe_id = row['recipe_id']
                    cluster = row['family']
                    
                    # 获取对应的家族名称
                    family = family_map.get(cluster, cluster)
                    
                    # 更新数据库
                    sql = "UPDATE recipe_balance_feature SET family = %s WHERE recipe_id = %s"
                    cursor.execute(sql, (family, recipe_id))
                    
            # 提交事务
            conn.commit()
            print(f"成功更新了 recipe_balance_feature 表中的 family 字段")
            
    finally:
        conn.close()

if __name__ == "__main__":
    csv_path = "data/phaseA/sqe_balance_results.csv"
    update_recipe_balance_family(csv_path)
