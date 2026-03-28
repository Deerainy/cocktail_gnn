from __future__ import annotations

from .step2_recommend import recommend_step2

if __name__ == "__main__":
    rid = 737
    recs = recommend_step2(recipe_id=rid, topk=20, min_support=2)

    print(f"recipe_id={rid}, got {len(recs)} recommendations")
    for r in recs:
        print(
            r["ingredient_id"],
            r["ingredient_name"],
            "score=", float(r["score"]),
            "freq=", int(r["freq"]),
            "raw=", float(r["raw_score"]),
            "evidence_co=", int(r["evidence_co"]),
            "support_cnt=", int(r["support_cnt"]),
        )
