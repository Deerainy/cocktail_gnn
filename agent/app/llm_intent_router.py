"""
LLM 意图分类器

使用 LLM 进行意图分类，提高分类准确性
"""

import json
import requests
import os
from typing import Dict, Any, Optional


class LLMBasedIntentRouter:
    """
    基于 LLM 的意图分类器
    使用 deepseek 进行意图分类
    """

    def __init__(self, deepseek_url: str = "http://localhost:8000/v1/chat/completions"):
        """
        初始化 LLM 意图分类器
        Args:
            deepseek_url: deepseek 模型的 API 地址
        """
        self.deepseek_url = deepseek_url
        self.intent_types = [
            "recipe_search",
            "recipe_structure",
            "ingredient_neighbors",
            "substitute_recommendation",
            "general_chat"
        ]
        # 确保日志目录存在
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "llm_intent_log.txt")

    def log(self, message: str):
        """
        记录日志
        Args:
            message: 日志消息
        """
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
        print(message)

    def classify(self, query: str) -> Dict[str, Any]:
        """
        使用 LLM 分类用户的查询意图
        Args:
            query: 用户的查询
        Returns: 包含意图和置信度的字典
        """
        self.log(f"\n=== LLM 意图分类 ===")
        self.log(f"用户查询: {query}")
        
        try:
            # 尝试使用 OpenAI 客户端调用 LLM（参考 llm_flavor_feature.py）
            import os
            from openai import OpenAI
            
            api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                # 没有 API key，使用规则分类作为回退
                self.log("未设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY，使用规则分类作为回退")
                return {
                    "intent": "general_chat",
                    "confidence": 0.5,
                    "query": query,
                    "method": "llm_error"
                }
            
            # 构建 OpenAI 客户端
            client = OpenAI(
                api_key=api_key,
                base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            )
            
            # 构建提示
            system_prompt = "你是一个食谱和食材相关的意图分类器，能够准确识别用户的查询意图。"
            user_prompt = f"""
            请将以下用户查询分类到以下意图之一：
            1. recipe_search: 搜索食谱，如"找一下 margarita"、"搜索鸡尾酒"
            2. recipe_structure: 询问食谱结构，如"这个配方结构是什么样的"、"查看食谱子图"
            3. ingredient_neighbors: 询问食材邻域，如"lime 的邻域有什么"、"与 gin 相关的食材"
            4. substitute_recommendation: 询问替代推荐，如"lime 可以换成什么"、"没有 gin 怎么办"
            5. general_chat: 一般聊天，如"你好"、"在吗"
            
            请只返回意图名称，不要返回其他内容。
            
            查询：{query}
            """

            self.log(f"LLM 提示: {user_prompt}")

            # 发送请求
            self.log(f"发送请求到: {client.base_url}")
            response = client.chat.completions.create(
                model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                temperature=0,
                max_tokens=50,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            # 解析响应
            intent = response.choices[0].message.content.strip()
            self.log(f"提取的意图: {intent}")

            # 验证意图是否有效
            if intent in self.intent_types:
                result = {
                    "intent": intent,
                    "confidence": 0.95,
                    "query": query,
                    "method": "llm"
                }
                self.log(f"分类结果: {json.dumps(result, ensure_ascii=False)}")
                return result
            else:
                # 意图无效，返回 general_chat
                result = {
                    "intent": "general_chat",
                    "confidence": 0.5,
                    "query": query,
                    "method": "llm_fallback"
                }
                self.log(f"分类结果 (回退): {json.dumps(result, ensure_ascii=False)}")
                return result

        except Exception as e:
            # LLM 分类失败，返回 general_chat
            error_message = f"LLM 分类失败: {str(e)}"
            self.log(error_message)
            result = {
                "intent": "general_chat",
                "confidence": 0.5,
                "query": query,
                "method": "llm_error"
            }
            self.log(f"分类结果 (错误): {json.dumps(result, ensure_ascii=False)}")
            return result


# 创建全局 LLM 意图分类器实例
llm_intent_router = LLMBasedIntentRouter()
