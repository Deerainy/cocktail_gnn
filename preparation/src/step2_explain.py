# src/step2_explain.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from .db import get_conn


SQL_STEP2_EXPLAIN_TOPK = r"""
WITH
base AS (
  SELECT DISTINCT v.llm_canonical_id AS ing
  FROM recipe_ingredient ri
  JOIN ingredient v ON v.ingredient_id = ri.ingredient_id
  WHERE ri.recipe_id = %s
),
cand AS (
  SELECT
    CASE
      WHEN ges.i_id IN (SELECT ing FROM base) THEN ges.j_id
      ELSE ges.i_id
    END AS cand_id,
    SUM(ges.weight)   AS raw_score,
    SUM(ges.co_count) AS evidence_co,
    COUNT(DISTINCT
      CASE
        WHEN ges.i_id IN (SELECT ing FROM base) THEN ges.i_id
        ELSE ges.j_id
      END
    ) AS support_cnt
  FROM graph_edge_stats_v2 ges
  WHERE ges.snapshot_id = %s
    AND (ges.i_id IN (SELECT ing FROM base)
     OR ges.j_id IN (SELECT ing FROM base))
  GROUP BY cand_id
),
ranked AS (
  SELECT
    c.cand_id,
    c.raw_score,
    IFNULL(cf.freq, 1) AS freq,
    (c.raw_score / LOG(2 + IFNULL(cf.freq, 1))) AS score,
    c.evidence_co,
    c.support_cnt
  FROM cand c
  LEFT JOIN canonical_freq_v2 cf
    ON cf.canonical_id = c.cand_id
   AND cf.snapshot_id = %s
  WHERE c.cand_id NOT IN (SELECT ing FROM base)
),
topk AS (
  SELECT cand_id, score
  FROM ranked
  ORDER BY score DESC
  LIMIT %s
),
edges AS (
  SELECT
    t.cand_id,
    t.score,
    CASE
      WHEN ges.i_id = t.cand_id THEN ges.j_id
      ELSE ges.i_id
    END AS base_id,
    ges.co_count,
    ges.weight
  FROM topk t
  JOIN graph_edge_stats_v2 ges
    ON ges.snapshot_id = %s
   AND (
        (ges.i_id = t.cand_id AND ges.j_id IN (SELECT ing FROM base))
     OR (ges.j_id = t.cand_id AND ges.i_id IN (SELECT ing FROM base))
   )
)
SELECT
  ic.ingredient_id AS ingredient_id,
  ic.name_norm     AS recommended,
  e.score          AS score,
  ib.ingredient_id AS evidence_base_id,
  ib.name_norm     AS evidence_base_ing,
  e.co_count       AS co_count,
  e.weight         AS weight
FROM edges e
JOIN ingredient ic ON ic.ingredient_id = e.cand_id
JOIN ingredient ib ON ib.ingredient_id = e.base_id
ORDER BY recommended, weight DESC;
"""


def explain_step2_topk(
    recipe_id: int,
    topk: int = 20,
    snapshot_id: str = "s0",
) -> List[Dict[str, Any]]:
    """
    Step2（高频惩罚版）的 Explain：
    - 先取 TopK 推荐原料
    - 再输出每个推荐原料与 base 原料之间的证据边（co_count/weight）
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(SQL_STEP2_EXPLAIN_TOPK, (recipe_id, snapshot_id, snapshot_id, topk, snapshot_id))
            rows = cur.fetchall()
        return rows
    finally:
        conn.close()
