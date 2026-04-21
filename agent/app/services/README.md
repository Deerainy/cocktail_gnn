# 服务模块 (Services Module)

## 模块概述

服务模块提供各种核心服务，包括后端服务、LLM服务和推荐服务。它是智能体的核心组件，负责处理业务逻辑和与外部系统的交互。

## 目录结构

```
services/
├── __init__.py
├── backend_service.py         # 后端服务
├── bartender_llm.py           # 调酒师LLM服务
├── llm_assist_service.py      # LLM辅助服务
└── recommendation_service.py  # 推荐服务
```

## 核心功能

### 1. 后端服务

- **数据库操作**：连接MySQL和Neo4j数据库，执行查询
- **数据检索**：检索食谱、食材、替代原料等信息
- **数据处理**：处理和转换数据，为前端和其他服务提供支持

### 2. 调酒师LLM服务

- **角色模拟**：模拟专业调酒师的角色
- **对话生成**：生成友好、专业的调酒师风格响应
- **上下文理解**：理解对话上下文，提供连贯的回答
- **快速响应**：处理常见问题的快速响应

### 3. LLM辅助服务

- **心情分析**：分析用户的心情和情绪
- **风味分析**：分析用户的风味偏好
- **材料提取**：提取用户输入中的材料信息
- **约束识别**：识别用户输入中的约束条件
- **综合分析**：综合分析用户需求

### 4. 推荐服务

- **基于风味推荐**：根据用户的风味偏好推荐饮品
- **基于约束条件**：考虑酒精浓度、价格、场合等约束条件
- **多数据库协同**：结合Neo4j图谱和MySQL关系数据
- **智能评分算法**：综合考虑风味匹配度、流行度和评分
- **专业推荐理由**：生成专业、个性化的推荐理由

## 使用方法

### 后端服务

```python
from app.services.backend_service import backend_service

# 搜索食谱
result = backend_service.search_recipe("Margarita")
print(f"搜索结果: {result}")

# 获取替代原料
result = backend_service.get_substitutes("lime")
print(f"替代原料: {result}")
```

### 调酒师LLM服务

```python
from app.services.bartender_llm import bartender_llm

# 生成响应
response = bartender_llm.generate_response("推荐一款适合夏天的鸡尾酒")
print(f"生成的响应: {response}")
```

### 推荐服务

```python
from app.services.recommendation_service import recommendation_service

# 基于风味推荐
flavors = [{"text": "酸甜", "label": "FLAVOR", "flavor_type": "sweet"}]
result = recommendation_service.recommend_by_flavor(flavors)
print(f"推荐结果: {result}")
```

## 配置

服务模块的配置在 `app/config.py` 文件中定义，支持从环境变量读取：

- `MYSQL_HOST` - MySQL主机地址
- `MYSQL_USER` - MySQL用户名
- `MYSQL_PASSWORD` - MySQL密码
- `NEO4J_URI` - Neo4j连接URI
- `NEO4J_USER` - Neo4j用户名
- `NEO4J_PASSWORD` - Neo4j密码
- `OPENAI_API_KEY` - OpenAI API密钥
- `OPENAI_API_BASE` - OpenAI API基础URL
- `MODEL_NAME` - LLM模型名称

## 常见问题

### 1. 服务调用失败

检查数据库连接是否正常，以及API密钥是否正确。

### 2. 推荐结果不相关

调整推荐算法和参数，或者更新数据库中的数据。

### 3. LLM响应质量差

调整LLM提示词和参数，或者使用更适合的模型。