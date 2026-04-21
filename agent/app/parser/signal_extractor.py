#!/usr/bin/env python3
"""
信号提取器模块

只提取当前句里看得见的信号，不做业务决定。
这是四层架构中第3层的第一步：显式信号提取。
"""

from typing import Dict, Any, List, Optional
import yaml
import os


class SignalExtractor:
    """信号提取器
    
    职责：只提取当前句里看得见的信号，不做业务决定。
    例如输出 mentions、cues、operators 等原始信号。
    """
    
    def __init__(self, rules_file: Optional[str] = None):
        """初始化信号提取器
        
        Args:
            rules_file: 规则配置文件路径，如果为None则使用默认路径
        """
        if rules_file is None:
            # 默认从 analysis 文件夹加载规则
            rules_file = os.path.join(os.path.dirname(__file__), "..", "analysis", "parser_rules.yaml")
        
        # 加载规则配置
        with open(rules_file, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
        
        self.pronouns = self.rules.get("pronouns", [])
        self.followup_cues = self.rules.get("followup_cues", [])
        self.intent_rules = self.rules.get("intent_rules", {})
    
    def extract(self, text: str) -> Dict[str, Any]:
        """提取当前句的信号
        
        Args:
            text: 用户输入文本
            
        Returns:
            Dict: 提取的信号，包含 mentions、cues、operators
            {
                "mentions": {
                    "recipe": None,
                    "ingredient": None,
                    "candidate_substitute": None
                },
                "cues": {
                    "has_pronoun": False,
                    "pronoun_text": None,
                    "is_question": False,
                    "has_followup_cue": False,
                    "followup_cue_text": None
                },
                "operators": [],
                "raw_text": text
            }
        """
        result = {
            "mentions": {
                "recipe": None,
                "ingredient": None,
                "candidate_substitute": None
            },
            "cues": {
                "has_pronoun": False,
                "pronoun_text": None,
                "is_question": False,
                "has_followup_cue": False,
                "followup_cue_text": None
            },
            "operators": [],
            "raw_text": text
        }
        
        # 1. 提取指代词信号
        self._extract_pronoun_signals(text, result["cues"])
        
        # 2. 提取追问信号
        self._extract_followup_signals(text, result["cues"])
        
        # 3. 提取问题信号
        self._extract_question_signals(text, result["cues"])
        
        # 4. 提取操作符信号（关键词）
        self._extract_operator_signals(text, result["operators"])
        
        return result
    
    def _extract_pronoun_signals(self, text: str, cues: Dict[str, Any]):
        """提取指代词信号"""
        for pronoun in self.pronouns:
            if pronoun in text:
                cues["has_pronoun"] = True
                cues["pronoun_text"] = pronoun
                break
    
    def _extract_followup_signals(self, text: str, cues: Dict[str, Any]):
        """提取追问信号"""
        for cue in self.followup_cues:
            if cue in text:
                cues["has_followup_cue"] = True
                cues["followup_cue_text"] = cue
                break
    
    def _extract_question_signals(self, text: str, cues: Dict[str, Any]):
        """提取问题信号"""
        # 检测是否是问题
        if any(marker in text for marker in ["?", "？", "吗", "什么", "怎么", "哪里", "谁", "多少"]):
            cues["is_question"] = True
    
    def _extract_operator_signals(self, text: str, operators: List[str]):
        """提取操作符信号（关键词）"""
        # 遍历所有意图规则，提取匹配的关键词
        for intent_name, intent_config in self.intent_rules.items():
            keywords = intent_config.get("keywords", [])
            for keyword in keywords:
                if keyword in text:
                    operators.append({
                        "type": intent_name,
                        "keyword": keyword
                    })
    
    def extract_mentions(self, text: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从实体识别结果中提取 mentions
        
        Args:
            text: 用户输入文本
            entities: 实体识别结果
            
        Returns:
            Dict: mentions 字典
        """
        mentions = {
            "recipe": None,
            "ingredient": None,
            "candidate_substitute": None
        }
        
        # 从实体中提取配方和食材
        for entity in entities:
            label = entity.get("label", "").upper()
            entity_text = entity.get("text", "")
            
            if label == "RECIPE":
                mentions["recipe"] = entity_text
            elif label in ["INGREDIENT", "CANONICAL"]:
                mentions["ingredient"] = entity.get("canonical_name") or entity_text
            elif label == "SUBSTITUTE":
                mentions["candidate_substitute"] = entity_text
        
        return mentions


# 创建全局信号提取器实例
signal_extractor = SignalExtractor()
