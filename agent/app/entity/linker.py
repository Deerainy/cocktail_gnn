#!/usr/bin/env python3
"""
实体归一化模块

加载 entity_lexicon.json 文件和 MySQL 数据库，将抽取到的实体映射到标准实体信息

实现四个层次的匹配策略：
1. 精确匹配
2. 规范化匹配
3. 别名字典 / bilingual lexicon
4. 模糊召回 / 向量召回
"""

import os
import json
from typing import List, Dict, Any, Optional
from .utils import normalize_text, map_bilingual

# 尝试导入 RapidFuzz 用于模糊匹配
try:
    from rapidfuzz import fuzz, process
except ImportError:
    print("RapidFuzz 未安装，模糊匹配功能将不可用")
    fuzz = None

# 尝试导入 MySQL 连接模块
try:
    from app.backend.db.mysql import get_mysql_connection
    MYSQL_AVAILABLE = True
except ImportError:
    print("警告: 无法导入 MySQL 连接模块，仅使用 JSON 文件实体")
    MYSQL_AVAILABLE = False

# 资源文件路径
LEXICON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entity_lexicon.json")

# 从 mappings.py 导入风味词映射
from .mappings import FLAVOR_MAPPING

class EntityLinker:
    def __init__(self):
        """初始化实体链接器"""
        self.MYSQL_AVAILABLE = MYSQL_AVAILABLE
        self.lexicon = self._load_lexicon()
        # 构建反向映射表
        self.alias_to_canonical = self._build_alias_map()
    
    def _load_lexicon(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """加载 lexicon 文件
        
        Returns:
            Dict: 加载的 lexicon 数据
        """
        try:
            with open(LEXICON_FILE, 'r', encoding='utf-8') as f:
                lexicon = json.load(f)
            print(f"成功加载 lexicon 文件，包含 {len(lexicon.get('recipe', {}))} 个 recipe, {len(lexicon.get('ingredient', {}))} 个 ingredient, {len(lexicon.get('canonical', {}))} 个 canonical")
            
            # 从 MySQL 数据库加载实体
            if self.MYSQL_AVAILABLE:
                try:
                    conn = get_mysql_connection()
                    cursor = conn.cursor()
                    
                    # 从 ingredient 表加载食材实体
                    cursor.execute("SELECT name_norm, ingredient_id FROM ingredient")
                    ingredients = cursor.fetchall()
                    for ingredient in ingredients:
                        name = ingredient[0]
                        ingredient_id = ingredient[1]
                        if name:
                            lexicon.setdefault("ingredient", {})[name] = {
                                "entity_id": ingredient_id,
                                "normalized_name": name
                            }
                    
                    # 从 recipe 表加载食谱实体
                    cursor.execute("SELECT name, recipe_name_zh, recipe_id FROM recipe")
                    recipes = cursor.fetchall()
                    for recipe in recipes:
                        name = recipe[0]
                        recipe_name_zh = recipe[1]
                        recipe_id = recipe[2]
                        if name:
                            lexicon.setdefault("recipe", {})[name] = {
                                "entity_id": recipe_id,
                                "normalized_name": name
                            }
                        if recipe_name_zh and recipe_name_zh != name:
                            lexicon.setdefault("recipe", {})[recipe_name_zh] = {
                                "entity_id": recipe_id,
                                "normalized_name": name
                            }
                    
                    print(f"从 MySQL 数据库中添加了 {len(ingredients)} 个食材实体和 {len(recipes)} 个食谱实体")
                    
                    cursor.close()
                    conn.close()
                except Exception as e:
                    print(f"从 MySQL 数据库加载实体失败: {e}")
            
            return lexicon
        except Exception as e:
            print(f"加载 lexicon 文件失败: {e}")
            return {
                "recipe": {},
                "ingredient": {},
                "canonical": {}
            }
    
    def _build_alias_map(self) -> Dict[str, Dict[str, Any]]:
        """构建 alias 到 canonical 的反向映射表
        
        Returns:
            Dict: alias 到 canonical 的映射
        """
        alias_map = {}
        
        # 处理 canonical 实体的别名
        canonical_lexicon = self.lexicon.get("canonical", {})
        for alias, info in canonical_lexicon.items():
            alias_map[alias] = info
        
        # 处理 ingredient 实体的别名
        ingredient_lexicon = self.lexicon.get("ingredient", {})
        for ingredient, info in ingredient_lexicon.items():
            # 添加 ingredient 本身
            alias_map[ingredient] = info
            # 添加 ingredient 的别名
            aliases = info.get("aliases", [])
            for alias in aliases:
                alias_map[alias] = info
        
        # 处理 recipe 实体
        recipe_lexicon = self.lexicon.get("recipe", {})
        for recipe, info in recipe_lexicon.items():
            alias_map[recipe] = info
        
        return alias_map
    
    def _exact_match(self, text: str, label: str) -> Optional[Dict[str, Any]]:
        """精确匹配
        
        Args:
            text: 规范化后的文本
            label: 实体标签
            
        Returns:
            Optional[Dict]: 匹配到的标准化信息
        """
        # 根据标签选择对应的 lexicon
        if label == "recipe" or label == "RECIPE":
            lexicon = self.alias_to_canonical
        elif label == "ingredient" or label == "INGREDIENT":
            # 食材实体也使用 alias_to_canonical，因为它包含了食材的别名
            lexicon = self.alias_to_canonical
        elif label == "canonical" or label == "CANONICAL":
            lexicon = self.alias_to_canonical
        else:
            return None
        
        # 精确匹配
        if text in lexicon:
            return lexicon[text]
        
        return None
    
    def _bilingual_match(self, text: str) -> Optional[Dict[str, Any]]:
        """双语匹配
        
        Args:
            text: 规范化后的文本
            
        Returns:
            Optional[Dict]: 匹配到的标准化信息
        """
        # 尝试中英文映射
        mapped_text = map_bilingual(text)
        
        # 如果映射后的文本与原文本不同，尝试匹配
        if mapped_text != text:
            normalized_mapped = normalize_text(mapped_text)
            if normalized_mapped in self.alias_to_canonical:
                return self.alias_to_canonical[normalized_mapped]
        
        return None
    
    def _fuzzy_match(self, text: str, label: str) -> Optional[Dict[str, Any]]:
        """模糊匹配
        
        Args:
            text: 规范化后的文本
            label: 实体标签
            
        Returns:
            Optional[Dict]: 匹配到的标准化信息
        """
        if fuzz is None:
            return None
        
        # 根据标签选择对应的 lexicon
        if label == "recipe":
            lexicon = self.lexicon.get("recipe", {})
        elif label == "ingredient":
            lexicon = self.lexicon.get("ingredient", {})
        elif label == "canonical":
            lexicon = self.alias_to_canonical
        else:
            return None
        
        # 模糊匹配
        if lexicon:
            # 获取所有键
            keys = list(lexicon.keys())
            # 查找最相似的键
            result = process.extractOne(text, keys, scorer=fuzz.token_sort_ratio)
            if result:
                best_match, score = result[0], result[1]
            else:
                return None
            
            # 设定阈值
            if score > 80:
                return lexicon[best_match]
        
        return None
    
    def link(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """链接单个实体
        
        Args:
            entity: 抽取到的实体，包含 text 和 label 字段
            
        Returns:
            Dict: 链接后的实体，包含标准化信息
        """
        text = entity.get("text", "").strip()
        label = entity.get("label", "").lower()
        
        # 处理 FLAVOR 实体的映射
        if label == "flavor" or (label == "constraint" and entity.get("constraint_type") == "flavor"):
            # 文本规范化
            normalized_text = normalize_text(text)
            # 检查是否在风味映射字典中
            if normalized_text in FLAVOR_MAPPING:
                # 映射到基本风味维度
                mapped_flavor = FLAVOR_MAPPING[normalized_text]
                linked_entity = {
                    **entity,
                    "normalized_flavor": mapped_flavor
                }
                return linked_entity
            else:
                # 尝试模糊匹配风味词
                if fuzz is not None:
                    flavor_keys = list(FLAVOR_MAPPING.keys())
                    result = process.extractOne(normalized_text, flavor_keys, scorer=fuzz.token_sort_ratio)
                    if result:
                        best_match, score = result[0], result[1]
                        if score > 80:
                            mapped_flavor = FLAVOR_MAPPING[best_match]
                            linked_entity = {
                                **entity,
                                "normalized_flavor": mapped_flavor
                            }
                            return linked_entity
                # 如果没有找到映射，返回原实体
                return entity
        
        # 文本规范化
        normalized_text = normalize_text(text)
        
        # 第 1 层：精确匹配
        exact_match = self._exact_match(normalized_text, label)
        if exact_match:
            linked_entity = {
                **entity,
                **exact_match
            }
            return linked_entity
        
        # 第 2 层：双语匹配
        bilingual_match = self._bilingual_match(normalized_text)
        if bilingual_match:
            linked_entity = {
                **entity,
                **bilingual_match
            }
            return linked_entity
        
        # 第 3 层：模糊匹配
        fuzzy_match = self._fuzzy_match(normalized_text, label)
        if fuzzy_match:
            linked_entity = {
                **entity,
                **fuzzy_match
            }
            return linked_entity
        
        # 如果所有匹配都失败，返回原实体
        return entity
    
    def link_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """链接多个实体
        
        Args:
            entities: 抽取到的实体列表
            
        Returns:
            List[Dict]: 链接后的实体列表
        """
        linked_entities = []
        for entity in entities:
            linked_entity = self.link(entity)
            linked_entities.append(linked_entity)
        return linked_entities

# 创建全局实体链接器实例
entity_linker = EntityLinker()
