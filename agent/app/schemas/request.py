"""
请求模型定义文件

该文件定义了领域智能体的输入数据模型，包括：
- 用户查询请求
- 查询参数
- 上下文信息

使用 Pydantic 进行数据验证，确保输入数据的格式正确
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class QueryRequest(BaseModel):
    """
    用户查询请求模型

    定义了用户向智能体发起查询时的标准输入格式
    适用于鸡尾酒网站场景
    """
    message: str = Field(..., description="用户输入的消息", min_length=1)
    session_id: str = Field(..., description="会话ID，用于多轮对话追踪")
    available_ingredients: Optional[List[str]] = Field(None, description="用户家里有的材料列表")
    cocktail_preferences: Optional[dict] = Field(None, description="鸡尾酒偏好，如风味、强度等")
    recipe_id: Optional[str] = Field(None, description="菜谱ID，可选")
    debug: Optional[bool] = Field(False, description="调试模式，可选")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "我想做一杯酸甜口味的鸡尾酒，家里有伏特加和柠檬汁",
                "session_id": "session_123",
                "available_ingredients": ["伏特加", "柠檬汁", "苏打水"],
                "cocktail_preferences": {
                    "flavor": "酸甜",
                    "strength": "中等",
                    "type": "摇匀"
                },
                "recipe_id": "recipe_456",
                "debug": true
            }
        }
