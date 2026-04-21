#!/usr/bin/env python3
"""
构建实体识别资源文件

从 MySQL 数据库读取数据，生成 entity_patterns.json 和 entity_lexicon.json 文件
"""

import os
import json
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 导入配置
from app.config import settings

# 数据库连接配置
DB_CONFIG = {
    "host": settings.MYSQL_HOST,
    "port": str(settings.MYSQL_PORT),
    "user": settings.MYSQL_USER,
    "password": settings.MYSQL_PASSWORD,
    "database": settings.MYSQL_DATABASE
}

# 输出文件路径
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
PATTERNS_FILE = os.path.join(OUTPUT_DIR, "entity_patterns.json")
LEXICON_FILE = os.path.join(OUTPUT_DIR, "entity_lexicon.json")

# 从数据库读取的 FLAVOR 和 ROLE 词表
FLAVOR_DIMENSIONS = ["sour", "sweet", "bitter", "aroma", "fruity", "body"]

class EntityResourceBuilder:
    def __init__(self):
        """初始化资源构建器"""
        self.engine = None
        self.session = None
        self.patterns = []
        self.lexicon = {
            "recipe": {},
            "ingredient": {},
            "canonical": {}
        }
        self.stats = {
            "total_patterns": 0,
            "recipe_patterns": 0,
            "ingredient_patterns": 0,
            "canonical_patterns": 0,
            "flavor_patterns": 0,
            "role_patterns": 0,
            "filtered_items": 0
        }
    
    def connect_db(self):
        """连接到 MySQL 数据库"""
        try:
            connection_string = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8mb4"
            self.engine = create_engine(connection_string)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            print("成功连接到数据库")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise
    
    def close_db(self):
        """关闭数据库连接"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
    
    def is_valid_pattern(self, text):
        """检查文本是否适合作为 pattern
        
        Args:
            text: 待检查的文本
            
        Returns:
            bool: 是否适合作为 pattern
        """
        # 过滤空值和空字符串
        if not text or not text.strip():
            return False
        
        # 过滤过短的词（少于2个字符）
        if len(text.strip()) < 2:
            return False
        
        # 过滤过于通用的词
        common_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "with", "by", "from", "as", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would", "should",
            "could", "can", "may", "might", "must", "shall"
        }
        if text.strip().lower() in common_words:
            return False
        
        # 过滤包含特殊字符或路径的文本
        if re.search(r'[<>"\\/|?*]', text):
            return False
        
        # 过滤看起来像 URL 或文件路径的文本
        if re.search(r'http://|https://|www\.|\\|/', text):
            return False
        
        # 过滤包含数字和字母混合的过长文本（可能是 ID 或编码）
        if len(text) > 50 or (re.search(r'[0-9]', text) and re.search(r'[a-zA-Z]', text) and len(text) > 20):
            return False
        
        return True
    
    def process_recipe_data(self):
        """处理 recipe 表数据"""
        try:
            # 从 recipe 表读取数据
            query = text("SELECT recipe_id, name, recipe_name_zh FROM recipe")
            result = self.session.execute(query)
            
            for row in result:
                recipe_id, name, name_zh = row
                
                # 处理英文名称
                if name and self.is_valid_pattern(name):
                    self.patterns.append({"label": "RECIPE", "pattern": name.strip()})
                    self.lexicon["recipe"][name.strip().lower()] = {
                        "entity_id": recipe_id,
                        "normalized_name": name.strip()
                    }
                    self.stats["recipe_patterns"] += 1
                else:
                    self.stats["filtered_items"] += 1
                
                # 处理中文名称
                if name_zh and self.is_valid_pattern(name_zh):
                    self.patterns.append({"label": "RECIPE", "pattern": name_zh.strip()})
                    self.lexicon["recipe"][name_zh.strip().lower()] = {
                        "entity_id": recipe_id,
                        "normalized_name": name.strip() if name else name_zh.strip()
                    }
                    self.stats["recipe_patterns"] += 1
                elif name_zh:
                    self.stats["filtered_items"] += 1
                    
        except Exception as e:
            print(f"处理 recipe 数据失败: {e}")
            raise
    
    def process_ingredient_data(self):
        """处理 ingredient 数据，从 llm_canonical_map 表获取"""
        try:
            # 从 llm_canonical_map 表读取数据，只获取唯一的 ingredient
            query = text("SELECT DISTINCT src_ingredient_id, src_name_norm FROM llm_canonical_map")
            result = self.session.execute(query)
            
            for row in result:
                ingredient_id, name_norm = row
                
                # 处理 ingredient 数据 - 不进行过滤
                if name_norm and name_norm.strip():
                    self.patterns.append({"label": "INGREDIENT", "pattern": name_norm.strip()})
                    self.lexicon["ingredient"][name_norm.strip().lower()] = {
                        "entity_id": ingredient_id,
                        "normalized_name": name_norm.strip()
                    }
                    self.stats["ingredient_patterns"] += 1
                else:
                    self.stats["filtered_items"] += 1
                    
        except Exception as e:
            print(f"处理 ingredient 数据失败: {e}")
            raise
    
    def process_canonical_data(self):
        """处理 canonical 数据"""
        try:
            # 从 llm_canonical_map 表读取数据，获取 canonical 及其对应的 ingredient
            query = text("SELECT DISTINCT canonical_id, canonical_name, canonical_name_zh, src_name_norm FROM llm_canonical_map")
            result = self.session.execute(query)
            
            # 用于存储每个 canonical 的别名
            canonical_aliases = {}
            
            for row in result:
                canonical_id, canonical_name, canonical_name_zh, src_name_norm = row
                
                # 确保 canonical_id 存在
                if not canonical_id:
                    self.stats["filtered_items"] += 1
                    continue
                
                # 初始化 canonical 条目
                canonical_key = str(canonical_id)
                if canonical_key not in canonical_aliases:
                    canonical_aliases[canonical_key] = {
                        "canonical_id": canonical_id,
                        "canonical_name": canonical_name.strip() if canonical_name else "",
                        "aliases": []
                    }
                
                # 添加英文名称作为别名
                if canonical_name and canonical_name.strip():
                    alias = canonical_name.strip()
                    if alias not in canonical_aliases[canonical_key]["aliases"]:
                        canonical_aliases[canonical_key]["aliases"].append(alias)
                    self.patterns.append({"label": "CANONICAL", "pattern": alias})
                    self.stats["canonical_patterns"] += 1
                else:
                    self.stats["filtered_items"] += 1
                
                # 添加中文名称作为别名
                if canonical_name_zh and canonical_name_zh.strip():
                    alias = canonical_name_zh.strip()
                    if alias not in canonical_aliases[canonical_key]["aliases"]:
                        canonical_aliases[canonical_key]["aliases"].append(alias)
                    self.patterns.append({"label": "CANONICAL", "pattern": alias})
                    self.stats["canonical_patterns"] += 1
                elif canonical_name_zh:
                    self.stats["filtered_items"] += 1
                
                # 添加 ingredient 名称作为别名
                if src_name_norm and src_name_norm.strip():
                    alias = src_name_norm.strip()
                    if alias not in canonical_aliases[canonical_key]["aliases"]:
                        canonical_aliases[canonical_key]["aliases"].append(alias)
                    self.patterns.append({"label": "CANONICAL", "pattern": alias})
                    self.stats["canonical_patterns"] += 1
                elif src_name_norm:
                    self.stats["filtered_items"] += 1
            
            # 构建 lexicon，包含别名信息
            for canonical_key, data in canonical_aliases.items():
                canonical_name = data["canonical_name"]
                aliases = data["aliases"]
                
                # 为每个别名创建反向映射
                for alias in aliases:
                    normalized_alias = alias.strip().lower()
                    self.lexicon["canonical"][normalized_alias] = {
                        "canonical_id": data["canonical_id"],
                        "canonical_name": canonical_name,
                        "aliases": aliases
                    }
                    
        except Exception as e:
            print(f"处理 canonical 数据失败: {e}")
            raise
    
    def add_manual_patterns(self):
        """添加 FLAVOR 和 ROLE 模式"""
        # 添加 FLAVOR 维度模式
        for flavor in FLAVOR_DIMENSIONS:
            if flavor and flavor.strip():
                self.patterns.append({"label": "FLAVOR", "pattern": flavor.strip()})
                self.stats["flavor_patterns"] += 1
        
        # 从数据库读取 ROLE 模式
        try:
            # 从 recipe_ingredient 表读取角色
            query = text("SELECT DISTINCT role FROM recipe_ingredient")
            result = self.session.execute(query)
            
            for row in result:
                role = row[0]
                if role and role.strip():
                    # 将下划线替换为空格，使角色名称更易读
                    role_display = role.replace('_', ' ')
                    self.patterns.append({"label": "ROLE", "pattern": role_display})
                    self.stats["role_patterns"] += 1
        except Exception as e:
            print(f"从数据库读取 ROLE 数据失败: {e}")
        
        # 从数据库读取 FLAVOR 锚点模式
        try:
            # 从 ingredient_flavor_anchor 表读取风味锚点
            query = text("SELECT DISTINCT anchor_name FROM ingredient_flavor_anchor")
            result = self.session.execute(query)
            
            for row in result:
                flavor_anchor = row[0]
                if flavor_anchor and flavor_anchor.strip():
                    self.patterns.append({"label": "FLAVOR", "pattern": flavor_anchor.strip()})
                    self.stats["flavor_patterns"] += 1
        except Exception as e:
            print(f"从数据库读取 FLAVOR 锚点数据失败: {e}")
    
    def deduplicate_patterns(self):
        """去重 patterns"""
        seen = set()
        unique_patterns = []
        
        for pattern in self.patterns:
            key = (pattern["label"], pattern["pattern"].lower())
            if key not in seen:
                seen.add(key)
                unique_patterns.append(pattern)
        
        self.patterns = unique_patterns
        self.stats["total_patterns"] = len(self.patterns)
    
    def save_resources(self):
        """保存资源文件"""
        # 保存 patterns 文件
        with open(PATTERNS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=2)
        
        # 保存 lexicon 文件
        with open(LEXICON_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.lexicon, f, ensure_ascii=False, indent=2)
        
        print(f"\n资源文件生成成功:")
        print(f"- entity_patterns.json: {len(self.patterns)} 条模式")
        print(f"- entity_lexicon.json: 包含 {len(self.lexicon['recipe'])} 个 recipe, {len(self.lexicon['ingredient'])} 个 ingredient, {len(self.lexicon['canonical'])} 个 canonical")
    
    def print_stats(self):
        """打印统计信息"""
        print(f"\n统计信息:")
        print(f"- 总模式数: {self.stats['total_patterns']}")
        print(f"- Recipe 模式: {self.stats['recipe_patterns']}")
        print(f"- Ingredient 模式: {self.stats['ingredient_patterns']}")
        print(f"- Canonical 模式: {self.stats['canonical_patterns']}")
        print(f"- Flavor 模式: {self.stats['flavor_patterns']}")
        print(f"- Role 模式: {self.stats['role_patterns']}")
        print(f"- 过滤掉的无效项: {self.stats['filtered_items']}")
    
    def build(self):
        """构建资源文件的主方法"""
        try:
            self.connect_db()
            
            print("开始处理数据...")
            
            # 处理各表数据
            self.process_recipe_data()
            self.process_ingredient_data()
            self.process_canonical_data()
            
            # 添加手工维护的模式
            self.add_manual_patterns()
            
            # 去重
            self.deduplicate_patterns()
            
            # 保存资源文件
            self.save_resources()
            
            # 打印统计信息
            self.print_stats()
            
            print("\n资源构建完成！")
            
        finally:
            self.close_db()

if __name__ == "__main__":
    builder = EntityResourceBuilder()
    builder.build()
