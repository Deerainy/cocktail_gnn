# -*- coding: utf-8 -*-
"""
Step2: Recipe completion / ingredient recommendation (snapshot-bound)

Hard rules:
- Always read canonical_freq_v2 / graph_edge_stats_v2
- Always filter by snapshot_id (and optionally weight_method)
- recipe_ingredient has NO canonical_id, so we map:
    canonical = COALESCE(llm_canonical_map.canonical_id, ingredient_id)

Usage examples:
1) Recommend from a recipe_id:
   python -m src.step2_recommend_snapshot --recipe-id 12 --snapshot s0 --topk 20

2) Recommend from explicit ingredient_ids (from recipe_ingredient):
   python -m src.step2_recommend_snapshot --ingredient-ids 12,34,56 --snapshot s0 --topk 20

3) If your input is already canonical ids:
   python -m src.step2_recommend_snapshot --canonical-ids 101,202 --snapshot s0 --topk 20

Optional:
- --weight-method "pmi_penalized_l0.20" to lock a specific version inside snapshot
- --min-co 2 to avoid co_count=1 edges
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine

# ✅ Replace this import path with your actual engine helper.
# If you already have src/db.py or config/engine.py, point to it.
try:
    from src.db import get_engine  # type: ignore
except Exception:
    # Fallback: minimal engine builder (edit env vars if needed)
    import os
    from sqlalchemy import create_engine

    def get_engine(env_path: str = "config/db.env") -> Engine:
        host = os.getenv("DB_HOST", "127.0.0.1")
        port = os.getenv("DB_PORT", "3306")
        user = os.getenv("DB_USER", "root")
        pwd = os.getenv("DB_PASSWORD", "")
        db = os.getenv("DB_NAME", "cocktail_graph")
        url = f"mysql+pymysql://{user}:{pwd}@{host}:{port}/{db}?charset=utf8mb4"
        return create_engine(url, pool_pre_ping=True, pool_recycle=3600, future=True)


@dataclass
class Candidate:
    canonical_id: int
    score: float
    freq: Optional[int] = None


def _fetch_recipe_ingredient_ids(engine: Engine, recipe_id: int) -> List[int]:
    sql = text(
        """
        SELECT ingredient_id
        FROM recipe_ingredient
        WHERE recipe_id = :rid
          AND ingredient_id IS NOT NULL
        """
    )
    with engine.begin() as conn:
        rows = conn.execute(sql, {"rid": recipe_id}).fetchall()
    return [int(r[0]) for r in rows]


def _map_to_canonical_ids(engine: Engine, ingredient_ids: Sequence[int]) -> List[int]:
    """Batch map ingredient_ids -> canonical_ids using llm_canonical_map; missing maps to itself."""
    if not ingredient_ids:
        return []

    sql = text(
        """
        SELECT src_ingredient_id, canonical_id
        FROM llm_canonical_map
        WHERE src_ingredient_id IN :ids
        """
    ).bindparams(bindparam("ids", expanding=True))

    mapping: Dict[int, int] = {}
    with engine.begin() as conn:
        rows = conn.execute(sql, {"ids": list(set(ingredient_ids))}).fetchall()
        for src_id, canon_id in rows:
            if src_id is None:
                continue
            mapping[int(src_id)] = int(canon_id)

    return [mapping.get(int(x), int(x)) for x in ingredient_ids]


def _dedup_keep_order(xs: Sequence[int]) -> List[int]:
    seen = set()
    out = []
    for x in xs:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out


def _recommend_candidates_sql(
    engine: Engine,
    snapshot_id: str,
    seed_canonical_ids: Sequence[int],
    topk: int,
    weight_method: Optional[str] = None,
    min_co: int = 1,
) -> List[Tuple[int, float]]:
    """
    One-shot SQL aggregation:
    For each edge that touches any seed node, we treat the other endpoint as candidate and sum weights.
    """
    if not seed_canonical_ids:
        return []

    base = """
    SELECT
      cand_id,
      SUM(w) AS score
    FROM (
      SELECT
        CASE
          WHEN e.i_id IN :seeds THEN e.j_id
          ELSE e.i_id
        END AS cand_id,
        e.weight AS w
      FROM graph_edge_stats_v2 e
      WHERE e.snapshot_id = :snap
        AND (e.i_id IN :seeds OR e.j_id IN :seeds)
        AND e.co_count >= :min_co
    """

    if weight_method:
        base += "        AND e.weight_method = :wm\n"

    base += """
    ) x
    WHERE cand_id NOT IN :seeds
    GROUP BY cand_id
    ORDER BY score DESC
    LIMIT :k
    """

    sql = text(base).bindparams(
        bindparam("seeds", expanding=True),
        bindparam("k"),
        bindparam("min_co"),
    )
    params = {
        "snap": snapshot_id,
        "seeds": list(set(seed_canonical_ids)),
        "k": int(topk),
        "min_co": int(min_co),
    }
    if weight_method:
        sql = sql.bindparams(bindparam("wm"))
        params["wm"] = weight_method

    with engine.begin() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [(int(r[0]), float(r[1])) for r in rows]


def _fetch_freqs(engine: Engine, snapshot_id: str, canonical_ids: Sequence[int]) -> Dict[int, int]:
    if not canonical_ids:
        return {}
    sql = text(
        """
        SELECT canonical_id, freq
        FROM canonical_freq_v2
        WHERE snapshot_id = :snap
          AND canonical_id IN :cids
        """
    ).bindparams(bindparam("cids", expanding=True))
    with engine.begin() as conn:
        rows = conn.execute(sql, {"snap": snapshot_id, "cids": list(set(canonical_ids))}).fetchall()
    return {int(cid): int(freq) for cid, freq in rows}


def fetch_names(engine: Engine, canonical_ids: Sequence[int]) -> Dict[int, str]:
    if not canonical_ids:
        return {}
    sql = text(
        """
        SELECT ingredient_id, name_norm
        FROM ingredient
        WHERE ingredient_id IN :ids
        """
    ).bindparams(bindparam("ids", expanding=True))
    with engine.begin() as conn:
        rows = conn.execute(sql, {"ids": list(set(canonical_ids))}).fetchall()
    return {int(i): str(n) for i, n in rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default="s0", help="snapshot_id, e.g., s0")
    ap.add_argument("--weight-method", default=None, help="lock graph_edge_stats_v2.weight_method (optional)")
    ap.add_argument("--min-co", type=int, default=1, help="min co_count threshold (default=1)")
    ap.add_argument("--topk", type=int, default=20)

    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--recipe-id", type=int, help="use ingredients from recipe_ingredient by recipe_id")
    group.add_argument("--ingredient-ids", type=str, help="comma-separated ingredient_ids (non-canonical)")
    group.add_argument("--canonical-ids", type=str, help="comma-separated canonical_ids (already canonical)")

    args = ap.parse_args()
    engine = get_engine()

    # 1) collect seed ingredient ids
    if args.recipe_id is not None:
        ingredient_ids = _fetch_recipe_ingredient_ids(engine, args.recipe_id)
        seed_cids = _map_to_canonical_ids(engine, ingredient_ids)
    elif args.ingredient_ids is not None:
        ingredient_ids = [int(x.strip()) for x in args.ingredient_ids.split(",") if x.strip()]
        seed_cids = _map_to_canonical_ids(engine, ingredient_ids)
    else:
        seed_cids = [int(x.strip()) for x in args.canonical_ids.split(",") if x.strip()]

    seed_cids = _dedup_keep_order(seed_cids)

    # 2) recommend
    recs = _recommend_candidates_sql(
        engine=engine,
        snapshot_id=args.snapshot,
        seed_canonical_ids=seed_cids,
        topk=args.topk,
        weight_method=args.weight_method,
        min_co=args.min_co,
    )

    # 3) attach freq for interpretability
    cand_ids = [cid for cid, _ in recs]
    freq_map = _fetch_freqs(engine, args.snapshot, cand_ids)
    name_map = fetch_names(engine, cand_ids + seed_cids)

    # 4) print
    print(f"[Step2] snapshot={args.snapshot} weight_method={args.weight_method} min_co={args.min_co}")
    print(f"Seed canonical_ids ({len(seed_cids)}): {seed_cids}")
    print("\nTop candidates:")
    for rank, (cid, score) in enumerate(recs, start=1):
        freq = freq_map.get(cid)
        print(f"{rank:>2}. {cid:<6} {name_map.get(cid,'?'):<25} score={score:.6f}  freq={freq}")


if __name__ == "__main__":
    main()