"""
SQE 评价工具函数文件

该文件提供了 SQE（Sensory Quality Evaluation）评价相关的工具函数，包括：
- SQE 分数计算
"""

from typing import List, Dict, Optional, Any
from .graph_api_tools import graph_api_tools


class SQETools:
    """
    SQE 评价工具类

    提供感官质量评价的工具方法
    """

    def calculate_taste_score(
        self,
        original_canonical: str,
        substitute_canonical: str
    ) -> float:
        """
        计算口味相似度分数

        Args:
            original_canonical: 原规范食材 ID
            substitute_canonical: 替代规范食材 ID

        Returns:
            口味分数 (0-100)
        """
        # 从后端 API 获取规范食材信息
        original_info = graph_api_tools.get_canonical_basic_info(original_canonical)
        substitute_info = graph_api_tools.get_canonical_basic_info(substitute_canonical)

        if not original_info or not substitute_info:
            return 50.0  # 默认分数

        # 从食材信息中提取口味属性
        original_taste = original_info.get("raw", {}).get("taste_profile", {})
        substitute_taste = substitute_info.get("raw", {}).get("taste_profile", {})

        # 计算口味相似度
        similarity = self._calculate_profile_similarity(
            original_taste,
            substitute_taste
        )

        return similarity * 100

    def calculate_texture_score(
        self,
        original_canonical: str,
        substitute_canonical: str
    ) -> float:
        """
        计算质地相似度分数

        Args:
            original_canonical: 原规范食材 ID
            substitute_canonical: 替代规范食材 ID

        Returns:
            质地分数 (0-100)
        """
        # 从后端 API 获取规范食材信息
        original_info = graph_api_tools.get_canonical_basic_info(original_canonical)
        substitute_info = graph_api_tools.get_canonical_basic_info(substitute_canonical)

        if not original_info or not substitute_info:
            return 50.0  # 默认分数

        # 从食材信息中提取质地属性
        original_texture = original_info.get("raw", {}).get("texture_profile", {})
        substitute_texture = substitute_info.get("raw", {}).get("texture_profile", {})

        # 计算质地相似度
        similarity = self._calculate_profile_similarity(
            original_texture,
            substitute_texture
        )

        return similarity * 100

    def calculate_nutrition_score(
        self,
        original_canonical: str,
        substitute_canonical: str
    ) -> float:
        """
        计算营养相似度分数

        Args:
            original_canonical: 原规范食材 ID
            substitute_canonical: 替代规范食材 ID

        Returns:
            营养分数 (0-100)
        """
        # 从后端 API 获取规范食材信息
        original_info = graph_api_tools.get_canonical_basic_info(original_canonical)
        substitute_info = graph_api_tools.get_canonical_basic_info(substitute_canonical)

        if not original_info or not substitute_info:
            return 50.0  # 默认分数

        # 从食材信息中提取营养属性
        original_nutrition = original_info.get("raw", {}).get("nutrition_profile", {})
        substitute_nutrition = substitute_info.get("raw", {}).get("nutrition_profile", {})

        # 计算营养相似度
        similarity = self._calculate_profile_similarity(
            original_nutrition,
            substitute_nutrition
        )

        return similarity * 100

    def calculate_comprehensive_sqe(
        self,
        original_canonical: str,
        substitute_canonical: str,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        计算综合 SQE 分数

        Args:
            original_canonical: 原规范食材 ID
            substitute_canonical: 替代规范食材 ID
            weights: 权重配置 {"taste": 0.4, "texture": 0.3, "nutrition": 0.3}

        Returns:
            SQE 评价结果
        """
        default_weights = {"taste": 0.4, "texture": 0.3, "nutrition": 0.3}
        weights = weights or default_weights

        taste_score = self.calculate_taste_score(
            original_canonical,
            substitute_canonical
        )
        texture_score = self.calculate_texture_score(
            original_canonical,
            substitute_canonical
        )
        nutrition_score = self.calculate_nutrition_score(
            original_canonical,
            substitute_canonical
        )

        total_score = (
            taste_score * weights["taste"] +
            texture_score * weights["texture"] +
            nutrition_score * weights["nutrition"]
        )

        return {
            "original_ingredient": original_canonical,
            "substitute_ingredient": substitute_canonical,
            "taste_score": round(taste_score, 2),
            "texture_score": round(texture_score, 2),
            "nutrition_score": round(nutrition_score, 2),
            "total_score": round(total_score, 2),
            "weights": weights
        }

    def _calculate_profile_similarity(
        self,
        profile1: Dict[str, Any],
        profile2: Dict[str, Any]
    ) -> float:
        """
        计算两个属性档案的相似度

        Args:
            profile1: 属性档案1
            profile2: 属性档案2

        Returns:
            相似度 (0-1)
        """
        if not profile1 or not profile2:
            return 0.5

        # 获取所有属性键
        all_keys = set(profile1.keys()) | set(profile2.keys())

        if not all_keys:
            return 0.5

        # 计算每个属性的相似度
        similarities = []
        for key in all_keys:
            value1 = profile1.get(key, 0)
            value2 = profile2.get(key, 0)

            if isinstance(value1, (int, float)) and isinstance(value2, (int, float)):
                # 数值型属性：计算相对差异
                max_val = max(abs(value1), abs(value2), 1)
                diff = abs(value1 - value2) / max_val
                similarity = 1 - diff
            elif isinstance(value1, str) and isinstance(value2, str):
                # 字符串型属性：简单匹配
                similarity = 1.0 if value1 == value2 else 0.0
            else:
                # 其他类型：默认中等相似度
                similarity = 0.5

            similarities.append(similarity)

        # 返回平均相似度
        return sum(similarities) / len(similarities) if similarities else 0.5

    def batch_calculate_sqe(
        self,
        original_canonical: str,
        substitute_canonicals: List[str],
        weights: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量计算 SQE 分数

        Args:
            original_canonical: 原规范食材 ID
            substitute_canonicals: 替代规范食材 ID 列表
            weights: 权重配置

        Returns:
            SQE 评价结果列表
        """
        results = []
        for substitute in substitute_canonicals:
            sqe_result = self.calculate_comprehensive_sqe(
                original_canonical,
                substitute,
                weights
            )
            results.append(sqe_result)

        # 按总分排序
        results.sort(key=lambda x: x["total_score"], reverse=True)

        return results


# 创建全局 SQE 工具实例
sqe_tools = SQETools()
