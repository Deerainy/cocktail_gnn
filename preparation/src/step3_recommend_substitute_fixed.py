# src/step3_recommend_substitute_fixed.py
import re
from src.db import get_conn

SQL_MAIN = r"""
WITH
t AS ( SELECT %s AS tid ),

recipe_ctx AS (
  SELECT DISTINCT
    COALESCE(m.canonical_id, ing.ingredient_id) AS ctx_id
  FROM recipe_ingredient ri
  JOIN ingredient ing ON ing.ingredient_id = ri.ingredient_id
  LEFT JOIN llm_canonical_map m
    ON m.src_ingredient_id = ing.ingredient_id
   AND m.status = 'ok'
  WHERE ri.recipe_id = %s
),

deg AS (
  SELECT x.id, COUNT(*) AS deg
  FROM (
    SELECT i_id AS id FROM graph_edge_stats_v2 WHERE snapshot_id = %s
    UNION ALL
    SELECT j_id AS id FROM graph_edge_stats_v2 WHERE snapshot_id = %s
  ) x
  GROUP BY x.id
),

nb AS (
  SELECT
    CASE WHEN ges.i_id = t.tid THEN ges.j_id ELSE ges.i_id END AS nb_id,
    ges.weight AS w_t
  FROM graph_edge_stats_v2 ges
  JOIN t
  WHERE (ges.i_id = t.tid OR ges.j_id = t.tid)
    AND ges.snapshot_id = %s
),

overlap AS (
  SELECT
    c.cand_id,
    SUM(LEAST(nb.w_t, c.w_c)) AS overlap_score
  FROM nb
  JOIN (
    SELECT
      CASE WHEN ges.i_id = nb.nb_id THEN ges.j_id ELSE ges.i_id END AS cand_id,
      ges.weight AS w_c,
      nb.nb_id AS shared_nb
    FROM graph_edge_stats_v2 ges
    JOIN nb
      ON (ges.i_id = nb.nb_id OR ges.j_id = nb.nb_id)
     AND ges.snapshot_id = %s
  ) c
    ON c.shared_nb = nb.nb_id
  GROUP BY c.cand_id
),

t_norm AS (
  SELECT SUM(ges.weight * ges.weight) AS sum_w_t
  FROM graph_edge_stats_v2 ges
  JOIN t
  WHERE (ges.i_id = t.tid OR ges.j_id = t.tid)
    AND ges.snapshot_id = %s
),
cand_norm AS (
  SELECT
    x.id AS cand_id,
    SUM(x.w * x.w) AS sum_w_c
  FROM (
    SELECT i_id AS id, weight AS w FROM graph_edge_stats_v2 WHERE snapshot_id = %s
    UNION ALL
    SELECT j_id AS id, weight AS w FROM graph_edge_stats_v2 WHERE snapshot_id = %s
  ) x
  GROUP BY x.id
),

ranked AS (
  SELECT
    o.cand_id,
    o.overlap_score,
    o.overlap_score / NULLIF(SQRT(tn.sum_w_t * cn.sum_w_c), 0) AS cosine_score
  FROM overlap o
  JOIN t_norm tn
  JOIN cand_norm cn ON cn.cand_id = o.cand_id
),

compat AS (
  SELECT
    cand_id,
    SUM(w) AS compat_score
  FROM (
    SELECT
      CASE WHEN ges.i_id = rc.ctx_id THEN ges.j_id ELSE ges.i_id END AS cand_id,
      ges.weight AS w
    FROM graph_edge_stats_v2 ges
    JOIN recipe_ctx rc
      ON (ges.i_id = rc.ctx_id OR ges.j_id = rc.ctx_id)
    WHERE ges.snapshot_id = %s
  ) z
  GROUP BY cand_id
),
compat_max AS ( SELECT MAX(compat_score) AS mx FROM compat ),

scored AS (
  SELECT
    r.cand_id,
    r.cosine_score,
    r.overlap_score,
    COALESCE(c.compat_score, 0) AS compat_score,
    CASE
      WHEN cm.mx IS NULL OR cm.mx = 0 THEN 0
      ELSE COALESCE(c.compat_score, 0) / cm.mx
    END AS compat_norm,
    (
      r.cosine_score
      + 0.45 * (
        CASE
          WHEN cm.mx IS NULL OR cm.mx = 0 THEN 0
          ELSE COALESCE(c.compat_score, 0) / cm.mx
        END
      )
      + %s * (i.name_norm REGEXP '(genever|aquavit|vodka|white rum|rum|tequila|mezcal|whisky|whiskey|bourbon|brandy|cognac|pisco)')
    ) AS final_score
  FROM ranked r
  JOIN ingredient i ON i.ingredient_id = r.cand_id
  LEFT JOIN compat c ON c.cand_id = r.cand_id
  CROSS JOIN compat_max cm
)

SELECT
  i.name_norm,
  s.cosine_score,
  s.compat_score,
  s.compat_norm,
  s.final_score
FROM scored s
JOIN ingredient i ON i.ingredient_id = s.cand_id
JOIN t
LEFT JOIN deg d ON d.id = s.cand_id
LEFT JOIN recipe_ctx rc ON rc.ctx_id = s.cand_id
WHERE s.cand_id <> t.tid
  AND rc.ctx_id IS NULL
  AND COALESCE(d.deg, 0) <= %s
ORDER BY s.final_score DESC
LIMIT %s;
"""

SQL_RESOLVE_TID = r"""
WITH
target AS (
  SELECT i.ingredient_id AS tid
  FROM ingredient i
  WHERE i.name_norm = %s
    AND i.llm_rationale = 'canonical node'
  LIMIT 1
),
target_fallback AS (
  SELECT m.canonical_id AS tid
  FROM llm_canonical_map m
  WHERE m.canonical_name = %s
  ORDER BY m.confidence DESC
  LIMIT 1
)
SELECT COALESCE((SELECT tid FROM target), (SELECT tid FROM target_fallback)) AS tid;
"""

# 以 gin 为例：烈酒过滤（防止 simple syrup / egg white 这种上榜）
SPIRIT_RE = re.compile(
    r"(gin|vodka|rum|tequila|mezcal|whisk|whiskey|bourbon|brandy|cognac|pisco|genever|aquavit)",
    re.I
)

def resolve_target_tid(conn, target_name: str) -> int:
    with conn.cursor() as cur:
        cur.execute(SQL_RESOLVE_TID, (target_name, target_name))
        row = cur.fetchone()
    tid = row["tid"] if row else None
    if tid is None:
        raise ValueError(f"target '{target_name}' 无 canonical_id：ingredient/llm_canonical_map 都没命中")
    return int(tid)

def recommend_fixed(
    recipe_id=2,
    target_name="gin",
    lambda_bonus=0.15,
    deg_cap=300,
    topk=20,
    snapshot_id: str = "s0",
):
    conn = get_conn()
    try:
        tid = resolve_target_tid(conn, target_name)

        with conn.cursor() as cur:
            cur.execute(
                SQL_MAIN,
                (
                    tid,
                    recipe_id,
                    snapshot_id,
                    snapshot_id,
                    snapshot_id,
                    snapshot_id,
                    snapshot_id,
                    snapshot_id,
                    snapshot_id,
                    snapshot_id,
                    lambda_bonus,
                    deg_cap,
                    topk,
                ),
            )
            rows = cur.fetchall()

        # ✅ 同类过滤：gin 的替代只保留烈酒候选（你后面可以做成按 target_name 切换规则）
        rows = [r for r in rows if SPIRIT_RE.search(r["name_norm"] or "")]

        return rows
    finally:
        conn.close()

if __name__ == "__main__":
    rows = recommend_fixed()
    for r in rows:
        print(r)
