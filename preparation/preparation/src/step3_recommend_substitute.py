# -*- coding: utf-8 -*-
"""
Step3: 替代推荐（Graph-based substitute recommendation）
- 基于加权共同邻居（overlap_score）+ Cosine 归一化（cosine_score）
- 叠加语义先验 bonus 得到 final_score，并按 final_score 排序
"""

from __future__ import annotations

import os
import argparse
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

import pymysql
import pandas as pd
from src.db import get_conn  # 或者你 db.py 里真实的函数名


@dataclass
class DBConfig:
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = "123456"
    database: str = "cocktail_graph"
    charset: str = "utf8mb4"


SQL_TEMPLATE = r"""
WITH
target AS (
  SELECT ingredient_id AS tid
  FROM ingredient
  WHERE name_norm = %(target_name)s
  LIMIT 1
),

-- 节点度：用于过滤 hub
deg AS (
  SELECT x.id, COUNT(*) AS deg
  FROM (
  SELECT i_id AS id FROM graph_edge_stats_v2 WHERE snapshot_id = %(snap)s
    UNION ALL
  SELECT j_id AS id FROM graph_edge_stats_v2 WHERE snapshot_id = %(snap)s
  ) x
  GROUP BY x.id
),

-- target 的邻居 (nb, w_t)
t_neighbors AS (
  SELECT
    CASE WHEN g.i_id = t.tid THEN g.j_id ELSE g.i_id END AS nb,
    g.weight AS w_t
  FROM graph_edge_stats_v2 g
  JOIN target t
    ON (g.i_id = t.tid OR g.j_id = t.tid)
  WHERE g.snapshot_id = %(snap)s
),

t_norm AS (
  SELECT SUM(w_t) AS sum_w_t FROM t_neighbors
),

/* 候选集合（从 target 一跳邻居中挑）：
   1) hub 抑制：deg <= %(deg_cap)s
   2) 排除 mixer：name_norm NOT REGEXP %(exclude_regex)s
   3) 保留“像酒基”的：name_norm REGEXP %(include_regex)s
*/
cand AS (
  SELECT DISTINCT
    CASE WHEN g.i_id = t.tid THEN g.j_id ELSE g.i_id END AS cand_id
  FROM graph_edge_stats_v2 g
  JOIN target t
    ON (g.i_id = t.tid OR g.j_id = t.tid)
  JOIN ingredient ci
    ON ci.ingredient_id = (CASE WHEN g.i_id = t.tid THEN g.j_id ELSE g.i_id END)
  JOIN deg d
    ON d.id = ci.ingredient_id
  WHERE
    g.snapshot_id = %(snap)s
    AND d.deg <= %(deg_cap)s
    AND ci.name_norm NOT REGEXP %(exclude_regex)s
    AND ci.name_norm REGEXP %(include_regex)s
),

-- cand 的邻居摊平
cand_neighbors AS (
  SELECT
    c.cand_id,
    CASE WHEN g.i_id = c.cand_id THEN g.j_id ELSE g.i_id END AS nb,
    g.weight AS w_c
  FROM cand c
  JOIN graph_edge_stats_v2 g
    ON (g.i_id = c.cand_id OR g.j_id = c.cand_id)
   AND g.snapshot_id = %(snap)s
),

cand_norm AS (
  SELECT cand_id, SUM(w_c) AS sum_w_c
  FROM cand_neighbors
  GROUP BY cand_id
),

-- overlap：加权共同邻居（min 聚合）
overlap AS (
  SELECT
    cn.cand_id,
    SUM(LEAST(tn.w_t, cn.w_c)) AS overlap_score
  FROM cand_neighbors cn
  JOIN t_neighbors tn
    ON tn.nb = cn.nb
  GROUP BY cn.cand_id
),

ranked AS (
  SELECT
    o.cand_id,
    o.overlap_score,
    o.overlap_score / SQRT(tn.sum_w_t * cn.sum_w_c) AS cosine_score
  FROM overlap o
  JOIN t_norm tn
  JOIN cand_norm cn
    ON cn.cand_id = o.cand_id
)

SELECT
  i.name_norm,
  r.cosine_score,
  r.overlap_score,
  (r.cosine_score + %(lambda_bonus)s * (i.name_norm REGEXP %(prefer_regex)s)) AS final_score
FROM ranked r
JOIN ingredient i ON i.ingredient_id = r.cand_id
JOIN target t ON r.cand_id <> t.tid
ORDER BY final_score DESC
LIMIT %(topk)s;
"""


DEFAULT_EXCLUDE_REGEX = (
    r"(juice|syrup|bitters|egg|milk|cream|soda|water|cola|tonic|"
    r"ginger beer|ginger ale|lemonade|tea|coffee|salt|pepper|"
    r"mint|basil|cucumber|puree|jam|honey|maple|grenadine|orchat|orgeat)"
)

# 你目前候选是“酒基/烈酒”，保持与你截图一致（可按数据再扩）
DEFAULT_INCLUDE_REGEX = r"(vodka|rum|tequila|mezcal|whisk|whiskey|bourbon|scotch|rye|brandy|cognac|genever|aquavit)"

# 先验优先集合：更像 gin 的替代
DEFAULT_PREFER_REGEX = r"(genever|aquavit|vodka|white rum)"


def connect_db(cfg: DBConfig):
    return pymysql.connect(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        charset=cfg.charset,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def recommend_substitutes(
    target_name_norm: str,
    topk: int = 20,
    lambda_bonus: float = 0.15,
    deg_cap: int = 300,
    include_regex: str = DEFAULT_INCLUDE_REGEX,
    exclude_regex: str = DEFAULT_EXCLUDE_REGEX,
    prefer_regex: str = DEFAULT_PREFER_REGEX,
    snapshot_id: str = "s0",
) -> pd.DataFrame:
    conn = get_conn()
    params = {
        "target_name": target_name_norm,
        "topk": topk,
        "lambda_bonus": float(lambda_bonus),
        "deg_cap": int(deg_cap),
        "include_regex": include_regex,
        "exclude_regex": exclude_regex,
        "prefer_regex": prefer_regex,
        "snap": snapshot_id,
    }

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(SQL_TEMPLATE, params)
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Step3 替代推荐（图相似度 + 先验 rerank）")
    parser.add_argument("--host", default=os.getenv("DB_HOST", "localhost"))
    parser.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "3306")))
    parser.add_argument("--user", default=os.getenv("DB_USER", "root"))
    parser.add_argument("--password", default=os.getenv("DB_PASSWORD", ""))
    parser.add_argument("--database", default=os.getenv("DB_NAME", "cocktail_graph"))

    parser.add_argument("--target", required=True, help="target ingredient name_norm, e.g., gin")
    parser.add_argument("--topk", type=int, default=20)
    parser.add_argument("--lambda_bonus", type=float, default=0.15)
    parser.add_argument("--deg_cap", type=int, default=300)
    parser.add_argument("--snapshot", default="s0", help="snapshot id, e.g., s0")

    parser.add_argument("--include_regex", default=DEFAULT_INCLUDE_REGEX)
    parser.add_argument("--exclude_regex", default=DEFAULT_EXCLUDE_REGEX)
    parser.add_argument("--prefer_regex", default=DEFAULT_PREFER_REGEX)

    parser.add_argument("--out", default="", help="optional output csv path")
    args = parser.parse_args()

    df = recommend_substitutes(
        target_name_norm=args.target,
        topk=args.topk,
        lambda_bonus=args.lambda_bonus,
        deg_cap=args.deg_cap,
        include_regex=args.include_regex,
        exclude_regex=args.exclude_regex,
        prefer_regex=args.prefer_regex,
        snapshot_id=args.snapshot,
    )

    # 展示
    if df.empty:
        print("No results. Check target_name_norm or filters.")
    else:
        print(df.to_string(index=False))

    # 可选输出
    if args.out:
        df.to_csv(args.out, index=False, encoding="utf-8-sig")
        print(f"\nSaved: {args.out}")


if __name__ == "__main__":
    main()
