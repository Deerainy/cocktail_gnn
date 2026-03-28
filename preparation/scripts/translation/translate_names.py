# -*- coding: utf-8 -*-
"""
使用大模型翻译 recipe name 和 canonical name 为中文

功能：
1. 从 recipe 表读取 recipe name，翻译为中文，写入 recipe_name_zh 字段
2. 从 llm_canonical_map 表读取 canonical name，翻译为中文，写入 canonical_name_zh 字段
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
def save_progress(processed_recipes: List[int], processed_canonicals: List[int]) -> None:
    """保存已处理的 recipe_id 和 canonical_id 列表到进度文件"""
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "processed_recipes": processed_recipes,
            "processed_canonicals": processed_canonicals,
            "timestamp": time.time()
        }, f, ensure_ascii=False, indent=2)


def load_progress() -> Dict[str, List[int]]:
    """从进度文件加载已处理的 recipe_id 和 canonical_id 列表"""
    if not os.path.exists(PROGRESS_FILE):
        return {"processed_recipes": [], "processed_canonicals": []}
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "processed_recipes": data.get("processed_recipes", []),
                "processed_canonicals": data.get("processed_canonicals", [])
            }
    except (json.JSONDecodeError, Exception):
        return {"processed_recipes": [], "processed_canonicals": []}

# =========================
# 数据库操作
# =========================
def get_recipes_to_translate(limit: int) -> List[Dict[str, Any]]:
    """从 recipe 表读取尚未翻译的记录"""
    engine = get_engine()
    
    # 加载已处理的 ID
    progress = load_progress()
    processed_ids = progress["processed_recipes"]
    
    # 构建 SQL 查询，排除已处理的 ID
    if processed_ids:
        sql = text("""
            SELECT recipe_id, name, instructions
            FROM recipe
            WHERE recipe_name_zh IS NULL OR TRIM(recipe_name_zh) = ''
              AND recipe_id NOT IN :processed_ids
            ORDER BY recipe_id
        """)
        with engine.begin() as conn:
            rows = conn.execute(sql, {"processed_ids": processed_ids}).mappings().all()
    else:
        sql = text("""
            SELECT recipe_id, name, instructions
            FROM recipe
            WHERE recipe_name_zh IS NULL OR TRIM(recipe_name_zh) = ''
            ORDER BY recipe_id
        """)
        with engine.begin() as conn:
            rows = conn.execute(sql).mappings().all()
    
    out = [dict(r) for r in rows]
    if limit > 0:
        out = out[:limit]
    return out

def get_canonicals_to_translate(limit: int) -> List[Dict[str, Any]]:
    """从 llm_canonical_map 表读取尚未翻译的记录"""
    engine = get_engine()
    
    # 加载已处理的 ID
    progress = load_progress()
    processed_ids = progress["processed_canonicals"]
    
    # 构建 SQL 查询，排除已处理的 ID
    if processed_ids:
        sql = text("""
            SELECT canonical_id, canonical_name
            FROM llm_canonical_map
            WHERE canonical_name_zh IS NULL OR TRIM(canonical_name_zh) = ''
              AND canonical_id NOT IN :processed_ids
            ORDER BY canonical_id
        """)
        with engine.begin() as conn:
            rows = conn.execute(sql, {"processed_ids": processed_ids}).mappings().all()
    else:
        sql = text("""
            SELECT canonical_id, canonical_name
            FROM llm_canonical_map
            WHERE canonical_name_zh IS NULL OR TRIM(canonical_name_zh) = ''
            ORDER BY canonical_id
        """)
        with engine.begin() as conn:
            rows = conn.execute(sql).mappings().all()
    
    out = [dict(r) for r in rows]
    if limit > 0:
        out = out[:limit]
    return out

def update_recipe_translation(engine, recipe_id: int, translation: str) -> None:
    """更新 recipe 表的中文翻译"""
    sql = text("""
        UPDATE recipe
        SET recipe_name_zh = :translation
        WHERE recipe_id = :recipe_id
    """)
    with engine.begin() as conn:
        conn.execute(sql, {"translation": translation, "recipe_id": recipe_id})

def update_canonical_translation(engine, canonical_id: int, translation: str) -> None:
    """更新 llm_canonical_map 表的中文翻译"""
    sql = text("""
        UPDATE llm_canonical_map
        SET canonical_name_zh = :translation
        WHERE canonical_id = :canonical_id
    """)
    with engine.begin() as conn:
        conn.execute(sql, {"translation": translation, "canonical_id": canonical_id})

# =========================
# 大模型翻译
# =========================
def translate_recipe_name(client: OpenAI, recipe_name: str, instructions: str = None) -> str:
    """翻译 recipe name 为中文"""
    instructions_text = """
制作方法：
{instructions}
"""
    if instructions and instructions.strip():
        instructions_text = instructions_text.format(instructions=instructions)
    else:
        instructions_text = ""
    
    prompt = f"""请将以下鸡尾酒配方名称翻译成中文，要求：

1. 翻译要准确，保留原有的专业术语
2. 翻译要好听，符合中文表达习惯
3. 翻译要简洁，不要冗长
4. 请参考制作方法来理解配方的特点，以便翻译更加准确
5. 请只返回翻译结果，不要返回任何其他文字或解释

配方名称：{recipe_name}
{instructions_text}
"""
    
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "你是一个专业的鸡尾酒配方名称翻译专家，能够将英文鸡尾酒配方名称翻译成优美、准确的中文。"},
                {"role": "user", "content": prompt}
            ],
        )
        
        content = resp.choices[0].message.content.strip()
        return content
    except Exception as e:
        print(f"[ERROR] 翻译 recipe name 失败: {e}")
        return recipe_name

def translate_canonical_name(client: OpenAI, canonical_name: str) -> str:
    """翻译 canonical name 为中文"""
    prompt = f"""请将以下鸡尾酒原料名称翻译成中文，要求：

1. 翻译要准确，保留原有的专业术语
2. 翻译要符合中文表达习惯
3. 翻译要简洁，不要冗长
4. 翻译时请记住，这是鸡尾酒的原料名称
5. 请只返回翻译结果，不要返回任何其他文字或解释

原料名称：{canonical_name}
"""
    
    try:
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "你是一个专业的鸡尾酒原料名称翻译专家，能够将英文鸡尾酒原料名称翻译成准确、规范的中文。"},
                {"role": "user", "content": prompt}
            ],
        )
        
        content = resp.choices[0].message.content.strip()
        return content
    except Exception as e:
        print(f"[ERROR] 翻译 canonical name 失败: {e}")
        return canonical_name

# =========================
# 主函数
# =========================
def main():
    """主函数"""
    print("开始翻译 recipe name 和 canonical name...")
    
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
    progress = load_progress()
    processed_recipes = progress["processed_recipes"]
    processed_canonicals = progress["processed_canonicals"]
    
    # 获取待翻译的 recipe
    recipes = get_recipes_to_translate(TOP_N)
    print(f"[INFO] 待翻译的 recipe: {len(recipes)} 个")
    
    # 获取待翻译的 canonical
    canonicals = get_canonicals_to_translate(TOP_N)
    print(f"[INFO] 待翻译的 canonical: {len(canonicals)} 个")
    
    # 处理 recipes
    engine = get_engine()
    for i, recipe in enumerate(recipes, 1):
        recipe_id = recipe["recipe_id"]
        recipe_name = recipe["name"]
        
        print(f"[INFO] 翻译 recipe ({i}/{len(recipes)}): {recipe_name}")
        
        # 翻译
        translation = translate_recipe_name(client, recipe_name, recipe.get('instructions'))
        print(f"[INFO] 翻译结果: {translation}")
        
        # 更新数据库
        if not DRY_RUN:
            update_recipe_translation(engine, recipe_id, translation)
        
        # 记录进度
        processed_recipes.append(recipe_id)
        save_progress(processed_recipes, processed_canonicals)
        
        # 避免请求过于频繁
        time.sleep(SLEEP_SEC)
    
    # 处理 canonicals
    for i, canonical in enumerate(canonicals, 1):
        canonical_id = canonical["canonical_id"]
        canonical_name = canonical["canonical_name"]
        
        print(f"[INFO] 翻译 canonical ({i}/{len(canonicals)}): {canonical_name}")
        
        # 翻译
        translation = translate_canonical_name(client, canonical_name)
        print(f"[INFO] 翻译结果: {translation}")
        
        # 更新数据库
        if not DRY_RUN:
            update_canonical_translation(engine, canonical_id, translation)
        
        # 记录进度
        processed_canonicals.append(canonical_id)
        save_progress(processed_recipes, processed_canonicals)
        
        # 避免请求过于频繁
        time.sleep(SLEEP_SEC)
    
    print(f"[INFO] 翻译完成！已翻译 {len(processed_recipes)} 个 recipe 和 {len(processed_canonicals)} 个 canonical")

if __name__ == "__main__":
    main()
