# 轨迹收集模块 (Tracing Module)

## 模块概述

轨迹收集模块负责记录和可视化系统的处理过程，用于调试和分析。它跟踪用户输入的处理流程，记录各个环节的结果和执行时间。

## 目录结构

```
tracing/
├── __init__.py
├── trace_collector.py    # 轨迹收集器
└── trace_schema.py       # 轨迹数据结构定义
```

## 核心功能

### 1. 轨迹收集

- **开始轨迹**：开始一个新的处理轨迹
- **添加步骤**：添加处理步骤和结果
- **结束轨迹**：结束处理轨迹并保存
- **查询轨迹**：查询历史轨迹数据

### 2. 轨迹数据结构

- **会话信息**：会话ID、用户ID等
- **输入信息**：用户输入的文本、语言等
- **处理步骤**：各个处理环节的结果和执行时间
- **输出信息**：系统生成的回答、推荐等

## 使用方法

### 轨迹收集

```python
from app.tracing.trace_collector import TraceCollector

# 创建轨迹收集器
collector = TraceCollector()

# 开始轨迹
trace_id = collector.start_trace("用户输入", "我想喝酸甜的鸡尾酒")

# 添加步骤
collector.add_step(trace_id, "实体识别", {"entities": [{"text": "酸甜", "label": "FLAVOR"}]})
collector.add_step(trace_id, "意图分类", {"intent": "recommendation", "confidence": 0.9})

# 结束轨迹
collector.end_trace(trace_id, {"answer": "推荐您尝试玛格丽特鸡尾酒，它酸甜可口，非常适合夏天饮用。"})
```

### 查询轨迹

```python
from app.tracing.trace_collector import TraceCollector

# 创建轨迹收集器
collector = TraceCollector()

# 查询轨迹
trace = collector.get_trace("trace_id")
print(f"轨迹数据: {trace}")

# 查询会话轨迹
session_traces = collector.get_session_traces("session_id")
print(f"会话轨迹: {session_traces}")
```

## 常见问题

### 1. 轨迹保存失败

检查数据库连接是否正常，以及权限是否足够。

### 2. 轨迹查询失败

确保轨迹ID或会话ID正确，并且轨迹数据存在。