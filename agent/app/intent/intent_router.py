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
            "recommendation": [
                r"推荐.*",
                r"能做什么",
                r"适合喝什么",
                r"想喝.*",
                r"心情.*",
                r"我有.*材料",
                r"只有.*",
                r"可以用.*",
                r"推荐.*酒",
                r"适合.*酒",
                r"想喝.*酒",
                r"什么酒.*",
                r"能做.*酒",
                r"有.*材料",
                r"材料.*",
                r"食材.*",
                r"风味.*",
                r"口味.*",
                r"酸甜.*",
                r"清爽.*",
                r"醇厚.*",
                r"酒精度.*",
                r"低.*酒",
                r"高.*酒",
                r"喝法",
                r"怎么喝",
                r"如何喝",
                r"常见.*喝法",
                r".*喝法"
            ],
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
                r"有什么替代",
                r"替换成什么"
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
        # 缓存意图分类结果
        self.intent_cache = {}
    
    def _normalize_query(self, query: str) -> str:
        """规范化查询字符串，用于缓存键的生成
        
        Args:
            query: 原始查询字符串
            
        Returns:
            规范化后的查询字符串
        """
        # 移除特殊字符和多余空格
        import re
        # 将查询转换为小写
        query = query.lower()
        # 移除非字母数字、非空格、非中文字符
        query = re.sub(r'[^a-z0-9\s\u4e00-\u9fff]', '', query)
        # 移除多余空格
        query = ' '.join(query.split())
        return query.strip()

    def classify(self, query: str, trace=None) -> Dict[str, Any]:
        """分类用户的查询意图
        先使用规则分类，如果失败则使用 LLM 分类
        Args:query: 用户的查询
        Returns: 包含意图和置信度的字典
        """
        # 规范化查询用于缓存
        normalized_query = self._normalize_query(query)
        print(f"[DEBUG] 规范化查询: {normalized_query}")
        
        # 检查缓存
        if normalized_query in self.intent_cache:
            cached_result = self.intent_cache[normalized_query]
            print(f"[DEBUG] 从缓存中获取意图分类: {normalized_query} -> {cached_result}")
            # 即使从缓存获取，也要添加trace步骤
            if trace:
                trace.add_step(
                    name="intent_classification",
                    title="意图判断",
                    status="success",
                    data={
                        "intent": cached_result.get("intent"),
                        "confidence": cached_result.get("confidence"),
                        "router": cached_result.get("method", "cached")
                    }
                )
            return cached_result
        
        # 先使用规则分类
        rule_result = self.rule_based_classify(query)
        print(f"[DEBUG] 规则分类原始结果: {rule_result}")
        print(f"[DEBUG] 规则分类置信度: {rule_result.get('confidence', 0)}")
        print(f"[DEBUG] 规则分类条件判断: {rule_result.get('confidence', 0) > 0.8}")
        
        # 如果规则分类成功且置信度高于 0.8，则使用规则分类结果
        confidence = rule_result.get("confidence", 0)
        print(f"[DEBUG] confidence类型: {type(confidence)}, 值: {confidence}")
        print(f"[DEBUG] isinstance检查: {isinstance(confidence, (int, float))}")
        print(f"[DEBUG] 数值比较: {confidence > 0.8}")
        if isinstance(confidence, (int, float)) and confidence > 0.8:
            print(f"[DEBUG] 使用规则分类结果: {rule_result}")
            
            # 添加trace步骤
            if trace:
                trace.add_step(
                    name="intent_classification",
                    title="意图判断",
                    status="success",
                    data={
                        "intent": rule_result.get("intent"),
                        "confidence": rule_result.get("confidence"),
                        "router": rule_result.get("method", "rule")
                    }
                )
                print(f"[DEBUG] 已添加规则分类trace步骤: {rule_result.get('intent')}")
            
            # 缓存结果
            self.intent_cache[normalized_query] = rule_result
            print(f"[DEBUG] 返回规则分类结果: {rule_result}")
            return rule_result
        
        print(f"[DEBUG] 规则分类置信度不足，尝试LLM分类")
        
        # 规则分类失败或置信度低，使用 LLM 分类
        try:
            llm_result = llm_intent_router.classify(query)
            print(f"[DEBUG] LLM分类结果: {llm_result}")
            # 如果 LLM 分类成功且置信度高于 0.7，则使用 LLM 分类结果
            if llm_result.get("confidence", 0) > 0.7:
                # 添加trace步骤
                if trace:
                    trace.add_step(
                        name="intent_classification",
                        title="意图判断",
                        status="success",
                        data={
                            "intent": llm_result.get("intent"),
                            "confidence": llm_result.get("confidence"),
                            "router": "llm"
                        }
                    )
                    print(f"[DEBUG] 已添加LLM分类trace步骤: {llm_result.get('intent')}")
                
                # 缓存结果
                self.intent_cache[normalized_query] = llm_result
                return llm_result
        except Exception as e:
            print(f"[DEBUG] LLM 分类失败: {str(e)}")
        
        # 所有分类方法都失败，使用默认分类
        default_result = {
            "intent": "general_chat",
            "confidence": 0.5,
            "query": query,
            "method": "default"
        }
        
        # 添加trace步骤
        if trace:
            trace.add_step(
                name="intent_classification",
                title="意图判断",
                status="success",
                data={
                    "intent": default_result.get("intent"),
                    "confidence": default_result.get("confidence"),
                    "router": default_result.get("method", "default")
                }
            )
        
        # 缓存结果
        self.intent_cache[normalized_query] = default_result
        return default_result

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
