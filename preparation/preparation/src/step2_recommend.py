from __future__ import annotations

from typing import Any, Dict, List
from .db import get_conn

# Step2: 配方补全推荐（高频惩罚版）
# score = raw_score / LOG(2 + freq)
# support_cnt = 与 base 相连的边条数（越大越“稳”）
STEP2_SQL = """
WITH base AS (
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
    SUM(ges.weight) AS raw_score,
    SUM(ges.co_count) AS evidence_co,
    COUNT(*) AS support_cnt
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
)
SELECT
  i.ingredient_id,
  i.name_norm AS ingredient_name,
  r.raw_score,
  r.freq,
  r.score,
  r.evidence_co,
  r.support_cnt
FROM ranked r
JOIN ingredient i ON i.ingredient_id = r.cand_id
-- 稳定性开关：你可以要求至少被 2 个 base 原料支撑（避免“只跟一个原料相关”的噪声推荐）
WHERE r.support_cnt >= %s
ORDER BY r.score DESC
LIMIT %s;
"""


def recommend_step2(
    recipe_id: int,
    topk: int = 20,
    min_support: int = 2,
    snapshot_id: str = "s0",
) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(STEP2_SQL, (recipe_id, snapshot_id, snapshot_id, min_support, topk))
            return cur.fetchall()
    finally:
        conn.close()

# src/step2_recommend.py
from typing import List, Dict, Any, Optional

# 你项目里已有的 db 连接方式：把这里改成你现有的连接函数名即可
# 例如：from .db import get_connection
from .db import get_conn  # <- 如果你这里不是这个名字，把它替换成你实际的

def explain_step2_full(
    recipe_id: int,
    topk: int = 20,
    min_support_cnt: int = 1,
    snapshot_id: str = "s0",
) -> List[Dict[str, Any]]:
    """
    Step2 Explain（补全缺失证据）：
    - 先按高频惩罚 score 选 TopK 推荐
    - 然后对每个推荐 cand 与 base 中每个原料，输出一行证据
      (即使没有边，也输出 co_count=0 weight=0)
    """

    sql = """
    WITH
    base AS (
      SELECT DISTINCT v.llm_canonical_id AS ing
      FROM recipe_ingredient ri
      JOIN ingredient v ON v.ingredient_id = ri.ingredient_id
      WHERE ri.recipe_id = %(rid)s
    ),
    base_cnt AS (
      SELECT COUNT(*) AS n_base FROM base
    ),
    cand AS (
      SELECT
        CASE WHEN ges.i_id IN (SELECT ing FROM base) THEN ges.j_id ELSE ges.i_id END AS cand_id,
        SUM(ges.weight)   AS raw_score,
        SUM(ges.co_count) AS evidence_co,
        COUNT(DISTINCT CASE
          WHEN ges.i_id IN (SELECT ing FROM base) THEN ges.i_id
          WHEN ges.j_id IN (SELECT ing FROM base) THEN ges.j_id
          ELSE NULL
        END) AS support_cnt
      FROM graph_edge_stats_v2 ges
      WHERE ges.snapshot_id = %(snap)s
        AND (ges.i_id IN (SELECT ing FROM base)
         OR ges.j_id IN (SELECT ing FROM base))
      GROUP BY cand_id
    ),
    ranked AS (
      SELECT
        c.cand_id,
        c.raw_score,
        IFNULL(cf.freq, 1) AS freq,
        (c.raw_score / LN(2 + IFNULL(cf.freq, 1))) AS score,
        c.evidence_co,
        c.support_cnt
      FROM cand c
      LEFT JOIN canonical_freq_v2 cf
        ON cf.canonical_id = c.cand_id
       AND cf.snapshot_id = %(snap)s
      WHERE c.cand_id NOT IN (SELECT ing FROM base)
        AND c.support_cnt >= %(min_support_cnt)s
    ),
    topk_tbl AS (
      SELECT cand_id, score
      FROM ranked
      ORDER BY score DESC
      LIMIT %(topk)s
    ),
    -- 关键：对 topk × base 做笛卡尔积，然后 LEFT JOIN 边，缺失的补 0
    full_edges AS (
      SELECT
        t.cand_id,
        b.ing AS base_id,
        COALESCE(ges.co_count, 0) AS co_count,
        COALESCE(ges.weight, 0)   AS weight
      FROM topk_tbl t
      CROSS JOIN base b
      LEFT JOIN graph_edge_stats_v2 ges
        ON ges.snapshot_id = %(snap)s
       AND (
            (ges.i_id = t.cand_id AND ges.j_id = b.ing)
         OR (ges.j_id = t.cand_id AND ges.i_id = b.ing)
       )
    )
    SELECT
      ic.ingredient_id AS cand_id,
      ic.name_norm     AS recommended,
      t.score          AS score,
      ib.ingredient_id AS base_id,
      ib.name_norm     AS evidence_base_ing,
      e.co_count,
      e.weight
    FROM full_edges e
    JOIN topk_tbl t      ON t.cand_id = e.cand_id
    JOIN ingredient ic   ON ic.ingredient_id = e.cand_id
    JOIN ingredient ib   ON ib.ingredient_id = e.base_id
    ORDER BY recommended, weight DESC, evidence_base_ing;
    """

    conn = get_conn()
    try:
        with conn.cursor() as cur:  # ✅ 不要 dictionary=True
            cur.execute(
                sql,
                {
                    "rid": recipe_id,
                    "topk": int(topk),
                    "min_support_cnt": int(min_support_cnt),
                    "snap": snapshot_id,
                },
            )
            rows = cur.fetchall()   # ✅ rows: List[Dict]
        return rows
    finally:
        conn.close()
