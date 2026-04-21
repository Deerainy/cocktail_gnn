#!/usr/bin/env python3
"""
解析结果结构模块

定义统一的解析结果结构，用于后续的执行层处理
"""

from typing import Dict, Any, List, Optional

class ParsedEntity:
    """解析后的实体结构"""
    def __init__(self, text: str, label: str, entity_id: Optional[int] = None,
                 canonical_name: Optional[str] = None, confidence: float = 0.0):
        """初始化解析后的实体
        
        Args:
            text: 实体文本
            label: 实体标签
            entity_id: 实体ID
            canonical_name: 规范化名称
            confidence: 置信度
        """
        self.text = text
        self.label = label
        self.entity_id = entity_id
        self.canonical_name = canonical_name
        self.confidence = confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict: 实体字典
        """
        return {
            "text": self.text,
            "label": self.label,
            "entity_id": self.entity_id,
            "canonical_name": self.canonical_name,
            "confidence": self.confidence
        }

class ParsedQuery:
    """解析后的查询结构"""
    def __init__(self, intent: str, entities: List[ParsedEntity],
                 suggested_action: Optional[str] = None, constraints: Optional[Dict[str, Any]] = None,
                 top_k: int = 5, need_explanation: bool = True):
        """初始化解析后的查询
        
        Args:
            intent: 意图
            entities: 实体列表
            suggested_action: 建议的动作
            constraints: 约束条件
            top_k: 返回结果数量
            need_explanation: 是否需要解释
        """
        self.intent = intent
        self.entities = entities
        self.suggested_action = suggested_action
        self.constraints = constraints or {}
        self.top_k = top_k
        self.need_explanation = need_explanation
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict: 查询字典
        """
        return {
            "intent": self.intent,
            "entities": [entity.to_dict() for entity in self.entities],
            "suggested_action": self.suggested_action,
            "constraints": self.constraints,
            "top_k": self.top_k,
            "need_explanation": self.need_explanation
        }
    
    @classmethod
    def from_analysis_result(cls, analysis_result: Dict[str, Any]) -> "ParsedQuery":
        """从分析结果创建解析查询
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            ParsedQuery: 解析后的查询
        """
        # 提取实体
        entities = []
        for entity in analysis_result.get("entities", []):
            parsed_entity = ParsedEntity(
                text=entity.get("text"),
                label=entity.get("label"),
                entity_id=entity.get("entity_id"),
                canonical_name=entity.get("canonical_name"),
                confidence=entity.get("confidence", 0.0)
            )
            entities.append(parsed_entity)
        
        # 提取建议动作
        suggested_action = None
        response_suggestion = analysis_result.get("response_suggestion", {})
        if response_suggestion:
            suggested_action = response_suggestion.get("action")
        
        # 提取约束条件
        constraints = {}
        if response_suggestion:
            target = response_suggestion.get("target")
            if target:
                constraints["target"] = target
        
        # 创建解析查询
        parsed_query = cls(
            intent=analysis_result.get("intent", "general_chat"),
            entities=entities,
            suggested_action=suggested_action,
            constraints=constraints,
            top_k=5,
            need_explanation=True
        )
        
        return parsed_query
