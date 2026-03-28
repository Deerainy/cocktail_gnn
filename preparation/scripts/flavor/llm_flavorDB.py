from __future__ import annotations

import os
import sys
import json
import time
import re
from typing import Dict, Any, List, Tuple

# 保证从 scripts/ 或项目根目录运行都能找到 src
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import text

# 若存在 config/llm.env 则加载（可放 DEEPSEEK_API_KEY、DEEPSEEK_BASE_URL 等），避免每次在终端设环境变量
_llm_env = os.path.join(_root, "config", "llm.env")
load_dotenv(_llm_env)

# 复用你已有的 get_engine()
from src.db import get_engine

# =========================
# 配置区
# =========================
LLM_VERSION = "deepseek_flavor_anchor_v1"
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "0.2"))
# 0 表示不限制，处理全部；>0 时最多处理该条数
TOP_N = int(os.getenv("TOP_N", "0"))
# 只处理该 id 范围内的记录（含首尾）；默认 1001-1208
ANCHOR_ID_FROM = os.getenv("ANCHOR_ID_FROM", "1001")
ANCHOR_ID_TO = os.getenv("ANCHOR_ID_TO", "1208")
MIN_CONF = float(os.getenv("MIN_CONF", "0.60"))
# 默认 0：处理范围内全部记录（含已有 anchor_name 的），便于补跑 1001-1208
ONLY_EMPTY = os.getenv("ONLY_EMPTY", "0") == "1"
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"         # 默认先不落库
CACHE_PATH = os.getenv("CACHE_PATH", "data/llm_cache_flavor_anchor.jsonl")

# =========================
# 基础工具
# =========================
def normalize_name(name: str) -> str:
    s = (name or "").strip().lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def ensure_cache_dir():
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)

def append_cache(obj: Dict[str, Any]):
    ensure_cache_dir()
    with open(CACHE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def load_cache() -> Dict[str, Dict[str, Any]]:
    cache = {}
    if not os.path.exists(CACHE_PATH):
        return cache
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                key = normalize_name(obj.get("canonical_name", ""))
                if key:
                    cache[key] = obj
            except Exception:
                continue
    return cache

# =========================
# 规则预处理
# =========================
SPECIAL_MAP = {
    "maraschino liqueur": ("cherry", "liqueur"),
    "mezcal": ("agave", "spirit"),
}

FORM_PATTERNS = [
    ("liqueur", "liqueur"),
    ("juice", "juice"),
    ("syrup", "syrup"),
    ("cordial", "cordial"),
    ("bitters", "bitters"),
    ("vermouth", "fortified_wine"),
    ("whisky", "spirit"),
    ("whiskey", "spirit"),
    ("gin", "spirit"),
    ("rum", "spirit"),
    ("vodka", "spirit"),
    ("tequila", "spirit"),
    ("mezcal", "spirit"),
    ("brandy", "spirit"),
    ("cognac", "spirit"),
    ("pisco", "spirit"),
    ("amaro", "liqueur"),
    ("fernet", "liqueur"),
]

def infer_form(name: str) -> str:
    n = normalize_name(name)
    for pat, form in FORM_PATTERNS:
        if pat in n:
            return form
    return "other"

def simple_candidate(name: str) -> Tuple[str, str]:
    """
    不再负责最终 anchor 映射，只做：
    1. 基础清洗
    2. form 识别
    3. 给 LLM 一个弱提示 candidate
    """
    n = normalize_name(name)
    form = infer_form(n)

    # 去前缀
    for prefix in ["fresh ", "house-made ", "homemade "]:
        if n.startswith(prefix):
            n = n[len(prefix):].strip()

    # 去常见后缀，生成一个“弱候选”
    weak_anchor = n
    for suf in [" juice", " syrup", " liqueur", " cordial", " bitters"]:
        if n.endswith(suf):
            weak_anchor = n[:-len(suf)].strip()
            break

    return weak_anchor, form

# =========================
# LLM 调用
# =========================
def call_llm_json(client: OpenAI, prompt: str) -> Dict[str, Any]:
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a precise food/flavor ontology mapping assistant."},
            {"role": "user", "content": prompt},
        ],
    )
    content = resp.choices[0].message.content
    return json.loads(content)

def llm_map_anchor(client: OpenAI, canonical_name: str) -> Dict[str, Any]:
    n = normalize_name(canonical_name)
    weak_anchor, rule_form = simple_candidate(n)

    prompt = f"""
You are mapping cocktail ingredient names into a flavor-anchor representation.

Task:
Given a cocktail ingredient name, infer:
1. anchor_name: the main flavor source / sensory anchor
2. anchor_form: the ingredient form/category

Definitions:
- anchor_name = the main flavor-bearing object, usually a fruit, flower, herb, spice, plant source, or base ingredient.
- anchor_form = one of:
  ["juice", "syrup", "liqueur", "cordial", "bitters", "fortified_wine", "spirit", "other"]

Rules:
- Do NOT simply repeat the surface form unless necessary.
- Remove preparation/style modifiers when identifying anchor_name.
- Keep the main flavor source.
- Example:
  - "lime juice" -> anchor_name="lime", anchor_form="juice"
  - "elderflower liqueur" -> anchor_name="elderflower", anchor_form="liqueur"
  - "maraschino liqueur" -> anchor_name="cherry", anchor_form="liqueur"
  - "mezcal" -> anchor_name="agave", anchor_form="spirit"
- If the ingredient is a spirit or liqueur, anchor_name should still reflect the main flavor source if one is clearly identifiable.
- If no better abstraction is possible, return a reasonable sensory source close to the ingredient.

Input:
canonical_name = "{n}"
weak_anchor_candidate = "{weak_anchor}"
rule_form_candidate = "{rule_form}"

Return JSON only:
{{
  "anchor_name": "...",
  "anchor_form": "...",
  "confidence": 0.0,
  "reason": "..."
}}
"""
    return call_llm_json(client, prompt)

# =========================
# 数据库读写
# =========================
def fetch_rows(limit: int = TOP_N) -> List[Dict[str, Any]]:
    engine = get_engine()
    where_clause = "1=1"
    if ONLY_EMPTY:
        where_clause += " AND (anchor_name IS NULL OR TRIM(anchor_name) = '')"
    params = {}
    try:
        if ANCHOR_ID_FROM and str(ANCHOR_ID_FROM).strip():
            where_clause += " AND id >= :id_from"
            params["id_from"] = int(ANCHOR_ID_FROM)
        if ANCHOR_ID_TO and str(ANCHOR_ID_TO).strip():
            where_clause += " AND id <= :id_to"
            params["id_to"] = int(ANCHOR_ID_TO)
    except ValueError:
        pass

    sql = f"""
    SELECT
        id,
        ingredient_id,
        ingredient_name,
        canonical_id,
        canonical_name,
        anchor_name,
        anchor_source,
        match_confidence
    FROM ingredient_flavor_anchor
    WHERE {where_clause}
    ORDER BY ingredient_id
    """
    if limit > 0:
        sql += " LIMIT :limit"
        params["limit"] = limit
    with engine.begin() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
        return [dict(r) for r in rows]

import pymysql
import json

# 数据库更新函数
def update_anchor_result(row: Dict[str, Any], mapped: Dict[str, Any]):
    engine = get_engine()

    sql = """
    UPDATE ingredient_flavor_anchor
    SET
        anchor_name = :anchor_name,
        anchor_form = :anchor_form,
        anchor_source = :anchor_source,
        match_confidence = :match_confidence,
        notes = :notes,
        is_direct_match = :is_direct_match,
        review_status = :review_status,
        updated_at = NOW()
    WHERE ingredient_id = :ingredient_id
    """

    notes_obj = {
        "llm_version": LLM_VERSION,
        "model": MODEL_NAME,
        "anchor_form": mapped.get("anchor_form"),
        "reason": mapped.get("reason"),
        "canonical_name": row.get("canonical_name"),
    }

    params = {
        "anchor_name": mapped.get("anchor_name"),
        "anchor_form": mapped.get("anchor_form") or "other",
        "anchor_source": mapped.get("anchor_source"),
        "match_confidence": mapped.get("confidence"),
        "notes": json.dumps(notes_obj, ensure_ascii=False),
        "is_direct_match": 1 if mapped.get("anchor_source") == "flavordb_direct" else 0,
        "review_status": "pending",
        "ingredient_id": row["ingredient_id"],
    }

    with engine.begin() as conn:
        conn.execute(text(sql), params)


# =========================
# 主映射逻辑
# =========================
def resolve_one(client: OpenAI, row: Dict[str, Any], cache: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    canonical_name = normalize_name(row.get("canonical_name", ""))
    if not canonical_name:
        return {
            "canonical_name": "",
            "anchor_name": "",
            "anchor_form": "other",
            "confidence": 0.0,
            "anchor_source": "invalid",
            "reason": "empty canonical_name",
        }

    if canonical_name in cache:
        cached = cache[canonical_name]
        return {
            "canonical_name": canonical_name,
            "anchor_name": cached["anchor_name"],
            "anchor_form": cached.get("anchor_form", "other"),
            "confidence": float(cached.get("confidence", 0.6)),
            "anchor_source": cached.get("anchor_source", "cache"),
            "reason": cached.get("reason", "cache hit"),
        }

    # 先给一层规则候选
    rule_anchor, rule_form = simple_candidate(canonical_name)

    # 再让 LLM 判断
    llm_obj = llm_map_anchor(client, canonical_name)

    anchor_name = normalize_name(llm_obj.get("anchor_name", rule_anchor)) or rule_anchor
    anchor_form = llm_obj.get("anchor_form", rule_form) or rule_form
    confidence = float(llm_obj.get("confidence", 0.6))
    reason = llm_obj.get("reason", "")

    result = {
        "canonical_name": canonical_name,
        "anchor_name": anchor_name,
        "anchor_form": anchor_form,
        "confidence": confidence,
        "anchor_source": "deepseek_llm",
        "reason": reason,
    }

    append_cache(result)
    cache[canonical_name] = result
    time.sleep(SLEEP_SEC)
    return result

# =========================
# 批处理
# =========================
def main():
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "未设置 DEEPSEEK_API_KEY（或 OPENAI_API_KEY）。"
            "可在终端设置，或创建 config/llm.env 写入: DEEPSEEK_API_KEY=sk-xxx"
        )

    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )

    cache = load_cache()
    rows = fetch_rows(TOP_N)
    total = len(rows)

    print(f"[INFO] 共 {total} 条待处理, dry_run={DRY_RUN}, only_empty={ONLY_EMPTY}")
    if total == 0:
        # 简单诊断：看表总行数 vs 空 anchor_name 行数
        try:
            eng = get_engine()
            with eng.begin() as conn:
                total_in_table = conn.execute(text("SELECT COUNT(*) AS n FROM ingredient_flavor_anchor")).scalar()
                empty_count = conn.execute(text(
                    "SELECT COUNT(*) AS n FROM ingredient_flavor_anchor WHERE anchor_name IS NULL OR TRIM(COALESCE(anchor_name,'')) = ''"
                )).scalar()
            print(f"[INFO] 无待处理数据。表 ingredient_flavor_anchor 共 {total_in_table} 条，其中 anchor_name 为空的有 {empty_count} 条。")
            if total_in_table > 0 and empty_count == 0 and ONLY_EMPTY:
                print("[INFO] 当前 ONLY_EMPTY=1 只处理空记录；若要处理全部，请设置环境变量 ONLY_EMPTY=0 后重试。")
        except Exception as e:
            print(f"[INFO] 无数据（查表诊断失败: {e}），退出")
        return
    start_at = time.time()

    results = []
    for i, row in enumerate(rows, 1):
        try:
            pct = int(100 * i / total)
            elapsed = time.time() - start_at
            print(f"\r[进度 {pct:3d}%] ({i}/{total}) 已用 {elapsed:.0f}s | ", end="", flush=True)

            mapped = resolve_one(client, row, cache)
            results.append({
                "ingredient_id": row["ingredient_id"],
                "canonical_name": row["canonical_name"],
                **mapped
            })

            print(f"{row['canonical_name']} -> {mapped['anchor_name']} ({mapped['anchor_form']}, {mapped['confidence']})")

            if (not DRY_RUN) and mapped["confidence"] >= MIN_CONF:
                update_anchor_result(row, mapped)

        except Exception as e:
            print(f"[ERROR] ingredient_id={row.get('ingredient_id')} canonical_name={row.get('canonical_name')} err={e}")

    elapsed_total = time.time() - start_at
    print(f"\n[完成] 共处理 {len(results)}/{total} 条，耗时 {elapsed_total:.1f}s")

    out_path = "data/flavor_anchor_results.json"
    os.makedirs("data", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"[INFO] saved results to {out_path}")

if __name__ == "__main__":
    main()