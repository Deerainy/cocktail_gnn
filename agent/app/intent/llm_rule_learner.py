#!/usr/bin/env python3
"""
LLM 规则学习器模块

结合 LLM 分析用户输入，自动学习新的意图规则和关键词，
并将其添加到配置文件中，实现规则的持续优化。
"""

import json
import os
import yaml
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class LLMRuleLearner:
    """LLM 规则学习器
    
    职责：
    1. 使用 LLM 分析无法识别的用户输入
    2. 提取新的意图、关键词和槽位
    3. 验证新规则的质量
    4. 自动合并到现有配置
    5. 持久化更新到配置文件
    """
    
    def __init__(self, 
                 rules_file: Optional[str] = None,
                 llm_client=None,
                 auto_save: bool = True,
                 confidence_threshold: float = 0.7):
        """初始化 LLM 规则学习器
        
        Args:
            rules_file: 规则配置文件路径
            llm_client: LLM 客户端（如 OpenAI 客户端）
            auto_save: 是否自动保存学习到的规则
            confidence_threshold: 规则置信度阈值，低于此值不保存
        """
        if rules_file is None:
            rules_file = os.path.join(
                os.path.dirname(__file__), 
                "..", "analysis", 
                "parser_rules.yaml"
            )
        
        self.rules_file = rules_file
        self.llm_client = llm_client
        self.auto_save = auto_save
        self.confidence_threshold = confidence_threshold
        
        # 加载现有规则
        self._load_rules()
        
        # 学习历史（用于避免重复学习）
        self.learned_rules_history = []
    
    def _load_rules(self):
        """加载现有规则"""
        if os.path.exists(self.rules_file):
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                self.rules = yaml.safe_load(f) or {}
        else:
            self.rules = {
                "pronouns": [],
                "followup_cues": [],
                "intent_rules": {},
                "intent_slots": {},
                "slot_config": {}
            }
    
    def _save_rules(self):
        """保存规则到文件"""
        # 备份原文件
        if os.path.exists(self.rules_file):
            backup_file = f"{self.rules_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                with open(backup_file, 'w', encoding='utf-8') as bf:
                    bf.write(f.read())
        
        # 保存新规则
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.rules, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    
    def analyze_unknown_input(self, 
                             text: str, 
                             context: Optional[Dict[str, Any]] = None,
                             current_intent: Optional[str] = None) -> Dict[str, Any]:
        """分析无法识别的用户输入
        
        Args:
            text: 用户输入文本
            context: 当前会话上下文
            current_intent: 当前识别到的意图（可能不准确）
            
        Returns:
            Dict: 分析结果，包含建议的新规则
        """
        if not self.llm_client:
            return {
                "success": False,
                "error": "LLM 客户端未配置",
                "suggested_rules": None
            }
        
        # 构建提示
        prompt = self._build_analysis_prompt(text, context, current_intent)
        
        try:
            # 调用 LLM 分析
            response = self._call_llm(prompt)
            
            # 解析 LLM 响应
            suggested_rules = self._parse_llm_response(response)
            
            # 验证规则质量
            validated_rules = self._validate_rules(suggested_rules, text)
            
            return {
                "success": True,
                "original_text": text,
                "suggested_rules": validated_rules,
                "confidence": validated_rules.get("confidence", 0.0),
                "raw_response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggested_rules": None
            }
    
    def _build_analysis_prompt(self, 
                              text: str, 
                              context: Optional[Dict[str, Any]],
                              current_intent: Optional[str]) -> str:
        """构建 LLM 分析提示"""
        
        # 获取现有规则作为参考
        existing_intents = list(self.rules.get("intent_rules", {}).keys())
        existing_pronouns = self.rules.get("pronouns", [])
        existing_followup_cues = self.rules.get("followup_cues", [])
        
        prompt = f"""你是一个专业的对话系统规则学习助手。请分析以下用户输入，并判断是否需要创建新的意图规则或扩展现有规则。

## 用户输入
"{text}"

## 当前会话上下文
{json.dumps(context, ensure_ascii=False, indent=2) if context else "无"}

## 当前识别到的意图
{current_intent if current_intent else "未识别"}

## 现有意图规则
{json.dumps(existing_intents, ensure_ascii=False)}

## 现有指代词
{json.dumps(existing_pronouns, ensure_ascii=False)}

## 现有追问连接词
{json.dumps(existing_followup_cues, ensure_ascii=False)}

## 任务
请分析这个用户输入，并返回 JSON 格式的结果：

```json
{{
  "analysis": "对用户输入的分析",
  "intent_classification": {{
    "is_new_intent": true/false,
    "intent_name": "意图名称（英文小写+下划线）",
    "confidence": 0.0-1.0,
    "reason": "判断理由"
  }},
  "suggested_keywords": ["关键词1", "关键词2"],
  "required_slots": ["必需的槽位"],
  "optional_slots": ["可选的槽位"],
  "new_pronouns": ["新的指代词（如果有）"],
  "new_followup_cues": ["新的追问连接词（如果有）"],
  "description": "意图描述"
}}
```

注意事项：
1. 如果用户输入可以归类到现有意图，is_new_intent 设为 false
2. 只有当现有意图都无法匹配时，才创建新意图
3. 意图名称使用英文小写+下划线格式，如 "recipe_query"
4. 关键词应该包含触发该意图的典型词汇
5. 槽位包括：recipe（配方）、ingredient（食材）、candidate_substitute（候选替代）
6. 置信度表示你对这个分类的确信程度（0-1）
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        # 这里使用简单的实现，实际项目中可以使用 OpenAI、DeepSeek 等
        # 如果已经有 bartender_llm，可以复用
        try:
            from services.bartender_llm import bartender_llm
            return bartender_llm.generate_response(prompt)
        except Exception as e:
            # 如果没有配置 LLM，返回模拟响应
            print(f"LLM 调用失败: {e}")
            return self._mock_llm_response(prompt)
    
    def _mock_llm_response(self, prompt: str) -> str:
        """模拟 LLM 响应（用于测试）"""
        # 简单的规则匹配，实际项目中应该调用真实 LLM
        if "价格" in prompt or "多少钱" in prompt:
            return json.dumps({
                "analysis": "用户询问价格信息",
                "intent_classification": {
                    "is_new_intent": True,
                    "intent_name": "price_query",
                    "confidence": 0.85,
                    "reason": "包含'价格'、'多少钱'等关键词"
                },
                "suggested_keywords": ["价格", "多少钱", "费用", "贵不贵"],
                "required_slots": ["recipe"],
                "optional_slots": ["ingredient"],
                "new_pronouns": [],
                "new_followup_cues": [],
                "description": "价格查询"
            }, ensure_ascii=False)
        
        return json.dumps({
            "analysis": "无法确定意图",
            "intent_classification": {
                "is_new_intent": False,
                "intent_name": "general_chat",
                "confidence": 0.5,
                "reason": "无法匹配到明确的意图模式"
            },
            "suggested_keywords": [],
            "required_slots": [],
            "optional_slots": [],
            "new_pronouns": [],
            "new_followup_cues": [],
            "description": ""
        }, ensure_ascii=False)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        try:
            # 尝试直接解析 JSON
            return json.loads(response)
        except json.JSONDecodeError:
            # 尝试从 Markdown 代码块中提取 JSON
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # 尝试从文本中提取 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            raise ValueError("无法解析 LLM 响应")
    
    def _validate_rules(self, suggested_rules: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """验证规则质量"""
        validated = suggested_rules.copy()
        
        # 检查置信度
        confidence = validated.get("intent_classification", {}).get("confidence", 0.0)
        validated["confidence"] = confidence
        
        # 检查是否已有相似规则（避免重复）
        intent_name = validated.get("intent_classification", {}).get("intent_name", "")
        if intent_name in self.rules.get("intent_rules", {}):
            validated["is_duplicate"] = True
            validated["validation_message"] = f"意图 '{intent_name}' 已存在"
        else:
            validated["is_duplicate"] = False
        
        # 检查关键词是否为空
        keywords = validated.get("suggested_keywords", [])
        if not keywords and validated.get("intent_classification", {}).get("is_new_intent", False):
            validated["validation_message"] = "新意图必须有至少一个关键词"
            validated["confidence"] = 0.0
        
        return validated
    
    def learn_rules(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """学习新规则并更新配置
        
        Args:
            analysis_result: analyze_unknown_input 的返回结果
            
        Returns:
            Dict: 学习结果
        """
        if not analysis_result.get("success", False):
            return {
                "success": False,
                "error": analysis_result.get("error", "分析失败"),
                "rules_added": []
            }
        
        suggested_rules = analysis_result.get("suggested_rules", {})
        
        # 检查置信度
        confidence = suggested_rules.get("confidence", 0.0)
        if confidence < self.confidence_threshold:
            return {
                "success": False,
                "error": f"置信度 {confidence:.2f} 低于阈值 {self.confidence_threshold}",
                "rules_added": []
            }
        
        # 检查是否重复
        if suggested_rules.get("is_duplicate", False):
            return {
                "success": False,
                "error": suggested_rules.get("validation_message", "规则重复"),
                "rules_added": []
            }
        
        rules_added = []
        
        # 1. 学习新意图规则
        intent_class = suggested_rules.get("intent_classification", {})
        if intent_class.get("is_new_intent", False):
            intent_name = intent_class.get("intent_name", "")
            keywords = suggested_rules.get("suggested_keywords", [])
            required_slots = suggested_rules.get("required_slots", [])
            optional_slots = suggested_rules.get("optional_slots", [])
            description = suggested_rules.get("description", "")
            
            if intent_name and keywords:
                # 添加到意图规则
                self.rules["intent_rules"][intent_name] = {
                    "keywords": keywords,
                    "required_slots": required_slots,
                    "optional_slots": optional_slots,
                    "description": description,
                    "learned_from": analysis_result.get("original_text", ""),
                    "learned_at": datetime.now().isoformat(),
                    "confidence": confidence
                }
                
                # 添加到意图槽位配置
                self.rules["intent_slots"][intent_name] = {
                    "required": required_slots,
                    "optional": optional_slots
                }
                
                rules_added.append(f"intent:{intent_name}")
        
        # 2. 学习新的指代词
        new_pronouns = suggested_rules.get("new_pronouns", [])
        for pronoun in new_pronouns:
            if pronoun not in self.rules.get("pronouns", []):
                self.rules["pronouns"].append(pronoun)
                rules_added.append(f"pronoun:{pronoun}")
        
        # 3. 学习新的追问连接词
        new_followup_cues = suggested_rules.get("new_followup_cues", [])
        for cue in new_followup_cues:
            if cue not in self.rules.get("followup_cues", []):
                self.rules["followup_cues"].append(cue)
                rules_added.append(f"followup_cue:{cue}")
        
        # 保存规则
        if rules_added and self.auto_save:
            self._save_rules()
        
        # 记录学习历史
        self.learned_rules_history.append({
            "timestamp": datetime.now().isoformat(),
            "original_text": analysis_result.get("original_text", ""),
            "rules_added": rules_added,
            "confidence": confidence
        })
        
        return {
            "success": True,
            "rules_added": rules_added,
            "confidence": confidence,
            "rules_file": self.rules_file if self.auto_save else None
        }
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """获取学习统计信息"""
        return {
            "total_learned_rules": len(self.learned_rules_history),
            "learned_rules_history": self.learned_rules_history,
            "current_intent_rules_count": len(self.rules.get("intent_rules", {})),
            "current_pronouns_count": len(self.rules.get("pronouns", [])),
            "current_followup_cues_count": len(self.rules.get("followup_cues", []))
        }


# 创建全局 LLM 规则学习器实例
llm_rule_learner = LLMRuleLearner()
