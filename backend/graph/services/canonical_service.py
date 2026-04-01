"""
规范食材相关的服务层

提供规范食材相关的业务逻辑处理
"""

from typing import Dict, Any, List
from ..client import neo4j_client
from ..queries.canonical_queries import CanonicalQueries
from ..utils.formatters import format_canonical_neighbors, format_node


class CanonicalService:
    """
    规范食材相关的服务类
    """

    @staticmethod
    def get_canonical_neighbors(canonical_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        获取规范食材邻域
        Args:
            canonical_id: 规范食材 ID
            limit: 返回数量限制
        Returns: 格式化后的邻域数据
        """
        query = CanonicalQueries.get_canonical_neighbors_query(canonical_id, limit)
        results = neo4j_client.execute_query(query, {"canonical_id": canonical_id, "limit": limit})
        return format_canonical_neighbors(results)

    @staticmethod
    def get_canonical_basic_info(canonical_id: str) -> Dict[str, Any]:
        """
        获取规范食材基本信息
        Args:
            canonical_id: 规范食材 ID
        Returns: 格式化后的规范食材信息
        """
        query = CanonicalQueries.get_canonical_basic_info_query(canonical_id)
        results = neo4j_client.execute_query(query, {"canonical_id": canonical_id})
        if results:
            return format_node(results[0]['c'])
        return {}

    @staticmethod
    def search_canonical_by_name(keyword: str) -> List[Dict[str, Any]]:
        """
        根据名称搜索规范食材
        Args:
            keyword: 搜索关键词
        Returns: 格式化后的规范食材列表
        """
        query = CanonicalQueries.search_canonical_by_name_query(keyword)
        results = neo4j_client.execute_query(query, {"keyword": keyword})
        return [format_node(record['c']) for record in results]
