import os
import json
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入配置
from config import settings

# 尝试导入 spaCy，如果失败则提供回退实现
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    print("警告: spaCy 未安装，使用回退实现")
    SPACY_AVAILABLE = False

# 尝试导入 MySQL 连接模块
try:
    from app.backend.db.mysql import get_mysql_connection
    MYSQL_AVAILABLE = True
except ImportError:
    print("警告: 无法导入 MySQL 连接模块，仅使用 JSON 文件实体")
    MYSQL_AVAILABLE = False

# 资源文件路径
PATTERNS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entity_patterns.json")
LEXICON_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entity_lexicon.json")

# 从 mappings.py 导入通用名词
try:
    from .mappings import COMMON_NOUNS
except ImportError:
    COMMON_NOUNS = []

# 常见风味描述词
COMMON_FLAVOR_TERMS = [
    # sour 相关
    "sour", "acidic", "tart", "tangy", "citrusy", "lemony", "limey", "vinegary",
    # sweet 相关
    "sweet", "sugary", "honeyed", "syrupy", "fruity sweet", "candy-like", "dessert-like",
    # bitter 相关
    "bitter", "sharp", "astringent", "hoppy", "medicinal", "herbal bitter",
    # aroma 相关
    "aroma", "fragrant", "aromatic", "smoky", "woody", "earthy", "spicy", "herbal", "floral",
    "nutty", "vanilla", "chocolate", "coffee", "caramel", "toasty", "burnt", "smokey",
    # fruity 相关
    "fruity", "berry", "apple", "banana", "cherry", "grape", "orange", "peach", "pear",
    "pineapple", "strawberry", "watermelon", "citrus",
    # body 相关
    "body", "full-bodied", "light-bodied", "medium-bodied", "heavy", "light", "creamy",
    "rich", "smooth", "silky", "watery", "thick", "thin",
    # 中文风味词
    "酸", "甜", "苦", "香", "果香", "顺滑", "酸甜"
]

class EntityExtractor:
    def __init__(self, model_name="en_core_web_sm"):
        self.SPACY_AVAILABLE = SPACY_AVAILABLE
        self.MYSQL_AVAILABLE = MYSQL_AVAILABLE
        self.nlp = None
        
        if SPACY_AVAILABLE:
            # 尝试加载中文模型
            try:
                self.nlp = spacy.load("zh_core_web_sm")
                print("成功加载中文模型 zh_core_web_sm")
            except Exception as e:
                print(f"加载中文模型失败: {e}，使用英文模型 en_core_web_sm")
                try:
                    self.nlp = spacy.load(model_name)
                    print("成功加载英文模型 en_core_web_sm")
                except Exception as e:
                    print(f"加载英文模型失败: {e}")
                    print("使用回退实现")
        else:
            print("使用回退实现")
        
        self.patterns = self._load_patterns()
        self._add_common_flavor_terms()
        self._add_constraint_patterns()
        if SPACY_AVAILABLE and self.nlp is not None:
            self._init_ruler()

    def _load_patterns(self) -> list:
        """加载 patterns 文件
        
        Returns:
            list: 加载的 patterns 列表
        """
        try:
            with open(PATTERNS_FILE, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
            print(f"成功加载 patterns 文件，包含 {len(patterns)} 条模式")
            
            # 加载 lexicon 文件，添加食材实体
            try:
                with open(LEXICON_FILE, 'r', encoding='utf-8') as f:
                    lexicon = json.load(f)
                
                # 添加食材实体
                ingredient_lexicon = lexicon.get("ingredient", {})
                for ingredient, info in ingredient_lexicon.items():
                    # 添加食材本身
                    patterns.append({"label": "INGREDIENT", "pattern": ingredient})
                    # 添加食材的别名
                    aliases = info.get("aliases", [])
                    for alias in aliases:
                        patterns.append({"label": "INGREDIENT", "pattern": alias})
                
                # 添加规范实体
                canonical_lexicon = lexicon.get("canonical", {})
                for canonical, info in canonical_lexicon.items():
                    patterns.append({"label": "CANONICAL", "pattern": canonical})
                
                # 添加食谱实体
                recipe_lexicon = lexicon.get("recipe", {})
                for recipe, info in recipe_lexicon.items():
                    patterns.append({"label": "RECIPE", "pattern": recipe})
                
                print(f"从 lexicon 文件中添加了 {len(ingredient_lexicon) + len(canonical_lexicon) + len(recipe_lexicon)} 个实体")
            except Exception as e:
                print(f"加载 lexicon 文件失败: {e}")
            
            # 从 MySQL 数据库加载实体
            if self.MYSQL_AVAILABLE:
                try:
                    conn = get_mysql_connection()
                    cursor = conn.cursor()
                    
                    # 从 ingredient 表加载食材实体
                    cursor.execute("SELECT name_norm FROM ingredient")
                    ingredients = cursor.fetchall()
                    for ingredient in ingredients:
                        name = ingredient[0]
                        if name:
                            patterns.append({"label": "INGREDIENT", "pattern": name})
                    
                    # 从 recipe 表加载食谱实体
                    cursor.execute("SELECT name, recipe_name_zh FROM recipe")
                    recipes = cursor.fetchall()
                    for recipe in recipes:
                        name = recipe[0]
                        recipe_name_zh = recipe[1]
                        if name:
                            patterns.append({"label": "RECIPE", "pattern": name})
                        if recipe_name_zh and recipe_name_zh != name:
                            patterns.append({"label": "RECIPE", "pattern": recipe_name_zh})
                    
                    print(f"从 MySQL 数据库中添加了 {len(ingredients) + len(recipes)} 个实体")
                    
                    cursor.close()
                    conn.close()
                except Exception as e:
                    print(f"从 MySQL 数据库加载实体失败: {e}")
            
            return patterns
        except Exception as e:
            print(f"加载 patterns 文件失败: {e}")
            return []

    def _add_common_flavor_terms(self):
        """添加常见的风味描述词和通用名词到 patterns 中"""
        # 去重，避免重复添加
        existing_patterns = set()
        for pattern in self.patterns:
            existing_patterns.add(pattern.get("pattern", "").lower())
        
        # 从配置文件获取风味词和通用名词
        flavor_terms = settings.get_flavor_terms()
        common_nouns = settings.get_common_nouns()
        
        # 添加新的风味描述词
        flavor_count = 0
        noun_count = 0
        
        for term in flavor_terms:
            if term.lower() not in existing_patterns:
                self.patterns.append({"label": "FLAVOR", "pattern": term})
                flavor_count += 1
        
        # 添加通用名词
        for noun in common_nouns:
            if noun.lower() not in existing_patterns:
                self.patterns.append({"label": "NOUN", "pattern": noun})
                noun_count += 1
        
        print(f"从配置文件添加了 {flavor_count} 个风味词和 {noun_count} 个通用名词到 patterns 中")

    def _init_ruler(self):
        """初始化 EntityRuler"""
        if "entity_ruler" in self.nlp.pipe_names:
            self.nlp.remove_pipe("entity_ruler")
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        ruler.add_patterns(self.patterns)

    def extract(self, text: str):
        """提取文本中的实体
        
        Args:
            text: 待提取的文本
            
        Returns:
            list: 提取的实体列表
        """
        if SPACY_AVAILABLE and self.nlp is not None:
            try:
                doc = self.nlp(text)
                entities = []
                for ent in doc.ents:
                    entities.append({
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char
                    })
                return entities
            except Exception as e:
                print(f"实体抽取失败: {e}")
                return self._fallback_extract(text)
        else:
            # 回退实现：基于规则的实体抽取
            return self._fallback_extract(text)
    
    def _fallback_extract(self, text: str):
        """回退实体抽取实现
        
        Args:
            text: 待提取的文本
            
        Returns:
            list: 提取的实体列表
        """
        entities = []
        
        # 从 patterns 中提取实体
        for pattern in self.patterns:
            label = pattern.get("label")
            pattern_text = pattern.get("pattern")
            
            if pattern_text and pattern_text.lower() in text.lower():
                start = text.lower().find(pattern_text.lower())
                if start != -1:
                    entities.append({
                        "text": text[start:start+len(pattern_text)],
                        "label": label,
                        "start": start,
                        "end": start+len(pattern_text)
                    })
        
        # 去重
        unique_entities = []
        seen = set()
        for entity in entities:
            key = (entity["start"], entity["end"], entity["label"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        # 提取约束条件
        unique_entities = self._extract_constraints(text, unique_entities)
        
        return unique_entities
    
    def _add_constraint_patterns(self):
        """添加约束条件模式"""
        # 心情约束
        mood_patterns = [
            {"label": "CONSTRAINT", "pattern": "开心", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "难过", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "放松", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "兴奋", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "疲惫", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "焦虑", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "心情", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "失落", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "郁闷", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "烦躁", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "伤心", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "沮丧", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "愉快", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "激动", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "压力", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "紧张", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "平静", "constraint_type": "mood"},
            {"label": "CONSTRAINT", "pattern": "舒服", "constraint_type": "mood"}
        ]
        
        # 风味约束
        flavor_patterns = [
            {"label": "CONSTRAINT", "pattern": "甜", "constraint_type": "flavor"},
            {"label": "CONSTRAINT", "pattern": "酸", "constraint_type": "flavor"},
            {"label": "CONSTRAINT", "pattern": "苦", "constraint_type": "flavor"},
            {"label": "CONSTRAINT", "pattern": "清爽", "constraint_type": "flavor"},
            {"label": "CONSTRAINT", "pattern": "醇厚", "constraint_type": "flavor"},
            {"label": "CONSTRAINT", "pattern": "酸甜", "constraint_type": "flavor"},
            {"label": "CONSTRAINT", "pattern": "浓郁", "constraint_type": "flavor"},
            {"label": "CONSTRAINT", "pattern": "清淡", "constraint_type": "flavor"},
            {"label": "CONSTRAINT", "pattern": "水果味", "constraint_type": "flavor"},
            {"label": "CONSTRAINT", "pattern": "果味", "constraint_type": "flavor"}
        ]
        
        # 酒精含量约束
        alcohol_patterns = [
            {"label": "CONSTRAINT", "pattern": "无酒精", "constraint_type": "alcohol"},
            {"label": "CONSTRAINT", "pattern": "低度", "constraint_type": "alcohol"},
            {"label": "CONSTRAINT", "pattern": "高度", "constraint_type": "alcohol"},
            {"label": "CONSTRAINT", "pattern": "低酒精度", "constraint_type": "alcohol"},
            {"label": "CONSTRAINT", "pattern": "高酒精度", "constraint_type": "alcohol"}
        ]
        
        # 场合约束
        occasion_patterns = [
            {"label": "CONSTRAINT", "pattern": "聚会", "constraint_type": "occasion"},
            {"label": "CONSTRAINT", "pattern": "约会", "constraint_type": "occasion"},
            {"label": "CONSTRAINT", "pattern": "晚餐", "constraint_type": "occasion"},
            {"label": "CONSTRAINT", "pattern": "派对", "constraint_type": "occasion"},
            {"label": "CONSTRAINT", "pattern": "安静", "constraint_type": "occasion"},
            {"label": "CONSTRAINT", "pattern": "庆祝", "constraint_type": "occasion"}
        ]
        
        # 季节约束
        season_patterns = [
            {"label": "CONSTRAINT", "pattern": "夏天", "constraint_type": "time"},
            {"label": "CONSTRAINT", "pattern": "冬天", "constraint_type": "time"},
            {"label": "CONSTRAINT", "pattern": "春天", "constraint_type": "time"},
            {"label": "CONSTRAINT", "pattern": "秋天", "constraint_type": "time"}
        ]
        
        # 材料约束
        ingredient_patterns = [
            {"label": "CONSTRAINT", "pattern": "材料", "constraint_type": "ingredient"},
            {"label": "CONSTRAINT", "pattern": "只有", "constraint_type": "ingredient"},
            {"label": "CONSTRAINT", "pattern": "有", "constraint_type": "ingredient"}
        ]
        
        # 添加所有约束模式
        all_constraint_patterns = mood_patterns + flavor_patterns + alcohol_patterns + occasion_patterns + season_patterns + ingredient_patterns
        self.patterns.extend(all_constraint_patterns)
        print(f"添加了 {len(all_constraint_patterns)} 个约束条件模式")
    
    def _extract_constraints(self, text: str, entities: list) -> list:
        """提取约束条件
        
        Args:
            text: 待提取的文本
            entities: 已提取的实体列表
            
        Returns:
            list: 包含约束条件的实体列表
        """
        # 从 patterns 中提取约束条件
        for pattern in self.patterns:
            if pattern.get("label") == "CONSTRAINT":
                pattern_text = pattern.get("pattern")
                constraint_type = pattern.get("constraint_type")
                
                if pattern_text and pattern_text in text:
                    # 找到所有出现的位置
                    start = 0
                    while start < len(text):
                        start = text.find(pattern_text, start)
                        if start == -1:
                            break
                        
                        # 检查是否已存在相同的约束
                        exists = False
                        for entity in entities:
                            if (entity["label"] == "CONSTRAINT" and 
                                entity["start"] == start and 
                                entity["end"] == start + len(pattern_text)):
                                exists = True
                                break
                        
                        if not exists:
                            constraint_entity = {
                                "text": text[start:start+len(pattern_text)],
                                "label": "CONSTRAINT",
                                "constraint_type": constraint_type,
                                "start": start,
                                "end": start + len(pattern_text)
                            }
                            entities.append(constraint_entity)
                        
                        start += 1
        
        return entities
