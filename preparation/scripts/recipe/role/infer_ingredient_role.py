# -*- coding: utf-8 -*-
"""
鸡尾酒配方中 ingredient 在 recipe 上下文中的功能角色推断模块

功能：
1. 读取数据库表
2. 对 recipe_ingredient 的每条记录推断 role
3. 生成结果 DataFrame
4. 回写到数据库 recipe_ingredient.role 字段

角色：base_spirit, modifier, sweetener, acid, bitters, garnish, dilution, other

使用 LLM 进行角色推断，然后进行程序约束校正
"""

import os
import sys
import re
import json
import time
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv
from openai import OpenAI

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

# 加载环境变量
_llm_env = os.path.join(_root, "config", "llm.env")
load_dotenv(_llm_env)

from src.db import get_engine

# 数据库引擎
engine = get_engine()

# 配置
LLM_VERSION = "deepseek_role_inference_v1"
MODEL_NAME = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
SLEEP_SEC = float(os.getenv("SLEEP_SEC", "0.3"))

# 进度保存文件
PROGRESS_FILE = os.path.join(_root, "data", "role_inference_progress.json")

# 角色枚举
ROLES = [
    "base_spirit",
    "modifier",
    "sweetener",
    "acid",
    "bitters",
    "garnish",
    "dilution",
    "other"
]

# 系统提示
PROMPT_SYSTEM = """
You are a cocktail expert. Your task is to infer the functional role of each ingredient in a cocktail recipe context.

Roles:
- base_spirit: The primary alcoholic component that forms the foundation of the drink
- modifier: An ingredient that modifies or enhances the base spirit's flavor
- sweetener: An ingredient that adds sweetness to balance other flavors
- acid: An ingredient that adds acidity (e.g., citrus juices)
- bitters: Concentrated flavoring agents used in small quantities
- garnish: Decorative or aromatic elements added to the drink
- dilution: Ingredients that dilute the drink (e.g., soda water, tonic)
- other: Ingredients that don't fit into the above categories

Instructions:
1. Analyze the entire recipe context, not just individual ingredients
2. Consider the amount, unit, and typical usage of each ingredient
3. Return a JSON array where each item contains:
   - ingredient_id: The ID of the ingredient
   - role: One of the roles listed above
   - confidence: A float between 0.0 and 1.0 indicating your confidence
   - reason: A brief explanation for your decision
4. Ensure each ingredient has exactly one role
5. Prioritize clear, context-aware decisions
"""

# 用户提示模板
USER_TEMPLATE = """
Analyze this cocktail recipe and assign a role to each ingredient:

Recipe ID: {recipe_id}

Ingredients:
{ingredients_list}

Return JSON only in this format:
{{
  "roles": [
    {{
      "ingredient_id": 1,
      "role": "base_spirit",
      "confidence": 0.95,
      "reason": "Primary alcoholic component"
    }}
  ]
}}
"""



# =========================================================
# 辅助函数
# =========================================================
def safe_parse_amount(amount: Any) -> Optional[float]:
    """
    安全解析 amount 字段
    """
    if amount is None:
        return None
    
    try:
        # 处理字符串类型
        if isinstance(amount, str):
            # 先处理分数形式
            # 处理带整数的分数，如 "1 1/2"
            mixed_fraction_pattern = r'^\s*(\d+)\s+(\d+)/(\d+)\s*$'
            match = re.match(mixed_fraction_pattern, amount)
            if match:
                integer_part = int(match.group(1))
                numerator = int(match.group(2))
                denominator = int(match.group(3))
                return integer_part + (numerator / denominator)
            
            # 处理纯分数，如 "1/2"
            fraction_pattern = r'^\s*(\d+)/(\d+)\s*$'
            match = re.match(fraction_pattern, amount)
            if match:
                numerator = int(match.group(1))
                denominator = int(match.group(2))
                return numerator / denominator
            
            # 处理小数形式
            decimal_pattern = r'^\s*\d*\.?\d+\s*$'
            match = re.match(decimal_pattern, amount)
            if match:
                return float(amount)
            
            # 清理非数字字符后尝试转换
            cleaned_amount = re.sub(r'[^0-9.]', '', amount)
            if cleaned_amount:
                return float(cleaned_amount)
        # 处理数字类型
        elif isinstance(amount, (int, float)):
            return float(amount)
    except:
        pass
    
    return None


def normalize_text(text: Any) -> str:
    """
    规范化文本
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    return text.strip().lower()


def save_progress(processed_recipes, total_recipes):
    """
    保存处理进度
    """
    # 处理 numpy 类型，转换为 Python 原生类型
    processed_recipes = [int(rid) if hasattr(rid, 'dtype') else rid for rid in processed_recipes]
    total_recipes = int(total_recipes) if hasattr(total_recipes, 'dtype') else total_recipes
    
    progress = {
        "processed_recipes": processed_recipes,
        "total_recipes": total_recipes,
        "last_updated": time.time()
    }
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)
    print(f"进度保存到: {PROGRESS_FILE}")


def load_progress():
    """
    加载处理进度
    """
    if not os.path.exists(PROGRESS_FILE):
        return {"processed_recipes": [], "total_recipes": 0}
    
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        return progress
    except Exception as e:
        print(f"加载进度失败: {e}")
        return {"processed_recipes": [], "total_recipes": 0}


def build_recipe_context(recipe_df: pd.DataFrame) -> pd.DataFrame:
    """
    构建 recipe 上下文
    """
    df = recipe_df.copy()
    
    # 解析 amount
    df['amount_value'] = df['amount'].apply(safe_parse_amount)
    
    # 计算 amount 总和
    total_amount = df['amount_value'].sum()
    
    # 计算 amount_ratio_all
    df['amount_ratio_all'] = df['amount_value'] / total_amount if total_amount > 0 else 0
    
    # 计算 amount_rank_all（从大到小排序）
    df['amount_rank_all'] = df['amount_value'].rank(ascending=False, method='dense')
    
    return df


def call_llm(client: OpenAI, recipe_id: int, ingredients_list: str) -> List[Dict[str, Any]]:
    """
    调用 LLM 推断角色
    """
    try:
        user_content = USER_TEMPLATE.format(
            recipe_id=recipe_id,
            ingredients_list=ingredients_list
        )

        resp = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.1,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": PROMPT_SYSTEM},
                {"role": "user", "content": user_content},
            ],
        )

        raw = resp.choices[0].message.content
        data = json.loads(raw)
        roles = data.get("roles", [])
        
        return roles
    except Exception as e:
        print(f"[ERROR] LLM 调用失败: {repr(e)}")
        return []


def infer_roles_for_recipe(recipe_df: pd.DataFrame, client: OpenAI) -> pd.DataFrame:
    """
    对单个 recipe 内所有 ingredient 推断角色
    """
    # 构建上下文
    recipe_ctx_df = build_recipe_context(recipe_df)
    
    # 准备 ingredients_list
    recipe_id = recipe_ctx_df['recipe_id'].iloc[0]
    ingredients_list = []
    for _, row in recipe_ctx_df.iterrows():
        ingredient_info = f"- ingredient_id: {row['ingredient_id']}"
        ingredient_info += f", amount: {row['amount']}, unit: {row['unit']}, raw_text: {row['raw_text']}"
        ingredient_info += f", type_tag: {row.get('type_tag', 'unknown')}"
        ingredient_info += f", anchor_name: {row.get('anchor_name', 'unknown')}, anchor_form: {row.get('anchor_form', 'unknown')}"
        ingredient_info += f", flavor: sour={row.get('sour', 0)}, sweet={row.get('sweet', 0)}, bitter={row.get('bitter', 0)}, aroma={row.get('aroma', 0)}, fruity={row.get('fruity', 0)}, body={row.get('body', 0)}"
        
        # 处理 amount_ratio_all
        amount_ratio = row.get('amount_ratio_all', 0)
        if pd.isna(amount_ratio):
            amount_ratio = 0
        
        # 处理 amount_rank_all
        amount_rank = row.get('amount_rank_all', 0)
        if pd.isna(amount_rank):
            amount_rank = 0
        else:
            amount_rank = int(amount_rank)
        
        ingredient_info += f", amount_ratio: {amount_ratio:.3f}, amount_rank: {amount_rank}"
        ingredients_list.append(ingredient_info)
    ingredients_list_str = "\n".join(ingredients_list)
    
    # 调用 LLM 推断角色
    llm_roles = call_llm(client, recipe_id, ingredients_list_str)
    
    # 构建角色映射
    role_map = {}
    valid_ingredient_ids = set(recipe_ctx_df['ingredient_id'].tolist())
    
    for role_info in llm_roles:
        ingredient_id = role_info.get('ingredient_id')
        if ingredient_id not in valid_ingredient_ids:
            print(f"[WARNING] 无效的 ingredient_id: {ingredient_id}")
            continue
        
        role = role_info.get('role', 'other')
        if role not in ROLES:
            print(f"[WARNING] 无效的 role: {role}")
            role = 'other'
        
        confidence = role_info.get('confidence', 0.5)
        try:
            confidence = float(confidence)
            if not (0 <= confidence <= 1):
                print(f"[WARNING] 无效的 confidence: {confidence}")
                confidence = 0.5
        except:
            print(f"[WARNING] 无法解析 confidence: {confidence}")
            confidence = 0.5
        
        reason = role_info.get('reason', 'LLM inference')
        
        role_map[ingredient_id] = {
            "role": role,
            "confidence": confidence,
            "reason": reason
        }
    
    # 构建结果
    roles = []
    for _, row in recipe_ctx_df.iterrows():
        ingredient_id = row['ingredient_id']
        role_info = role_map.get(ingredient_id, {
            "role": "other",
            "confidence": 0.5,
            "reason": "No LLM inference result"
        })
        
        roles.append({
            "recipe_id": row['recipe_id'],
            "ingredient_id": ingredient_id,
            "line_no": row['line_no'],
            "amount": row['amount'],
            "unit": row['unit'],
            "raw_text": row['raw_text'],
            "type_tag": row['type_tag'],
            "anchor_name": row['anchor_name'],
            "anchor_form": row['anchor_form'],
            "sour": row.get('sour'),
            "sweet": row.get('sweet'),
            "bitter": row.get('bitter'),
            "aroma": row.get('aroma'),
            "fruity": row.get('fruity'),
            "body": row.get('body'),
            "role_rule": role_info["role"],
            "role_confidence": role_info["confidence"],
            "role_reason": role_info["reason"],
            "role_source": "llm_contextual_v1",
            "amount_value": row.get('amount_value'),
            "amount_ratio_all": row.get('amount_ratio_all'),
            "amount_rank_all": row.get('amount_rank_all')
        })
    
    result_df = pd.DataFrame(roles)
    
    # 关键修正规则
    # 1. 同一个 recipe 中最多只允许一个 base_spirit
    base_spirits = result_df[result_df['role_rule'] == 'base_spirit']
    if len(base_spirits) > 1:
        # 找出用量最大的
        largest_spirit_idx = base_spirits['amount_value'].idxmax()
        # 将其他 base_spirit 改为 modifier
        for idx in base_spirits.index:
            if idx != largest_spirit_idx:
                result_df.loc[idx, 'role_rule'] = "modifier"
                result_df.loc[idx, 'role_confidence'] = 0.85
                result_df.loc[idx, 'role_reason'] = "Multiple base spirits, demoted to modifier"
    
    # 2. 多个 acid 时只优先保留一个主 acid
    acids = result_df[result_df['role_rule'] == 'acid']
    if len(acids) > 1:
        # 找出用量最大的
        largest_acid_idx = acids['amount_value'].idxmax()
        # 将其他 acid 改为 modifier
        for idx in acids.index:
            if idx != largest_acid_idx:
                result_df.loc[idx, 'role_rule'] = "modifier"
                result_df.loc[idx, 'role_confidence'] = 0.80
                result_df.loc[idx, 'role_reason'] = "Multiple acids, demoted to modifier"
    
    # 3. 多个 sweetener 时优先保留一个主 sweetener
    sweeteners = result_df[result_df['role_rule'] == 'sweetener']
    if len(sweeteners) > 1:
        # 找出用量最大的
        largest_sweetener_idx = sweeteners['amount_value'].idxmax()
        # 将其他 sweetener 改为 modifier
        for idx in sweeteners.index:
            if idx != largest_sweetener_idx:
                result_df.loc[idx, 'role_rule'] = "modifier"
                result_df.loc[idx, 'role_confidence'] = 0.80
                result_df.loc[idx, 'role_reason'] = "Multiple sweeteners, demoted to modifier"
    
    return result_df


def infer_roles_all(recipes_df: pd.DataFrame) -> pd.DataFrame:
    """
    对全部 recipe 批量处理
    """
    results = []
    processed_recipes = []
    
    # 初始化 OpenAI 客户端
    client = OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    )
    
    # 加载进度
    progress = load_progress()
    already_processed = set(progress.get("processed_recipes", []))
    print(f"已处理 {len(already_processed)} 个 recipe，跳过这些 recipe")
    
    # 获取所有 recipe_id
    recipe_ids = recipes_df['recipe_id'].unique()
    total_recipes = len(recipe_ids)
    
    # 过滤掉已处理的 recipe
    remaining_recipe_ids = [rid for rid in recipe_ids if rid not in already_processed]
    remaining_count = len(remaining_recipe_ids)
    print(f"剩余 {remaining_count} 个 recipe 需要处理")
    
    # 按 recipe_id 分组处理
    for i, recipe_id in enumerate(remaining_recipe_ids, 1):
        recipe_group = recipes_df[recipes_df['recipe_id'] == recipe_id]
        ingredient_count = len(recipe_group)
        
        # 显示进度
        print(f"处理进度: {i}/{remaining_count} - Recipe {recipe_id} (包含 {ingredient_count} 个成分)")
        
        try:
            recipe_result = infer_roles_for_recipe(recipe_group, client)
            # 确保所有 ingredient 都被处理到
            if len(recipe_result) != ingredient_count:
                print(f"[WARNING] Recipe {recipe_id} 处理不完整: 期望 {ingredient_count} 个成分，实际处理 {len(recipe_result)} 个")
            results.append(recipe_result)
            
            # 添加到已处理列表
            processed_recipes.append(recipe_id)
            
            # 每处理 10 个 recipe 保存一次进度和 CSV
            if i % 10 == 0:
                all_processed = list(already_processed) + processed_recipes
                save_progress(all_processed, total_recipes)
                
                # 保存到 CSV
                if results:
                    temp_df = pd.concat(results, ignore_index=True)
                    output_csv = os.path.join(_root, "data", "ingredient_roles.csv")
                    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
                    temp_df.to_csv(output_csv, index=False, encoding='utf-8')
                    print(f"已保存 {len(temp_df)} 条记录到 CSV")
                
                print(f"已处理 {len(all_processed)}/{total_recipes} 个 recipe")
                
        except Exception as e:
            print(f"处理 recipe {recipe_id} 时出错: {e}")
            continue
    
    # 处理完成后保存最终进度
    all_processed = list(already_processed) + processed_recipes
    save_progress(all_processed, total_recipes)
    
    if not results:
        return pd.DataFrame()
    
    return pd.concat(results, ignore_index=True)


# =========================================================
# 数据加载函数
# =========================================================
def load_data() -> pd.DataFrame:
    """
    加载数据
    """
    # 加载 recipe_ingredient
    recipe_ingredient_sql = text("""
    SELECT
        recipe_id,
        ingredient_id,
        line_no,
        amount,
        unit,
        raw_text
    FROM recipe_ingredient
    """)
    
    # 加载 ingredient_type
    ingredient_type_sql = text("""
    SELECT
        ingredient_id,
        type_tag,
        confidence
    FROM ingredient_type
    """)
    
    # 加载 ingredient_flavor_feature
    flavor_feature_sql = text("""
    SELECT
        ingredient_id,
        anchor_name,
        sour,
        sweet,
        bitter,
        aroma,
        fruity,
        body,
        feature_confidence
    FROM ingredient_flavor_feature
    """)
    
    # 加载 ingredient_flavor_anchor
    flavor_anchor_sql = text("""
    SELECT
        ingredient_id,
        anchor_name,
        anchor_form,
        match_confidence
    FROM ingredient_flavor_anchor
    """)
    
    with engine.begin() as conn:
        recipe_ingredient_df = pd.read_sql(recipe_ingredient_sql, conn)
        ingredient_type_df = pd.read_sql(ingredient_type_sql, conn)
        flavor_feature_df = pd.read_sql(flavor_feature_sql, conn)
        flavor_anchor_df = pd.read_sql(flavor_anchor_sql, conn)
    
    # 合并数据
    df = recipe_ingredient_df.merge(
        ingredient_type_df, on='ingredient_id', how='left'
    )
    df = df.merge(
        flavor_feature_df, on='ingredient_id', how='left'
    )
    df = df.merge(
        flavor_anchor_df, on='ingredient_id', how='left', suffixes=('_feature', '_anchor')
    )
    
    # 处理重复的 anchor_name
    df['anchor_name'] = df['anchor_name_feature'].fillna(df['anchor_name_anchor'])
    df = df.drop(['anchor_name_feature', 'anchor_name_anchor'], axis=1)
    
    return df


# =========================================================
# 数据库更新函数
# =========================================================
def create_result_table():
    """
    创建结果表 recipe_ingredient_role_result
    """
    sql = text("""
    CREATE TABLE IF NOT EXISTS recipe_ingredient_role_result (
        recipe_id INT NOT NULL,
        ingredient_id INT NOT NULL,
        line_no INT NOT NULL,
        amount VARCHAR(255),
        unit VARCHAR(50),
        raw_text VARCHAR(255),
        type_tag VARCHAR(100),
        anchor_name VARCHAR(255),
        anchor_form VARCHAR(100),
        sour FLOAT,
        sweet FLOAT,
        bitter FLOAT,
        aroma FLOAT,
        fruity FLOAT,
        body FLOAT,
        role_rule VARCHAR(50),
        role_confidence FLOAT,
        role_reason TEXT,
        role_source VARCHAR(100),
        amount_value FLOAT,
        amount_ratio_all FLOAT,
        amount_rank_all INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (recipe_id, ingredient_id, line_no)
    )
    """)
    
    with engine.begin() as conn:
        conn.execute(sql)
    print("结果表创建完成")


def insert_role_result(row):
    """
    插入角色结果到结果表
    """
    sql = text("""
    INSERT INTO recipe_ingredient_role_result (
        recipe_id, ingredient_id, line_no, amount, unit, raw_text, type_tag, 
        anchor_name, anchor_form, sour, sweet, bitter, aroma, fruity, body, 
        role_rule, role_confidence, role_reason, role_source, 
        amount_value, amount_ratio_all, amount_rank_all
    ) VALUES (
        :recipe_id, :ingredient_id, :line_no, :amount, :unit, :raw_text, :type_tag, 
        :anchor_name, :anchor_form, :sour, :sweet, :bitter, :aroma, :fruity, :body, 
        :role_rule, :role_confidence, :role_reason, :role_source, 
        :amount_value, :amount_ratio_all, :amount_rank_all
    ) ON DUPLICATE KEY UPDATE
        role_rule = VALUES(role_rule),
        role_confidence = VALUES(role_confidence),
        role_reason = VALUES(role_reason),
        role_source = VALUES(role_source),
        updated_at = CURRENT_TIMESTAMP
    """)
    
    with engine.begin() as conn:
        conn.execute(sql, {
            "recipe_id": row['recipe_id'],
            "ingredient_id": row['ingredient_id'],
            "line_no": row['line_no'],
            "amount": row['amount'],
            "unit": row['unit'],
            "raw_text": row['raw_text'],
            "type_tag": row.get('type_tag'),
            "anchor_name": row.get('anchor_name'),
            "anchor_form": row.get('anchor_form'),
            "sour": row.get('sour'),
            "sweet": row.get('sweet'),
            "bitter": row.get('bitter'),
            "aroma": row.get('aroma'),
            "fruity": row.get('fruity'),
            "body": row.get('body'),
            "role_rule": row['role_rule'],
            "role_confidence": row['role_confidence'],
            "role_reason": row['role_reason'],
            "role_source": row['role_source'],
            "amount_value": row.get('amount_value'),
            "amount_ratio_all": row.get('amount_ratio_all'),
            "amount_rank_all": row.get('amount_rank_all')
        })


def batch_insert_roles(result_df: pd.DataFrame):
    """
    批量插入角色结果
    """
    total = len(result_df)
    for i, row in result_df.iterrows():
        if i % 100 == 0:
            print(f"插入进度: {i}/{total}")
        try:
            insert_role_result(row)
        except Exception as e:
            print(f"插入失败: recipe_id={row['recipe_id']}, ingredient_id={row['ingredient_id']}, error={e}")
    print(f"插入完成，共处理 {total} 条记录")


# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("加载数据...")
    data_df = load_data()
    print(f"加载完成，共 {len(data_df)} 条记录")
    
    print("推断角色...")
    result_df = infer_roles_all(data_df)
    print(f"推断完成，共 {len(result_df)} 条记录")
    
    # 保存结果到 CSV
    output_csv = os.path.join(_root, "data", "ingredient_roles.csv")
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    result_df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"最终结果保存到: {output_csv}")
    
    print("处理完成！")


if __name__ == "__main__":
    main()
