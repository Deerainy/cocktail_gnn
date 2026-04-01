"""
意图分类器
用于识别用户的意图，将用户的问题分类到不同的处理流程
"""

import re
from typing import Dict, Any, Optional
from .llm_intent_router import llm_intent_router


class IntentRouter:
    def __init__(self):
        """
        初始化意图分类器
        """
        # 定义意图模式
        self.intent_patterns = {
            "recipe_search": [
                r"找一下.*",
                r"搜索.*",
                r"查找.*",
                r"有没有.*",
                r".* recipe",
                r".* Recipe"
            ],
            "recipe_structure": [
                r"配方结构",
                r"结构是什么",
                r"子图",
                r"图谱",
                r"结构.*样"
            ],
            "ingredient_neighbors": [
                r"邻域",
                r"邻居",
                r"相关.*食材",
                r"食材.*相关"
            ],
            "substitute_recommendation": [
                r"换成什么",
                r"替代",
                r"替代品",
                r"替代建议",
                r"可以换成",
                r"有什么替代"
            ],
            "general_chat": [
                r"你好",
                r"hi",
                r"hello",
                r"hey",
                r"在吗",
                r"在不在"
            ]
        }

    def classify(self, query: str) -> Dict[str, Any]:
        """分类用户的查询意图
        先使用 LLM 分类，如果失败则使用规则分类
        Args:query: 用户的查询
        Returns: 包含意图和置信度的字典
        """
        try:
            # 先使用 LLM 分类
            llm_result = llm_intent_router.classify(query)
            # 如果 LLM 分类成功且置信度高于 0.7，则使用 LLM 分类结果
            if llm_result.get("confidence", 0) > 0.7:
                return llm_result
        except Exception as e:
            print(f"LLM 分类失败: {str(e)}")
        
        # LLM 分类失败或置信度低，使用规则分类
        rule_result = self.rule_based_classify(query)
        print(f"规则分类结果: {rule_result}")
        return rule_result

    def rule_based_classify(self, query: str) -> Dict[str, Any]:
        """
        基于规则的意图分类
        Args:
            query: 用户的查询
        Returns: 包含意图和置信度的字典
        """
        # 遍历所有意图模式
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query):
                    return {
                        "intent": intent,
                        "confidence": 0.9,
                        "query": query,
                        "method": "rule"
                    }
        
        # 如果没有匹配到任何意图，默认分类为 general_chat
        return {
            "intent": "general_chat",
            "confidence": 0.5,
            "query": query,
            "method": "rule_fallback"
        }


# 创建全局意图分类器实例
intent_router = IntentRouter()
