"""
检索服务文件

该文件实现了从后端图谱服务 API 和向量数据库的检索逻辑，包括：
- 调用后端 API 获取图谱数据
- 向量相似度检索
- 混合检索策略
- 结果过滤和排序

检索类型：
- recipe: 菜谱检索
- ingredient: 食材检索
- substitute: 替代检索
"""

from typing import List, Dict, Optional, Any
from ..config import settings
from ..tools.graph_api_tools import graph_api_tools
from .llm_service import llm_service


class RetrievalService:
    """
    检索服务类

    封装所有数据检索逻辑
    """

    def __init__(self):
        """
        初始化检索服务
        """
        self.top_k = settings.RETRIEVAL_TOP_K
        self.score_threshold = settings.RETRIEVAL_SCORE_THRESHOLD

    def retrieve_recipes(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        检索菜谱

        Args:
            query: 查询文本
            filters: 过滤条件

        Returns:
            菜谱列表
        """
        # 调用后端 API 搜索菜谱
        recipes = graph_api_tools.search_recipe_by_name(query)

        # 应用过滤条件
        if filters:
            recipes = self._apply_filters(recipes, filters)

        return recipes

    def retrieve_ingredients(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        检索食材

        Args:
            query: 查询文本
            filters: 过滤条件

        Returns:
            食材列表
        """
        # 调用后端 API 搜索规范食材
        ingredients = graph_api_tools.search_canonical_by_name(query)

        # 应用过滤条件
        if filters:
            ingredients = self._apply_filters(ingredients, filters)

        return ingredients

    def retrieve_substitutes(
        self,
        canonical_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        检索替代候选

        Args:
            canonical_id: 规范食材 ID
            filters: 过滤条件

        Returns:
            替代候选列表
        """
        # 调用后端 API 获取全局替代候选
        result = graph_api_tools.get_global_substitutes(canonical_id, self.top_k)
        substitutes = [item["canonical"] for item in result.get("candidates", [])]

        # 应用过滤条件
        if filters:
            substitutes = self._apply_filters(substitutes, filters)

        return substitutes

    def retrieve_recipe_subgraph(
        self,
        recipe_id: str
    ) -> Dict[str, Any]:
        """
        检索菜谱子图

        Args:
            recipe_id: 菜谱 ID

        Returns:
            菜谱子图数据
        """
        # 调用后端 API 获取菜谱子图
        return graph_api_tools.get_recipe_subgraph(recipe_id)

    def hybrid_retrieval(
        self,
        query: str,
        retrieval_type: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        混合检索（图谱 + 向量）

        Args:
            query: 查询文本
            retrieval_type: 检索类型
            filters: 过滤条件

        Returns:
            检索结果列表
        """
        # 先从知识图谱检索
        if retrieval_type == "recipe":
            graph_results = self.retrieve_recipes(query, filters)
        elif retrieval_type == "ingredient":
            graph_results = self.retrieve_ingredients(query, filters)
        elif retrieval_type == "substitute":
            # 对于替代检索，需要先获取规范食材 ID
            # 这里简化处理，假设 query 是规范食材 ID
            graph_results = self.retrieve_substitutes(query, filters)
        else:
            graph_results = []

        # TODO: 添加向量检索并融合结果

        return graph_results

    def _apply_filters(
        self,
        results: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        应用过滤条件

        Args:
            results: 检索结果
            filters: 过滤条件

        Returns:
            过滤后的结果
        """
        filtered = results

        if filters.get("dietary_type"):
            filtered = [
                r for r in filtered
                if r.get("dietary_type") == filters["dietary_type"]
            ]

        if filters.get("min_protein"):
            filtered = [
                r for r in filtered
                if r.get("protein_content", 0) >= filters["min_protein"]
            ]

        return filtered


# 创建全局检索服务实例
retrieval_service = RetrievalService()
