"""
LLM 意图分类器

使用 LLM 进行意图分类，提高分类准确性
"""

import json
import os
import time
import sys
from typing import Dict, Any, Optional

# 添加 agent 目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入 settings
from app.config import settings


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
        # 意图类型不再硬编码，支持动态识别
        self.intent_types = []
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
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{log_message}\n")

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
            from openai import OpenAI
            
            # 从 config 文件中读取密钥
            api_key = settings.OPENAI_API_KEY
            base_url = settings.OPENAI_API_BASE
            model_name = settings.MODEL_NAME
            
            if not api_key:
                # 没有 API key，使用规则分类作为回退
                self.log("未设置 API key，使用规则分类作为回退")
                return {
                    "intent": "general_chat",
                    "confidence": 0.5,
                    "query": query,
                    "method": "llm_error"
                }
            
            # 构建 OpenAI 客户端
            client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            
            # 从配置文件获取提示词
            system_prompt = settings.get_system_prompt("intent_classification") or "你是一个食谱和食材相关的意图分类器，能够准确识别用户的查询意图。"
            user_prompt_template = settings.get_user_prompt("intent_classification")
            
            if user_prompt_template:
                user_prompt = user_prompt_template.format(query=query)
            else:
                # 使用默认提示词
                user_prompt = f"""
                请将以下用户查询分类到合适的意图类型，并返回JSON格式：
                {{"intent": "意图名称", "confidence": 0.9, "description": "描述"}}
                
                常见意图类型包括：
                - recipe_search: 搜索具体的食谱或配方
                - recipe_structure: 询问食谱的结构或组成
                - ingredient_neighbors: 询问食材的相关食材
                - substitute_recommendation: 询问食材的替代品
                - price_inquiry: 询问价格
                - recommendation: 推荐饮品、喝法或基于特定需求的饮品建议
                - general_chat: 一般聊天
                - other: 其他意图（请描述）
                
                查询：{query}
                """

            self.log(f"LLM 提示: {user_prompt}")

            # 发送请求
            self.log(f"发送请求到: {client.base_url}")
            response = client.chat.completions.create(
                model=model_name,
                temperature=0,
                max_tokens=100,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            # 解析响应
            response_text = response.choices[0].message.content.strip()
            self.log(f"提取的响应: {response_text}")

            # 尝试解析JSON格式的响应
            try:
                result_data = json.loads(response_text)
                intent = result_data.get("intent", "general_chat")
                confidence = result_data.get("confidence", 0.8)
                description = result_data.get("description", "")
                
                result = {
                    "intent": intent,
                    "confidence": confidence,
                    "query": query,
                    "description": description,
                    "method": "llm"
                }
                self.log(f"分类结果: {json.dumps(result, ensure_ascii=False)}")
                return result
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试提取意图名称
                intent = response_text.split()[0] if response_text else "general_chat"
                result = {
                    "intent": intent,
                    "confidence": 0.7,
                    "query": query,
                    "method": "llm"
                }
                self.log(f"分类结果 (文本解析): {json.dumps(result, ensure_ascii=False)}")
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
