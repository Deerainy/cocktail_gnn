"""
后端图数据库工具

封装后端图数据库接口，提供给 agent 使用
"""

import requests
import json
import os
from typing import Dict, Any, List


class BackendGraphTools:
    """
    后端图数据库工具类
    封装后端图数据库接口，提供给 agent 使用
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8000/api/graph"):
        """
        初始化后端图数据库工具
        Args:
            base_url: 后端图数据库接口的基础 URL
        """
        self.base_url = base_url
        # 确保日志目录存在
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "neo4j_retrieval_log.txt")

    def log(self, message: str):
        """
        记录日志
        Args:
            message: 日志消息
        """
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
        print(message)

    def search_recipe(self, keyword: str) -> Dict[str, Any]:
        """
        根据关键词搜索食谱
        Args:
            keyword: 搜索关键词
        Returns: 统一格式的搜索结果
        """
        self.log(f"\n=== Neo4j 检索 ===")
        self.log(f"搜索食谱: {keyword}")
        url = f"{self.base_url}/search/recipe/"
        params = {"keyword": keyword}
        self.log(f"请求 URL: {url}")
        self.log(f"请求参数: {params}")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            self.log(f"响应状态码: {response.status_code}")
            self.log(f"响应结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return {
                "success": True,
                "data": data,
                "source": "search_recipe",
                "message": ""
            }
        except Exception as e:
            error_message = f"搜索食谱失败: {str(e)}"
            self.log(error_message)
            return {
                "success": False,
                "data": [],
                "source": "search_recipe",
                "message": error_message
            }

    def search_canonical(self, keyword: str) -> Dict[str, Any]:
        """
        根据关键词搜索规范食材
        Args:
            keyword: 搜索关键词
        Returns: 统一格式的搜索结果
        """
        self.log(f"\n=== Neo4j 检索 ===")
        self.log(f"搜索规范食材: {keyword}")
        url = f"{self.base_url}/search/canonical/"
        params = {"keyword": keyword}
        self.log(f"请求 URL: {url}")
        self.log(f"请求参数: {params}")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            self.log(f"响应状态码: {response.status_code}")
            self.log(f"响应结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return {
                "success": True,
                "data": data,
                "source": "search_canonical",
                "message": ""
            }
        except Exception as e:
            error_message = f"搜索规范食材失败: {str(e)}"
            self.log(error_message)
            return {
                "success": False,
                "data": [],
                "source": "search_canonical",
                "message": error_message
            }

    def get_recipe_subgraph(self, recipe_id: str) -> Dict[str, Any]:
        """
        获取食谱子图
        Args:
            recipe_id: 食谱 ID
        Returns: 统一格式的食谱子图数据
        """
        self.log(f"\n=== Neo4j 检索 ===")
        self.log(f"获取食谱子图: {recipe_id}")
        url = f"{self.base_url}/recipe/subgraph/{recipe_id}/"
        self.log(f"请求 URL: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            self.log(f"响应状态码: {response.status_code}")
            self.log(f"响应结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return {
                "success": True,
                "data": data,
                "source": "recipe_subgraph",
                "message": ""
            }
        except Exception as e:
            error_message = f"获取食谱子图失败: {str(e)}"
            self.log(error_message)
            return {
                "success": False,
                "data": {},
                "source": "recipe_subgraph",
                "message": error_message
            }

    def get_canonical_neighbors(self, canonical_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        获取规范食材邻域
        Args:
            canonical_id: 规范食材 ID
            limit: 返回数量限制
        Returns: 统一格式的规范食材邻域数据
        """
        self.log(f"\n=== Neo4j 检索 ===")
        self.log(f"获取规范食材邻域: {canonical_id}")
        url = f"{self.base_url}/canonical/neighbors/{canonical_id}/"
        params = {"limit": limit}
        self.log(f"请求 URL: {url}")
        self.log(f"请求参数: {params}")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            self.log(f"响应状态码: {response.status_code}")
            self.log(f"响应结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return {
                "success": True,
                "data": data,
                "source": "canonical_neighbors",
                "message": ""
            }
        except Exception as e:
            error_message = f"获取规范食材邻域失败: {str(e)}"
            self.log(error_message)
            return {
                "success": False,
                "data": {},
                "source": "canonical_neighbors",
                "message": error_message
            }

    def get_global_substitutes(self, canonical_id: str, top_k: int = 10) -> Dict[str, Any]:
        """
        获取全局替代候选
        Args:
            canonical_id: 规范食材 ID
            top_k: 返回数量限制
        Returns: 统一格式的全局替代候选数据
        """
        self.log(f"\n=== Neo4j 检索 ===")
        self.log(f"获取全局替代候选: {canonical_id}")
        url = f"{self.base_url}/canonical/substitutes/{canonical_id}/"
        params = {"top_k": top_k}
        self.log(f"请求 URL: {url}")
        self.log(f"请求参数: {params}")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            self.log(f"响应状态码: {response.status_code}")
            self.log(f"响应结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return {
                "success": True,
                "data": data,
                "source": "global_substitutes",
                "message": ""
            }
        except Exception as e:
            error_message = f"获取全局替代候选失败: {str(e)}"
            self.log(error_message)
            return {
                "success": False,
                "data": {},
                "source": "global_substitutes",
                "message": error_message
            }

    def get_recipe_substitute_results(self, recipe_id: str) -> Dict[str, Any]:
        """
        获取食谱替代结果
        Args:
            recipe_id: 食谱 ID
        Returns: 统一格式的食谱替代结果数据
        """
        self.log(f"\n=== Neo4j 检索 ===")
        self.log(f"获取食谱替代结果: {recipe_id}")
        url = f"{self.base_url}/recipe/substitute-results/{recipe_id}/"
        self.log(f"请求 URL: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            self.log(f"响应状态码: {response.status_code}")
            self.log(f"响应结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return {
                "success": True,
                "data": data,
                "source": "recipe_substitute_results",
                "message": ""
            }
        except Exception as e:
            error_message = f"获取食谱替代结果失败: {str(e)}"
            self.log(error_message)
            return {
                "success": False,
                "data": {},
                "source": "recipe_substitute_results",
                "message": error_message
            }


# 创建全局后端图数据库工具实例
backend_graph_tools = BackendGraphTools()
