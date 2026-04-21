#!/usr/bin/env python3
"""
槽位解析器模块

只负责"缺什么补什么"，而且要记录来源。
支持统一的槽位解析流程，避免为每个字段写重复逻辑。
"""

from typing import Dict, Any, List, Optional
import yaml
import os


class SlotResolver:
    """槽位解析器
    
    职责：统一槽位解析，记录来源和置信度。
    支持从多个来源填充槽位：显式提到、会话上下文等。
    """
    
    def __init__(self, rules_file: Optional[str] = None):
        """初始化槽位解析器
        
        Args:
            rules_file: 规则配置文件路径，如果为None则使用默认路径
        """
        if rules_file is None:
            # 默认从 analysis 文件夹加载规则
            rules_file = os.path.join(os.path.dirname(__file__), "..", "analysis", "parser_rules.yaml")
        
        # 加载规则配置
        with open(rules_file, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
        
        self.slot_config = self.rules.get("slot_config", {})
        self.intent_slots = self.rules.get("intent_slots", {})
    
    def resolve_slots(
        self, 
        intent: str, 
        signals: Dict[str, Any], 
        session_context=None,
        context_mode: str = "followup"
    ) -> Dict[str, Any]:
        """解析槽位
        
        Args:
            intent: 意图名称
            signals: 信号提取器输出的信号
            session_context: 会话上下文（可选）
            context_mode: 上下文模式（followup/new_topic/uncertain）
            
        Returns:
            Dict: 解析后的槽位，包含值、来源、置信度
            {
                "slots": {
                    "recipe": {
                        "value": "Margarita",
                        "source": "session.current_recipe",
                        "confidence": 0.9
                    },
                    "ingredient": {
                        "value": "lime juice",
                        "source": "explicit",
                        "confidence": 1.0
                    }
                },
                "missing_slots": [],
                "filled_slots": ["recipe", "ingredient"]
            }
        """
        # 获取该意图所需的槽位
        slots_config = self.intent_slots.get(intent, {"required": [], "optional": []})
        required_slots = slots_config.get("required", [])
        optional_slots = slots_config.get("optional", [])
        
        result = {
            "slots": {},
            "missing_slots": [],
            "filled_slots": []
        }
        
        # 显式提到的值
        explicit_mentions = signals.get("mentions", {})
        
        # 解析每个必需槽位
        for slot_name in required_slots:
            slot_result = self._resolve_single_slot(
                slot_name, 
                explicit_mentions, 
                session_context,
                context_mode
            )
            result["slots"][slot_name] = slot_result
            
            if slot_result["value"] is not None:
                result["filled_slots"].append(slot_name)
            else:
                result["missing_slots"].append(slot_name)
        
        # 解析每个可选槽位
        for slot_name in optional_slots:
            slot_result = self._resolve_single_slot(
                slot_name, 
                explicit_mentions, 
                session_context,
                context_mode
            )
            if slot_result["value"] is not None:
                result["slots"][slot_name] = slot_result
                result["filled_slots"].append(slot_name)
        
        return result
    
    def _resolve_single_slot(
        self, 
        slot_name: str, 
        explicit_mentions: Dict[str, Any],
        session_context=None,
        context_mode: str = "followup"
    ) -> Dict[str, Any]:
        """解析单个槽位
        
        Args:
            slot_name: 槽位名称
            explicit_mentions: 显式提到的值
            session_context: 会话上下文
            context_mode: 上下文模式
            
        Returns:
            Dict: 槽位解析结果
        """
        # 获取槽位配置
        slot_cfg = self.slot_config.get(slot_name, {})
        sources = slot_cfg.get("sources", ["explicit"])
        default_confidence = slot_cfg.get("default_confidence", {})
        
        # 1. 首先检查显式提到
        if "explicit" in sources:
            explicit_value = explicit_mentions.get(slot_name)
            if explicit_value is not None:
                return {
                    "value": explicit_value,
                    "source": "explicit",
                    "confidence": default_confidence.get("explicit", 1.0)
                }
        
        # 2. 如果不是新话题，尝试从上下文补全
        if context_mode != "new_topic" and session_context:
            # 从当前配方补全
            if slot_name == "recipe" and "session.current_recipe" in sources:
                if session_context.current_recipe_name:
                    return {
                        "value": session_context.current_recipe_name,
                        "source": "session.current_recipe",
                        "confidence": default_confidence.get("session.current_recipe", 0.9)
                    }
            
            # 从当前食材补全
            if slot_name == "ingredient" and "session.current_canonical" in sources:
                if session_context.current_canonical_name:
                    return {
                        "value": session_context.current_canonical_name,
                        "source": "session.current_canonical",
                        "confidence": default_confidence.get("session.current_canonical", 0.9)
                    }
            
            # 从上一个实体补全
            if session_context.last_entities:
                last_value = session_context.last_entities.get(slot_name)
                if last_value is not None:
                    return {
                        "value": last_value,
                        "source": "session.last_entities",
                        "confidence": default_confidence.get("session.recent_recipes", 0.7)
                    }
        
        # 3. 无法补全
        return {
            "value": None,
            "source": None,
            "confidence": 0.0
        }
    
    def determine_context_mode(
        self, 
        signals: Dict[str, Any], 
        session_context=None,
        intent_confidence: float = 0.0
    ) -> str:
        """判定上下文模式
        
        Args:
            signals: 信号提取器输出的信号
            session_context: 会话上下文
            intent_confidence: 意图置信度
            
        Returns:
            str: 上下文模式（followup/new_topic/uncertain）
        """
        cues = signals.get("cues", {})
        
        # 1. 新话题判定
        # 如果出现了新的 recipe 名，认为是新话题
        mentions = signals.get("mentions", {})
        if mentions.get("recipe") is not None and session_context:
            # 检查是否是新的 recipe
            if session_context.current_recipe_name is None:
                return "new_topic"
            if mentions["recipe"] != session_context.current_recipe_name:
                return "new_topic"
        
        # 2. 不确定判定
        # 如果意图置信度低，或指代模糊
        if intent_confidence < 0.3:
            return "uncertain"
        
        if cues.get("has_pronoun") and not session_context:
            # 有指代词但没有上下文
            return "uncertain"
        
        # 3. 追问判定
        # 有指代词、追问连接词、且槽位兼容
        if cues.get("has_pronoun") or cues.get("has_followup_cue"):
            if session_context and (session_context.current_recipe_name or session_context.current_canonical_name):
                return "followup"
        
        # 默认：新话题
        return "new_topic"


# 创建全局槽位解析器实例
slot_resolver = SlotResolver()
