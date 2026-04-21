#!/usr/bin/env python3
"""
智能推荐服务
基于用户输入的各种约束条件和要求推荐酒

支持的推荐场景：
1. 基于风味偏好的推荐
2. 基于可用材料的推荐
3. 基于心情的推荐
4. 基于场合/季节的推荐
5. 复合约束条件的推荐
"""

from typing import List, Dict, Any, Optional
import sys
import os
import json

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.db.neo4j import get_neo4j_driver
from backend.db.mysql import get_mysql_connection
from config import settings
from app.services.llm_assist_service import llm_assist_service
from app.entity.extractor import EntityExtractor


class RecommendationService:
    """智能推荐服务"""
    
    def __init__(self):
        """初始化推荐服务"""
        self.entity_extractor = EntityExtractor()
        self.ingredient_mapping = self._build_ingredient_mapping()
        
        # 确保日志目录存在
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.recommendation_log_file = os.path.join(self.log_dir, "recommendation_log.txt")
        
        # 内存缓存（一级缓存）
        self.memory_cache = {}
        self.memory_cache_size = 200  # 内存缓存大小
        self.memory_cache_ttl = 3600  # 内存缓存过期时间（秒）
        
        # 心情与风味映射
        self.mood_flavor_mapping = {
            "开心": ["sweet", "fruity", "aroma"],
            "难过": ["bitter", "sour"],
            "放松": ["smooth", "aroma"],
            "兴奋": ["fruity", "sweet"],
            "疲惫": ["aroma", "smooth"],
            "焦虑": ["sour", "bitter"],
            # 添加变体映射
            "郁闷": ["bitter", "sour"],  # 映射到难过
            "烦躁": ["sour", "bitter"],  # 映射到焦虑
            "开心得": ["sweet", "fruity", "aroma"],  # 映射到开心
            "特别开心": ["sweet", "fruity", "aroma"],  # 映射到开心
        }
        
        # 场合与酒的映射
        self.occasion_mapping = {
            "聚会": ["high_energy", "fruity", "sweet"],
            "约会": ["elegant", "smooth", "aroma"],
            "晚餐": ["sophisticated", "balanced"],
            "派对": ["fun", "fruity", "sweet"],
            "安静": ["smooth", "elegant"],
            "庆祝": ["special", "sparkling"]
        }
        
        # 季节与酒的映射
        self.season_mapping = {
            "夏天": ["refreshing", "sour", "light"],
            "冬天": ["warm", "rich", "spiced"],
            "春天": ["fresh", "fruity"],
            "秋天": ["warm", "spiced", "rich"]
        }
    
    def _build_ingredient_mapping(self) -> Dict[str, List[str]]:
        """
        建立中英文材料映射
        
        Returns:
            Dict: 中文材料名到英文材料名的映射
        """
        try:
            # 从lexicon文件加载映射
            lexicon_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'lexicon.json')
            print(f"尝试加载lexicon文件: {lexicon_path}")
            print(f"文件存在: {os.path.exists(lexicon_path)}")
            
            if os.path.exists(lexicon_path):
                with open(lexicon_path, 'r', encoding='utf-8') as f:
                    lexicon = json.load(f)
                
                ingredient_lexicon = lexicon.get("ingredient", {})
                mapping = {}
                
                for chinese_name, info in ingredient_lexicon.items():
                    # 获取英文名
                    english_name = info.get("name", "")
                    if english_name:
                        if chinese_name not in mapping:
                            mapping[chinese_name] = []
                        mapping[chinese_name].append(english_name)
                    
                    # 获取别名
                    aliases = info.get("aliases", [])
                    for alias in aliases:
                        if alias not in mapping:
                            mapping[alias] = []
                        mapping[alias].append(english_name)
                
                print(f"建立了 {len(mapping)} 个中英文材料映射")
                return mapping
            else:
                print(f"lexicon文件不存在: {lexicon_path}")
            
        except Exception as e:
            print(f"建立材料映射失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 返回空映射
        return {}
    
    def _get_ingredient_mapping(self) -> Dict[str, List[str]]:
        """获取材料映射"""
        return self.ingredient_mapping
    
    def _get_current_season(self) -> str:
        """获取当前季节
        
        Returns:
            str: 当前季节 (spring, summer, autumn, winter)
        """
        import datetime
        month = datetime.datetime.now().month
        
        if 3 <= month <= 5:
            return "spring"
        elif 6 <= month <= 8:
            return "summer"
        elif 9 <= month <= 11:
            return "autumn"
        else:
            return "winter"
    
    def _get_user_preferences(self, user_id: str = "default") -> Dict:
        """获取用户偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict: 用户偏好
        """
        import json
        import os
        
        # 偏好存储文件路径
        pref_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'user_preferences.json')
        
        try:
            if os.path.exists(pref_file):
                with open(pref_file, 'r', encoding='utf-8') as f:
                    all_preferences = json.load(f)
                return all_preferences.get(user_id, {})
        except Exception as e:
            print(f"读取用户偏好失败: {e}")
        
        return {
            "flavors": [],
            "ingredients": [],
            "moods": [],
            "recent_recipes": [],
            "ratings": {}
        }
    
    def _save_user_preferences(self, user_id: str = "default", preferences: Dict = None):
        """保存用户偏好
        
        Args:
            user_id: 用户ID
            preferences: 用户偏好
        """
        import json
        import os
        
        # 偏好存储文件路径
        pref_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'user_preferences.json')
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(pref_file), exist_ok=True)
            
            # 读取现有偏好
            all_preferences = {}
            if os.path.exists(pref_file):
                with open(pref_file, 'r', encoding='utf-8') as f:
                    all_preferences = json.load(f)
            
            # 更新偏好
            all_preferences[user_id] = preferences
            
            # 保存
            with open(pref_file, 'w', encoding='utf-8') as f:
                json.dump(all_preferences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户偏好失败: {e}")
    
    def update_user_preferences(self, user_id: str = "default", recipe_id: str = None, rating: int = None, 
                               flavors: List[str] = None, ingredients: List[str] = None, mood: str = None):
        """更新用户偏好
        
        Args:
            user_id: 用户ID
            recipe_id: 食谱ID
            rating: 评分 (1-5)
            flavors: 偏好的风味
            ingredients: 偏好的材料
            mood: 偏好的心情
        """
        # 获取现有偏好
        preferences = self._get_user_preferences(user_id)
        
        # 更新评分
        if recipe_id and rating:
            preferences["ratings"][recipe_id] = rating
        
        # 更新风味偏好
        if flavors:
            for flavor in flavors:
                if flavor not in preferences["flavors"]:
                    preferences["flavors"].append(flavor)
        
        # 更新材料偏好
        if ingredients:
            for ingredient in ingredients:
                if ingredient not in preferences["ingredients"]:
                    preferences["ingredients"].append(ingredient)
        
        # 更新心情偏好
        if mood and mood not in preferences["moods"]:
            preferences["moods"].append(mood)
        
        # 更新最近推荐
        if recipe_id:
            preferences["recent_recipes"].insert(0, recipe_id)
            # 只保留最近10个
            preferences["recent_recipes"] = preferences["recent_recipes"][:10]
        
        # 保存偏好
        self._save_user_preferences(user_id, preferences)
        
        # 清除相关缓存
        self._clear_cache()
    
    def _get_cache(self, key: str) -> Any:
        """获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值
        """
        import json
        import os
        import time
        
        # 1. 尝试从内存缓存中获取（一级缓存）
        if key in self.memory_cache:
            cache_item = self.memory_cache[key]
            if time.time() - cache_item.get("timestamp", 0) < self.memory_cache_ttl:
                return cache_item.get("value")
            else:
                # 内存缓存过期，删除
                del self.memory_cache[key]
        
        # 2. 尝试从文件缓存中获取（二级缓存）
        cache_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache.json')
        
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                if key in cache_data:
                    cache_item = cache_data[key]
                    # 检查缓存是否过期（1小时）
                    if time.time() - cache_item.get("timestamp", 0) < 3600:
                        # 将文件缓存同步到内存缓存
                        self._set_memory_cache(key, cache_item.get("value"))
                        return cache_item.get("value")
        except Exception as e:
            print(f"读取缓存失败: {e}")
        
        return None
    
    def _set_memory_cache(self, key: str, value: Any):
        """设置内存缓存
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        import time
        
        # 设置内存缓存
        self.memory_cache[key] = {
            "value": value,
            "timestamp": time.time()
        }
        
        # 限制内存缓存大小
        if len(self.memory_cache) > self.memory_cache_size:
            # 按时间戳排序，删除最旧的条目
            sorted_keys = sorted(self.memory_cache.keys(), key=lambda k: self.memory_cache[k].get("timestamp", 0))
            for old_key in sorted_keys[:len(self.memory_cache) - self.memory_cache_size]:
                del self.memory_cache[old_key]
    
    def _set_cache(self, key: str, value: Any):
        """设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        import json
        import os
        import time
        
        # 1. 设置内存缓存（一级缓存）
        self._set_memory_cache(key, value)
        
        # 2. 设置文件缓存（二级缓存）
        # 缓存文件路径
        cache_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache.json')
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            
            # 读取现有缓存
            cache_data = {}
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            
            # 更新缓存
            cache_data[key] = {
                "value": value,
                "timestamp": time.time()
            }
            
            # 限制缓存大小（最多100个条目）
            if len(cache_data) > 100:
                # 删除最旧的缓存
                sorted_keys = sorted(cache_data.keys(), key=lambda k: cache_data[k].get("timestamp", 0))
                for old_key in sorted_keys[:len(cache_data) - 100]:
                    del cache_data[old_key]
            
            # 保存
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def _clear_cache(self, key: str = None):
        """清除缓存
        
        Args:
            key: 缓存键，不指定则清除所有缓存
        """
        import json
        import os
        
        # 1. 清除内存缓存
        if key:
            if key in self.memory_cache:
                del self.memory_cache[key]
        else:
            # 清除所有内存缓存
            self.memory_cache.clear()
        
        # 2. 清除文件缓存
        # 缓存文件路径
        cache_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache.json')
        
        try:
            if os.path.exists(cache_file):
                if key:
                    # 清除指定缓存
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    if key in cache_data:
                        del cache_data[key]
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                else:
                    # 清除所有缓存
                    os.remove(cache_file)
        except Exception as e:
            print(f"清除缓存失败: {e}")
    
    def _generate_cache_key(self, ingredients: List[str] = None, flavors: List[str] = None, 
                          mood: str = None, constraints: List[Dict[str, Any]] = None, 
                          user_id: str = "default") -> str:
        """生成缓存键
        
        Args:
            ingredients: 材料列表
            flavors: 风味类型列表
            mood: 心情
            constraints: 其他约束条件
            user_id: 用户ID
            
        Returns:
            str: 缓存键
        """
        import hashlib
        
        # 构建缓存键内容
        # 处理constraints，确保所有元素都是字典
        processed_constraints = []
        if constraints:
            for constraint in constraints:
                if isinstance(constraint, dict):
                    processed_constraints.append(constraint)
                elif isinstance(constraint, str):
                    processed_constraints.append({"constraint_type": "other", "text": constraint})
        
        cache_content = {
            "ingredients": sorted(ingredients) if ingredients else [],
            "flavors": sorted(flavors) if flavors else [],
            "mood": mood or "",
            "constraints": sorted(processed_constraints, key=lambda x: x.get("constraint_type", "")) if processed_constraints else [],
            "user_id": user_id
        }
        
        # 转换为字符串并哈希
        import json
        content_str = json.dumps(cache_content, ensure_ascii=False, sort_keys=True)
        hash_obj = hashlib.md5(content_str.encode('utf-8'))
        return f"recommendation:{hash_obj.hexdigest()}"
    
    def recommend(self, user_input: str, entities: List[Dict[str, Any]], constraints: List[Dict[str, Any]] = None, limit: int = 5, user_id: str = "default") -> Dict[str, Any]:
        """智能推荐
        
        Args:
            user_input: 用户输入
            entities: 识别的实体
            constraints: 约束条件列表
            limit: 推荐数量限制
            user_id: 用户ID，用于个性化推荐
            
        Returns:
            Dict: 推荐结果
        """
        try:
            # 1. 分析用户需求
            analysis_result = self._analyze_user_needs(user_input, entities, constraints)
            
            # 2. 提取所有相关信息
            ingredients = analysis_result.get("ingredients", [])
            mood = analysis_result.get("mood", "")
            flavors = analysis_result.get("flavors", [])
            other_constraints = analysis_result.get("other_constraints", [])
            
            # 提取风味类型
            flavor_types = []
            for flavor in flavors:
                if isinstance(flavor, dict):
                    flavor_type = flavor.get("flavor_type")
                    if flavor_type:
                        flavor_types.append(flavor_type)
                elif isinstance(flavor, str):
                    flavor_type = self._infer_flavor_type(flavor)
                    if flavor_type:
                        flavor_types.append(flavor_type)
            
            # 3. 生成缓存键并检查缓存
            cache_key = self._generate_cache_key(
                ingredients=ingredients,
                flavors=flavor_types,
                mood=mood,
                constraints=other_constraints,
                user_id=user_id
            )
            
            # 尝试从缓存获取结果
            cached_result = self._get_cache(cache_key)
            if cached_result:
                print("使用缓存推荐结果")
                return cached_result
            
            # 4. 使用统一查询机制获取推荐
            recommendations = self._unified_query(
                ingredients=ingredients,
                flavors=flavor_types,
                mood=mood,
                constraints=other_constraints,
                limit=limit * 3  # 多获取一些结果以便排序
            )
            
            # 4. 应用综合排序
            try:
                # 获取当前季节
                current_season = self._get_current_season()
                
                # 获取用户偏好
                user_preferences = self._get_user_preferences(user_id)
                
                # 计算综合评分并排序
                for recipe in recommendations:
                    comprehensive_score = self._calculate_comprehensive_score(
                        recipe,
                        ingredients=ingredients,
                        user_preferences=user_preferences,
                        current_season=current_season
                    )
                    recipe["comprehensive_score"] = comprehensive_score
                
                # 按综合评分排序
                recommendations.sort(key=lambda x: x.get("comprehensive_score", x.get("score", 0)) or 0, reverse=True)
            except Exception as e:
                print(f"排序失败: {e}")
                # 使用备选排序方法
                recommendations.sort(key=lambda x: (x.get("score", 0) or 0), reverse=True)
            
            # 5. 限制返回数量
            recommendations = recommendations[:limit]
            
            # 6. 构建返回结果
            result = {
                "success": True,
                "data": {
                    "recommendations": recommendations,
                    "ingredients": ingredients,
                    "mood": mood,
                    "flavors": flavor_types,
                    "constraints": other_constraints,
                    "count": len(recommendations),
                    "analysis_source": analysis_result.get("analysis_source", "hybrid")
                }
            }
            
            # 7. 缓存结果
            self._set_cache(cache_key, result)
            
            # 记录推荐结果
            self._log_recommendation(f"\n=== 推荐结果 ===")
            self._log_recommendation(f"用户输入: {user_input}")
            self._log_recommendation(f"推荐数量: {len(recommendations)}")
            for i, recipe in enumerate(recommendations, 1):
                recipe_name = recipe.get("recipe_name_zh", recipe.get("name"))
                score = recipe.get("comprehensive_score", recipe.get("score"))
                self._log_recommendation(f"{i}. {recipe_name} (评分: {score:.2f})")
            
            return result
                
        except Exception as e:
            print(f"推荐失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"推荐失败: {str(e)}"}
    
    def _analyze_user_needs(self, user_input: str, entities: List[Dict[str, Any]], constraints: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析用户需求（混合方案：硬编码 + LLM辅助）
        
        Args:
            user_input: 用户输入
            entities: 识别的实体
            constraints: 约束条件列表
            
        Returns:
            Dict: 分析结果
        """
        analysis = {
            "has_ingredients": False,
            "ingredients": [],
            "has_mood": False,
            "mood": "",
            "has_flavors": False,
            "flavors": [],
            "other_constraints": [],
            "analysis_source": "hybrid"
        }
        
        # 第一步：使用EntityExtractor提取实体（主要识别方法）
        extracted_entities = self.entity_extractor.extract(user_input)
        
        # 合并传入的实体和提取的实体
        all_entities = entities + extracted_entities
        
        # 处理实体
        for entity in all_entities:
            label = entity.get("label", "").lower()
            text = entity.get("text", "")
            
            if "ingredient" in label:
                analysis["has_ingredients"] = True
                if text not in analysis["ingredients"]:
                    analysis["ingredients"].append(text)
            elif "flavor" in label:
                analysis["has_flavors"] = True
                analysis["flavors"].append({
                    "text": text,
                    "flavor_type": entity.get("flavor_type", ""),
                    "source": "entity_extractor"
                })
        
        # 第二步：处理约束条件（硬编码）
        if constraints:
            for constraint in constraints:
                constraint_type = constraint.get("constraint_type")
                text = constraint.get("text")
                
                if constraint_type == "mood":
                    analysis["has_mood"] = True
                    analysis["mood"] = text
                elif constraint_type == "flavor":
                    analysis["has_flavors"] = True
                    analysis["flavors"].append({
                        "text": text,
                        "flavor_type": self._infer_flavor_type(text),
                        "source": "constraint"
                    })
                else:
                    analysis["other_constraints"].append(constraint)
        
        # 第三步：硬编码关键词检查（作为EntityExtractor的补充）
        user_input_lower = user_input.lower()
        
        # 检查是否包含心情词汇（硬编码）
        mood_keywords = ["开心", "难过", "放松", "兴奋", "疲惫", "焦虑", "心情", "失落", "郁闷", "烦躁", "伤心", "沮丧", "愉快", "激动", "压力", "紧张", "平静", "舒服"]
        for keyword in mood_keywords:
            if keyword in user_input_lower:
                analysis["has_mood"] = True
                analysis["mood"] = keyword
                break
        
        # 检查是否包含风味词汇（硬编码）
        flavor_keywords = ["甜", "酸", "苦", "清爽", "醇厚", "酸甜", "浓郁", "清淡", "水果味", "果味"]
        for keyword in flavor_keywords:
            if keyword in user_input_lower:
                analysis["has_flavors"] = True
                analysis["flavors"].append({
                    "text": keyword,
                    "flavor_type": self._infer_flavor_type(keyword),
                    "source": "hardcoded"
                })
        
        # 第四步：如果硬编码和EntityExtractor都无法覆盖，使用LLM辅助分析
        needs_llm_assist = False
        
        # 如果没有识别到心情，但用户输入包含情绪相关词汇，使用LLM分析
        if not analysis["has_mood"]:
            emotion_keywords = ["心情", "感觉", "情绪", "郁闷", "烦躁", "开心得", "很", "非常", "特别"]
            if any(keyword in user_input for keyword in emotion_keywords):
                needs_llm_assist = True
        
        # 如果没有识别到风味，但用户输入包含味道相关词汇，使用LLM分析
        if not analysis["has_flavors"]:
            flavor_keywords = ["味道", "口感", "风味", "有点", "很", "微", "稍微"]
            if any(keyword in user_input for keyword in flavor_keywords):
                needs_llm_assist = True
        
        # 如果没有识别到材料，但用户输入包含材料相关词汇，使用LLM分析
        if not analysis["has_ingredients"]:
            material_keywords = ["材料", "只有", "加上", "添加", "包含", "家里有"]
            if any(keyword in user_input for keyword in material_keywords):
                needs_llm_assist = True
        
        # 使用LLM辅助分析
        if needs_llm_assist:
            try:
                llm_analysis = llm_assist_service.analyze_comprehensive(user_input, all_entities)
                
                # 合并LLM分析结果
                if llm_analysis.get("has_mood") and not analysis["has_mood"]:
                    analysis["has_mood"] = True
                    analysis["mood"] = llm_analysis.get("mood", "")
                
                if llm_analysis.get("has_flavors") and not analysis["has_flavors"]:
                    analysis["has_flavors"] = True
                    analysis["flavors"] = llm_analysis.get("flavors", [])
                
                if llm_analysis.get("has_ingredients") and not analysis["has_ingredients"]:
                    analysis["has_ingredients"] = True
                    llm_ingredients = llm_analysis.get("ingredients", [])
                    for ingredient in llm_ingredients:
                        if ingredient not in analysis["ingredients"]:
                            analysis["ingredients"].append(ingredient)
                
                if llm_analysis.get("has_constraints"):
                    new_constraints = llm_analysis.get("constraints", [])
                    for constraint in new_constraints:
                        if constraint not in analysis["other_constraints"]:
                            analysis["other_constraints"].append(constraint)
                
                analysis["analysis_source"] = "hybrid_with_llm"
                
            except Exception as e:
                print(f"LLM辅助分析失败: {e}")
                # LLM失败，继续使用硬编码结果
                analysis["analysis_source"] = "hardcoded_fallback"
        
        return analysis
    
    def _recommend_by_ingredients(self, ingredients: List[str], constraints: List[Dict[str, Any]], limit: int = 5) -> Dict[str, Any]:
        """基于可用材料推荐
        
        Args:
            ingredients: 可用材料列表
            constraints: 其他约束条件
            limit: 推荐数量
            
        Returns:
            Dict: 推荐结果
        """
        try:
            if not ingredients:
                return {"success": False, "message": "未识别到可用材料"}
            
            # 建立中英文映射
            ingredient_mapping = self._build_ingredient_mapping()
            
            # 将中文材料名转换为英文
            english_ingredients = []
            for ingredient in ingredients:
                if ingredient in ingredient_mapping:
                    english_ingredients.extend(ingredient_mapping[ingredient])
                else:
                    # 如果没有映射，尝试直接使用
                    english_ingredients.append(ingredient)
            
            if not english_ingredients:
                return {"success": False, "message": "无法将材料映射到数据库"}
            
            # 从MySQL查询包含这些材料的食谱
            conn = get_mysql_connection()
            cursor = conn.cursor()
            recommendations = []
            
            try:
                # 构建查询 - 使用name_norm字段，确保包含所有材料
                # 使用INTERSECT确保食谱包含所有指定的材料
                
                if len(english_ingredients) == 1:
                    # 单个材料，简单查询
                    ingredient = english_ingredients[0]
                    query = f"""
                    SELECT DISTINCT r.recipe_id, r.name, r.recipe_name_zh, r.instructions,
                           rbf.f_sour, rbf.f_sweet, rbf.f_bitter, rbf.f_aroma, 
                           rbf.f_fruity, rbf.f_body, rbf.flavor_balance_score
                    FROM recipe_ingredient ri
                    JOIN recipe r ON ri.recipe_id = r.recipe_id
                    JOIN ingredient i ON ri.ingredient_id = i.ingredient_id
                    JOIN recipe_balance_feature rbf ON rbf.recipe_id = r.recipe_id
                    WHERE i.name_norm LIKE '%{ingredient}%'
                    ORDER BY rbf.flavor_balance_score DESC
                    LIMIT 10
                    """
                else:
                    # 多个材料，使用INTERSECT确保包含所有材料
                    ingredient_subqueries = []
                    for ingredient in english_ingredients:
                        ingredient_subqueries.append(f"""
                            SELECT ri.recipe_id
                            FROM recipe_ingredient ri
                            JOIN ingredient i ON ri.ingredient_id = i.ingredient_id
                            WHERE i.name_norm LIKE '%{ingredient}%'
                        """)
                    
                    intersect_query = " INTERSECT ".join(ingredient_subqueries)
                    
                    query = f"""
                    SELECT DISTINCT r.recipe_id, r.name, r.recipe_name_zh, r.instructions,
                           rbf.f_sour, rbf.f_sweet, rbf.f_bitter, rbf.f_aroma, 
                           rbf.f_fruity, rbf.f_body, rbf.flavor_balance_score
                    FROM recipe r
                    JOIN recipe_balance_feature rbf ON rbf.recipe_id = r.recipe_id
                    WHERE r.recipe_id IN (
                        {intersect_query}
                    )
                    ORDER BY rbf.flavor_balance_score DESC
                    LIMIT 10
                    """
                
                print(f"查询材料: {english_ingredients}")
                print(f"SQL查询: {query[:200]}...")
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                print(f"查询结果数量: {len(results)}")
                
                for row in results:
                    (recipe_id, name, recipe_name_zh, instructions, 
                     f_sour, f_sweet, f_bitter, f_aroma, f_fruity, f_body, 
                     flavor_balance_score) = row
                    
                    recipe = {
                        "recipe_id": recipe_id,
                        "name": name,
                        "recipe_name_zh": recipe_name_zh or name,
                        "instructions": instructions,
                        "flavor_profile": {
                            "sour": float(f_sour) if f_sour else 0.0,
                            "sweet": float(f_sweet) if f_sweet else 0.0,
                            "bitter": float(f_bitter) if f_bitter else 0.0,
                            "aroma": float(f_aroma) if f_aroma else 0.0,
                            "fruity": float(f_fruity) if f_fruity else 0.0,
                            "body": float(f_body) if f_body else 0.0
                        },
                        "alcohol_content": "未知",
                        "score": float(flavor_balance_score) if flavor_balance_score else 0.0
                    }
                    
                    if self._apply_constraints(recipe, constraints):
                        recommendations.append(recipe)
            
            finally:
                cursor.close()
                conn.close()
            
            # 补充MySQL中的详细信息（已经在上面的查询中获取了instructions）
            # if recommendations:
            #     recommendations = self._enrich_with_mysql(recommendations)
            
            # 排序并限制数量
            try:
                recommendations.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
            except Exception as e:
                print(f"排序失败: {e}")
                # 使用备选排序方法
                recommendations.sort(key=lambda x: (x.get("score", 0) or 0), reverse=True)
            recommendations = recommendations[:limit]
            
            return {
                "success": True,
                "data": {
                    "recommendations": recommendations,
                    "ingredients": ingredients,
                    "constraints": constraints,
                    "count": len(recommendations)
                }
            }
            
        except Exception as e:
            print(f"基于材料推荐失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"基于材料推荐失败: {str(e)}"}
    
    def _recommend_by_mood(self, mood: str, constraints: List[Dict[str, Any]], limit: int = 5) -> Dict[str, Any]:
        """基于心情推荐
        
        Args:
            mood: 心情
            constraints: 其他约束条件
            limit: 推荐数量
            
        Returns:
            Dict: 推荐结果
        """
        try:
            # 获取心情对应的风味
            flavor_types = self.mood_flavor_mapping.get(mood, ["balanced"])
            
            # 从MySQL查询
            conn = get_mysql_connection()
            cursor = conn.cursor()
            recommendations = []
            
            try:
                # 构建查询条件
                flavor_conditions = []
                flavor_mapping = {
                    "sour": "rbf.f_sour",
                    "sweet": "rbf.f_sweet", 
                    "bitter": "rbf.f_bitter",
                    "aroma": "rbf.f_aroma",
                    "fruity": "rbf.f_fruity",
                    "body": "rbf.f_body"
                }
                
                for flavor_type in flavor_types:
                    if flavor_type in flavor_mapping:
                        flavor_conditions.append(f"{flavor_mapping[flavor_type]} > 0.4")
                
                if not flavor_conditions:
                    # 如果没有有效的风味类型，返回空结果
                    return {
                        "success": True,
                        "data": {
                            "recommendations": [],
                            "mood": mood,
                            "flavor_types": flavor_types,
                            "constraints": constraints,
                            "count": 0
                        }
                    }
                
                where_clause = " OR ".join(flavor_conditions)
                
                # 查询MySQL的recipe_balance_feature表
                query = f"""
                SELECT rbf.recipe_id, r.name, r.recipe_name_zh, r.instructions,
                       rbf.f_sour, rbf.f_sweet, rbf.f_bitter, rbf.f_aroma, 
                       rbf.f_fruity, rbf.f_body, rbf.flavor_balance_score
                FROM recipe_balance_feature rbf
                JOIN recipe r ON rbf.recipe_id = r.recipe_id
                WHERE {where_clause}
                ORDER BY rbf.flavor_balance_score DESC
                LIMIT 10
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                for row in results:
                    (recipe_id, name, recipe_name_zh, instructions, 
                     f_sour, f_sweet, f_bitter, f_aroma, f_fruity, f_body, 
                     flavor_balance_score) = row
                    
                    recipe = {
                        "recipe_id": recipe_id,
                        "name": name,
                        "recipe_name_zh": recipe_name_zh or name,
                        "instructions": instructions,
                        "flavor_profile": {
                            "sour": float(f_sour) if f_sour else 0.0,
                            "sweet": float(f_sweet) if f_sweet else 0.0,
                            "bitter": float(f_bitter) if f_bitter else 0.0,
                            "aroma": float(f_aroma) if f_aroma else 0.0,
                            "fruity": float(f_fruity) if f_fruity else 0.0,
                            "body": float(f_body) if f_body else 0.0
                        },
                        "alcohol_content": "未知",
                        "score": float(flavor_balance_score) if flavor_balance_score else 0.0
                    }
                    
                    if self._apply_constraints(recipe, constraints):
                        recommendations.append(recipe)
                
            finally:
                cursor.close()
                conn.close()
            
            try:
                recommendations.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
            except Exception as e:
                print(f"排序失败: {e}")
                # 使用备选排序方法
                recommendations.sort(key=lambda x: (x.get("score", 0) or 0), reverse=True)
            recommendations = recommendations[:limit]
            
            return {
                "success": True,
                "data": {
                    "recommendations": recommendations,
                    "mood": mood,
                    "flavor_types": flavor_types,
                    "constraints": constraints,
                    "count": len(recommendations)
                }
            }
            
        except Exception as e:
            print(f"基于心情推荐失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"基于心情推荐失败: {str(e)}"}
    
    def _recommend_by_flavor(self, flavors: List[Dict[str, Any]], constraints: List[Dict[str, Any]], limit: int = 5) -> Dict[str, Any]:
        """基于风味推荐
        
        Args:
            flavors: 风味列表
            constraints: 其他约束条件
            limit: 推荐数量
            
        Returns:
            Dict: 推荐结果
        """
        try:
            flavor_types = set()
            for flavor in flavors:
                if "flavor_type" in flavor:
                    flavor_types.add(flavor["flavor_type"])
                else:
                    # 尝试从风味词推断类型
                    flavor_type = self._infer_flavor_type(flavor["text"])
                    if flavor_type:
                        flavor_types.add(flavor_type)
            
            if not flavor_types:
                return {"success": False, "message": "未识别到风味词"}
            
            # 从MySQL查询风味信息
            conn = get_mysql_connection()
            cursor = conn.cursor()
            recommendations = []
            
            try:
                # 构建查询条件
                flavor_conditions = []
                flavor_mapping = {
                    "sour": "rbf.f_sour",
                    "sweet": "rbf.f_sweet", 
                    "bitter": "rbf.f_bitter",
                    "aroma": "rbf.f_aroma",
                    "fruity": "rbf.f_fruity",
                    "body": "rbf.f_body"
                }
                
                for flavor_type in flavor_types:
                    if flavor_type in flavor_mapping:
                        flavor_conditions.append(f"{flavor_mapping[flavor_type]} > 0.3")
                
                if not flavor_conditions:
                    # 如果没有有效的风味类型，返回空结果
                    return {
                        "success": True,
                        "data": {
                            "recommendations": [],
                            "flavor_types": list(flavor_types),
                            "constraints": constraints,
                            "count": 0
                        }
                    }
                
                where_clause = " AND ".join(flavor_conditions)
                
                # 查询MySQL的recipe_balance_feature表
                query = f"""
                SELECT rbf.recipe_id, r.name, r.recipe_name_zh, r.instructions,
                       rbf.f_sour, rbf.f_sweet, rbf.f_bitter, rbf.f_aroma, 
                       rbf.f_fruity, rbf.f_body, rbf.flavor_balance_score
                FROM recipe_balance_feature rbf
                JOIN recipe r ON rbf.recipe_id = r.recipe_id
                WHERE {where_clause}
                ORDER BY rbf.flavor_balance_score DESC
                LIMIT 10
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                for row in results:
                    (recipe_id, name, recipe_name_zh, instructions, 
                     f_sour, f_sweet, f_bitter, f_aroma, f_fruity, f_body, 
                     flavor_balance_score) = row
                    
                    recipe = {
                        "recipe_id": recipe_id,
                        "name": name,
                        "recipe_name_zh": recipe_name_zh or name,
                        "instructions": instructions,
                        "flavor_profile": {
                            "sour": float(f_sour) if f_sour else 0.0,
                            "sweet": float(f_sweet) if f_sweet else 0.0,
                            "bitter": float(f_bitter) if f_bitter else 0.0,
                            "aroma": float(f_aroma) if f_aroma else 0.0,
                            "fruity": float(f_fruity) if f_fruity else 0.0,
                            "body": float(f_body) if f_body else 0.0
                        },
                        "alcohol_content": "未知",
                        "score": float(flavor_balance_score) if flavor_balance_score else 0.0
                    }
                    
                    if self._apply_constraints(recipe, constraints):
                        recommendations.append(recipe)
                
            finally:
                cursor.close()
                conn.close()
            
            try:
                recommendations.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
            except Exception as e:
                print(f"排序失败: {e}")
                # 使用备选排序方法
                recommendations.sort(key=lambda x: (x.get("score", 0) or 0), reverse=True)
            recommendations = recommendations[:limit]
            
            return {
                "success": True,
                "data": {
                    "recommendations": recommendations,
                    "flavor_types": list(flavor_types),
                    "constraints": constraints,
                    "count": len(recommendations)
                }
            }
            
        except Exception as e:
            print(f"基于风味推荐失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"基于风味推荐失败: {str(e)}"}
    
    def _recommend_by_constraints(self, constraints: List[Dict[str, Any]], limit: int = 5) -> Dict[str, Any]:
        """基于约束条件推荐
        
        Args:
            constraints: 约束条件
            limit: 推荐数量
            
        Returns:
            Dict: 推荐结果
        """
        try:
            # 从MySQL查询热门食谱
            conn = get_mysql_connection()
            cursor = conn.cursor()
            recommendations = []
            
            try:
                # 查询MySQL的recipe_balance_feature表
                query = """
                SELECT rbf.recipe_id, r.name, r.recipe_name_zh, r.instructions,
                       rbf.f_sour, rbf.f_sweet, rbf.f_bitter, rbf.f_aroma, 
                       rbf.f_fruity, rbf.f_body, rbf.flavor_balance_score
                FROM recipe_balance_feature rbf
                JOIN recipe r ON rbf.recipe_id = r.recipe_id
                ORDER BY rbf.flavor_balance_score DESC
                LIMIT 15
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                for row in results:
                    (recipe_id, name, recipe_name_zh, instructions, 
                     f_sour, f_sweet, f_bitter, f_aroma, f_fruity, f_body, 
                     flavor_balance_score) = row
                    
                    recipe = {
                        "recipe_id": recipe_id,
                        "name": name,
                        "recipe_name_zh": recipe_name_zh or name,
                        "instructions": instructions,
                        "flavor_profile": {
                            "sour": float(f_sour) if f_sour else 0.0,
                            "sweet": float(f_sweet) if f_sweet else 0.0,
                            "bitter": float(f_bitter) if f_bitter else 0.0,
                            "aroma": float(f_aroma) if f_aroma else 0.0,
                            "fruity": float(f_fruity) if f_fruity else 0.0,
                            "body": float(f_body) if f_body else 0.0
                        },
                        "alcohol_content": "未知",
                        "score": float(flavor_balance_score) if flavor_balance_score else 0.0
                    }
                    
                    if self._apply_constraints(recipe, constraints):
                        recommendations.append(recipe)
                
            finally:
                cursor.close()
                conn.close()
            
            try:
                recommendations.sort(key=lambda x: x.get("score", 0) or 0, reverse=True)
            except Exception as e:
                print(f"排序失败: {e}")
                # 使用备选排序方法
                recommendations.sort(key=lambda x: (x.get("score", 0) or 0), reverse=True)
            recommendations = recommendations[:limit]
            
            return {
                "success": True,
                "data": {
                    "recommendations": recommendations,
                    "constraints": constraints,
                    "count": len(recommendations)
                }
            }
            
        except Exception as e:
            print(f"基于约束条件推荐失败: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"基于约束条件推荐失败: {str(e)}"}
    
    def _calculate_ingredient_score(self, record: Dict[str, Any], ingredients: List[str]) -> float:
        """计算材料匹配得分
        
        Args:
            record: 食谱记录
            ingredients: 可用材料
            
        Returns:
            float: 得分
        """
        # 基础得分：流行度和评分
        base_score = record.get("popularity", 0) * 0.7 + record.get("rating", 0) * 0.3
        
        # 材料匹配加分
        # 这里简化处理，实际应该查询食谱包含的材料
        match_score = len(ingredients) * 0.2
        
        return base_score + match_score
    
    def _calculate_mood_score(self, record: Dict[str, Any], flavor_types: List[str]) -> float:
        """计算心情匹配得分
        
        Args:
            record: 食谱记录
            flavor_types: 风味类型
            
        Returns:
            float: 得分
        """
        score = 0.0
        weight = 1.0 / len(flavor_types)
        
        for flavor_type in flavor_types:
            score += record.get(flavor_type, 0) * weight
        
        # 考虑流行度和评分
        score = score * 0.7 + (record.get("popularity", 0) * 0.2 + record.get("rating", 0) * 0.1)
        
        return score
    
    def _calculate_flavor_score(self, record: Dict[str, Any], flavor_types: set) -> float:
        """计算风味匹配得分
        
        Args:
            record: 食谱记录
            flavor_types: 风味类型
            
        Returns:
            float: 得分
        """
        score = 0.0
        weight = 1.0 / len(flavor_types)
        
        for flavor_type in flavor_types:
            score += record.get(flavor_type, 0) * weight
        
        # 考虑流行度和评分
        score = score * 0.7 + (record.get("popularity", 0) * 0.2 + record.get("rating", 0) * 0.1)
        
        return score
    
    def _apply_constraints(self, recipe: Dict[str, Any], constraints: List[Dict[str, Any]]) -> bool:
        """应用约束条件过滤
        
        Args:
            recipe: 食谱信息
            constraints: 约束条件列表
            
        Returns:
            bool: 是否满足所有约束条件
        """
        if not constraints:
            return True
        
        # 确保constraints是列表
        if isinstance(constraints, str):
            constraints = [{"constraint_type": "other", "text": constraints, "priority": 1}]
        elif not isinstance(constraints, list):
            constraints = []
        
        # 处理constraints，确保所有元素都是字典
        processed_constraints = []
        for constraint in constraints:
            if isinstance(constraint, dict):
                processed_constraints.append(constraint)
            elif isinstance(constraint, str):
                processed_constraints.append({"constraint_type": "other", "text": constraint, "priority": 1})
        
        # 按优先级排序，优先级高的约束先处理
        processed_constraints.sort(key=lambda x: x.get("priority", 1), reverse=True)
        
        for constraint in processed_constraints:
            # 确保constraint是字典
            if not isinstance(constraint, dict):
                continue
                
            constraint_type = constraint.get("constraint_type")
            constraint_text = constraint.get("text")
            priority = constraint.get("priority", 1)
            
            # 1. 酒精含量约束
            if constraint_type == "alcohol":
                alcohol_content = recipe.get("alcohol_content", "")
                if "无酒精" in constraint_text and "无酒精" not in str(alcohol_content):
                    return False
                elif "低度" in constraint_text and isinstance(alcohol_content, (int, float)) and alcohol_content > 15:
                    return False
                elif "高度" in constraint_text and isinstance(alcohol_content, (int, float)) and alcohol_content < 30:
                    return False
                elif "中度" in constraint_text:
                    if isinstance(alcohol_content, (int, float)):
                        if alcohol_content < 15 or alcohol_content > 30:
                            return False
            
            # 2. 风味约束
            elif constraint_type == "flavor":
                flavor_profile = recipe.get("flavor_profile", {})
                
                # 处理复杂风味描述
                if "酸甜适中" in constraint_text:
                    sour = flavor_profile.get("sour", 0)
                    sweet = flavor_profile.get("sweet", 0)
                    if abs(sour - sweet) > 0.2:
                        return False
                elif "酸甜" in constraint_text:
                    sour = flavor_profile.get("sour", 0)
                    sweet = flavor_profile.get("sweet", 0)
                    if sour < 0.3 or sweet < 0.3:
                        return False
                elif "苦甜" in constraint_text:
                    bitter = flavor_profile.get("bitter", 0)
                    sweet = flavor_profile.get("sweet", 0)
                    if bitter < 0.3 or sweet < 0.3:
                        return False
                elif "清爽" in constraint_text:
                    sour = flavor_profile.get("sour", 0)
                    aroma = flavor_profile.get("aroma", 0)
                    if sour < 0.3 or aroma < 0.3:
                        return False
                elif "浓郁" in constraint_text:
                    body = flavor_profile.get("body", 0)
                    if body < 0.4:
                        return False
                
                # 处理具体风味类型
                flavor_keywords = {
                    "酸": "sour",
                    "甜": "sweet",
                    "苦": "bitter",
                    "香": "aroma",
                    "果香": "fruity",
                    "醇厚": "body"
                }
                
                for keyword, flavor_type in flavor_keywords.items():
                    if keyword in constraint_text:
                        if flavor_profile.get(flavor_type, 0) < 0.3:
                            return False
            
            # 3. 材料约束
            elif constraint_type == "ingredient":
                ingredient = constraint.get("value", constraint_text)
                if ingredient:
                    recipe_instructions = str(recipe.get("instructions", ""))
                    # 检查中文材料
                    if ingredient not in recipe_instructions:
                        # 检查英文材料
                        if ingredient in self.ingredient_mapping:
                            english_ingredients = self.ingredient_mapping[ingredient]
                            found = False
                            for eng_ingredient in english_ingredients:
                                if eng_ingredient.lower() in recipe_instructions.lower():
                                    found = True
                                    break
                            if not found:
                                return False
                        else:
                            return False
            
            # 4. 场合约束
            elif constraint_type == "occasion":
                occasion_keywords = {
                    "派对": ["party", "celebration", "festive"],
                    "约会": ["date", "romantic", "intimate"],
                    "放松": ["relax", "chill", "calm"],
                    "工作": ["work", "professional", "light"]
                }
                
                recipe_text = str(recipe.get("instructions", "")) + " " + str(recipe.get("name", ""))
                
                for occasion, keywords in occasion_keywords.items():
                    if occasion in constraint_text:
                        found = False
                        for keyword in keywords:
                            if keyword.lower() in recipe_text.lower():
                                found = True
                                break
                        if not found:
                            return False
            
            # 5. 时间/季节约束
            elif constraint_type == "time":
                current_season = self._get_current_season()
                season_keywords = {
                    "spring": ["fresh", "bloom", "light"],
                    "summer": ["refreshing", "cool", "citrus"],
                    "autumn": ["warm", "spice", "harvest"],
                    "winter": ["cozy", "rich", "warm"]
                }
                
                recipe_text = str(recipe.get("instructions", "")) + " " + str(recipe.get("name", ""))
                keywords = season_keywords.get(current_season, [])
                
                found = False
                for keyword in keywords:
                    if keyword.lower() in recipe_text.lower():
                        found = True
                        break
                if not found:
                    return False
            
            # 6. 其他约束
            elif constraint_type == "other":
                # 处理通用约束
                if "简单" in constraint_text:
                    instructions = str(recipe.get("instructions", ""))
                    if len(instructions) > 200:
                        return False
                elif "复杂" in constraint_text:
                    instructions = str(recipe.get("instructions", ""))
                    if len(instructions) < 150:
                        return False
        
        return True
    
    def _calculate_comprehensive_score(self, recipe: Dict[str, Any], ingredients: List[str] = None, 
                                      user_preferences: Dict = None, current_season: str = None) -> float:
        """计算综合评分
        
        Args:
            recipe: 食谱信息
            ingredients: 用户提供的材料列表
            user_preferences: 用户偏好
            current_season: 当前季节
            
        Returns:
            float: 综合评分
        """
        # 基础评分
        base_score = recipe.get("score", 0) or 0
        
        # 1. 材料匹配度评分 (0-0.3)
        ingredient_score = 0.0
        if ingredients and len(ingredients) > 0:
            matched_count = 0
            recipe_instructions = str(recipe.get("instructions", ""))
            
            for ingredient in ingredients:
                # 检查中文材料
                if ingredient in recipe_instructions:
                    matched_count += 1
                # 检查英文材料
                if ingredient in self.ingredient_mapping:
                    english_ingredients = self.ingredient_mapping[ingredient]
                    for eng_ingredient in english_ingredients:
                        if eng_ingredient.lower() in recipe_instructions.lower():
                            matched_count += 1
                            break
            
            if len(ingredients) > 0:
                ingredient_score = (matched_count / len(ingredients)) * 0.3
        
        # 2. 季节匹配度评分 (0-0.2)
        season_score = 0.0
        if current_season:
            season_flavors = {
                "spring": ["fresh", "fruity", "light"],
                "summer": ["refreshing", "sour", "light"],
                "autumn": ["warm", "spiced", "rich"],
                "winter": ["warm", "rich", "spiced"]
            }
            
            season_keywords = season_flavors.get(current_season, [])
            recipe_text = str(recipe.get("instructions", "")) + " " + str(recipe.get("name", ""))
            
            for keyword in season_keywords:
                if keyword.lower() in recipe_text.lower():
                    season_score += 0.05
            
            season_score = min(season_score, 0.2)
        
        # 3. 风味平衡评分 (0-0.2)
        flavor_profile = recipe.get("flavor_profile", {})
        flavor_values = [v for v in flavor_profile.values() if isinstance(v, (int, float))]
        flavor_balance_score = 0.0
        
        if flavor_values:
            avg_flavor = sum(flavor_values) / len(flavor_values)
            variance = sum((v - avg_flavor) ** 2 for v in flavor_values) / len(flavor_values)
            # 方差越小，平衡度越高
            flavor_balance_score = max(0, 0.2 - (variance * 0.5))
        
        # 4. 用户偏好评分 (0-0.3)
        preference_score = 0.0
        if user_preferences:
            # 偏好的风味
            preferred_flavors = user_preferences.get("flavors", [])
            for flavor in preferred_flavors:
                if flavor in flavor_profile:
                    preference_score += flavor_profile[flavor] * 0.1
            
            # 偏好的材料
            preferred_ingredients = user_preferences.get("ingredients", [])
            for ingredient in preferred_ingredients:
                if ingredient in str(recipe.get("instructions", "")):
                    preference_score += 0.1
            
            preference_score = min(preference_score, 0.3)
        
        # 综合评分
        comprehensive_score = base_score + ingredient_score + season_score + flavor_balance_score + preference_score
        
        return comprehensive_score
    
    def _unified_query(self, ingredients: List[str] = None, flavors: List[str] = None, mood: str = None, 
                      constraints: List[Dict[str, Any]] = None, limit: int = 15) -> List[Dict[str, Any]]:
        """统一查询机制
        
        Args:
            ingredients: 材料列表
            flavors: 风味类型列表
            mood: 心情
            constraints: 其他约束条件
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 食谱列表
        """
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            recommendations = []
            
            # 构建查询条件
            where_clauses = []
            
            # 处理材料约束
            if ingredients and len(ingredients) > 0:
                # 转换为英文
                english_ingredients = []
                for ingredient in ingredients:
                    if ingredient in self.ingredient_mapping:
                        english_ingredients.extend(self.ingredient_mapping[ingredient])
                    else:
                        english_ingredients.append(ingredient)
                
                if len(english_ingredients) > 0:
                    # 使用INTERSECT确保包含所有材料
                    ingredient_subqueries = []
                    for ingredient in english_ingredients:
                        ingredient_subqueries.append(f"""
                            SELECT ri.recipe_id 
                            FROM recipe_ingredient ri 
                            JOIN ingredient i ON ri.ingredient_id = i.ingredient_id 
                            WHERE i.name_norm LIKE '%{ingredient}%'
                        """)
                    
                    intersect_query = " INTERSECT ".join(ingredient_subqueries)
                    where_clauses.append(f"r.recipe_id IN ({intersect_query})")
            
            # 处理风味约束
            if flavors and len(flavors) > 0:
                flavor_mapping = {
                    "sour": "rbf.f_sour",
                    "sweet": "rbf.f_sweet", 
                    "bitter": "rbf.f_bitter",
                    "aroma": "rbf.f_aroma",
                    "fruity": "rbf.f_fruity",
                    "body": "rbf.f_body"
                }
                
                for flavor in flavors:
                    if flavor in flavor_mapping:
                        where_clauses.append(f"{flavor_mapping[flavor]} > 0.3")
            
            # 处理心情约束
            if mood:
                flavor_types = self.mood_flavor_mapping.get(mood, [])
                flavor_mapping = {
                    "sour": "rbf.f_sour",
                    "sweet": "rbf.f_sweet", 
                    "bitter": "rbf.f_bitter",
                    "aroma": "rbf.f_aroma",
                    "fruity": "rbf.f_fruity",
                    "body": "rbf.f_body"
                }
                
                mood_conditions = []
                for flavor_type in flavor_types:
                    if flavor_type in flavor_mapping:
                        mood_conditions.append(f"{flavor_mapping[flavor_type]} > 0.4")
                
                if mood_conditions:
                    where_clauses.append("(" + " OR ".join(mood_conditions) + ")")
            
            # 构建最终查询
            base_query = """
            SELECT rbf.recipe_id, r.name, r.recipe_name_zh, r.instructions,
                   rbf.f_sour, rbf.f_sweet, rbf.f_bitter, rbf.f_aroma, 
                   rbf.f_fruity, rbf.f_body, rbf.flavor_balance_score
            FROM recipe_balance_feature rbf
            JOIN recipe r ON rbf.recipe_id = r.recipe_id
            """
            
            if where_clauses:
                base_query += " WHERE " + " AND ".join(where_clauses)
            
            base_query += " ORDER BY rbf.flavor_balance_score DESC LIMIT %s"
            
            cursor.execute(base_query, (limit,))
            results = cursor.fetchall()
            
            for row in results:
                (recipe_id, name, recipe_name_zh, instructions, 
                 f_sour, f_sweet, f_bitter, f_aroma, f_fruity, f_body, 
                 flavor_balance_score) = row
                
                recipe = {
                    "recipe_id": recipe_id,
                    "name": name,
                    "recipe_name_zh": recipe_name_zh or name,
                    "instructions": instructions,
                    "flavor_profile": {
                        "sour": float(f_sour) if f_sour else 0.0,
                        "sweet": float(f_sweet) if f_sweet else 0.0,
                        "bitter": float(f_bitter) if f_bitter else 0.0,
                        "aroma": float(f_aroma) if f_aroma else 0.0,
                        "fruity": float(f_fruity) if f_fruity else 0.0,
                        "body": float(f_body) if f_body else 0.0
                    },
                    "alcohol_content": "未知",
                    "score": float(flavor_balance_score) if flavor_balance_score else 0.0
                }
                
                if self._apply_constraints(recipe, constraints):
                    recommendations.append(recipe)
            
            return recommendations
            
        except Exception as e:
            print(f"统一查询失败: {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
    
    def _enrich_with_mysql(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从MySQL补充详细信息
        
        Args:
            recommendations: 推荐结果列表
            
        Returns:
            List[Dict]: 补充后的推荐结果
        """
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            
            for recipe in recommendations:
                recipe_name = recipe.get("name")
                if recipe_name:
                    # 查询详细信息（使用正确的字段名）
                    cursor.execute("SELECT instructions FROM recipe WHERE name = %s", (recipe_name,))
                    result = cursor.fetchone()
                    if result:
                        recipe["instructions"] = result[0]
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"从MySQL补充信息失败: {e}")
        
        return recommendations
    
    def _log_recommendation(self, message: str):
        """记录推荐相关日志
        
        Args:
            message: 日志消息
        """
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        with open(self.recommendation_log_file, "a", encoding="utf-8") as f:
            f.write(f"{log_message}\n")
    
    def _infer_flavor_type(self, flavor_text: str) -> Optional[str]:
        """
        从风味词推断风味类型 (混合方案: 硬编码 + LLM辅助)
        
        Args:
            flavor_text: 风味词
            
        Returns:
            Optional[str]: 风味类型
        """
        # 第一步：硬编码映射
        flavor_mapping = {
            "酸": "sour",
            "甜": "sweet",
            "苦": "bitter",
            "香": "aroma",
            "果香": "fruity",
            "顺滑": "body",
            "清爽": "sour",
            "浓郁": "body",
            "果味": "fruity",
            "芳香": "aroma",
            "水果味": "fruity",
            "酸甜": "sweet",
            "醇厚": "body",
            "清淡": "body"
        }
        
        for key, value in flavor_mapping.items():
            if key in flavor_text:
                return value
        
        # 第二步：从配置文件获取
        flavor_terms = settings.get_flavor_terms()
        if flavor_terms:
            for flavor_type, terms in flavor_terms.items():
                if flavor_text in terms:
                    return flavor_type
        
        # 第三步：硬编码无法匹配，使用LLM分析
        try:
            llm_flavors = llm_assist_service.analyze_flavors(flavor_text, {})
            if llm_flavors and len(llm_flavors) > 0:
                return llm_flavors[0].get("flavor_type")
        except Exception as e:
            print(f"LLM推断风味类型失败: {e}")
        
        # 所有方法都失败，返回None
        return None


# 创建全局推荐服务实例
recommendation_service = RecommendationService()
