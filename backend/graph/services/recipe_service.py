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
            record = results[0]
            return {
                "id": record.get('r.recipe_id'),
                "name": record.get('r.name'),
                "raw": {
                    "recipe_id": record.get('r.recipe_id'),
                    "name": record.get('r.name')
                }
            }
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
        return [{
            "id": record.get('i.name_norm'),
            "name": record.get('i.name_norm'),
            "raw": {
                "name_norm": record.get('i.name_norm')
            }
        } for record in results]

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
        return [{
            "id": record.get('ci.canonical_id'),
            "name": record.get('ci.canonical_name'),
            "raw": {
                "canonical_id": record.get('ci.canonical_id'),
                "canonical_name": record.get('ci.canonical_name')
            }
        } for record in results]

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
        recipe = None
        substitute_results = []
        
        for record in results:
            # 处理食谱节点
            if not recipe:
                recipe = {
                    "id": record.get('r.recipe_id'),
                    "name": record.get('r.name'),
                    "raw": {
                        "recipe_id": record.get('r.recipe_id'),
                        "name": record.get('r.name')
                    }
                }
            
            # 处理替代结果
            sr_data = record.get('substitute_result', {})
            sr_id = sr_data.get('id')
            if sr_id:
                substitute_result = {
                    "substitute_result": {
                        "id": sr_id,
                        "raw": sr_data
                    },
                    "target": None,
                    "candidates": []
                }
                
                # 处理目标节点
                if record.get('t.canonical_id'):
                    substitute_result['target'] = {
                        "id": record.get('t.canonical_id'),
                        "name": record.get('target_ingredient'),
                        "raw": {
                            "canonical_id": record.get('t.canonical_id'),
                            "canonical_name": record.get('target_ingredient')
                        }
                    }
                
                # 处理候选节点
                if record.get('c.canonical_id'):
                    candidate = {
                        "id": record.get('c.canonical_id'),
                        "name": record.get('candidate_ingredient'),
                        "raw": {
                            "canonical_id": record.get('c.canonical_id'),
                            "canonical_name": record.get('candidate_ingredient')
                        },
                        "relation": {}
                    }
                    substitute_result['candidates'].append(candidate)
                
                substitute_results.append(substitute_result)
        
        return {
            "recipe": recipe,
            "results": substitute_results
        }

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
        return [{
            "id": record.get('r.recipe_id'),
            "name": record.get('r.name'),
            "raw": {
                "recipe_id": record.get('r.recipe_id'),
                "name": record.get('r.name')
            }
        } for record in results]
