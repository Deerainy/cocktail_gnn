#!/usr/bin/env python3
"""
当前轮解析器模块（重构版）

实现四层架构中的第3层：当前轮解析器
采用职责分离的设计：
- SignalExtractor: 只提取当前句的信号
- IntentResolver: 基于规则配置+打分推断意图
- SlotResolver: 统一槽位解析，记录来源和置信度
"""

from typing import Dict, Any, Optional, List
import sys
import os

# 添加父目录到路径以支持导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from analysis.session_context import SessionContext
from parser.signal_extractor import signal_extractor
from intent.intent_resolver import intent_resolver
from parser.slot_resolver import slot_resolver


class CurrentTurnParser:
    """当前轮解析器（重构版）
    
    职责：协调 SignalExtractor、IntentResolver、SlotResolver 完成解析。
    输出包含完整证据链的解析结果，便于调试和可视化。
    """
    
    def __init__(self):
        """初始化当前轮解析器"""
        self.signal_extractor = signal_extractor
        self.intent_resolver = intent_resolver
        self.slot_resolver = slot_resolver
    
    def parse(self, text: str, session_context: Optional[SessionContext] = None) -> Dict[str, Any]:
        """完整解析流程
        
        Args:
            text: 用户输入文本
            session_context: 会话上下文（可选）
            
        Returns:
            Dict: 包含完整证据链的解析结果
            {
                "intent": {
                    "value": "ingredient_substitute",
                    "confidence": 0.84,
                    "source": "intent_resolver"
                },
                "slots": {
                    "recipe": {
                        "value": "Margarita",
                        "source": "session.current_recipe",
                        "confidence": 0.90
                    },
                    "ingredient": {
                        "value": "lime juice",
                        "source": "explicit",
                        "confidence": 1.0
                    }
                },
                "context_mode": "followup",
                "missing_slots": [],
                "resolver_trace": [
                    "detected_pronoun: 这个",
                    "followup_cue: 那",
                    "filled recipe from session.current_recipe"
                ],
                "signals": { ... },  # 原始信号
                "raw_text": text
            }
        """
        # Step 1: 信号提取
        signals = self.signal_extractor.extract(text)
        
        # Step 1.5: 尝试进行实体识别来填充 mentions
        # 这里我们使用简单的规则匹配，实际项目中可以使用更复杂的 NER 模型
        entities = self._extract_entities_simple(text)
        mentions = self.signal_extractor.extract_mentions(text, entities)
        signals["mentions"] = mentions
        signals["entities"] = entities
        
        # Step 2: 意图解析
        intent_result = self.intent_resolver.resolve(signals, session_context)
        
        # Step 3: 判定上下文模式
        context_mode = self.slot_resolver.determine_context_mode(
            signals, 
            session_context,
            intent_result.get("confidence", 0.0)
        )
        
        # Step 4: 槽位解析
        slots_result = self.slot_resolver.resolve_slots(
            intent_result["intent"],
            signals,
            session_context,
            context_mode
        )
        
        # Step 5: 构建解析追踪
        resolver_trace = self._build_resolver_trace(
            signals, 
            intent_result, 
            slots_result,
            context_mode
        )
        
        # Step 6: 组装最终结果
        result = {
            "intent": {
                "value": intent_result["intent"],
                "confidence": intent_result["confidence"],
                "reason": intent_result.get("reason", []),
                "source": "intent_resolver"
            },
            "slots": slots_result["slots"],
            "context_mode": context_mode,
            "missing_slots": slots_result["missing_slots"],
            "filled_slots": slots_result["filled_slots"],
            "resolver_trace": resolver_trace,
            "signals": signals,
            "raw_text": text
        }
        
        return result
    
    def _build_resolver_trace(
        self,
        signals: Dict[str, Any],
        intent_result: Dict[str, Any],
        slots_result: Dict[str, Any],
        context_mode: str
    ) -> List[str]:
        """构建解析追踪记录
        
        Args:
            signals: 信号
            intent_result: 意图解析结果
            slots_result: 槽位解析结果
            context_mode: 上下文模式
            
        Returns:
            List[str]: 解析追踪记录
        """
        trace = []
        
        cues = signals.get("cues", {})
        
        # 记录信号检测
        if cues.get("has_pronoun"):
            trace.append(f"detected_pronoun: {cues.get('pronoun_text')}")
        
        if cues.get("has_followup_cue"):
            trace.append(f"followup_cue: {cues.get('followup_cue_text')}")
        
        if cues.get("is_question"):
            trace.append("detected_question")
        
        # 记录意图解析
        trace.append(f"intent_resolved: {intent_result['intent']} (confidence: {intent_result['confidence']:.2f})")
        for reason in intent_result.get("reason", []):
            trace.append(f"  reason: {reason}")
        
        # 记录上下文模式
        trace.append(f"context_mode: {context_mode}")
        
        # 记录槽位填充
        for slot_name, slot_info in slots_result["slots"].items():
            if slot_info["value"] is not None:
                trace.append(f"filled {slot_name}: {slot_info['value']} (source: {slot_info['source']}, confidence: {slot_info['confidence']:.2f})")
        
        # 记录缺失槽位
        for missing_slot in slots_result["missing_slots"]:
            trace.append(f"missing_slot: {missing_slot}")
        
        return trace
    
    def _extract_entities_simple(self, text: str) -> List[Dict[str, Any]]:
        """简单的实体提取（规则匹配）
        
        Args:
            text: 用户输入文本
            
        Returns:
            List[Dict]: 提取的实体列表
        """
        entities = []
        text_lower = text.lower()
        
        # 常见的配方名称
        common_recipes = [
            "margarita", "mojito", "martini", "negroni", "cosmopolitan",
            "daiquiri", "old fashioned", "manhattan", "whiskey sour",
            "玛格丽特", "莫吉托", "马天尼", "尼格罗尼", "大都会",
            "戴吉利", "古典", "曼哈顿", "威士忌酸"
        ]
        
        # 常见的食材名称
        common_ingredients = [
            "lime juice", "lemon juice", "orange juice", "vodka", "gin", "rum",
            "tequila", "mezcal", "whiskey", "bourbon", "scotch", "brandy",
            "cognac", "vermouth", "bitters", "syrup", "soda", "tonic",
            "青柠汁", "柠檬汁", "橙汁", "伏特加", "金酒", "朗姆酒",
            "龙舌兰", "威士忌", "波本", "白兰地", "苦精", "糖浆"
        ]
        
        # 提取配方
        for recipe in common_recipes:
            if recipe.lower() in text_lower:
                start = text_lower.find(recipe.lower())
                entities.append({
                    "text": text[start:start+len(recipe)],
                    "label": "RECIPE",
                    "start": start,
                    "end": start + len(recipe),
                    "confidence": 0.8
                })
                break  # 只取第一个匹配的配方
        
        # 提取食材（按长度排序，优先匹配长的）
        sorted_ingredients = sorted(common_ingredients, key=len, reverse=True)
        for ingredient in sorted_ingredients:
            if ingredient.lower() in text_lower:
                start = text_lower.find(ingredient.lower())
                entities.append({
                    "text": text[start:start+len(ingredient)],
                    "label": "INGREDIENT",
                    "start": start,
                    "end": start + len(ingredient),
                    "confidence": 0.8
                })
                break  # 只取第一个匹配的食材
        
        return entities
    
    def get_simple_result(self, parse_result: Dict[str, Any]) -> Dict[str, Any]:
        """获取简化版解析结果（兼容旧接口）
        
        Args:
            parse_result: 完整解析结果
            
        Returns:
            Dict: 简化版结果，兼容旧接口
        """
        intent_value = parse_result["intent"]["value"]
        slots = parse_result["slots"]
        
        # 提取槽位值
        recipe = slots.get("recipe", {}).get("value")
        ingredient = slots.get("ingredient", {}).get("value")
        candidate_substitute = slots.get("candidate_substitute", {}).get("value")
        
        # 提取信号
        signals = parse_result.get("signals", {})
        cues = signals.get("cues", {})
        
        return {
            "intent": intent_value,
            "recipe": recipe,
            "ingredient": ingredient,
            "candidate_substitute": candidate_substitute,
            "has_pronoun_reference": cues.get("has_pronoun", False),
            "reference_text": cues.get("pronoun_text"),
            "is_followup": cues.get("has_followup_cue", False),
            "is_short_question": cues.get("is_question", False) and len(parse_result.get("raw_text", "")) < 20,
            "context_mode": parse_result.get("context_mode"),
            "missing_slots": parse_result.get("missing_slots", [])
        }


# 创建全局当前轮解析器实例
current_turn_parser = CurrentTurnParser()
