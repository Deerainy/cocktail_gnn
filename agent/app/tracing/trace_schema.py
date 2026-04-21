#!/usr/bin/env python3
"""
思考流程数据结构模块

定义统一的思考流程数据结构，将系统的处理过程转换为结构化的推理轨迹
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

class TraceStep:
    """思考流程步骤"""
    def __init__(self, step: int, name: str, title: str, status: str, data: Dict[str, Any]):
        self.step = step
        self.name = name
        self.title = title
        self.status = status
        self.data = data
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step": self.step,
            "name": self.name,
            "title": self.title,
            "status": self.status,
            "timestamp": self.timestamp,
            "data": self.data
        }

class Trace:
    """思考流程轨迹"""
    def __init__(self, user_query: str):
        self.trace_id = str(uuid.uuid4())
        self.user_query = user_query
        self.steps: List[TraceStep] = []
        self.created_at = datetime.now().isoformat()

    def add_step(self, step: int, name: str, title: str, status: str, data: Dict[str, Any]):
        """添加步骤"""
        trace_step = TraceStep(step, name, title, status, data)
        self.steps.append(trace_step)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "user_query": self.user_query,
            "created_at": self.created_at,
            "steps": [step.to_dict() for step in self.steps]
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        import json
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def save_to_file(self, file_path: str):
        """保存到文件"""
        import json
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Trace':
        """从字典创建Trace对象"""
        trace = cls(data.get('user_query', ''))
        trace.trace_id = data.get('trace_id', str(uuid.uuid4()))
        trace.created_at = data.get('created_at', datetime.now().isoformat())
        
        for step_data in data.get('steps', []):
            step = step_data.get('step', 0)
            name = step_data.get('name', '')
            title = step_data.get('title', '')
            status = step_data.get('status', 'unknown')
            step_data_dict = step_data.get('data', {})
            trace_step = TraceStep(step, name, title, status, step_data_dict)
            trace.steps.append(trace_step)
        
        return trace

# 示例使用
def create_sample_trace():
    """创建示例trace"""
    trace = Trace("龙舌兰酒可以换成什么")
    
    # 输入理解
    trace.add_step(
        step=1,
        name="input_analysis",
        title="输入理解",
        status="success",
        data={
            "language": "zh",
            "normalized_text": "龙舌兰酒可以换成什么"
        }
    )
    
    # 实体识别
    trace.add_step(
        step=2,
        name="entity_recognition",
        title="实体识别",
        status="success",
        data={
            "entities": [
                {
                    "text": "龙舌兰酒",
                    "type": "CANONICAL",
                    "canonical_name": "tequila",
                    "source": "bilingual_mapping"
                }
            ]
        }
    )
    
    # 意图判断
    trace.add_step(
        step=3,
        name="intent_classification",
        title="意图判断",
        status="success",
        data={
            "intent": "substitute_recommendation",
            "router": "llm_intent_router"
        }
    )
    
    # 动作规划
    trace.add_step(
        step=4,
        name="action_planning",
        title="动作规划",
        status="success",
        data={
            "action": "get_substitute",
            "params": {
                "canonical_name": "tequila"
            }
        }
    )
    
    # 数据检索
    trace.add_step(
        step=5,
        name="tool_execution",
        title="数据检索",
        status="success",
        data={
            "backend": "neo4j",
            "result_count": 5
        }
    )
    
    # 答案生成
    trace.add_step(
        step=6,
        name="answer_generation",
        title="答案生成",
        status="success",
        data={
            "summary": "为你找到 5 个可替代原料"
        }
    )
    
    return trace

if __name__ == "__main__":
    # 创建示例trace
    trace = create_sample_trace()
    print(trace.to_json())
    
    # 保存到文件
    trace.save_to_file("sample_trace.json")
    print("Sample trace saved to sample_trace.json")
