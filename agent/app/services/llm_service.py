"""
LLM 服务文件

该文件封装了与大语言模型（LLM）的交互逻辑，包括：
- 模型初始化和配置
- 提示词模板管理
- 模型调用和响应处理
- 错误处理和重试机制

支持的模型类型：
- OpenAI GPT 系列
- 其他兼容 OpenAI API 的模型
"""

from typing import Optional, List, Dict, Any
from openai import OpenAI
from ..config import settings


class LLMService:
    """
    LLM 服务类

    封装所有与 LLM 交互的逻辑，提供统一的调用接口
    """

    def __init__(self):
        """
        初始化 LLM 服务

        根据配置创建 OpenAI 客户端实例
        """
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )
        self.model_name = settings.MODEL_NAME
        self.temperature = settings.MODEL_TEMPERATURE
        self.max_tokens = settings.MODEL_MAX_TOKENS

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        调用聊天补全 API

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数，控制输出的随机性
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数

        Returns:
            模型生成的文本响应
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            if settings.DEBUG:
                print(f"LLM 调用失败: {e}")
            raise

    def generate_answer(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> str:
        """
        生成答案

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            **kwargs: 其他参数

        Returns:
            生成的答案
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        return self.chat_completion(messages, **kwargs)

    def classify_query(
        self,
        query: str,
        system_prompt: str,
        **kwargs
    ) -> str:
        """
        分类查询类型

        Args:
            query: 用户查询
            system_prompt: 系统提示词
            **kwargs: 其他参数

        Returns:
            查询类型
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        return self.chat_completion(messages, temperature=0.1, **kwargs)


# 创建全局 LLM 服务实例
llm_service = LLMService()
