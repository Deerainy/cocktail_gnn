#!/usr/bin/env python3
"""
Analysis 模块 - 用户输入分析系统

实现了四层架构的用户输入分析系统：
- 第1层：原始对话历史 (Raw History)
- 第2层：结构化会话状态 (Session Context)
- 第3层：当前轮解析器 (Current Turn Parser) -> 已移动到 parser 模块
- 第4层：任务执行器 (Task Executor)

当前模块保留：
- SessionContext: 会话上下文管理
- ParsedQuery: 解析结果结构
- UserInputAnalyzer: 用户输入分析器主入口
- parser_rules.yaml: 解析规则配置
"""

from .session_context import SessionContext, SessionContextManager, session_context_manager
from .parsed_query import ParsedEntity, ParsedQuery

__all__ = [
    # 会话上下文
    'SessionContext',
    'SessionContextManager',
    'session_context_manager',
    
    # 解析结果结构
    'ParsedEntity',
    'ParsedQuery',
]
