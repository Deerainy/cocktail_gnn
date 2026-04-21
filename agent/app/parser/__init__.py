#!/usr/bin/env python3
"""
Parser 模块 - 当前轮解析器

实现四层架构中的第3层：当前轮解析器
采用职责分离的设计：
- SignalExtractor: 只提取当前句的信号，不做业务决定
- SlotResolver: 统一槽位解析，记录来源和置信度
- CurrentTurnParser: 协调各组件完成完整解析流程
"""

from .signal_extractor import SignalExtractor, signal_extractor
from .slot_resolver import SlotResolver, slot_resolver
from .current_turn_parser import CurrentTurnParser, current_turn_parser

__all__ = [
    # 信号提取
    'SignalExtractor',
    'signal_extractor',
    
    # 槽位解析
    'SlotResolver',
    'slot_resolver',
    
    # 当前轮解析器
    'CurrentTurnParser',
    'current_turn_parser',
]
