"""
1. 为表 ingredient_flavor_anchor 添加列 anchor_form（若不存在）
2. 从 data/flavor_anchor_results.json 读取结果，写回数据库（含 anchor_name, anchor_source, match_confidence, anchor_form, notes 等）

运行方式（在 scripts/ 或项目根目录均可）：
  python scripts/write_flavor_anchor_to_db.py
  python write_flavor_anchor_to_db.py
"""
from __future__ import annotations

import os
import sys
import json
from typing import Dict, Any, List

# 保证从 scripts/ 或项目根目录运行都能找到 src
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy import text
from src.db import get_engine

# 结果 JSON 路径：优先脚本同目录下的 data/，其次项目根下的 data/
RESULTS_JSON = os.getenv("FLAVOR_ANCHOR_JSON", "data/flavor_anchor_results.json")
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"


def _results_path() -> str:
    for base in (_script_dir, _root):
        p = os.path.join(base, RESULTS_JSON)
        if os.path.isfile(p):
            return p
    return os.path.join(_script_dir, RESULTS_JSON)


def add_anchor_form_column(engine) -> bool:
    """若表中没有 anchor_form 列则添加。返回是否执行了 ADD COLUMN。"""
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT 1 FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'ingredient_flavor_anchor'
              AND COLUMN_NAME = 'anchor_form'
        """)).fetchone()
        if r:
            return False
    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE ingredient_flavor_anchor
            ADD COLUMN anchor_form VARCHAR(64) NULL DEFAULT NULL
            COMMENT 'juice/syrup/liqueur/cordial/bitters/fortified_wine/spirit/other'
            AFTER anchor_name
        """))
    return True


def load_results(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def sync_to_db(engine, results: List[Dict[str, Any]]) -> int:
    """按 ingredient_id 更新表，写入 anchor_name, anchor_source, match_confidence, anchor_form, notes 等。返回更新行数。"""
    sql = text("""
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
    """)
    updated = 0
    with engine.begin() as conn:
        for rec in results:
            ingredient_id = rec.get("ingredient_id")
            if ingredient_id is None:
                continue
            notes_obj = {
                "canonical_name": rec.get("canonical_name"),
                "anchor_form": rec.get("anchor_form"),
                "reason": rec.get("reason"),
                "source": "flavor_anchor_results.json",
            }
            params = {
                "anchor_name": rec.get("anchor_name") or "",
                "anchor_form": rec.get("anchor_form") or "other",
                "anchor_source": rec.get("anchor_source") or "",
                "match_confidence": float(rec.get("confidence", 0)),
                "notes": json.dumps(notes_obj, ensure_ascii=False),
                "is_direct_match": 1 if (rec.get("anchor_source") == "flavordb_direct") else 0,
                "review_status": "pending",
                "ingredient_id": ingredient_id,
            }
            res = conn.execute(sql, params)
            updated += res.rowcount
    return updated


def main():
    engine = get_engine()
    path = _results_path()
    if not os.path.isfile(path):
        print(f"[ERROR] 未找到结果文件: {path}")
        return

    # 1. 添加列 anchor_form（若不存在）
    if add_anchor_form_column(engine):
        print("[INFO] 已添加列 ingredient_flavor_anchor.anchor_form")
    else:
        print("[INFO] 列 anchor_form 已存在，跳过 ALTER")

    # 2. 加载 JSON 并写回数据库
    results = load_results(path)
    print(f"[INFO] 从 {path} 加载到 {len(results)} 条记录")
    if not results:
        print("[INFO] 无数据，退出")
        return

    if DRY_RUN:
        print("[INFO] DRY_RUN=1，仅预览不写库。前 3 条示例:", json.dumps(results[:3], ensure_ascii=False, indent=2))
        return

    updated = sync_to_db(engine, results)
    print(f"[INFO] 已更新 {updated} 条记录到表 ingredient_flavor_anchor")


if __name__ == "__main__":
    main()
