"""
将 flavor_feature_backup.jsonl 中的数据导入到 ingredient_flavor_feature 表中
并处理冗余数据：如果 anchor_name 和 anchor_form 同时完全一致，只保留一条
"""
from __future__ import annotations

import os
import sys
import json
from typing import Dict, Any, List

_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.db import get_engine
from sqlalchemy import text

# 配置
BACKUP_FILE = os.path.join(_root, "data", "flavor_feature_backup.jsonl")


def load_backup_data() -> List[Dict[str, Any]]:
    """加载 backup 文件中的数据"""
    data = []
    if not os.path.exists(BACKUP_FILE):
        print(f"备份文件不存在: {BACKUP_FILE}")
        return data
    
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                data.append(item)
            except json.JSONDecodeError as e:
                print(f"解析 JSON 错误: {e}")
                continue
    
    print(f"加载了 {len(data)} 条数据")
    return data


def deduplicate_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """去重：如果 anchor_name 和 anchor_form 同时完全一致，只保留一条"""
    seen = set()
    deduplicated = []
    
    for item in data:
        # 生成唯一键：anchor_name + anchor_form
        key = (item.get("anchor_name", ""), item.get("anchor_form", ""))
        if key not in seen:
            seen.add(key)
            deduplicated.append(item)
    
    print(f"去重后剩余 {len(deduplicated)} 条数据")
    return deduplicated


def import_to_database(data: List[Dict[str, Any]]):
    """将数据导入到 ingredient_flavor_feature 表中"""
    engine = get_engine()
    total = len(data)
    
    with engine.begin() as conn:
        for i, item in enumerate(data, 1):
            # 提取数据
            ingredient_id = item.get("ingredient_id")
            anchor_name = item.get("anchor_name")
            anchor_form = item.get("anchor_form")
            feature = item.get("feature", {})
            confidence = item.get("confidence", 0.7)
            feature_source = item.get("feature_source", "llm_anchor_only")
            reason = item.get("reason", "")
            evidence_text = item.get("evidence_text", "")
            
            # 构建 notes
            notes_parts = []
            if evidence_text:
                notes_parts.append(evidence_text)
            if reason:
                notes_parts.append("LLM reason: " + reason)
            notes = "\n\n".join(notes_parts) if notes_parts else None
            
            # 检查 ingredient_id 是否已存在
            id_exist = conn.execute(
                text("SELECT 1 FROM ingredient_flavor_feature WHERE ingredient_id = :id"),
                {"id": ingredient_id}
            ).fetchone()
            
            if id_exist:
                # 更新现有记录
                conn.execute(
                    text("""
                    UPDATE ingredient_flavor_feature SET
                    anchor_name = :anchor_name, sour = :sour, sweet = :sweet, bitter = :bitter,
                    aroma = :aroma, fruity = :fruity, body = :body,
                    feature_source = :feature_source, feature_confidence = :feature_confidence,
                    derivation_method = :derivation_method, review_status = :review_status,
                    notes = :notes, updated_at = NOW()
                    WHERE ingredient_id = :ingredient_id
                    """),
                    {
                        "ingredient_id": ingredient_id,
                        "anchor_name": anchor_name,
                        "sour": feature.get("sour", 0),
                        "sweet": feature.get("sweet", 0),
                        "bitter": feature.get("bitter", 0),
                        "aroma": feature.get("aroma", 0),
                        "fruity": feature.get("fruity", 0),
                        "body": feature.get("body", 0),
                        "feature_source": feature_source,
                        "feature_confidence": confidence,
                        "derivation_method": "LLM_inference_with_FlavorDB_context",
                        "review_status": "pending",
                        "notes": notes[:4000] if notes else None
                    }
                )
            else:
                # 插入新记录
                conn.execute(
                    text("""
                    INSERT INTO ingredient_flavor_feature
                    (ingredient_id, anchor_name, sour, sweet, bitter, aroma, fruity, body,
                     feature_source, feature_confidence, derivation_method, review_status, notes)
                    VALUES
                    (:ingredient_id, :anchor_name, :sour, :sweet, :bitter, :aroma, :fruity, :body,
                     :feature_source, :feature_confidence, :derivation_method, :review_status, :notes)
                    """),
                    {
                        "ingredient_id": ingredient_id,
                        "anchor_name": anchor_name,
                        "sour": feature.get("sour", 0),
                        "sweet": feature.get("sweet", 0),
                        "bitter": feature.get("bitter", 0),
                        "aroma": feature.get("aroma", 0),
                        "fruity": feature.get("fruity", 0),
                        "body": feature.get("body", 0),
                        "feature_source": feature_source,
                        "feature_confidence": confidence,
                        "derivation_method": "LLM_inference_with_FlavorDB_context",
                        "review_status": "pending",
                        "notes": notes[:4000] if notes else None
                    }
                )
            
            # 显示进度
            if i % 10 == 0 or i == total:
                print(f"进度: {i}/{total}")
    
    print(f"导入完成！总共 {total} 条数据")


def main():
    """主函数"""
    # 加载数据
    data = load_backup_data()
    if not data:
        print("没有数据需要导入")
        return
    
    # 直接导入所有数据，不进行去重
    print("开始导入数据到数据库...")
    import_to_database(data)
    print("数据导入完成！")


if __name__ == "__main__":
    main()
