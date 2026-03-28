# -*- coding: utf-8 -*-
"""
检查 ingredient 表的结构
"""

import os
import sys

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_script_dir))
if _root not in sys.path:
    sys.path.insert(0, _root)

# 从 src/db 导入数据库连接函数
from src.db import get_engine

# 数据库引擎
engine = get_engine()

from sqlalchemy import text

# 检查 ingredient 表结构
print("检查 ingredient 表结构...")
with engine.begin() as conn:
    result = conn.execute(text('DESCRIBE ingredient'))
    for row in result:
        print(f"{row[0]}: {row[1]}")

# 检查是否有 canonical 相关的列
print("\n检查是否有 canonical 相关的列...")
with engine.begin() as conn:
    result = conn.execute(text('SELECT * FROM ingredient LIMIT 5'))
    columns = result.keys()
    print(f"列名: {columns}")
    
    # 打印前 5 行数据
    print("\n前 5 行数据:")
    for row in result:
        print(dict(row))
