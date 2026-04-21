"""
配置文件

该文件用于管理领域智能体的所有配置项，包括：
- LLM 模型配置（API 密钥、模型名称、温度参数等）
- Neo4j 数据库连接配置（URI、用户名、密码）
- MySQL 数据库连接配置
- 检索系统配置（向量数据库、索引参数等）
- 超时设置和调试开关
- 动态配置文件加载

注意：该配置应与 backend 保持一致，避免重复造轮子
"""

import os
import yaml
from typing import Optional, Dict, Any, List


class Settings:
    """
    领域智能体配置类

    集中管理所有配置项，支持从环境变量读取
    """

    # Neo4j 连接配置
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "Lyx040410")

    # MySQL 连接配置
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "123456")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "cocktail_graph")

    # LLM API 配置 (DeepSeek)
    OPENAI_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "sk-ede8258f75cd47aa90248b99bb1c6a6f")
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

    # 图谱 API 配置
    GRAPH_API_BASE_URL: str = os.getenv("GRAPH_API_BASE_URL", "http://localhost:8000/api/graph")

    # 配置文件路径
    CONFIG_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
    RETRIEVAL_CONFIG_FILE: str = os.path.join(CONFIG_DIR, "retrieval_config.yaml")
    QUERY_TEMPLATES_FILE: str = os.path.join(CONFIG_DIR, "query_templates.yaml")
    LLM_PROMPTS_FILE: str = os.path.join(CONFIG_DIR, "llm_prompts.yaml")

    def __init__(self):
        """初始化配置，加载动态配置文件"""
        self._load_dynamic_configs()

    def _load_dynamic_configs(self):
        """加载动态配置文件"""
        self.retrieval_config = self._load_yaml_file(self.RETRIEVAL_CONFIG_FILE, {})
        self.query_templates = self._load_yaml_file(self.QUERY_TEMPLATES_FILE, {})
        self.llm_prompts = self._load_yaml_file(self.LLM_PROMPTS_FILE, {})

    def _load_yaml_file(self, file_path: str, default: Any) -> Any:
        """加载YAML文件

        Args:
            file_path: 文件路径
            default: 默认值

        Returns:
            加载的配置或默认值
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                print(f"警告: 配置文件不存在: {file_path}，使用默认值")
                return default
        except Exception as e:
            print(f"加载配置文件失败 {file_path}: {e}，使用默认值")
            return default

    def get_retrieval_keywords(self) -> List[str]:
        """获取检索关键词列表

        Returns:
            List[str]: 检索关键词列表
        """
        return self.retrieval_config.get("retrieval_keywords", [])

    def get_english_ingredients(self) -> List[str]:
        """获取英文食材列表

        Returns:
            List[str]: 英文食材列表
        """
        return self.retrieval_config.get("english_ingredients", [])

    def get_confidence_threshold(self, threshold_type: str) -> float:
        """获取置信度阈值

        Args:
            threshold_type: 阈值类型 (rule_based, llm_based, fuzzy_match, entity_recognition)

        Returns:
            float: 置信度阈值
        """
        thresholds = self.retrieval_config.get("confidence_thresholds", {})
        return thresholds.get(threshold_type, 0.7)

    def get_daily_chat_keywords(self) -> List[str]:
        """获取日常交流关键词列表

        Returns:
            List[str]: 日常交流关键词列表
        """
        daily_chat_config = self.retrieval_config.get("daily_chat_config", {})
        return daily_chat_config.get("keywords", [])

    def use_llm_for_daily_chat(self) -> bool:
        """是否使用LLM判断日常交流

        Returns:
            bool: 是否使用LLM
        """
        daily_chat_config = self.retrieval_config.get("daily_chat_config", {})
        return daily_chat_config.get("use_llm", True)

    def get_query_template(self, db_type: str, query_name: str) -> Optional[str]:
        """获取查询模板

        Args:
            db_type: 数据库类型 (neo4j, mysql)
            query_name: 查询名称

        Returns:
            Optional[str]: 查询模板
        """
        queries = self.query_templates.get(f"{db_type}_queries", {})
        template_info = queries.get(query_name, {})
        return template_info.get("template")

    def get_system_prompt(self, prompt_type: str) -> Optional[str]:
        """获取系统提示词

        Args:
            prompt_type: 提示词类型

        Returns:
            Optional[str]: 系统提示词
        """
        return self.llm_prompts.get("system_prompts", {}).get(prompt_type)

    def get_user_prompt(self, prompt_type: str) -> Optional[str]:
        """获取用户提示词

        Args:
            prompt_type: 提示词类型

        Returns:
            Optional[str]: 用户提示词
        """
        return self.llm_prompts.get("user_prompts", {}).get(prompt_type)

    def get_example_conversations(self) -> List[Dict[str, str]]:
        """获取示例对话

        Returns:
            List[Dict[str, str]]: 示例对话列表
        """
        return self.llm_prompts.get("example_conversations", [])

    def get_flavor_terms(self, flavor_type: str = None) -> List[str]:
        """获取风味词列表

        Args:
            flavor_type: 风味类型 (sour, sweet, bitter, aroma, fruity, body)，如果为None则返回所有

        Returns:
            List[str]: 风味词列表
        """
        flavor_terms = self.llm_prompts.get("flavor_terms", {})
        if flavor_type:
            return flavor_terms.get(flavor_type, [])
        else:
            # 返回所有风味词
            all_flavors = []
            for flavors in flavor_terms.values():
                all_flavors.extend(flavors)
            return all_flavors

    def get_common_nouns(self) -> List[str]:
        """获取通用名词列表

        Returns:
            List[str]: 通用名词列表
        """
        return self.llm_prompts.get("common_nouns", [])

    def get_enhanced_prompt(self, prompt_type: str) -> Optional[str]:
        """获取增强的提示词模板

        Args:
            prompt_type: 提示词类型 (enhanced_response_generation, recipe_search_enhanced, etc.)

        Returns:
            Optional[str]: 提示词模板，如果不存在则返回None
        """
        return self.llm_prompts.get(prompt_type)

    def reload_configs(self):
        """重新加载配置文件"""
        self._load_dynamic_configs()
        print("配置文件已重新加载")


# 创建全局配置实例
settings = Settings()
