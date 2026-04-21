#!/usr/bin/env python3
"""
意图解析器模块

根据当前信号 + 上下文状态，推断意图。
使用规则配置 + 打分的方式，而不是硬编码 if-else。
"""

from typing import Dict, Any, List, Optional, Tuple
import yaml
import os


class IntentResolver:
    """意图解析器
    
    职责：根据当前信号 + 上下文状态，推断意图。
    使用规则配置 + 打分的方式，支持扩展新的意图。
    """
    
    def __init__(self, rules_file: Optional[str] = None):
        """初始化意图解析器
        
        Args:
            rules_file: 规则配置文件路径，如果为None则使用默认路径
        """
        if rules_file is None:
            # 默认从 analysis 文件夹加载规则
            rules_file = os.path.join(os.path.dirname(__file__), "..", "analysis", "parser_rules.yaml")
        
        # 加载规则配置
        with open(rules_file, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
        
        self.intent_rules = self.rules.get("intent_rules", {})
    
    def resolve(self, signals: Dict[str, Any], session_context=None) -> Dict[str, Any]:
        """解析意图
        
        Args:
            signals: 信号提取器输出的信号
            session_context: 会话上下文（可选）
            
        Returns:
            Dict: 解析结果，包含意图、置信度、原因
            {
                "intent": "ingredient_substitute",
                "confidence": 0.82,
                "reason": ["keyword:换成", "context:current_recipe_exists"]
            }
        """
        operators = signals.get("operators", [])
        cues = signals.get("cues", {})
        
        # 计算每个意图的得分
        intent_scores = []
        
        for intent_name, intent_config in self.intent_rules.items():
            score, reasons = self._calculate_intent_score(
                intent_name, 
                intent_config, 
                operators, 
                cues,
                session_context
            )
            intent_scores.append({
                "intent": intent_name,
                "score": score,
                "reasons": reasons,
                "config": intent_config
            })
        
        # 按得分排序
        intent_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # 选择得分最高的意图
        if intent_scores and intent_scores[0]["score"] > 0:
            best_match = intent_scores[0]
            return {
                "intent": best_match["intent"],
                "confidence": best_match["score"],
                "reason": best_match["reasons"],
                "all_candidates": intent_scores[:3]  # 保留前3个候选
            }
        
        # 默认返回日常交流
        return {
            "intent": "general_chat",
            "confidence": 0.5,
            "reason": ["no_matching_keywords"],
            "all_candidates": intent_scores[:3]
        }
    
    def _calculate_intent_score(
        self, 
        intent_name: str, 
        intent_config: Dict[str, Any],
        operators: List[Dict[str, Any]],
        cues: Dict[str, Any],
        session_context=None
    ) -> Tuple[float, List[str]]:
        """计算意图得分
        
        Args:
            intent_name: 意图名称
            intent_config: 意图配置
            operators: 操作符信号
            cues: 线索信号
            session_context: 会话上下文
            
        Returns:
            Tuple[float, List[str]]: (得分, 原因列表)
        """
        score = 0.0
        reasons = []
        
        # 1. 关键词匹配得分
        keywords = intent_config.get("keywords", [])
        for op in operators:
            if op["type"] == intent_name:
                # 根据关键词长度给予不同权重
                keyword = op["keyword"]
                if len(keyword) >= 4:
                    score += 0.4  # 长关键词权重更高
                elif len(keyword) >= 2:
                    score += 0.3
                else:
                    score += 0.2
                reasons.append(f"keyword:{keyword}")
        
        # 2. 上下文增强
        if intent_config.get("boost_if_context_has_recipe") and session_context:
            if session_context.current_recipe_name:
                score += 0.2
                reasons.append("context:current_recipe_exists")
        
        # 3. 追问信号增强
        if cues.get("has_followup_cue") and session_context:
            # 如果有追问信号且有上下文，增加置信度
            if session_context.last_intent == intent_name:
                score += 0.15
                reasons.append("context:followup_same_intent")
        
        # 4. 指代词信号
        if cues.get("has_pronoun") and session_context:
            if session_context.current_recipe_name or session_context.current_canonical_name:
                score += 0.1
                reasons.append("context:pronoun_with_context")
        
        # 5. 限制最高得分
        score = min(score, 1.0)
        
        return score, reasons
    
    def get_intent_slots(self, intent: str) -> Dict[str, List[str]]:
        """获取意图所需的槽位
        
        Args:
            intent: 意图名称
            
        Returns:
            Dict: 包含 required 和 optional 槽位列表
        """
        intent_slots_config = self.rules.get("intent_slots", {})
        slots = intent_slots_config.get(intent, {"required": [], "optional": []})
        return slots


# 创建全局意图解析器实例
intent_resolver = IntentResolver()
