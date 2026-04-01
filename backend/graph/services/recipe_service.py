"""
食谱相关的服务层

提供食谱相关的业务逻辑处理
"""

from typing import Dict, Any, List
from ..client import neo4j_client
from ..queries.recipe_queries import RecipeQueries
from ..utils.formatters import (
    format_recipe_subgraph,
    format_recipe_substitute_results,
    format_node
)


class RecipeService:
    """
    食谱相关的服务类
    """

    @staticmethod
    def get_recipe_subgraph(recipe_id: str) -> Dict[str, Any]:
        """
        获取食谱子图
        Args:
            recipe_id: 食谱 ID
        Returns: 格式化后的子图数据
        """
        query = RecipeQueries.get_recipe_subgraph_query(recipe_id)
        results = neo4j_client.execute_query(query, {"recipe_id": recipe_id})
        return format_recipe_subgraph(results)

    @staticmethod
    def get_recipe_basic_info(recipe_id: str) -> Dict[str, Any]:
        """
        获取食谱基本信息
        Args:
            recipe_id: 食谱 ID
        Returns: 格式化后的食谱信息
        """
        query = RecipeQueries.get_recipe_basic_info_query(recipe_id)
        results = neo4j_client.execute_query(query, {"recipe_id": recipe_id})
        if results:
            return format_node(results[0]['r'])
        return {}

    @staticmethod
    def get_recipe_ingredients(recipe_id: str) -> List[Dict[str, Any]]:
        """
        获取食谱食材
        Args:
            recipe_id: 食谱 ID
        Returns: 格式化后的食材列表
        """
        query = RecipeQueries.get_recipe_ingredients_query(recipe_id)
        results = neo4j_client.execute_query(query, {"recipe_id": recipe_id})
        return [format_node(record['i']) for record in results]

    @staticmethod
    def get_recipe_canonicals(recipe_id: str) -> List[Dict[str, Any]]:
        """
        获取食谱规范食材
        Args:
            recipe_id: 食谱 ID
        Returns: 格式化后的规范食材列表
        """
        query = RecipeQueries.get_recipe_canonicals_query(recipe_id)
        results = neo4j_client.execute_query(query, {"recipe_id": recipe_id})
        return [format_node(record['ci']) for record in results]

    @staticmethod
    def get_recipe_substitute_results(recipe_id: str) -> Dict[str, Any]:
        """
        获取食谱替代结果
        Args:
            recipe_id: 食谱 ID
        Returns: 格式化后的替代结果数据
        """
        query = RecipeQueries.get_recipe_substitute_results_query(recipe_id)
        results = neo4j_client.execute_query(query, {"recipe_id": recipe_id})
        return format_recipe_substitute_results(results)

    @staticmethod
    def search_recipe_by_name(keyword: str) -> List[Dict[str, Any]]:
        """
        根据名称搜索食谱
        Args:
            keyword: 搜索关键词
        Returns: 格式化后的食谱列表
        """
        query = RecipeQueries.search_recipe_by_name_query(keyword)
        results = neo4j_client.execute_query(query, {"keyword": keyword})
        return [format_node(record['r']) for record in results]
