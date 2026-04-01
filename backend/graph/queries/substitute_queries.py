"""
替代相关的 Cypher 查询
"""

from typing import List, Dict, Optional, Any


class SubstituteQueries:
    """
    替代相关的 Cypher 查询
    """

    @staticmethod
    def get_global_substitutes_query(canonical_id: str, top_k: int = 10) -> str:
        """
        获取全局替代候选的 Cypher 查询
        Args:
            canonical_id: 规范食材 ID
            top_k: 返回数量限制
        Returns: Cypher 查询语句
        """
        return """
        MATCH (c:CanonicalIngredient)
        WHERE c.id = $canonical_id OR c.id = toInteger($canonical_id) OR c.canonical_id = $canonical_id OR c.canonical_id = toInteger($canonical_id)
        MATCH (c)-[gs:GLOBAL_SUBSTITUTE]->(cs:CanonicalIngredient)
        RETURN c, gs, cs
        LIMIT $top_k
        """


