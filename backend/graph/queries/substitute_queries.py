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
        WHERE c.canonical_id = $canonical_id OR c.canonical_id = toInteger($canonical_id)
        MATCH (c)-[gs:GLOBAL_SUBSTITUTE]->(cs:CanonicalIngredient)
        RETURN c.canonical_id, c.canonical_name, 
               gs.best_rank, gs.accepted_best_rank, gs.avg_delta_balance, 
               gs.snapshot_count, gs.last_model_version, gs.recipe_count, 
               gs.avg_delta_sqe, gs.accept_count, gs.avg_delta_synergy, 
               gs.avg_delta_conflict, gs.support_count, gs.accept_rate, 
               cs.canonical_id, cs.canonical_name
        ORDER BY gs.best_rank ASC
        LIMIT $top_k
        """


