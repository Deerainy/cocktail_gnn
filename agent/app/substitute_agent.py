"""
替代推荐智能体

专注于处理用户关于替代推荐的问题，如“这个 recipe 里 lime juice 可以换成什么？”、“如果没有 gin，有什么替代建议？”等
"""

import re
from typing import Dict, Any, Optional
from app.tools.backend_graph_tools import backend_graph_tools
from app.intent_router import intent_router
from app.entity_recognizer import entity_recognizer


class SubstituteAgent:
    def __init__(self):
        """初始化替代推荐智能体"""
        pass

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        处理用户的查询
        Args:
            query: 用户的查询
        Returns: 处理结果
        """
        # 识别用户查询中的实体
        entity_result = entity_recognizer.recognize(query)
        entities = entity_result.get("entities", {})
        recipe_entities = entities.get("RECIPE", [])
        ingredient_entities = entities.get("INGREDIENT", [])
        
        # 分类用户意图
        intent_result = intent_router.classify(query)
        intent = intent_result["intent"]
        
        # 根据意图和识别到的实体处理查询
        if intent == "substitute_recommendation":
            return self.handle_substitute_recommendation(query, ingredient_entities)
        elif intent == "recipe_search":
            return self.handle_recipe_search(query, recipe_entities)
        elif intent == "recipe_structure":
            return self.handle_recipe_structure(query, recipe_entities)
        elif intent == "ingredient_neighbors":
            return self.handle_ingredient_neighbors(query, ingredient_entities)
        else:
            return self.handle_general_chat(query)

    def handle_substitute_recommendation(self, query: str, ingredient_entities: list) -> Dict[str, Any]:
        """
        处理替代推荐问题
        Args:
            query: 用户的查询
            ingredient_entities: 识别到的食材实体列表
        Returns: 处理结果
        """
        # 优先使用实体识别器识别到的食材实体
        if ingredient_entities:
            ingredient_name = ingredient_entities[0]
        else:
            # 回退到传统的提取方法
            ingredient_name = self.extract_ingredient_name(query)
        
        if not ingredient_name:
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": "抱歉，我没有识别出您提到的食材名称，请尝试更明确地表达您的问题。"
            }
        
        # 搜索规范食材
        search_result = backend_graph_tools.search_canonical(ingredient_name)
        
        if not search_result["success"] or not search_result["data"]:
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": f"抱歉，我没有找到与 '{ingredient_name}' 相关的食材信息。"
            }
        
        # 获取第一个匹配的规范食材
        canonical = search_result["data"][0]
        canonical_id = canonical["id"]
        
        # 获取全局替代候选
        substitutes_result = backend_graph_tools.get_global_substitutes(canonical_id)
        
        if not substitutes_result["success"] or not substitutes_result["data"].get("candidates"):
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": f"抱歉，我没有找到与 '{ingredient_name}' 相关的替代建议。"
            }
        
        # 构建响应
        candidates = substitutes_result["data"]["candidates"]
        substitute_names = [candidate["canonical"]["name"] for candidate in candidates[:3]]
        substitute_list = ", ".join(substitute_names)
        
        return {
            "success": True,
            "data": {
                "ingredient": ingredient_name,
                "substitutes": substitute_names,
                "full_result": substitutes_result["data"]
            },
            "source": "substitute_agent",
            "message": f"{ingredient_name} 的替代建议有：{substitute_list}。"
        }

    def handle_recipe_search(self, query: str, recipe_entities: list) -> Dict[str, Any]:
        """
        处理食谱搜索问题
        Args:
            query: 用户的查询
            recipe_entities: 识别到的食谱实体列表
        Returns: 处理结果
        """
        # 优先使用实体识别器识别到的食谱实体
        if recipe_entities:
            keyword = recipe_entities[0]
        else:
            # 回退到传统的提取方法
            keyword = self.extract_keyword(query)
        
        if not keyword:
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": "抱歉，我没有识别出您要搜索的关键词，请尝试更明确地表达您的问题。"
            }
        
        # 搜索食谱
        search_result = backend_graph_tools.search_recipe(keyword)
        
        if not search_result["success"] or not search_result["data"]:
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": f"抱歉，我没有找到与 '{keyword}' 相关的食谱。"
            }
        
        # 构建响应
        recipes = search_result["data"][:3]
        recipe_names = [recipe["name"] for recipe in recipes]
        recipe_list = ", ".join(recipe_names)
        
        return {
            "success": True,
            "data": {
                "keyword": keyword,
                "recipes": recipe_names,
                "full_result": search_result["data"]
            },
            "source": "substitute_agent",
            "message": f"找到与 '{keyword}' 相关的食谱：{recipe_list}。"
        }

    def handle_recipe_structure(self, query: str, recipe_entities: list) -> Dict[str, Any]:
        """
        处理食谱结构问题
        Args:
            query: 用户的查询
            recipe_entities: 识别到的食谱实体列表
        Returns: 处理结果
        """
        # 优先使用实体识别器识别到的食谱实体
        if recipe_entities:
            recipe_name = recipe_entities[0]
        else:
            # 回退到传统的提取方法
            recipe_name = self.extract_recipe_name(query)
        
        if not recipe_name:
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": "抱歉，我没有识别出您提到的食谱名称，请尝试更明确地表达您的问题。"
            }
        
        # 搜索食谱
        search_result = backend_graph_tools.search_recipe(recipe_name)
        
        if not search_result["success"] or not search_result["data"]:
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": f"抱歉，我没有找到与 '{recipe_name}' 相关的食谱。"
            }
        
        # 获取第一个匹配的食谱
        recipe = search_result["data"][0]
        recipe_id = recipe["id"]
        
        # 获取食谱子图
        subgraph_result = backend_graph_tools.get_recipe_subgraph(recipe_id)
        
        if not subgraph_result["success"] or not subgraph_result["data"].get("recipe"):
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": f"抱歉，我没有找到与 '{recipe_name}' 相关的结构信息。"
            }
        
        # 构建响应
        subgraph = subgraph_result["data"]
        ingredients = subgraph.get("ingredients", [])
        ingredient_names = [ingredient["name"] for ingredient in ingredients]
        ingredient_list = ", ".join(ingredient_names)
        
        return {
            "success": True,
            "data": {
                "recipe": recipe_name,
                "ingredients": ingredient_names,
                "full_result": subgraph
            },
            "source": "substitute_agent",
            "message": f"{recipe_name} 的食材包括：{ingredient_list}。"
        }

    def handle_ingredient_neighbors(self, query: str, ingredient_entities: list) -> Dict[str, Any]:
        """
        处理食材邻域问题
        Args:
            query: 用户的查询
            ingredient_entities: 识别到的食材实体列表
        Returns: 处理结果
        """
        # 优先使用实体识别器识别到的食材实体
        if ingredient_entities:
            ingredient_name = ingredient_entities[0]
        else:
            # 回退到传统的提取方法
            ingredient_name = self.extract_ingredient_name(query)
        
        if not ingredient_name:
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": "抱歉，我没有识别出您提到的食材名称，请尝试更明确地表达您的问题。"
            }
        
        # 搜索规范食材
        search_result = backend_graph_tools.search_canonical(ingredient_name)
        
        if not search_result["success"] or not search_result["data"]:
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": f"抱歉，我没有找到与 '{ingredient_name}' 相关的食材信息。"
            }
        
        # 获取第一个匹配的规范食材
        canonical = search_result["data"][0]
        canonical_id = canonical["id"]
        
        # 获取规范食材邻域
        neighbors_result = backend_graph_tools.get_canonical_neighbors(canonical_id)
        
        if not neighbors_result["success"] or not neighbors_result["data"].get("neighbors"):
            return {
                "success": False,
                "data": {},
                "source": "substitute_agent",
                "message": f"抱歉，我没有找到与 '{ingredient_name}' 相关的邻域信息。"
            }
        
        # 构建响应
        neighbors = neighbors_result["data"]["neighbors"]
        neighbor_names = [neighbor["node"]["name"] for neighbor in neighbors[:3]]
        neighbor_list = ", ".join(neighbor_names)
        
        return {
            "success": True,
            "data": {
                "ingredient": ingredient_name,
                "neighbors": neighbor_names,
                "full_result": neighbors_result["data"]
            },
            "source": "substitute_agent",
            "message": f"与 {ingredient_name} 相关的食材有：{neighbor_list}。"
        }

    def handle_general_chat(self, query: str) -> Dict[str, Any]:
        """
        处理一般聊天问题
        Args:
            query: 用户的查询
        Returns: 处理结果
        """
        return {
            "success": True,
            "data": {},
            "source": "substitute_agent",
            "message": "你好！我是一个专注于食谱和食材替代推荐的智能助手。你可以问我关于食谱搜索、食谱结构、食材邻域或替代推荐的问题。"
        }

    def extract_ingredient_name(self, query: str) -> Optional[str]:
        """
        从查询中提取食材名称
        Args:
            query: 用户的查询
        Returns: 食材名称
        """
        # 简单的规则提取食材名称
        patterns = [
            r"(?:换成什么|替代|替代品|替代建议|可以换成|有什么替代).*?([\w\s]+?)(?:\?|。|，|$)",
            r"([\w\s]+?).*?(?:换成什么|替代|替代品|替代建议|可以换成|有什么替代)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1).strip()
        
        # 如果没有匹配到，返回整个查询作为食材名称
        return query.strip()

    def extract_keyword(self, query: str) -> Optional[str]:
        """
        从查询中提取搜索关键词
        Args:
            query: 用户的查询
        Returns: 搜索关键词
        """
        # 简单的规则提取搜索关键词
        patterns = [
            r"(?:找一下|搜索|查找|有没有).*?([\w\s]+?)(?:\?|。|，|$)",
            r"([\w\s]+?).*?(?:recipe|Recipe)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1).strip()
        
        # 如果没有匹配到，返回整个查询作为关键词
        return query.strip()

    def extract_recipe_name(self, query: str) -> Optional[str]:
        """
        从查询中提取食谱名称
        Args:
            query: 用户的查询
        Returns: 食谱名称
        """
        # 简单的规则提取食谱名称
        patterns = [
            r"(?:配方结构|结构是什么|子图|图谱|结构.*样).*?([\w\s]+?)(?:\?|。|，|$)",
            r"([\w\s]+?).*?(?:配方结构|结构是什么|子图|图谱|结构.*样)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1).strip()
        
        # 如果没有匹配到，返回整个查询作为食谱名称
        return query.strip()


# 创建全局替代推荐智能体实例
substitute_agent = SubstituteAgent()
