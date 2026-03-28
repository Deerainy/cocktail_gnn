from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection

SOURCE = "kaggle_hotaling"


def upsert_recipe(conn: Connection, source_key: str, name: str, instructions: str | None):
    sql = """
    INSERT INTO recipe (source, source_recipe_key, name, instructions)
    VALUES (:source, :source_key, :name, :instructions)
    ON DUPLICATE KEY UPDATE
      name = VALUES(name),
      instructions = VALUES(instructions)
    """
    conn.execute(
        text(sql),
        {
            "source": SOURCE,
            "source_key": source_key,
            "name": name,
            "instructions": instructions,
        },
    )


def get_recipe_id(conn: Connection, source_key: str) -> int:
    row = conn.execute(
        text(
            """
            SELECT recipe_id
            FROM recipe
            WHERE source=:source AND source_recipe_key=:key
            """
        ),
        {"source": SOURCE, "key": source_key},
    ).fetchone()
    if row is None:
        raise RuntimeError(f"recipe_id not found for source_key={source_key}")
    return int(row[0])


def ensure_ingredient(conn: Connection, name_norm: str) -> int:
    """
    Ensure ingredient exists by name_norm (UNIQUE).
    Returns ingredient_id.
    """
    conn.execute(
        text(
            """
            INSERT INTO ingredient (name_norm)
            VALUES (:name_norm)
            ON DUPLICATE KEY UPDATE name_norm=VALUES(name_norm)
            """
        ),
        {"name_norm": name_norm},
    )

    row = conn.execute(
        text("SELECT ingredient_id FROM ingredient WHERE name_norm=:name_norm"),
        {"name_norm": name_norm},
    ).fetchone()
    if row is None:
        raise RuntimeError(f"ingredient_id not found for name_norm={name_norm}")
    return int(row[0])


def upsert_alias(conn: Connection, alias_raw: str, ingredient_id: int, confidence: float | None = None):
    """
    Map raw ingredient string (may include quantity/unit) to ingredient_id.
    For Kaggle single-source import, confidence can be 1.0.
    """
    conn.execute(
        text(
            """
            INSERT INTO ingredient_alias (source, alias_raw, ingredient_id, confidence)
            VALUES (:source, :alias_raw, :ingredient_id, :confidence)
            ON DUPLICATE KEY UPDATE
              ingredient_id = VALUES(ingredient_id),
              confidence = COALESCE(VALUES(confidence), confidence)
            """
        ),
        {
            "source": SOURCE,
            "alias_raw": alias_raw,
            "ingredient_id": ingredient_id,
            "confidence": confidence,
        },
    )


def add_unknown_alias(conn: Connection, alias_raw: str, example_recipe_key: str | None):
    """
    If you later want stricter aliasing, you can push unresolved raw strings here.
    In current Kaggle flow we usually resolve directly, so it's optional.
    """
    conn.execute(
        text(
            """
            INSERT INTO unknown_ingredient_alias (source, alias_raw, example_recipe_key, hit_count)
            VALUES (:source, :alias_raw, :example_key, 1)
            ON DUPLICATE KEY UPDATE
              hit_count = hit_count + 1,
              example_recipe_key = COALESCE(example_recipe_key, VALUES(example_recipe_key))
            """
        ),
        {"source": SOURCE, "alias_raw": alias_raw, "example_key": example_recipe_key},
    )


def insert_recipe_ingredient(conn: Connection, recipe_id: int, ingredient_id: int, line_no: int, raw_text: str | None):
    """
    Insert into fact table. Using INSERT IGNORE to avoid duplication on rerun.
    """
    conn.execute(
        text(
            """
            INSERT IGNORE INTO recipe_ingredient (recipe_id, ingredient_id, line_no, raw_text)
            VALUES (:recipe_id, :ingredient_id, :line_no, :raw_text)
            """
        ),
        {
            "recipe_id": recipe_id,
            "ingredient_id": ingredient_id,
            "line_no": line_no,
            "raw_text": raw_text,
        },
    )
