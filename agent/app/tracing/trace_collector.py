#!/usr/bin/env python3
"""
Trace 收集器

负责收集和管理系统执行过程中的各个步骤，生成结构化的 trace 数据
"""

import uuid
from datetime import datetime

class TraceStep:
    """单个步骤的 trace 数据"""
    def __init__(self, step, name, title, status, data):
        self.step = step
        self.name = name
        self.title = title
        self.status = status
        self.data = data
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "step": self.step,
            "name": self.name,
            "title": self.title,
            "status": self.status,
            "data": self.data,
            "timestamp": self.timestamp
        }

class Trace:
    """完整的 trace 数据"""
    def __init__(self, user_query, session_id=None):
        self.trace_id = str(uuid.uuid4())
        self.user_query = user_query
        self.session_id = session_id
        self.steps = []
        self.created_at = datetime.now().isoformat()
        self.status = "running"
        self.final_answer = None
        self.error_message = None
        # 初始化5大类步骤数据
        self.visualization_steps = {
            "input_analysis": {
                "name": "input_analysis",
                "title": "输入理解",
                "status": "pending",
                "data": {
                    "original_question": user_query,
                    "normalized_question": user_query,
                    "language": "zh" if any('\u4e00' <= char <= '\u9fff' for char in user_query) else "en"
                }
            },
            "entity_recognition": {
                "name": "entity_recognition",
                "title": "实体识别",
                "status": "pending",
                "data": {
                    "entities": [],
                    "hit_method": "none",
                    "needs_review": False
                }
            },
            "intent_classification": {
                "name": "intent_classification",
                "title": "意图判断",
                "status": "pending",
                "data": {
                    "final_intent": None,
                    "candidate_intents": [],
                    "used_fallback": False
                }
            },
            "action_execution": {
                "name": "action_execution",
                "title": "动作执行",
                "status": "pending",
                "data": {
                    "action": None,
                    "params": {},
                    "tool": None
                }
            },
            "retrieval_and_generation": {
                "name": "retrieval_and_generation",
                "title": "检索与结果生成",
                "status": "pending",
                "data": {
                    "database_type": None,
                    "result_count": 0,
                    "final_answer": None,
                    "error_reason": None
                }
            }
        }
    
    def add_step(self, name, title, status, data):
        """添加一个步骤"""
        step = len(self.steps) + 1
        trace_step = TraceStep(step, name, title, status, data)
        self.steps.append(trace_step)
        
        # 更新可视化步骤
        self._update_visualization_step(name, status, data)
        
        return trace_step
    
    def _update_visualization_step(self, name, status, data):
        """更新可视化步骤"""
        if name == "input_analysis":
            self.visualization_steps["input_analysis"].update({
                "status": status,
                "data": {
                    "original_question": self.user_query,
                    "normalized_question": data.get("normalized_text", self.user_query),
                    "language": data.get("language", "zh" if any('\u4e00' <= char <= '\u9fff' for char in self.user_query) else "en")
                }
            })
        elif name == "entity_recognition":
            entities = data.get("entities", [])
            processing_level = data.get("processing_level", "none")
            
            # 确定命中方式
            hit_method = "none"
            if processing_level == "lexicon_rule":
                hit_method = "词典"
            elif processing_level == "fuzzy_match":
                hit_method = "模糊匹配"
            elif processing_level == "llm_analysis":
                hit_method = "LLM"
            
            # 检查是否需要审核
            needs_review = any(e.get("processing_level") in ["llm_analysis", "unrecognized", "fallback"] for e in entities)
            
            self.visualization_steps["entity_recognition"].update({
                "status": status,
                "data": {
                    "entities": entities,
                    "hit_method": hit_method,
                    "needs_review": needs_review
                }
            })
        elif name == "intent_classification":
            self.visualization_steps["intent_classification"].update({
                "status": status,
                "data": {
                    "final_intent": data.get("intent"),
                    "candidate_intents": [data.get("intent")],
                    "used_fallback": data.get("router") in ["rule_fallback", "error_fallback"]
                }
            })
        elif name == "action_planning":
            self.visualization_steps["action_execution"].update({
                "status": status,
                "data": {
                    "action": data.get("action"),
                    "params": data.get("params", {}),
                    "tool": data.get("action")
                }
            })
        elif name == "tool_execution":
            self.visualization_steps["retrieval_and_generation"].update({
                "status": status,
                "data": {
                    "database_type": data.get("backend"),
                    "result_count": data.get("result_count", 0),
                    "final_answer": data.get("recipe") or data.get("ingredient") or None,
                    "error_reason": data.get("error") or data.get("message")
                }
            })
        elif name == "answer_generation":
            self.visualization_steps["retrieval_and_generation"].update({
                "data": {
                    "final_answer": data.get("summary")
                }
            })
    
    def set_final_answer(self, answer):
        """设置最终答案"""
        self.final_answer = answer
        self.status = "success"
        # 更新可视化步骤
        self.visualization_steps["retrieval_and_generation"].update({
            "data": {
                "final_answer": answer
            }
        })
    
    def set_error(self, error_message):
        """设置错误信息"""
        self.error_message = error_message
        self.status = "error"
        # 更新可视化步骤
        self.visualization_steps["retrieval_and_generation"].update({
            "status": "error",
            "data": {
                "error_reason": error_message
            }
        })
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "user_query": self.user_query,
            "status": self.status,
            "final_answer": self.final_answer,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "steps": [step.to_dict() for step in self.steps],
            "visualization_steps": list(self.visualization_steps.values())
        }

class TraceCollector:
    """Trace 收集器"""
    def __init__(self):
        self.traces = {}
    
    def create_trace(self, user_query, session_id=None):
        """创建一个新的 trace"""
        trace = Trace(user_query, session_id)
        self.traces[trace.trace_id] = trace
        return trace
    
    def get_trace(self, trace_id):
        """获取指定的 trace"""
        return self.traces.get(trace_id)
    
    def remove_trace(self, trace_id):
        """移除指定的 trace"""
        if trace_id in self.traces:
            del self.traces[trace_id]
    
    def clear(self):
        """清空所有 trace"""
        self.traces.clear()

# 创建全局 trace 收集器实例
trace_collector = TraceCollector()

# 辅助函数
def create_trace(user_query, session_id=None):
    """创建一个新的 trace"""
    return trace_collector.create_trace(user_query, session_id)

def get_trace(trace_id):
    """获取指定的 trace"""
    return trace_collector.get_trace(trace_id)

def remove_trace(trace_id):
    """移除指定的 trace"""
    trace_collector.remove_trace(trace_id)
