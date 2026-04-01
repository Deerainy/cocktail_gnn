"""
图谱 API 工具函数文件

该文件提供了与后端图谱服务 API 交互的工具函数，包括：
- 调用后端 API 获取图谱数据
- 处理 API 响应
- 格式化返回结果

这些工具函数被 services 层调用，用于执行具体的图谱操作
"""

from typing import List, Dict, Optional, Any
import requests
from ..config import settings


class GraphApiTools:
    """
    图谱 API 工具类
    提供与后端图谱服务 API 交互的工具方法
    """

    def __init__(self):
        """初始化图谱 API 工具"""
        self.api_base_url = "http://localhost:8000/api/graph"

    def _call_api(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        调用后端 API
        Args:
            endpoint: API 端点
            params: 查询参数
        Returns: API 响应数据
        """
        url = f"{self.api_base_url}{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API 调用失败: {str(e)}")
            return {}

    def get_recipe_subgraph(self, recipe_id: str) -> Dict[str, Any]:
        """
        获取食谱子图
        Args:
            recipe_id: 食谱 ID
        Returns: 食谱子图数据
        """
        endpoint = f"/recipe/subgraph/{recipe_id}/"
        return self._call_api(endpoint)

    def get_global_substitutes(self, canonical_id: str, top_k: int = 10) -> Dict[str, Any]:
        """
        获取全局替代候选
        Args:
            canonical_id: 规范食材 ID
            top_k: 返回数量限制
        Returns: 替代候选数据
        """
        endpoint = f"/canonical/substitutes/{canonical_id}/"
        params = {"top_k": top_k}
        return self._call_api(endpoint, params)

    def get_recipe_substitute_results(self, recipe_id: str) -> Dict[str, Any]:
        """
        获取食谱替代结果
        Args:
            recipe_id: 食谱 ID
        Returns: 替代结果数据
        """
        endpoint = f"/recipe/substitute-results/{recipe_id}/"
        return self._call_api(endpoint)

    def get_canonical_neighbors(self, canonical_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        获取规范食材邻域
        Args:
            canonical_id: 规范食材 ID
            limit: 返回数量限制
        Returns: 邻域数据
        """
        endpoint = f"/canonical/neighbors/{canonical_id}/"
        params = {"limit": limit}
        return self._call_api(endpoint, params)

    def get_recipe_basic_info(self, recipe_id: str) -> Dict[str, Any]:
        """
        获取食谱基本信息
        Args:
            recipe_id: 食谱 ID
        Returns: 食谱基本信息
        """
        endpoint = f"/recipe/basic/{recipe_id}/"
        return self._call_api(endpoint)

    def get_recipe_ingredients(self, recipe_id: str) -> List[Dict[str, Any]]:
        """
        获取食谱食材
        Args:
            recipe_id: 食谱 ID
        Returns: 食材列表
        """
        endpoint = f"/recipe/ingredients/{recipe_id}/"
        response = self._call_api(endpoint)
        return response if isinstance(response, list) else []

    def get_recipe_canonicals(self, recipe_id: str) -> List[Dict[str, Any]]:
        """
        获取食谱规范食材
        Args:
            recipe_id: 食谱 ID
        Returns: 规范食材列表
        """
        endpoint = f"/recipe/canonicals/{recipe_id}/"
        response = self._call_api(endpoint)
        return response if isinstance(response, list) else []

    def get_canonical_basic_info(self, canonical_id: str) -> Dict[str, Any]:
        """
        获取规范食材基本信息
        Args:
            canonical_id: 规范食材 ID
        Returns: 规范食材基本信息
        """
        endpoint = f"/canonical/basic/{canonical_id}/"
        return self._call_api(endpoint)

    def search_recipe_by_name(self, keyword: str) -> List[Dict[str, Any]]:
        """
        根据名称搜索食谱
        Args:
            keyword: 搜索关键词
        Returns: 食谱列表
        """
        endpoint = "/search/recipe/"
        params = {"keyword": keyword}
        response = self._call_api(endpoint, params)
        return response if isinstance(response, list) else []

    def search_canonical_by_name(self, keyword: str) -> List[Dict[str, Any]]:
        """
        根据名称搜索规范食材
        Args:
            keyword: 搜索关键词
        Returns: 规范食材列表
        """
        endpoint = "/search/canonical/"
        params = {"keyword": keyword}
        response = self._call_api(endpoint, params)
        return response if isinstance(response, list) else []


# 创建全局图谱 API 工具实例
graph_api_tools = GraphApiTools()