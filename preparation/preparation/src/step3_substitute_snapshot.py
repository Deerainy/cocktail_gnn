# -*- coding: utf-8 -*-
"""
Step3: Ingredient substitution (snapshot-bound)

Hard rules:
- Always read canonical_freq_v2 / graph_edge_stats_v2
- Always filter by snapshot_id (and optionally weight_method)
- recipe_ingredient has NO canonical_id, so we map:
    canonical = COALESCE(llm_canonical_map.canonical_id, ingredient_id)

Usage:
1) Substitute by recipe_id + target ingredient_id:
   python -m src.step3_substitute_snapshot --recipe-id 12 --target-ingredient-id 345 --snapshot s0 --topk 20

2) If target is already canonical:
   python -m src.step3_substitute_snapshot --recipe-id 12 --target-canonical-id 789 --snapshot s0 --topk 20

Optional:
- --weight-method "pmi_penalized_l0.20"
- --min-co 2
- --deg-cap 300  (simple hub filter using degree from v2 edges)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine

try:
    from src.db import get_engine  # type: ignore
except Exception:
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


def fetch_type_map(engine: Engine, canonical_ids: Sequence[int]) -> Dict[int, Optional[str]]:
    if not canonical_ids:
        return {}
    sql = text(
        """
        SELECT ingredient_id, type_tag
        FROM ingredient_type
        WHERE ingredient_id IN :ids
        """
    ).bindparams(bindparam("ids", expanding=True))
    with engine.begin() as conn:
        rows = conn.execute(sql, {"ids": list(set(canonical_ids))}).fetchall()
    return {int(i): (c if c is not None else None) for i, c in rows}


def _degree_filter_ids(engine: Engine, snapshot_id: str, cand_ids: Sequence[int], deg_cap: int) -> List[int]:
    """
    Simple hub filter: degree = count of edges touching node (within snapshot).
    Keep ids with degree <= deg_cap.
    """
    if not cand_ids:
        return []

    sql = text(
        """
        SELECT node_id, deg
        FROM (
          SELECT i_id AS node_id, COUNT(*) AS deg
          FROM graph_edge_stats_v2
          WHERE snapshot_id = :snap AND i_id IN :cids
          GROUP BY i_id
          UNION ALL
          SELECT j_id AS node_id, COUNT(*) AS deg
          FROM graph_edge_stats_v2
          WHERE snapshot_id = :snap AND j_id IN :cids
          GROUP BY j_id
        ) t
        """
    ).bindparams(bindparam("cids", expanding=True))

    deg_map: Dict[int, int] = {int(x): 0 for x in cand_ids}
    with engine.begin() as conn:
        rows = conn.execute(sql, {"snap": snapshot_id, "cids": list(set(cand_ids))}).fetchall()
        for node_id, deg in rows:
            deg_map[int(node_id)] = deg_map.get(int(node_id), 0) + int(deg)

    return [cid for cid in cand_ids if deg_map.get(int(cid), 0) <= deg_cap]


def _substitute_candidates_sql(
    engine: Engine,
    snapshot_id: str,
    context_canonical_ids: Sequence[int],  # S = recipe canonical set without target
    target_canonical_id: int,
    topk: int,
    weight_method: Optional[str] = None,
    min_co: int = 1,
) -> List[Tuple[int, float]]:
    """
    Score(candidate) = SUM_{s in S} weight(candidate, s).
    We compute by scanning edges touching S, and taking the "other endpoint" as candidate.
    """
    if not context_canonical_ids:
        return []

    base = """
    SELECT
      cand_id,
      SUM(w) AS score
    FROM (
      SELECT
        CASE
          WHEN e.i_id IN :S THEN e.j_id
          ELSE e.i_id
        END AS cand_id,
        e.weight AS w
      FROM graph_edge_stats_v2 e
      WHERE e.snapshot_id = :snap
        AND (e.i_id IN :S OR e.j_id IN :S)
        AND e.co_count >= :min_co
    """
    if weight_method:
        base += "        AND e.weight_method = :wm\n"

    base += """
    ) x
    WHERE cand_id <> :target
      AND cand_id NOT IN :S
    GROUP BY cand_id
    ORDER BY score DESC
    LIMIT :k
    """

    sql = text(base).bindparams(
        bindparam("S", expanding=True),
        bindparam("k"),
        bindparam("min_co"),
    )

    params = {
        "snap": snapshot_id,
        "S": list(set(context_canonical_ids)),
        "target": int(target_canonical_id),
        "k": int(topk),
        "min_co": int(min_co),
    }
    if weight_method:
        sql = sql.bindparams(bindparam("wm"))
        params["wm"] = weight_method

    with engine.begin() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [(int(r[0]), float(r[1])) for r in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default="s0")
    ap.add_argument("--weight-method", default=None)
    ap.add_argument("--min-co", type=int, default=1)
    ap.add_argument("--topk", type=int, default=20)
    ap.add_argument("--deg-cap", type=int, default=300, help="hub filter (degree cap), default=300")
    ap.add_argument("--same-type-tag", action="store_true", default=True, help="only keep same type_tag as target")

    ap.add_argument("--recipe-id", type=int, required=True)
    tg = ap.add_mutually_exclusive_group(required=True)
    tg.add_argument("--target-ingredient-id", type=int, help="target ingredient_id (non-canonical)")
    tg.add_argument("--target-canonical-id", type=int, help="target canonical_id")

    args = ap.parse_args()
    engine = get_engine()

    # 1) recipe ingredients -> canonical set
    ingredient_ids = _fetch_recipe_ingredient_ids(engine, args.recipe_id)
    canonical_ids = _map_to_canonical_ids(engine, ingredient_ids)
    canonical_ids = _dedup_keep_order(canonical_ids)

    # 2) target canonical
    if args.target_canonical_id is not None:
        target_cid = int(args.target_canonical_id)
    else:
        target_cid = _map_to_canonical_ids(engine, [int(args.target_ingredient_id)])[0]

    print(f"canonical_ids_in_recipe ({len(canonical_ids)}): {canonical_ids}")
    print(f"target_canonical_id: {target_cid}")

    if target_cid not in set(canonical_ids):
        raise SystemExit(
            f"Target canonical_id={target_cid} is not in recipe_id={args.recipe_id}. "
            f"Likely wrong target-ingredient-id. Please pick one from recipe_ingredient."
        )

    # 3) context set S = recipe canonical set without target
    S = [cid for cid in canonical_ids if cid != target_cid]
    if not S:
        raise SystemExit("Context set is empty after removing target. Recipe may be too small.")

    # 4) candidates from edges touching S
    raw = _substitute_candidates_sql(
        engine=engine,
        snapshot_id=args.snapshot,
        context_canonical_ids=S,
        target_canonical_id=target_cid,
        topk=max(args.topk * 3, args.topk),  # fetch more then hub-filter
        weight_method=args.weight_method,
        min_co=args.min_co,
    )

    if args.same_type_tag:
        type_map = fetch_type_map(engine, [target_cid] + [cid for cid, _ in raw])
        target_type = type_map.get(target_cid)
        if target_type is not None:
            raw = [(cid, sc) for cid, sc in raw if type_map.get(cid) == target_type]

    cand_ids = [cid for cid, _ in raw]
    kept_ids = _degree_filter_ids(engine, args.snapshot, cand_ids, args.deg_cap)
    kept_set = set(kept_ids)

    filtered = [(cid, sc) for cid, sc in raw if cid in kept_set][: args.topk]

    # 5) attach freq for readability
    freq_map = _fetch_freqs(engine, args.snapshot, [cid for cid, _ in filtered])
    name_map = fetch_names(engine, [cid for cid, _ in filtered] + canonical_ids + [target_cid])

    print(f"[Step3] snapshot={args.snapshot} weight_method={args.weight_method} min_co={args.min_co} deg_cap={args.deg_cap}")
    print(f"target: {target_cid} ({name_map.get(target_cid)})")
    print(f"context S ({len(S)}): {S}")

    print("\nTop substitutes:")
    for rank, (cid, score) in enumerate(filtered, start=1):
        print(f"{rank:>2}. {cid:<6} {name_map.get(cid,'?'):<25} score={score:.6f}  freq={freq_map.get(cid)}")




if __name__ == "__main__":
    main()