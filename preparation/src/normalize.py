from __future__ import annotations

import re


_SPACE_RE = re.compile(r"\s+")
_PAREN_RE = re.compile(r"\([^)]*\)")

# 处理 Kaggle Hotaling 常见前缀：
#  - 数量：1, 1.5, .75, 1/2
#  - 单位：oz, ml, dash, tsp, tbsp, cup(s), part(s) ...
#  - 动作词：top, mist
_PREFIX_RE = re.compile(
    r"""^\s*
    (?:
        (\d+(\.\d+)?|\.\d+|\d+/\d+)\s*
        (oz|ounce|ounces|ml|cl|dash|dashes|tsp|tbsp|teaspoon|tablespoon|cup|cups|part|parts)?\s*
      |
        (top|mist)\s*
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def norm_ingredient_name(raw: str) -> str:
    """Normalize to a stable node name for ingredient table."""
    if raw is None:
        return ""
    s = str(raw).strip().lower()
    if not s:
        return ""
    s = _PAREN_RE.sub("", s)  # remove (...) notes
    s = s.replace("–", "-").replace("—", "-")
    s = _SPACE_RE.sub(" ", s)
    s = s.strip(" ,;.")
    return s


def split_ingredients(cell: str) -> list[str]:
    """
    Kaggle Hotaling: Ingredients 是逗号分隔的一行字符串
    e.g. '1.5 oz Mezcal, 1 oz Hibiscus Simple Syrup*, .5 oz Lime Juice,  top Soda Water'
    """
    if cell is None:
        return []
    s = str(cell).strip()
    if not s:
        return []
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]


def extract_ingredient_name(raw_part: str) -> str:
    """
    Extract ingredient name from one comma-separated chunk.
    Examples:
      '1.5 oz Mezcal' -> 'Mezcal'
      '.75 oz House-made Cranberry Syrup*' -> 'House-made Cranberry Syrup'
      '4 dash ... Bitters' -> '... Bitters'
      'top Soda Water' -> 'Soda Water'
      'mist Laphroaig' -> 'Laphroaig'
    """
    if raw_part is None:
        return ""
    s = str(raw_part).strip()
    if not s:
        return ""

    # 子配方标记：Simple Syrup* 这种，先去掉 *
    s = s.replace("*", "").strip()

    # 去掉前导“数量+单位”或“top/mist”
    s = _PREFIX_RE.sub("", s).strip()

    # 结尾清理
    s = s.strip(" -–—,;.")
    return s
