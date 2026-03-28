from __future__ import annotations

import re
import json
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://cosylab.iiitd.edu.in"
ENTITY_SEARCH_URL = f"{BASE_URL}/flavordb2/entities"
ENTITY_DETAILS_URL = f"{BASE_URL}/flavordb2/entity_details"
FOOD_PAIRING_URL = f"{BASE_URL}/flavordb2/food_pairing"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
})


def normalize_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_id_from_href(href: str) -> Optional[int]:
    m = re.search(r"[?&]id=(\d+)", href or "")
    return int(m.group(1)) if m else None


def search_flavordb_entity_candidates(anchor_name: str) -> List[Dict[str, Any]]:
    """
    搜索实体候选。FlavorDB2 的 entities 接口返回 JSON 数组，不是 HTML。
    返回格式统一为：entity_name, entity_id, category, natural_source, detail_url
    """
    query = normalize_text(anchor_name)
    resp = SESSION.get(ENTITY_SEARCH_URL, params={"entity": query}, timeout=20)
    resp.raise_for_status()

    # 优先按 JSON 解析（FlavorDB2 返回的可能是字符串形式的 JSON，需二次解析）
    try:
        data = resp.json()
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, list) and len(data) > 0:
            candidates: List[Dict[str, Any]] = []
            for item in data:
                if not isinstance(item, dict):
                    continue
                entity_id = item.get("entity_id")
                if entity_id is None:
                    continue
                name = (item.get("entity_alias_readable") or item.get("entity_alias") or "").strip()
                if not name:
                    continue
                candidates.append({
                    "entity_name": name,
                    "entity_id": int(entity_id),
                    "category": (item.get("category_readable") or item.get("category") or ""),
                    "natural_source": (item.get("natural_source_name") or ""),
                    "detail_url": f"{BASE_URL}/flavordb2/entity_details?id={entity_id}",
                })
            return candidates
    except (json.JSONDecodeError, TypeError, KeyError):
        pass

    # 兼容：若返回的是 HTML（旧版或其它入口），按表格解析
    html = resp.text
    if "No results found" in html or "未找到您的查询结果" in html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    candidates = []

    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue
        header_cells = rows[0].find_all(["th", "td"])
        headers = [normalize_text(h.get_text(" ", strip=True)) for h in header_cells]
        if not headers or not any("entity name" in h for h in headers):
            continue
        for tr in rows[1:]:
            cells = tr.find_all("td")
            if len(cells) < 3:
                continue
            link = cells[0].find("a", href=True)
            entity_name = cells[0].get_text(" ", strip=True)
            detail_url = urljoin(BASE_URL, link["href"]) if link else None
            entity_id = extract_id_from_href(detail_url or "")
            category = cells[1].get_text(" ", strip=True) if len(cells) > 1 else ""
            natural_source = cells[2].get_text(" ", strip=True) if len(cells) > 2 else ""
            if entity_name and entity_id:
                candidates.append({
                    "entity_name": entity_name,
                    "entity_id": entity_id,
                    "category": category,
                    "natural_source": natural_source,
                    "detail_url": detail_url,
                })

    return candidates


def choose_best_entity(anchor_name: str, anchor_form: str, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    规则选最优 entity：
    1. 名称精确匹配优先
    2. 排除明显误匹配（如 grape vs grapefruit）
    3. category 合理性加分
    """
    if not candidates:
        return None

    anchor = normalize_text(anchor_name)
    form = normalize_text(anchor_form)

    def score(c: Dict[str, Any]) -> float:
        name = normalize_text(c["entity_name"])
        cat = normalize_text(c.get("category", ""))
        src = normalize_text(c.get("natural_source", ""))

        s = 0.0

        # 精确匹配
        if name == anchor:
            s += 100

        # token 匹配
        if anchor in name:
            s += 20
        if name in anchor:
            s += 10

        # 惩罚明显“包含但不是同物”
        if anchor == "grape" and "grapefruit" in name:
            s -= 80
        if anchor == "lime" and "lime oil" in name:
            s -= 20
        if anchor == "lemon" and "lemon oil" in name:
            s -= 20

        # 类别偏好
        preferred = {
            "juice": ["fruit", "fruit citrus", "flower", "herb", "vegetable"],
            "syrup": ["fruit", "flower", "herb", "spice", "vegetable"],
            "liqueur": ["fruit", "flower", "herb", "spice"],
            "spirit": ["fruit", "herb", "spice", "plant", "seed"],
            "bitters": ["spice", "herb", "fruit", "flower"],
            "fortified_wine": ["fruit", "berry", "grape"],
            "other": ["fruit", "flower", "herb", "spice", "vegetable"],
        }

        pref_list = preferred.get(form, preferred["other"])
        for p in pref_list:
            if p in cat or p in src:
                s += 8
                break

        # 避免 essential oil 优先
        if "essential oil" in cat:
            s -= 15

        # dried 不是首选
        if "dried" in name:
            s -= 10

        return s

    ranked = sorted(candidates, key=score, reverse=True)
    return ranked[0]


def get_entity_profiles(entity_id: int, top_n: int = 30) -> Dict[str, Any]:
    """
    抓 entity_details 页面，从 table#molecules 提取 Flavor Profile（及 Chem ID 等）。
    返回：entity_id, entity_name, profiles（去重 flavor 词）, molecules, detail_url
    """
    url = f"{ENTITY_DETAILS_URL}?id={entity_id}"
    resp = SESSION.get(url, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    page_text = soup.get_text(" ", strip=True)

    entity_name = None
    m = re.search(r"Flavor Molecules in\s+(.+?)(?:\s{2,}|Search:|Show)", page_text, re.I)
    if m:
        entity_name = m.group(1).strip()

    molecules: List[Dict[str, Any]] = []
    profiles: List[str] = []

    # 优先用 id="molecules" 的表（Flavor Molecules 表：Chem ID, Flavor Profile）
    table = soup.find("table", id="molecules")
    if not table:
        tables = soup.find_all("table")
    else:
        tables = [table]

    for tbl in tables:
        rows = tbl.find_all("tr")
        if not rows:
            continue
        header_cells = rows[0].find_all(["th", "td"])
        headers = [normalize_text(x.get_text(" ", strip=True)) for x in header_cells]
        if not headers:
            continue
        if not any("flavor profile" in h for h in headers):
            continue
        idx_flavor = next((i for i, h in enumerate(headers) if "flavor profile" in h), None)
        idx_id = next((i for i, h in enumerate(headers) if "chem id" in h or "common name" in h), 0)
        if idx_flavor is None:
            continue

        for tr in rows[1:]:
            cells = tr.find_all("td")
            if len(cells) <= max(idx_flavor, idx_id):
                continue
            chem_id = cells[idx_id].get_text(" ", strip=True)
            flavor_profile = cells[idx_flavor].get_text(" ", strip=True)
            pubchem_id = cells[1].get_text(" ", strip=True) if len(cells) > 1 and idx_id != 1 else chem_id

            item = {
                "common_name": chem_id,
                "pubchem_id": pubchem_id,
                "flavor_profile": flavor_profile,
            }
            molecules.append(item)
            if flavor_profile:
                profiles.append(flavor_profile)
            if len(molecules) >= top_n:
                break
        if molecules:
            break

    # 去重
    dedup_profiles = []
    seen = set()
    for p in profiles:
        p_norm = normalize_text(p)
        if p_norm and p_norm not in seen:
            seen.add(p_norm)
            dedup_profiles.append(p)

    return {
        "entity_id": entity_id,
        "entity_name": entity_name,
        "profiles": dedup_profiles,
        "molecules": molecules,
        "detail_url": url,
    }


def get_food_pairing(entity_id: int, top_n: int = 20) -> Dict[str, Any]:
    """
    抓 food_pairing 页面「Detailed Flavor Pairing Analysis」表（table#matching_entities）。
    提取：复合实体 (成分) -> entity_name，类型 -> type，共烹饪分子数量 -> shared_count。
    返回：entity_id, food_pairing_url, pairs: [{entity_name, type, shared_count}, ...]
    """
    url = f"{FOOD_PAIRING_URL}?id={entity_id}"
    resp = SESSION.get(url, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    pairs: List[Dict[str, Any]] = []

    # 优先用 id="matching_entities"（详细口味搭配分析表）
    table = soup.find("table", id="matching_entities")
    if not table:
        tables = soup.find_all("table")
    else:
        tables = [table]

    for tbl in tables:
        rows = tbl.find_all("tr")
        if not rows:
            continue
        header_cells = rows[0].find_all(["th", "td"])
        headers = [normalize_text(x.get_text(" ", strip=True)) for x in header_cells]
        if not headers:
            continue
        # 找「复合实体」/ entity 列（成分名）和「类型」/ type 列
        idx_entity = next(
            (i for i, h in enumerate(headers) if "复合实体" in h or "entity" in h or "成分" in h or "pair" in h),
            0,
        )
        idx_type = next((i for i, h in enumerate(headers) if "类型" in h or "type" in h), 1)
        idx_count = next(
            (i for i, h in enumerate(headers) if "共烹饪" in h or "molecule" in h or "count" in h or "数量" in h),
            idx_type + 1 if idx_type + 1 < len(headers) else 2,
        )

        for tr in rows[1:]:
            cells = tr.find_all("td")
            if len(cells) <= max(idx_entity, idx_type):
                continue
            entity_name = cells[idx_entity].get_text(" ", strip=True)
            type_val = cells[idx_type].get_text(" ", strip=True) if idx_type < len(cells) else ""
            shared_count = cells[idx_count].get_text(" ", strip=True) if idx_count < len(cells) else ""
            if not entity_name:
                continue
            pairs.append({
                "entity_name": entity_name,
                "type": type_val,
                "shared_count": shared_count,
                "pair_name": entity_name,  # 兼容旧字段
            })
            if len(pairs) >= top_n:
                break
        if pairs:
            break

    return {
        "entity_id": entity_id,
        "food_pairing_url": url,
        "pairs": pairs,
    }


def fetch_flavordb_evidence(anchor_name: str, anchor_form: str = "other", with_pairing: bool = False) -> Dict[str, Any]:
    """
    一站式：
    anchor_name -> 搜索候选 -> 选最优 entity -> 抓 details -> 可选 pairing
    """
    candidates = search_flavordb_entity_candidates(anchor_name)
    chosen = choose_best_entity(anchor_name, anchor_form, candidates)

    if not chosen:
        return {
            "query": anchor_name,
            "anchor_form": anchor_form,
            "matched": False,
            "candidates": candidates,
            "chosen": None,
            "details": None,
            "pairing": None,
        }

    details = get_entity_profiles(chosen["entity_id"], top_n=30)
    pairing = get_food_pairing(chosen["entity_id"], top_n=15) if with_pairing else None

    return {
        "query": anchor_name,
        "anchor_form": anchor_form,
        "matched": True,
        "candidates": candidates,
        "chosen": chosen,
        "details": details,
        "pairing": pairing,
    }


if __name__ == "__main__":
    tests = [
        ("grape", "fortified_wine"),
        ("lime", "juice"),
        ("hibiscus", "syrup"),
        ("juniper", "spirit"),
        ("agave", "spirit"),
        ("cherry", "liqueur"),
    ]

    all_results = []
    for anchor_name, anchor_form in tests:
        print(f"\n=== {anchor_name} / {anchor_form} ===")
        result = fetch_flavordb_evidence(anchor_name, anchor_form, with_pairing=False)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        all_results.append(result)

    with open("flavordb_evidence_demo.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)