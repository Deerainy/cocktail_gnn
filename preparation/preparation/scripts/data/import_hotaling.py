from __future__ import annotations

import sys
import pandas as pd

from src.db import get_engine
from src.normalize import split_ingredients, extract_ingredient_name, norm_ingredient_name
from src.loaders import SOURCE, upsert_recipe, get_recipe_id, ensure_ingredient, upsert_alias, insert_recipe_ingredient


def main(csv_path: str, limit: int | None = None):
    df = pd.read_csv(csv_path)

    COL_NAME = "Cocktail Name"
    COL_ING = "Ingredients"
    COL_INS = "Preparation"

    missing = [c for c in [COL_NAME, COL_ING] if c not in df.columns]
    if missing:
        raise RuntimeError(f"CSV 缺少列：{missing}；当前列：{df.columns.tolist()}")

    if limit is not None:
        df = df.head(limit)

    eng = get_engine()

    with eng.begin() as conn:
        for idx, row in df.iterrows():
            name = str(row[COL_NAME]).strip()
            if not name or name.lower() == "nan":
                continue

            # Kaggle 单源：用 idx + name 做稳定 key（比单用 idx 稳一些）
            source_key = f"{idx}_{name}"

            instructions = None
            if COL_INS in df.columns and pd.notna(row.get(COL_INS, None)):
                instructions = str(row[COL_INS])

            # 1) upsert recipe
            upsert_recipe(conn, source_key, name, instructions)
            recipe_id = get_recipe_id(conn, source_key)

            # 2) parse ingredients
            ing_cell = row[COL_ING]
            parts = split_ingredients(ing_cell)

            line_no = 1
            for raw_part in parts:
                raw_part = str(raw_part).strip()
                if not raw_part:
                    continue

                name_only = extract_ingredient_name(raw_part)
                name_norm = norm_ingredient_name(name_only)
                if not name_norm:
                    continue

                ingredient_id = ensure_ingredient(conn, name_norm)
                # alias 存 raw_part（含数量单位也可以，方便追溯）
                upsert_alias(conn, raw_part, ingredient_id, confidence=1.0)
                insert_recipe_ingredient(conn, recipe_id, ingredient_id, line_no, raw_text=raw_part)
                line_no += 1

    print(f"✅ 导入完成：{len(df)} rows from {csv_path} into source={SOURCE}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_hotaling.py <path_to_csv> [limit]")
        sys.exit(1)

    path = sys.argv[1]
    lim = int(sys.argv[2]) if len(sys.argv) >= 3 else None
    main(path, lim)
