"""
配置文件

该文件用于管理领域智能体的所有配置项，包括：
- LLM 模型配置（API 密钥、模型名称、温度参数等）
- Neo4j 数据库连接配置（URI、用户名、密码）
- MySQL 数据库连接配置
- 检索系统配置（向量数据库、索引参数等）
- 超时设置和调试开关

注意：该配置应与 backend 保持一致，避免重复造轮子
"""

import os
from typing import Optional


class Settings:
    """
    领域智能体配置类

    集中管理所有配置项，支持从环境变量读取
    """

    # Neo4j 连接配置
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "***")

    # MySQL 连接配置
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "***")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "cocktail_graph")

    # LLM API 配置 (DeepSeek)
    OPENAI_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "***")
    OPENAI_API_BASE: Optional[str] = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    OPENAI_API_TYPE: str = os.getenv("OPENAI_API_TYPE", "openai")

    # 默认模型配置 (DeepSeek)
    MODEL_NAME: str = os.getenv("MODEL_NAME", "deepseek-chat")
    MODEL_TEMPERATURE: float = float(os.getenv("MODEL_TEMPERATURE", "0.7"))
    MODEL_MAX_TOKENS: int = int(os.getenv("MODEL_MAX_TOKENS", "4000"))

    # 调试开关
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # 超时设置
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    NEO4J_TIMEOUT: int = int(os.getenv("NEO4J_TIMEOUT", "10"))
    MYSQL_TIMEOUT: int = int(os.getenv("MYSQL_TIMEOUT", "10"))

    # 检索配置
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    RETRIEVAL_SCORE_THRESHOLD: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.7"))

    # SQE 评价配置
    SQE_WEIGHT_TASTE: float = float(os.getenv("SQE_WEIGHT_TASTE", "0.4"))
    SQE_WEIGHT_TEXTURE: float = float(os.getenv("SQE_WEIGHT_TEXTURE", "0.3"))
    SQE_WEIGHT_NUTRITION: float = float(os.getenv("SQE_WEIGHT_NUTRITION", "0.3"))


# 创建全局配置实例
settings = Settings()
