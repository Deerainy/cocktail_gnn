# 解析器模块 (Parser Module)

## 模块概述

解析器模块负责解析用户输入，提取信号和槽位，为意图识别和实体处理提供支持。它处理当前轮次的输入，并与会话上下文结合，生成结构化的解析结果。

## 目录结构

```
parser/
├── __init__.py
├── current_turn_parser.py    # 当前轮次解析器
├── signal_extractor.py       # 信号提取器
└── slot_resolver.py          # 槽位解析器
```

## 核心功能

### 1. 当前轮次解析

- **输入预处理**：处理用户输入的文本
- **信号提取**：提取输入中的各种信号
- **槽位解析**：解析输入中的槽位信息
- **上下文结合**：结合会话上下文进行解析

### 2. 信号提取

- **提及检测**：检测输入中提及的食谱、食材等实体
- **线索提取**：提取输入中的代词、问题标记等线索
- **操作符提取**：提取输入中的操作符
- **实体提取**：提取输入中的实体

### 3. 槽位解析

- **槽位填充**：填充识别到的槽位
- **槽位验证**：验证槽位的有效性
- **槽位冲突处理**：处理槽位冲突

## 使用方法

### 当前轮次解析

```python
from app.parser.current_turn_parser import CurrentTurnParser

# 创建当前轮次解析器
parser = CurrentTurnParser()

# 解析用户输入
text = "我想喝酸甜的鸡尾酒"
parsed_result = parser.parse(text)
print(f"解析结果: {parsed_result}")
```

### 信号提取

```python
from app.parser.signal_extractor import SignalExtractor

# 创建信号提取器	extractor = SignalExtractor()

# 提取信号
text = "我想喝酸甜的鸡尾酒"
signals = extractor.extract_signals(text)
print(f"提取的信号: {signals}")
```

### 槽位解析

```python
from app.parser.slot_resolver import SlotResolver

# 创建槽位解析器
resolver = SlotResolver()

# 解析槽位
signals = {"mentions": {"recipe": None, "ingredient": None}, "cues": {}, "operators": [], "entities": []}
slots = resolver.resolve_slots(signals)
print(f"解析的槽位: {slots}")
```

## 常见问题

### 1. 解析结果不准确

检查输入文本是否清晰，或者调整解析规则和模式。

### 2. 槽位填充失败

确保实体识别准确，并且槽位定义正确。