"""
响应模型定义文件

该文件定义了领域智能体的输出数据模型，包括：
- 查询响应
- 检索结果
- 推荐结果
- SQE 评价结果
- 错误响应

使用 Pydantic 确保输出数据的格式一致性和可验证性
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class QueryResponse(BaseModel):
    """
    查询响应模型

    定义了智能体对用户查询的完整响应格式
    固定输出格式：answer, intent, used_tools, evidence, debug_info
    """
    answer: str = Field(..., description="生成的答案")
    intent: str = Field(..., description="识别的用户意图")
    used_tools: List[str] = Field(default_factory=list, description="使用的工具列表")
    evidence: Optional[Dict[str, Any]] = Field(None, description="证据和推理过程")
    debug_info: Optional[Dict[str, Any]] = Field(None, description="调试信息")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "根据您提供的材料（伏特加、柠檬汁、苏打水）和偏好（酸甜口味、中等强度），我为您推荐制作一杯 Vodka Spritz。这款鸡尾酒口感清爽，酸甜平衡，非常适合您的需求。",
                "intent": "cocktail_recommendation",
                "used_tools": [
                    "ingredient_retrieval",
                    "cocktail_matching",
                    "preference_filtering"
                ],
                "evidence": {
                    "matched_cocktails": [
                        {
                            "name": "Vodka Spritz",
                            "match_score": 0.95,
                            "ingredients_match": ["伏特加", "柠檬汁"],
                            "flavor_match": "酸甜"
                        }
                    ],
                    "reasoning": "用户提供的材料可以制作多种鸡尾酒，根据酸甜口味偏好，Vodka Spritz 是最佳选择"
                },
                "debug_info": {
                    "processing_time": 1.23,
                    "retrieved_count": 15,
                    "filtered_count": 3
                }
            }
        }


class RetrievalResponse(BaseModel):
    """
    检索响应模型

    定义了从知识图谱和向量数据库检索的结果格式
    """
    query: str = Field(..., description="检索查询")
    results: List[dict] = Field(default_factory=list, description="检索结果列表")
    total: int = Field(..., description="结果总数")
    retrieval_type: str = Field(..., description="检索类型")
    scores: Optional[List[float]] = Field(None, description="检索分数")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "伏特加鸡尾酒",
                "results": [
                    {
                        "name": "Vodka Spritz",
                        "type": "cocktail",
                        "ingredients": ["伏特加", "柠檬汁", "苏打水"],
                        "flavor": "酸甜",
                        "strength": "中等"
                    }
                ],
                "total": 5,
                "retrieval_type": "cocktail",
                "scores": [0.95, 0.88, 0.82, 0.75, 0.70]
            }
        }


class RankingResponse(BaseModel):
    """
    排序响应模型

    定义了基于 SQE 评价的排序结果格式
    """
    ranked_candidates: List[dict] = Field(..., description="排序后的候选列表")
    sqe_scores: List[dict] = Field(..., description="详细的 SQE 评价分数")
    ranking_criteria: Optional[dict] = Field(None, description="使用的排序标准")

    class Config:
        json_schema_extra = {
            "example": {
                "ranked_candidates": [
                    {
                        "name": "Vodka Spritz",
                        "rank": 1,
                        "total_score": 85.0
                    },
                    {
                        "name": "Lemon Drop",
                        "rank": 2,
                        "total_score": 82.0
                    }
                ],
                "sqe_scores": [
                    {
                        "candidate": "Vodka Spritz",
                        "taste": 85,
                        "texture": 80,
                        "nutrition": 90,
                        "total": 85.0
                    }
                ],
                "ranking_criteria": {
                    "taste_weight": 0.4,
                    "texture_weight": 0.3,
                    "nutrition_weight": 0.3
                }
            }
        }


class ErrorResponse(BaseModel):
    """
    错误响应模型

    定义了错误发生时的统一响应格式
    """
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误详细信息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: Optional[str] = Field(None, description="错误发生时间")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "RetrievalError",
                "message": "无法从 Neo4j 检索数据",
                "details": {
                    "query": "伏特加鸡尾酒",
                    "error_code": "NEO4J_CONNECTION_FAILED"
                },
                "timestamp": "2024-01-01T12:00:00Z"
            }
        }
