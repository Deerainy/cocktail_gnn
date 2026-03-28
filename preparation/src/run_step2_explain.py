# src/run_step2_explain.py
from .step2_recommend import explain_step2_full

def main():
    recipe_id = 737
    topk = 20

    rows = explain_step2_full(recipe_id=recipe_id, topk=topk, min_support_cnt=1)

    print(f"recipe_id={recipe_id}, explain topk={topk}, got {len(rows)} rows (completed)")

    cur_cand = None
    for r in rows:
        if cur_cand != r["cand_id"]:
            cur_cand = r["cand_id"]
            print()
            print(f"=== {r['recommended']} (id={r['cand_id']}) score={r['score']:.12f} ===")

        # 即使无边，也会打印 co_count=0 weight=0
        print(
            f"  <- {r['evidence_base_ing']} (id={r['base_id']}) "
            f"co_count={r['co_count']} weight={r['weight']}"
        )

if __name__ == "__main__":
    main()
