# -*- coding: utf-8 -*-
"""
从 recipe_ingredient.raw_text 中提取 amount 和 unit，并更新回数据库

使用 LLM 来分析原始文本，提取用量和单位
"""

import os
import sys
import json
import time
import re
from typing import Dict, Any, List, Optional

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import text

# 加载环境变量
_llm_env = os.path.join(_root, "config", "llm.env")
load_dotenv(_llm_env)

from src.db import get_engine

# 数据库引擎
engine = get_engine()

# 配置
LLM_VERSION = "deepseek_amount_unit_extraction_v1"
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "0.3"))
MIN_LENGTH = 3  # 最小 raw_text 长度

# 系统提示
PROMPT_SYSTEM = """
You are extracting amount and unit from cocktail ingredient raw text.

Task:
Given a raw text string representing a cocktail ingredient, extract:
1. amount: the numerical value (as a float)
2. unit: the measurement unit (e.g., oz, ml, dash, tsp, tbsp, cup, etc.)
3. confidence: your confidence in the extraction (0.0-1.0)

Rules:
1. Extract only the amount and unit, not the ingredient name.
2. If no amount or unit is found, return null for that field.
3. Handle fractional amounts (e.g., "1/2", "½") and ranges (e.g., "1-2").
4. Be precise with units - use standard abbreviations when possible.
5. Return JSON only.
"""

# 用户提示模板
USER_TEMPLATE = """
Extract amount and unit from this raw text:

raw_text: {raw_text_json}

Return JSON only in this format:
{{
  "amount": 1.5,
  "unit": "oz",
  "confidence": 0.95
}}
"""

def extract_with_regex(raw_text: str) -> Dict[str, Any]:
    """
    使用正则表达式提取 amount 和 unit
    """
    # 常见的单位
    units = [
        "oz", "ml", "dash", "tsp", "tbsp", "cup", "glass", "shot", 
        "liter", "l", "cl", "ml", "drop", "drops", "pinch", "pinches",
        "leaf", "leaves", "slice", "slices", "piece", "pieces"
    ]
    
    # 构建单位正则表达式
    unit_pattern = "|" .join([re.escape(unit) for unit in units])
    
    # 匹配数字 + 单位的模式
    pattern = rf"(?P<amount>\d+(?:\.\d+)?|-?\d+(?:-\d+)?|\.\d+)\s*(?P<unit>{unit_pattern})"
    
    match = re.search(pattern, raw_text, re.IGNORECASE)
    
    if match:
        amount_str = match.group("amount")
        unit = match.group("unit").strip().lower()
        
        # 处理范围，如 "6-7"
        if "-" in amount_str:
            try:
                start, end = amount_str.split("-")
                amount = (float(start) + float(end)) / 2
            except:
                amount = None
        else:
            try:
                amount = float(amount_str)
            except:
                amount = None
        
        return {
            "amount": amount,
            "unit": unit,
            "confidence": 0.95
        }
    
    # 特殊情况：如 "top Tonic"
    if "top" in raw_text.lower():
        return {
            "amount": None,
            "unit": "top",
            "confidence": 0.8
        }
    
    # 没有找到匹配
    return {
        "amount": None,
        "unit": None,
        "confidence": 0.0
    }


def call_llm(client: OpenAI, raw_text: str) -> Dict[str, Any]:
    try:
        user_content = USER_TEMPLATE.format(
            raw_text_json=json.dumps(raw_text, ensure_ascii=False)
        )

        resp = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": PROMPT_SYSTEM},
                {"role": "user", "content": user_content},
            ],
        )

        raw = resp.choices[0].message.content
        print(f"[DEBUG] LLM 响应: {raw[:100]}")
        obj = json.loads(raw)

        amount = obj.get("amount")
        unit = obj.get("unit")
        confidence = obj.get("confidence", 0.7)

        if amount is not None:
            try:
                amount = float(amount)
            except (TypeError, ValueError):
                amount = None

        if unit is not None:
            unit = str(unit).strip().lower() or None

        try:
            confidence = max(0.0, min(1.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = 0.7

        return {
            "amount": amount,
            "unit": unit,
            "confidence": confidence
        }

    except Exception as e:
        print(f"[ERROR] LLM 调用失败: {repr(e)}")
        return {
            "amount": None,
            "unit": None,
            "confidence": 0.0
        }


def load_recipe_ingredients() -> List[Dict[str, Any]]:
    """
    加载需要处理的 recipe_ingredient 记录
    """
    sql = text("""
    SELECT
        recipe_id,
        ingredient_id,
        line_no,
        amount,
        unit,
        raw_text
    FROM recipe_ingredient
    WHERE raw_text IS NOT NULL
      AND LENGTH(raw_text) >= :min_length
      AND (amount IS NULL OR unit IS NULL)
    ORDER BY recipe_id, line_no
    """)
    
    with engine.begin() as conn:
        rows = conn.execute(sql, {"min_length": MIN_LENGTH}).mappings().all()
    
    return [dict(row) for row in rows]


def update_recipe_ingredient(recipe_id: int, ingredient_id: int, line_no: int, 
                           amount: Optional[float], unit: Optional[str]):
    """
    更新 recipe_ingredient 记录
    """
    sql = text("""
    UPDATE recipe_ingredient
    SET amount = :amount,
        unit = :unit
    WHERE recipe_id = :recipe_id
      AND ingredient_id = :ingredient_id
      AND line_no = :line_no
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {
            "recipe_id": recipe_id,
            "ingredient_id": ingredient_id,
            "line_no": line_no,
            "amount": amount,
            "unit": unit
        })


def main() -> None:
    """
    主函数
    """
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY or OPENAI_API_KEY")
    
    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    
    # 加载需要处理的记录
    print("[INFO] 加载需要处理的记录")
    rows = load_recipe_ingredients()
    total = len(rows)
    print(f"[INFO] 共加载 {total} 条记录")
    
    if total == 0:
        print("[INFO] 没有需要处理的记录")
        return
    
    # 处理每条记录
    processed = 0
    success = 0
    
    for i, row in enumerate(rows, 1):
        recipe_id = row["recipe_id"]
        ingredient_id = row["ingredient_id"]
        line_no = row["line_no"]
        raw_text = row["raw_text"]
        
        print(f"\r[进度 {int(100*i/total)}%] 处理 {i}/{total}: {raw_text[:50]}", end="", flush=True)
        
        try:
            # 优先使用正则表达式提取
            result = extract_with_regex(raw_text)
            amount = result["amount"]
            unit = result["unit"]
            confidence = result["confidence"]
            
            # 如果正则表达式提取失败，使用 LLM
            if amount is None and unit is None:
                print(f" -> 正则表达式提取失败，使用 LLM")
                result = call_llm(client, raw_text)
                amount = result["amount"]
                unit = result["unit"]
                confidence = result["confidence"]
            
            # 更新数据库
            update_recipe_ingredient(recipe_id, ingredient_id, line_no, amount, unit)
            
            success += 1
            print(f" -> 成功: amount={amount}, unit={unit}, confidence={confidence:.2f}")
            
        except Exception as e:
            print(f" -> 失败: {e}")
            # 继续处理下一条记录
        
        processed += 1
        time.sleep(SLEEP_SEC)
    
    print(f"\n[INFO] 处理完成")
    print(f"[INFO] 总共处理: {processed} 条")
    print(f"[INFO] 成功更新: {success} 条")
    print(f"[INFO] 失败: {processed - success} 条")


if __name__ == "__main__":
    main()
