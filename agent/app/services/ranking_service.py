"""
排序服务文件

该文件实现了基于 SQE（Sensory Quality Evaluation）的推荐排序逻辑，包括：
- SQE 分数计算
- 多维度评价（口味、质地、营养）
- 候选推荐排序
- 个性化排序调整

SQE 评价维度：
- Taste（口味）：替代后的味道相似度
- Texture（质地）：替代后的质地相似度
- Nutrition（营养）：替代后的营养价值
"""

from typing import List, Dict, Optional
from ..config import settings


class RankingService:
    """
    排序服务类

    基于 SQE 评价对候选推荐进行排序
    """

    def __init__(self):
        """
        初始化排序服务

        从配置中读取 SQE 权重
        """
        self.taste_weight = settings.SQE_WEIGHT_TASTE
        self.texture_weight = settings.SQE_WEIGHT_TEXTURE
        self.nutrition_weight = settings.SQE_WEIGHT_NUTRITION

    def calculate_sqe_score(
        self,
        taste_score: float,
        texture_score: float,
        nutrition_score: float,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        计算 SQE 综合分数

        Args:
            taste_score: 口味分数 (0-100)
            texture_score: 质地分数 (0-100)
            nutrition_score: 营养分数 (0-100)
            custom_weights: 自定义权重

        Returns:
            SQE 综合分数 (0-100)
        """
        weights = custom_weights or {
            "taste": self.taste_weight,
            "texture": self.texture_weight,
            "nutrition": self.nutrition_weight
        }

        total_score = (
            taste_score * weights["taste"] +
            texture_score * weights["texture"] +
            nutrition_score * weights["nutrition"]
        )

        return round(total_score, 2)

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        对候选推荐进行排序

        Args:
            candidates: 候选推荐列表，每个候选应包含 SQE 分数
            user_preferences: 用户偏好，用于个性化调整

        Returns:
            排序后的候选列表
        """
        # 计算每个候选的综合分数
        for candidate in candidates:
            taste = candidate.get("taste_score", 0)
            texture = candidate.get("texture_score", 0)
            nutrition = candidate.get("nutrition_score", 0)

            total_score = self.calculate_sqe_score(taste, texture, nutrition)
            candidate["total_score"] = total_score

            # 应用用户偏好调整
            if user_preferences:
                total_score = self._apply_preferences(
                    total_score, candidate, user_preferences
                )
                candidate["adjusted_score"] = total_score

        # 按分数降序排序
        ranked = sorted(
            candidates,
            key=lambda x: x.get("adjusted_score", x.get("total_score", 0)),
            reverse=True
        )

        # 添加排名
        for idx, candidate in enumerate(ranked, 1):
            candidate["rank"] = idx

        return ranked

    def _apply_preferences(
        self,
        base_score: float,
        candidate: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> float:
        """
        应用用户偏好调整分数

        Args:
            base_score: 基础分数
            candidate: 候选信息
            preferences: 用户偏好

        Returns:
            调整后的分数
        """
        adjusted_score = base_score

        # 根据用户偏好进行加分或减分
        if preferences.get("preferred_flavors"):
            candidate_flavors = candidate.get("flavors", [])
            for flavor in preferences["preferred_flavors"]:
                if flavor in candidate_flavors:
                    adjusted_score += 5  # 偏好匹配加分

        if preferences.get("dietary_restrictions"):
            candidate_type = candidate.get("dietary_type")
            if candidate_type in preferences["dietary_restrictions"]:
                adjusted_score += 10  # 符合饮食限制加分

        return min(adjusted_score, 100)  # 确保分数不超过 100

    def generate_ranking_explanation(
        self,
        ranked_candidates: List[Dict[str, Any]]
    ) -> str:
        """
        生成排序解释

        Args:
            ranked_candidates: 排序后的候选列表

        Returns:
            排序解释文本
        """
        explanation = "根据 SQE（感官质量评价）系统，推荐结果按以下标准排序：\n\n"
        explanation += f"- 口味权重：{self.taste_weight * 100}%\n"
        explanation += f"- 质地权重：{self.texture_weight * 100}%\n"
        explanation += f"- 营养权重：{self.nutrition_weight * 100}%\n\n"

        for candidate in ranked_candidates[:3]:  # 只显示前 3 个
            explanation += f"排名 {candidate['rank']}: {candidate.get('name', '未知')}\n"
            explanation += f"  - 综合分数：{candidate.get('total_score', 0)}\n"
            explanation += f"  - 口味：{candidate.get('taste_score', 0)}\n"
            explanation += f"  - 质地：{candidate.get('texture_score', 0)}\n"
            explanation += f"  - 营养：{candidate.get('nutrition_score', 0)}\n\n"

        return explanation


# 创建全局排序服务实例
ranking_service = RankingService()
