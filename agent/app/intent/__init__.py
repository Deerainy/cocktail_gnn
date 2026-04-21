#!/usr/bin/env python3
"""
Intent 模块 - 意图识别与解析

包含意图识别相关的组件：
- IntentResolver: 基于规则配置+打分推断意图（重构版）
- LLMRuleLearner: LLM 规则学习器，自动学习新意图并更新配置
- intent_router: 原有的意图路由器
- llm_intent_router: 基于LLM的意图路由器
"""

from .intent_resolver import IntentResolver, intent_resolver
from .llm_rule_learner import LLMRuleLearner, llm_rule_learner

try:
    from .intent_router import intent_router
    __all__ = [
        'IntentResolver',
        'intent_resolver',
        'LLMRuleLearner',
        'llm_rule_learner',
        'intent_router',
    ]
except ImportError:
    __all__ = [
        'IntentResolver',
        'intent_resolver',
        'LLMRuleLearner',
        'llm_rule_learner',
    ]
