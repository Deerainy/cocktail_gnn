# -*- coding: utf-8 -*-
"""
使用大模型翻译 recipe 表中的 instructions 为中文，填入 instructions_zh 字段

功能：
1. 从 recipe 表读取 instructions，翻译为中文，写入 instructions_zh 字段
2. 保持翻译后的格式美观
"""

import os
import sys
import time
import json
from typing import Dict, Any, List

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_scripts_dir = os.path.dirname(_script_dir)  # scripts
_root = os.path.dirname(_scripts_dir)  # 项目根目录
if _root not in sys.path:
    sys.path.insert(0, _root)

# 导入依赖
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import text

# 加载环境变量
_llm_env = os.path.join(_root, "config", "llm.env")
load_dotenv(_llm_env)

from src.db import get_engine

# =========================
# 配置
# =========================
# 0 表示不限制，处理全部未翻译的；>0 时最多处理该条数
TOP_N = int(os.getenv("TOP_N", "0"))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "0.3"))

# 进度文件路径
PROGRESS_FILE = os.path.join(_root, "data", "translation_progress.json")

# =========================
# 进度管理
# =========================
def save_progress(processed_recipes: List[int]) -> None:
    """保存已处理的 recipe_id 列表到进度文件"""
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    
    # 加载现有进度
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, Exception):
            existing_data = {}
    else:
        existing_data = {}
    
    # 更新进度
    existing_data["processed_instructions"] = processed_recipes
    existing_data["timestamp"] = time.time()
    
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)


def load_progress() -> List[int]:
    """从进度文件加载已处理的 recipe_id 列表"""
    if not os.path.exists(PROGRESS_FILE):
        return []
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("processed_instructions", [])
    except (json.JSONDecodeError, Exception):
        return []

# =========================
# 数据库操作
# =========================
def get_recipes_to_translate(limit: int) -> List[Dict[str, Any]]:
    """从 recipe 表读取尚未翻译 instructions 的记录"""
    engine = get_engine()
    
    # 加载已处理的 ID
    processed_ids = load_progress()
    
    # 构建 SQL 查询，排除已处理的 ID
    if processed_ids:
        sql = text("""
            SELECT recipe_id, name, instructions
            FROM recipe
            WHERE (instructions_zh IS NULL OR TRIM(instructions_zh) = '')
              AND instructions IS NOT NULL
              AND TRIM(instructions) != ''
              AND recipe_id NOT IN :processed_ids
            ORDER BY recipe_id
        """)
        with engine.begin() as conn:
            rows = conn.execute(sql, {"processed_ids": processed_ids}).mappings().all()
    else:
        sql = text("""
            SELECT recipe_id, name, instructions
            FROM recipe
            WHERE (instructions_zh IS NULL OR TRIM(instructions_zh) = '')
              AND instructions IS NOT NULL
              AND TRIM(instructions) != ''
            ORDER BY recipe_id
        """)
        with engine.begin() as conn:
            rows = conn.execute(sql).mappings().all()
    
    out = [dict(r) for r in rows]
    if limit > 0:
        out = out[:limit]
    return out

def get_recipe_ingredients(recipe_id: int) -> List[Dict[str, Any]]:
    """获取指定 recipe 的所有 ingredient"""
    engine = get_engine()
    sql = text("""
        SELECT i.name_norm, ri.amount, ri.unit, ri.role
        FROM recipe_ingredient ri
        JOIN ingredient i ON ri.ingredient_id = i.ingredient_id
        WHERE ri.recipe_id = :recipe_id
        ORDER BY ri.line_no
    """)
    with engine.begin() as conn:
        rows = conn.execute(sql, {"recipe_id": recipe_id}).mappings().all()
    return [dict(r) for r in rows]

def update_recipe_instructions_translation(engine, recipe_id: int, translation: str) -> None:
    """更新 recipe 表的中文翻译"""
    sql = text("""
        UPDATE recipe
        SET instructions_zh = :translation
        WHERE recipe_id = :recipe_id
    """)
    with engine.begin() as conn:
        conn.execute(sql, {"translation": translation, "recipe_id": recipe_id})

# =========================
# 大模型翻译
# =========================
def translate_instructions(client: OpenAI, instructions: str, recipe_name: str = None, ingredients: List[Dict[str, Any]] = None) -> str:
    """翻译 instructions 为中文，结合recipe名字和ingredient智能生成美观的中文制作方法"""
    recipe_text = f"配方名称：{recipe_name}\n" if recipe_name else ""
    
    # 构建原料列表文本
    ingredients_text = ""
    if ingredients:
        ingredients_text = "原料：\n"
        for ing in ingredients:
            amount = ing.get('amount', '')
            unit = ing.get('unit', '')
            name = ing.get('name_norm', '')
            role = ing.get('role', '')
            
            ingredient_line = "- "
            if amount:
                ingredient_line += f"{amount} {unit} " if unit else f"{amount} "
            ingredient_line += name
            if role:
                ingredient_line += f" ({role})"
            ingredient_line += "\n"
            ingredients_text += ingredient_line
        ingredients_text += "\n"
    
    prompt = f"""请将下面的鸡尾酒配方制作说明翻译为中文。

【翻译要求】
1. 准确翻译原文内容，不遗漏、不增补、不改写原意。
2. 保留鸡尾酒调制相关专业术语的准确性；常见术语可译为自然中文，必要时可保留英文原词。
3. 配方名称、人名、地名、酒吧名、专有名词若不适合直译，可保留原文。
4. 原文中的用量、比例、单位、时间、温度、步骤顺序必须完整保留，不得擅自修改。
5. 如果原文包含糖浆、浸泡液、装饰物、预制材料等子标题或说明，请清晰翻译并保留层级关系。
6. 结合配方名称和原料信息，确保翻译更加准确和专业。

【格式要求】
1. 严格保留原文的段落结构、换行、列表、星号、小标题、括号、冒号等格式。
2. 译文整体要清晰、自然、易读，符合中文配方说明的表达习惯。
3. 不要把原本分开的内容合并成一大段。
4. 若原文是分步说明，则译文也保持分步感和层次感。

【输出要求】
1. 只返回中文翻译结果。
2. 不要添加任何解释、注释、前言、总结、说明或多余标记。
3. 不要输出“翻译如下”“中文版本如下”等额外文字。

{recipe_text}{ingredients_text}制作方法：
{instructions}
"""
    
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "你是一个专业的鸡尾酒制作方法翻译专家，能够将英文制作方法翻译成准确、流畅、美观的中文，同时结合配方名称和原料信息进行智能翻译。"},
                {"role": "user", "content": prompt}
            ],
        )
        
        content = resp.choices[0].message.content.strip()
        return content
    except Exception as e:
        print(f"[ERROR] 翻译 instructions 失败: {e}")
        return instructions

# =========================
# 主函数
# =========================
def main():
    """主函数"""
    print("开始翻译 recipe instructions...")
    
    # 获取 API Key
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] 缺少 DEEPSEEK_API_KEY 或 OPENAI_API_KEY")
        return
    
    # 创建 OpenAI 客户端
    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    
    # 加载进度
    processed_recipes = load_progress()
    
    # 获取待翻译的 recipe
    recipes = get_recipes_to_translate(TOP_N)
    print(f"[INFO] 待翻译的 recipe: {len(recipes)} 个")
    
    # 处理 recipes
    engine = get_engine()
    for i, recipe in enumerate(recipes, 1):
        recipe_id = recipe["recipe_id"]
        recipe_name = recipe["name"]
        instructions = recipe["instructions"]
        
        print(f"[INFO] 翻译 recipe ({i}/{len(recipes)}): {recipe_name}")
        
        # 获取原料信息
        ingredients = get_recipe_ingredients(recipe_id)
        print(f"[INFO] 找到 {len(ingredients)} 种原料")
        
        # 翻译
        translation = translate_instructions(client, instructions, recipe_name, ingredients)
        print(f"[INFO] 翻译完成，长度: {len(translation)} 字符")
        
        # 更新数据库
        if not DRY_RUN:
            update_recipe_instructions_translation(engine, recipe_id, translation)
        
        # 记录进度
        processed_recipes.append(recipe_id)
        save_progress(processed_recipes)
        
        # 避免请求过于频繁
        time.sleep(SLEEP_SEC)
    
    print(f"[INFO] 翻译完成！已翻译 {len(processed_recipes)} 个 recipe 的 instructions")

if __name__ == "__main__":
    main()