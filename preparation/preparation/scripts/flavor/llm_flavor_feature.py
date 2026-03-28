"""
FlavorDB-grounded LLM 脚本：
1. 从 ingredient_flavor_anchor 读 ingredient_id / anchor_name / anchor_form
2. 用 anchor_name 查 FlavorDB2，若命中则抓 flavor profile + pairing 作为 evidence
3. 将 anchor_name + anchor_form + evidence 喂给 LLM，输出 six-dim feature（sour/sweet/bitter/aroma/fruity/body，0~1）
4. 写回 ingredient_flavor_feature

运行：python scripts/llm_flavor_feature.py  或  python llm_flavor_feature.py
环境变量：TOP_N, DRY_RUN, DEEPSEEK_API_KEY（或 OPENAI_API_KEY）, config/llm.env
"""
from __future__ import annotations

import os
import sys
import json
import time
from typing import Dict, Any, List, Optional

_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import text

_llm_env = os.path.join(_root, "config", "llm.env")
load_dotenv(_llm_env)

from src.db import get_engine
import flavor_fetch

# =========================
# 配置
# =========================
# 0 表示不限制，处理全部未算过的；>0 时最多处理该条数
TOP_N = int(os.getenv("TOP_N", "0"))
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"
LLM_VERSION = os.getenv("LLM_VERSION", "deepseek_flavor_feature_v1")
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "0.3"))

# 进度文件路径
PROGRESS_FILE = os.path.join(_root, "data", "flavor_feature_progress.json")

# 六维（与表 ingredient_flavor_feature 列一致）：sour, sweet, bitter, aroma, fruity, body，每维 0.0~1.0
FEATURE_DIMS = ["sour", "sweet", "bitter", "aroma", "fruity", "body"]

# =========================
# 进度管理
# =========================
def save_progress(processed_ids: List[int]) -> None:
    """保存已处理的 ingredient_id 列表到进度文件"""
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"processed_ids": processed_ids, "timestamp": time.time()}, f, ensure_ascii=False, indent=2)


def load_progress() -> List[int]:
    """从进度文件加载已处理的 ingredient_id 列表"""
    if not os.path.exists(PROGRESS_FILE):
        return []
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("processed_ids", [])
    except (json.JSONDecodeError, Exception):
        return []


def fetch_anchor_rows(limit: int) -> List[Dict[str, Any]]:
    """从 ingredient_flavor_anchor 读取尚未在 ingredient_flavor_feature 中存在的记录（不重复算）。limit<=0 表示不限制条数。"""
    engine = get_engine()
    
    # 加载已处理的 ingredient_id
    processed_ids = load_progress()
    
    # 构建 SQL 查询，排除已处理的 ID
    if processed_ids:
        # 使用命名参数处理 IN 子句
        sql = text("""
            SELECT a.ingredient_id, a.canonical_name, a.anchor_name, a.anchor_form
            FROM ingredient_flavor_anchor a
            LEFT JOIN ingredient_flavor_feature f ON f.ingredient_id = a.ingredient_id
            WHERE a.anchor_name IS NOT NULL AND TRIM(a.anchor_name) != ''
              AND f.ingredient_id IS NULL
              AND a.ingredient_id NOT IN :processed_ids
            ORDER BY a.ingredient_id
        """)
        with engine.begin() as conn:
            rows = conn.execute(sql, {"processed_ids": processed_ids}).mappings().all()
    else:
        sql = text("""
            SELECT a.ingredient_id, a.canonical_name, a.anchor_name, a.anchor_form
            FROM ingredient_flavor_anchor a
            LEFT JOIN ingredient_flavor_feature f ON f.ingredient_id = a.ingredient_id
            WHERE a.anchor_name IS NOT NULL AND TRIM(a.anchor_name) != ''
              AND f.ingredient_id IS NULL
            ORDER BY a.ingredient_id
        """)
        with engine.begin() as conn:
            rows = conn.execute(sql).mappings().all()
    
    out = [dict(r) for r in rows]
    if limit > 0:
        out = out[:limit]
    return out


def build_evidence_text(evidence: Dict[str, Any]) -> str:
    """从 fetch_flavordb_evidence 结果拼一段短文作为 LLM 的 evidence。"""
    parts = []
    if evidence.get("matched") and evidence.get("details"):
        d = evidence["details"]
        if d.get("profiles"):
            parts.append("Flavor profiles: " + ", ".join(d["profiles"][:20]))
        mols = d.get("molecules") or []
        if mols:
            profiles = [m.get("flavor_profile", "").strip() for m in mols[:15] if m.get("flavor_profile")]
            if profiles:
                parts.append("Molecule descriptors: " + "; ".join(profiles))
    if evidence.get("pairing") and evidence["pairing"].get("pairs"):
        pairs = evidence["pairing"]["pairs"][:15]
        names = [p.get("entity_name") or p.get("pair_name", "") for p in pairs if p.get("entity_name") or p.get("pair_name")]
        if names:
            parts.append("Pairing entities: " + ", ".join(names))
    return "\n".join(parts) if parts else ""


PROMPT_SYSTEM = """You are generating a flavor feature vector for cocktail ingredient modeling.

Task:
Given a cocktail ingredient with:
- canonical_name
- anchor_name
- anchor_form
- optional FlavorDB evidence

infer a 6-dimensional sensory feature vector with values in [0,1]:
- sour
- sweet
- bitter
- aroma
- fruity
- body

Definitions:
- sour = perceived acidity / tartness
- sweet = perceived sweetness
- bitter = bitterness
- aroma = aromatic intensity / olfactory richness
- fruity = fruit-like character
- body = heaviness / richness / mouthfeel weight

Important rules:
1. Use FlavorDB evidence as the primary grounding if available.
2. If FlavorDB evidence is missing or incomplete, infer reasonably from anchor_name + anchor_form.
3. anchor_name represents the main flavor source.
4. anchor_form adjusts the sensory profile:
   - juice: usually lighter body, more direct acidity/fruit expression
   - syrup: sweeter and fuller
   - liqueur: sweet, aromatic, fuller-bodied
   - spirit: stronger body/aroma, usually low sweetness
   - bitters: high bitterness, strong aroma, very low body
   - fortified_wine: moderate body and aroma
   - other: infer reasonably
5. Keep the six values internally consistent.
6. Do not output vague text; output numeric values.
7. Return JSON only."""


def call_llm_six_dim(
    client: OpenAI,
    canonical_name: str,
    anchor_name: str,
    anchor_form: str,
    evidence: str,
) -> Dict[str, Any]:
    """调用 LLM，输入 canonical_name + anchor + evidence，输出六维向量及 confidence / feature_source / reason。"""
    flavordb_evidence = evidence.strip() if evidence.strip() else "(none)"
    user = f"""Input:
canonical_name = "{canonical_name}"
anchor_name = "{anchor_name}"
anchor_form = "{anchor_form}"

FlavorDB evidence:
{flavordb_evidence}

Return format:
{{
  "sour": 0.0,
  "sweet": 0.0,
  "bitter": 0.0,
  "aroma": 0.0,
  "fruity": 0.0,
  "body": 0.0,
  "confidence": 0.0,
  "feature_source": "flavordb_grounded_llm or llm_anchor_only",
  "reason": "brief explanation"
}}"""
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": user},
        ],
    )
    raw = resp.choices[0].message.content
    obj = json.loads(raw)
    feature = {}
    for k in FEATURE_DIMS:
        v = obj.get(k)
        try:
            feature[k] = max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            feature[k] = 0.0
    try:
        confidence = max(0.0, min(1.0, float(obj.get("confidence", 0.7))))
    except (TypeError, ValueError):
        confidence = 0.7
    feature_source = obj.get("feature_source") or "llm_anchor_only"
    if isinstance(feature_source, str) and "flavordb" in feature_source.lower():
        feature_source = "flavordb_grounded_llm"
    else:
        feature_source = "llm_anchor_only"
    reason = (obj.get("reason") or "").strip()
    return {
        "feature": feature,
        "confidence": confidence,
        "feature_source": feature_source,
        "reason": reason,
    }


def write_feature(
    engine,
    ingredient_id: int,
    anchor_name: str,
    feature: Dict[str, float],
    notes: Optional[str],
    feature_source: str,
    feature_confidence: float,
) -> None:
    """写入或更新 ingredient_flavor_feature 一行（表结构：id, ingredient_id, anchor_name, sour, sweet, bitter, aroma, fruity, body, feature_source, feature_confidence, derivation_method, review_status, notes）。"""
    params = {
        "ingredient_id": ingredient_id,
        "anchor_name": anchor_name,
        "sour": feature.get("sour", 0),
        "sweet": feature.get("sweet", 0),
        "bitter": feature.get("bitter", 0),
        "aroma": feature.get("aroma", 0),
        "fruity": feature.get("fruity", 0),
        "body": feature.get("body", 0),
        "feature_source": feature_source if feature_source else "LLM_grounded_FlavorDB",
        "feature_confidence": feature_confidence,
        "derivation_method": "LLM_inference_with_FlavorDB_context",
        "review_status": "pending",
        "notes": notes[:4000] if notes else None,
    }
    with engine.begin() as conn:
        exist = conn.execute(
            text("SELECT 1 FROM ingredient_flavor_feature WHERE ingredient_id = :id"),
            {"id": ingredient_id},
        ).fetchone()
        if exist:
            conn.execute(
                text("""
                    UPDATE ingredient_flavor_feature SET
                    anchor_name = :anchor_name, sour = :sour, sweet = :sweet, bitter = :bitter,
                    aroma = :aroma, fruity = :fruity, body = :body,
                    feature_source = :feature_source, feature_confidence = :feature_confidence,
                    derivation_method = :derivation_method, review_status = :review_status,
                    notes = :notes, updated_at = NOW()
                    WHERE ingredient_id = :ingredient_id
                """),
                params,
            )
        else:
            conn.execute(
                text("""
                    INSERT INTO ingredient_flavor_feature
                    (ingredient_id, anchor_name, sour, sweet, bitter, aroma, fruity, body,
                     feature_source, feature_confidence, derivation_method, review_status, notes)
                    VALUES
                    (:ingredient_id, :anchor_name, :sour, :sweet, :bitter, :aroma, :fruity, :body,
                     :feature_source, :feature_confidence, :derivation_method, :review_status, :notes)
                """),
                params,
            )


def main() -> None:
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY or OPENAI_API_KEY")
    client = OpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )
    engine = get_engine()
    rows = fetch_anchor_rows(TOP_N)
    total = len(rows)
    
    # 加载已处理的 ID
    processed_ids = load_progress()
    print(f"[INFO] 已处理 {len(processed_ids)} 条，待处理 {total} 条（仅 anchor 表中尚未在 feature 表出现的），TOP_N={TOP_N or '全部'}，DRY_RUN={DRY_RUN}")
    if total == 0:
        return
    start = time.time()

    # 处理每条记录并保存进度
    for i, row in enumerate(rows, 1):
        ingredient_id = row["ingredient_id"]
        canonical_name = (row.get("canonical_name") or "").strip()
        anchor_name = (row.get("anchor_name") or "").strip()
        anchor_form = (row.get("anchor_form") or "other").strip()
        if not anchor_name:
            continue

        pct = int(100 * i / total)
        elapsed = time.time() - start
        print(f"\r[进度 {pct}%] ({i}/{total}) 已用 {elapsed:.0f}s | {anchor_name} / {anchor_form}", end="", flush=True)

        evidence_result = flavor_fetch.fetch_flavordb_evidence(
            anchor_name, anchor_form, with_pairing=True
        )
        evidence_text = build_evidence_text(evidence_result)

        llm_out = call_llm_six_dim(
            client,
            canonical_name=canonical_name,
            anchor_name=anchor_name,
            anchor_form=anchor_form,
            evidence=evidence_text,
        )
        feature = llm_out["feature"]
        time.sleep(SLEEP_SEC)

        notes_parts = []
        if evidence_text:
            notes_parts.append(evidence_text)
        if llm_out.get("reason"):
            notes_parts.append("LLM reason: " + llm_out["reason"])
        notes_combined = "\n\n".join(notes_parts) if notes_parts else None

        if not DRY_RUN:
            write_feature(
                engine,
                ingredient_id=ingredient_id,
                anchor_name=anchor_name,
                feature=feature,
                notes=notes_combined,
                feature_source=llm_out.get("feature_source", "llm_anchor_only"),
                feature_confidence=llm_out.get("confidence", 0.7),
            )
        
        # 将当前处理的 ID 添加到已处理列表并保存进度
        processed_ids.append(ingredient_id)
        save_progress(processed_ids)
        
        # 实时存储生成的风味特征数据到本地文件，作为备份
        feature_data = {
            "ingredient_id": ingredient_id,
            "canonical_name": canonical_name,
            "anchor_name": anchor_name,
            "anchor_form": anchor_form,
            "feature": feature,
            "confidence": llm_out.get("confidence", 0.7),
            "feature_source": llm_out.get("feature_source", "llm_anchor_only"),
            "reason": llm_out.get("reason", ""),
            "evidence_text": evidence_text,
            "timestamp": time.time()
        }
        
        # 保存到本地文件
        feature_backup_file = os.path.join(_root, "data", "flavor_feature_backup.jsonl")
        os.makedirs(os.path.dirname(feature_backup_file), exist_ok=True)
        with open(feature_backup_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(feature_data, ensure_ascii=False) + "\n")
        
        print(f" -> {feature} (conf={llm_out.get('confidence', 0):.2f}, src={llm_out.get('feature_source', '')})")

    print(f"\n[完成] 处理 {total} 条，总已处理 {len(processed_ids)} 条，耗时 {time.time() - start:.1f}s，DRY_RUN={DRY_RUN}")


if __name__ == "__main__":
    main()
