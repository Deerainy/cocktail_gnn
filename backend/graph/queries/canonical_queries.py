"""
规范食材相关的 Cypher 查询
"""

from typing import List, Dict, Optional, Any


class CanonicalQueries:
    """
    规范食材相关的 Cypher 查询
    """

    @staticmethod
    def get_canonical_neighbors_query(canonical_id: str, limit: int = 20) -> str:
        """
        获取规范食材邻域的 Cypher 查询
        Args:
            canonical_id: 规范食材 ID
            limit: 返回数量限制
        Returns: Cypher 查询语句
        """
        return """
        MATCH (c:CanonicalIngredient)
        WHERE c.canonical_id = $canonical_id OR c.canonical_id = toInteger($canonical_id)
        OPTIONAL MATCH (c)-[r:CO_OCCUR]->(neighbor:CanonicalIngredient)
        RETURN 'CO_OCCUR' as relationship_type, c.canonical_id, c.canonical_name, neighbor.canonical_id, neighbor.canonical_name, properties(r)
        UNION ALL
        OPTIONAL MATCH (c)-[r:FLAVOR_SIM]->(neighbor:CanonicalIngredient)
        RETURN 'FLAVOR_SIM' as relationship_type, c.canonical_id, c.canonical_name, neighbor.canonical_id, neighbor.canonical_name, properties(r)
        UNION ALL
        OPTIONAL MATCH (c)-[r:FLAVOR_COMPAT]->(neighbor:CanonicalIngredient)
        RETURN 'FLAVOR_COMPAT' as relationship_type, c.canonical_id, c.canonical_name, neighbor.canonical_id, neighbor.canonical_name, properties(r)
        UNION ALL
        OPTIONAL MATCH (c)-[r:GLOBAL_SUBSTITUTE]->(neighbor:CanonicalIngredient)
        RETURN 'GLOBAL_SUBSTITUTE' as relationship_type, c.canonical_id, c.canonical_name, neighbor.canonical_id, neighbor.canonical_name, properties(r)
        LIMIT $limit
        """

    @staticmethod
    def get_canonical_basic_info_query(canonical_id: str) -> str:
        """
        获取规范食材基本信息的 Cypher 查询
        Args:
            canonical_id: 规范食材 ID
        Returns: Cypher 查询语句
        """
        return """
        MATCH (c:CanonicalIngredient)
        WHERE c.canonical_id = $canonical_id OR c.canonical_id = toInteger($canonical_id)
        RETURN c.canonical_id, c.canonical_name
        """


    @staticmethod
    def search_canonical_by_name_query(keyword: str) -> str:
        """
        根据名称搜索规范食材的 Cypher 查询
        Args:
            keyword: 搜索关键词
        Returns: Cypher 查询语句
        """
        return """
        MATCH (c:CanonicalIngredient)
        WHERE LOWER(c.canonical_name) CONTAINS LOWER($keyword)
        RETURN c.canonical_id, c.canonical_name
        LIMIT 20
        """


