# 图数据库服务实现与 Agent 工具封装

## 一、项目背景

本项目旨在为 Django 后端设计并实现一层规范的 graph tool / graph service，用于前端页面、局部图谱展示、替代推理页面以及未来 agent 调用。

## 二、开发目标

当前阶段的目标是基于现有图数据库实现一层“最小可用但结构完整”的 graph tools / graph service，为：
1. 前端页面提供稳定的数据接口
2. 后续 agent 提供可调用的结构化图查询能力
3. 将 Neo4j 查询逻辑从业务逻辑中解耦
4. 为未来扩展到 GraphRAG / agent system 打下基础

## 三、技术实现

### 1. 后端图数据库服务

#### 目录结构

```
backend/
  graph/
    __init__.py
    client.py              # Neo4j 连接层
    queries/               # 查询层
      __init__.py
      recipe_queries.py    # 食谱相关查询
      substitute_queries.py # 替代相关查询
      canonical_queries.py # 规范食材相关查询
    services/              # 服务层
      __init__.py
      recipe_service.py    # 食谱相关服务
      substitute_service.py # 替代相关服务
      canonical_service.py # 规范食材相关服务
    utils/                 # 工具层
      __init__.py
      formatters.py        # 结果格式化工具
    views.py               # API 接口层
    urls.py                # 路由配置
```

#### 核心功能

1. **获取食谱子图**：根据 recipe_id，返回一个 recipe 的局部图谱信息
2. **获取全局替代候选**：根据某个 CanonicalIngredient，返回全局替代候选
3. **获取食谱替代结果**：返回某个 recipe 在具体配方上下文中的替代结果
4. **获取规范食材邻域**：围绕某个 CanonicalIngredient，返回其邻域结构
5. **搜索食谱**：根据关键词搜索食谱
6. **搜索规范食材**：根据关键词搜索规范食材

#### 技术特点

- **分层设计**：清晰的职责分离，便于维护和扩展
- **标准化输出**：所有函数输出为 Python dict / list，可直接 JSON 序列化
- **真实 schema**：严格基于提供的 Neo4j 图数据库 schema 设计
- **易于集成**：提供 REST API 接口，可直接与 Django 集成
- **异常处理**：包含基本的异常处理，确保服务稳定性

### 2. 问题解决过程

#### 问题 1：Neo4j 连接认证失败

**原因**：密码错误和认证速率限制
**解决方案**：
- 使用与 Neo4j Browser 相同的连接方式
- 确保使用正确的密码
- 避免频繁尝试连接，防止触发速率限制

#### 问题 2：查询结果为空

**原因**：字段类型和字段名不一致
**解决方案**：
- 在所有查询中添加类型转换，确保能够匹配字符串和整数类型的 ID
- 使用正确的字段名，如 `canonical_name` 而不是 `name`
- 确保使用正确的节点标签，如 `CanonicalIngredient` 而不是 `Canonical`

#### 问题 3：接口报错 500

**原因**：使用集合来去重时，字典不可哈希
**解决方案**：
- 修改 `format_recipe_subgraph` 函数，使用列表和字典来实现去重
- 避免使用 `set()` 来存储字典对象

### 3. Agent 工具封装

#### 目录结构

```
agent/
  app/
    tools/
      backend_graph_tools.py # 后端图数据库工具
```

#### 核心功能

1. `search_recipe(keyword)` - 根据关键词搜索食谱
2. `search_canonical(keyword)` - 根据关键词搜索规范食材
3. `get_recipe_subgraph(recipe_id)` - 获取食谱子图
4. `get_canonical_neighbors(canonical_id)` - 获取规范食材邻域
5. `get_global_substitutes(canonical_id)` - 获取全局替代候选
6. `get_recipe_substitute_results(recipe_id)` - 获取食谱替代结果

#### 统一返回格式

所有工具函数都返回统一格式的字典，包含以下字段：

```python
{
    "success": True,  # 布尔值，表示操作是否成功
    "data": ...,      # 具体的数据，根据不同的工具函数返回不同的结构
    "source": "tool_name",  # 工具名称，用于标识数据来源
    "message": ""     # 错误消息，成功时为空字符串
}
```

#### 技术特点

- **封装性**：封装了所有后端 API 调用，Agent 不需要直接知道 URL
- **错误处理**：包含基本的错误处理，确保即使 API 调用失败也能返回合理的默认值
- **易用性**：提供简洁的函数接口，便于 Agent 调用
- **统一格式**：所有工具函数返回统一格式的结果，便于 Agent 处理

#### 使用示例

```python
from app.tools.backend_graph_tools import backend_graph_tools

# 搜索食谱
result = backend_graph_tools.search_recipe("test")
if result["success"]:
    recipes = result["data"]
    # 处理食谱数据
else:
    error_message = result["message"]
    # 处理错误

# 获取食谱子图
result = backend_graph_tools.get_recipe_subgraph("1")
if result["success"]:
    subgraph = result["data"]
    # 处理子图数据
else:
    error_message = result["message"]
    # 处理错误
```

## 四、API 接口

所有 API 接口都以 `/api/graph/` 为前缀，例如：
- `GET /api/graph/recipe/subgraph/{recipe_id}/` - 获取食谱子图
- `GET /api/graph/canonical/substitutes/{canonical_id}/` - 获取全局替代候选
- `GET /api/graph/recipe/substitute-results/{recipe_id}/` - 获取食谱替代结果
- `GET /api/graph/canonical/neighbors/{canonical_id}/` - 获取规范食材邻域
- `GET /api/graph/search/recipe/?keyword=test` - 搜索食谱
- `GET /api/graph/search/canonical/?keyword=test` - 搜索规范食材

## 五、使用示例

### 后端 API 调用

```bash
# 获取食谱子图
curl http://127.0.0.1:8000/api/graph/recipe/subgraph/1/

# 获取全局替代候选
curl http://127.0.0.1:8000/api/graph/canonical/substitutes/1/

# 搜索食谱
curl http://127.0.0.1:8000/api/graph/search/recipe/?keyword=test

# 搜索规范食材
curl http://127.0.0.1:8000/api/graph/search/canonical/?keyword=test
```

### Agent 工具调用

```python
from app.tools.backend_graph_tools import backend_graph_tools

# 搜索食谱
recipes = backend_graph_tools.search_recipe("test")

# 搜索规范食材
canonicals = backend_graph_tools.search_canonical("test")

# 获取食谱子图
recipe_subgraph = backend_graph_tools.get_recipe_subgraph("1")

# 获取规范食材邻域
canonical_neighbors = backend_graph_tools.get_canonical_neighbors("1")

# 获取全局替代候选
global_substitutes = backend_graph_tools.get_global_substitutes("1")

# 获取食谱替代结果
recipe_substitute_results = backend_graph_tools.get_recipe_substitute_results("1")
```

### 4. 意图分类器

#### 目录结构

```
agent/
  app/
    intent_router.py         # 混合意图分类器
    llm_intent_router.py     # LLM 意图分类器
```

#### 核心功能

1. **混合意图分类**：结合 LLM 分类和规则分类，提高分类准确性
2. **LLM 分类**：使用 deepseek 模型进行意图分类
3. **规则分类**：使用正则表达式匹配关键词，作为 LLM 分类的回退
4. **意图类型**：支持 `recipe_search`、`recipe_structure`、`ingredient_neighbors`、`substitute_recommendation` 和 `general_chat` 等类型

#### 技术特点

- **混合分类**：结合 LLM 分类和规则分类，提高分类准确性
- **容错机制**：即使 LLM 分类失败，也能使用规则分类作为回退
- **统一格式**：所有分类结果返回统一格式的字典，便于处理
- **错误处理**：确保即使没有匹配到任何意图，也能返回一个合理的默认值
- **模块化设计**：便于扩展和维护

#### 使用示例

```python
from app.intent_router import intent_router

# 分类用户查询
result = intent_router.classify("lime 可以换成什么")
print(f"意图: {result['intent']}")
print(f"置信度: {result['confidence']}")
print(f"分类方法: {result.get('method', 'unknown')}")
```

### 5. 实体识别器

#### 目录结构

```
agent/
  app/
    entity_recognizer.py     # 实体识别器
```

#### 核心功能

1. **食谱实体识别**：从用户查询中识别食谱名称
2. **食材实体识别**：从用户查询中识别食材名称
3. **规则识别**：使用正则表达式和关键词列表识别实体
4. **日志记录**：记录实体识别的过程和结果

#### 技术特点

- **规则识别**：使用正则表达式和关键词列表识别实体
- **多实体类型**：支持识别食谱和食材等多种实体类型
- **容错机制**：即使没有识别到实体，也能回退到传统的提取方法
- **日志记录**：详细记录实体识别的过程和结果，便于调试和优化
- **模块化设计**：便于扩展和维护

#### 使用示例

```python
from app.entity_recognizer import entity_recognizer

# 识别用户查询中的实体
result = entity_recognizer.recognize("lime 可以换成什么")
print(f"食谱实体: {result['recipe_entities']}")
print(f"食材实体: {result['ingredient_entities']}")
```

## 六、总结

本项目成功实现了一层规范的 graph service，为前端页面和 Agent 提供了稳定的数据接口。通过分层设计和标准化输出，确保了代码的可维护性和可扩展性。同时，通过封装 Agent 工具，使得 Agent 可以方便地调用后端 API，而不需要直接处理 API 请求和响应。

此外，本项目还实现了一个混合意图分类器，结合 LLM 分类和规则分类，提高了意图识别的准确性。这为 Agent 能够正确理解用户的问题，并调用相应的工具提供了保障。

未来，可以在此基础上进一步扩展，实现更复杂的 GraphRAG 功能，如社区检测、全局摘要、多阶段调度等，为 Agent 提供更强大的图数据库能力。同时，可以进一步优化意图分类器，提高分类的准确性和效率。