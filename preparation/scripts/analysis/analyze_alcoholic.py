# -*- coding: utf-8 -*-
"""
分析 recipe 是否含酒精

功能：
1. 从 recipe 表读取所有 recipe
2. 对于每个 recipe，获取其所有 ingredient id
3. 对于每个 ingredient id，查询其在 ingredient_type 表中的 type_tag
4. 判断是否有酒精类型的 ingredient
5. 更新 recipe 表的 is_alcoholic 字段
"""

import os
import sys
from typing import Dict, Any, List

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_scripts_dir = os.path.dirname(_script_dir)  # scripts
_root = os.path.dirname(_scripts_dir)  # 项目根目录
if _root not in sys.path:
    sys.path.insert(0, _root)

# 导入依赖
from sqlalchemy import text

from src.db import get_engine

# =========================
# 配置
# =========================
# 0 表示不限制，处理全部；>0 时最多处理该条数
TOP_N = int(os.getenv("TOP_N", "0"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"

# 酒精类型列表
ALCOHOLIC_TYPES = {
    "liqueur",
    "spirit",
    "bitters",
    "fortified_wine"
}

# =========================
# 数据库操作
# =========================
def get_recipes(limit: int) -> List[Dict[str, Any]]:
    """从 recipe 表读取所有 recipe"""
    engine = get_engine()
    
    sql = text("""
        SELECT recipe_id, name
        FROM recipe
        ORDER BY recipe_id
    """)
    
    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()
    
    out = [dict(r) for r in rows]
    if limit > 0:
        out = out[:limit]
    return out

def get_recipe_ingredients(recipe_id: int) -> List[int]:
    """获取 recipe 的所有 ingredient id"""
    engine = get_engine()
    
    sql = text("""
        SELECT ingredient_id
        FROM recipe_ingredient
        WHERE recipe_id = :recipe_id
    """)
    
    with engine.begin() as conn:
        rows = conn.execute(sql, {"recipe_id": recipe_id}).mappings().all()
    
    return [row["ingredient_id"] for row in rows]

def get_ingredient_type(ingredient_id: int) -> str:
    """获取 ingredient 的 type_tag"""
    engine = get_engine()
    
    sql = text("""
        SELECT type_tag
        FROM ingredient_type
        WHERE ingredient_id = :ingredient_id
    """)
    
    with engine.begin() as conn:
        row = conn.execute(sql, {"ingredient_id": ingredient_id}).fetchone()
    
    return row[0] if row else "other"

def update_recipe_alcoholic(engine, recipe_id: int, is_alcoholic: bool) -> None:
    """更新 recipe 表的 is_alcoholic 字段"""
    sql = text("""
        UPDATE recipe
        SET is_alcoholic = :is_alcoholic
        WHERE recipe_id = :recipe_id
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {"is_alcoholic": 1 if is_alcoholic else 0, "recipe_id": recipe_id})

# =========================
# 分析函数
# =========================
def is_recipe_alcoholic(recipe_id: int) -> bool:
    """判断 recipe 是否含酒精"""
    # 获取 recipe 的所有 ingredient id
    ingredient_ids = get_recipe_ingredients(recipe_id)
    
    # 对于每个 ingredient id，查询其 type_tag
    for ingredient_id in ingredient_ids:
        type_tag = get_ingredient_type(ingredient_id)
        # 如果是酒精类型，返回 True
        if type_tag in ALCOHOLIC_TYPES:
            return True
    
    # 没有酒精类型的 ingredient，返回 False
    return False

# =========================
# 主函数
# =========================
def main():
    """主函数"""
    print("开始分析 recipe 是否含酒精...")
    
    # 获取所有 recipe
    recipes = get_recipes(TOP_N)
    print(f"[INFO] 待分析的 recipe: {len(recipes)} 个")
    
    # 处理每个 recipe
    engine = get_engine()
    alcoholic_count = 0
    non_alcoholic_count = 0
    
    for i, recipe in enumerate(recipes, 1):
        recipe_id = recipe["recipe_id"]
        recipe_name = recipe["name"]
        
        print(f"[INFO] 分析 recipe ({i}/{len(recipes)}): {recipe_name}")
        
        # 判断是否含酒精
        alcoholic = is_recipe_alcoholic(recipe_id)
        
        # 更新数据库
        if not DRY_RUN:
            update_recipe_alcoholic(engine, recipe_id, alcoholic)
        
        # 统计
        if alcoholic:
            alcoholic_count += 1
            print(f"[INFO] 结果: 含酒精")
        else:
            non_alcoholic_count += 1
            print(f"[INFO] 结果: 无酒精")
    
    print(f"[INFO] 分析完成！含酒精的 recipe: {alcoholic_count} 个，无酒精的 recipe: {non_alcoholic_count} 个")

if __name__ == "__main__":
    main()
