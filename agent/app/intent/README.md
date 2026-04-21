# 意图分析模块 (Intent Module)

## 模块概述

意图分析模块负责识别用户的意图，决定如何处理用户的请求。它采用混合分类方法，结合规则分类和LLM分类，提高分类准确性。

## 目录结构

```
intent/
├── __init__.py
├── intent_resolver.py         # 意图解析器
├── intent_router.py           # 意图路由器
├── llm_intent_router.py       # LLM意图路由器
└── llm_rule_learner.py        # LLM规则学习器
```

## 核心功能

### 1. 意图分类

- **规则分类**：使用正则表达式和关键词匹配识别意图
- **LLM分类**：使用大语言模型识别复杂意图
- **混合分类**：结合规则分类和LLM分类，提高准确性

### 2. 意图类型

- `recipe_search` - 搜索食谱
- `recipe_structure` - 查询食谱结构
- `ingredient_neighbors` - 查询食材邻域
- `substitute_recommendation` - 推荐替代原料
- `recommendation` - 推荐饮品
- `general_chat` - 日常交流

### 3. 意图解析

- **意图识别**：识别用户的意图类型
- **意图验证**：验证意图的有效性
- **意图路由**：根据意图类型路由到相应的处理逻辑

## 使用方法

### 意图分类

```python
from app.intent.intent_router import intent_router

# 分类用户查询
result = intent_router.classify("推荐一款适合夏天的鸡尾酒")
print(f"意图: {result['intent']}")
print(f"置信度: {result['confidence']}")
print(f"分类方法: {result.get('method', 'unknown')}")
```

### LLM意图分类

```python
from app.intent.llm_intent_router import llm_intent_router

# 使用LLM分类用户查询
result = llm_intent_router.classify("我想喝酸甜的酒")
print(f"意图: {result['intent']}")
print(f"置信度: {result['confidence']}")
print(f"分类方法: {result.get('method', 'unknown')}")
```

## 配置

意图分析的配置在以下文件中定义：

- `config/llm_prompts.yaml` - LLM提示词配置
- `config/retrieval_config.yaml` - 检索相关配置

## 常见问题

### 1. 意图分类错误

可以通过以下方式改进：

- 更新 `intent_router.py` 中的规则模式
- 调整 `llm_intent_router.py` 中的 LLM 提示词
- 增加更多的训练数据

### 2. 置信度低

检查用户输入是否清晰，或者调整置信度阈值配置。