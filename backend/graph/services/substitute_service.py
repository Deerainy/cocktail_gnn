"""
替代相关的服务层

提供替代相关的业务逻辑处理
"""

from typing import Dict, Any, List
from ..client import neo4j_client
from ..queries.substitute_queries import SubstituteQueries
from ..utils.formatters import format_global_substitutes


class SubstituteService:
    """
    替代相关的服务类
    """

    @staticmethod
    def get_global_substitutes(canonical_id: str, top_k: int = 10) -> Dict[str, Any]:
        """
        获取全局替代候选
        Args:
            canonical_id: 规范食材 ID
            top_k: 返回数量限制
        Returns: 格式化后的替代数据
        """
        query = SubstituteQueries.get_global_substitutes_query(canonical_id, top_k)
        results = neo4j_client.execute_query(query, {"canonical_id": canonical_id, "top_k": top_k})
        return format_global_substitutes(results)
