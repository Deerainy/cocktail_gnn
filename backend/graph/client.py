"""
Neo4j 连接层

负责初始化 driver、提供 query 执行方法、自动关闭 session、异常处理等
"""

from typing import List, Dict, Optional, Any
from neomodel import db


class Neo4jClient:
    """
    Neo4j 客户端类
    负责管理与 Neo4j 数据库的连接和查询执行
    """

    def __init__(self):
        """初始化 Neo4j 客户端"""
        # 使用 neomodel 的 db 实例，与 TestNeo4jConnectionView 相同的方式
        print("Neo4j 客户端初始化成功，使用 neomodel 的 db 实例")

    def execute_query(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        执行 Cypher 查询
        Args:
            cypher: Cypher 查询语句
            parameters: 查询参数
        Returns:查询结果列表
        """
        print(f"执行 Cypher 查询: {cypher}")
        print(f"查询参数: {parameters}")
        
        try:
            # 使用 neomodel 的 db.cypher_query 方法执行查询
            results, meta = db.cypher_query(cypher, parameters or {})
            print(f"查询结果数量: {len(results)}")
            
            # 格式化查询结果
            formatted_results = []
            for record in results:
                record_dict = {}
                for i, value in enumerate(record):
                    if hasattr(value, 'items'):
                        # 处理节点或关系对象
                        record_dict[meta[i]] = dict(value.items())
                    else:
                        # 处理普通值
                        record_dict[meta[i]] = value
                formatted_results.append(record_dict)
            
            if formatted_results:
                print(f"第一条结果: {formatted_results[0]}")
            return formatted_results
        except Exception as e:
            # 记录错误并返回空列表
            print(f"Neo4j 查询执行失败: {str(e)}")
            return []


# 创建全局 Neo4j 客户端实例
neo4j_client = Neo4jClient()
