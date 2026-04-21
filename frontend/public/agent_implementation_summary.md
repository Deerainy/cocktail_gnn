# Agent 实现功能总结

**生成时间**：2026-04-02 12:34:00

## ⚠️ 重要说明：双后端架构

本系统包含**两个后端服务**：

1. **Agent 服务**（端口 5000）：负责自然语言理解、实体识别、意图分析
2. **Backend 服务**（端口 8000）：负责数据管理、实体审核、系统管理

**前端需要同时连接两个服务**：
- 对话功能 → Agent 服务（5000端口）
- 管理功能 → Backend 服务（8000端口）

## 快速开始：解决 404 错误

### 问题描述
前端访问 `/api/chat/send` 等接口时出现 404 错误。

### 解决步骤

1. **启动 Agent 服务**：
   ```bash
   cd agent/app
   python main.py
   ```

2. **启动 Backend 服务**：
   ```bash
   cd backend
   python app.py
   ```

3. **修改前端 API 地址**：
   - 文件：`frontend/src/api/chatApi.js`
   - 修改前：`const BASE_URL = 'http://localhost:8080/api';`
   - 修改后：`const BASE_URL = 'http://localhost:5000/api';`

4. **重新启动前端应用**：
   ```bash
   cd frontend
   npm run serve
   ```

### 验证
访问 `http://localhost:8081/chat`，发送消息测试是否正常工作。

---

## 已实现的功能

### 1. 实体识别与处理系统

**核心功能**：

- **实体抽取**：从文本中提取实体，支持 RECIPE、INGREDIENT、CANONICAL、FLAVOR、ROLE 等类型
- **实体链接**：将抽取到的实体映射到标准实体信息，包括实体 ID、规范化名称等
- **风味词映射**：将常见风味描述词映射到六个基本风味维度（sour、sweet、bitter、aroma、fruity、body）
- **分层处理**：按照三层逻辑处理实体
  - 第一层：词典/规则优先（高精度识别）
  - 第二层：模糊匹配/检索兜底（处理未命中的实体）
  - 第三层：LLM 候选分析（处理前两层无法处理的实体）
- **多语言支持**：支持中英文双语输入
- **审核任务管理**：将需要审核的实体信息写入数据库，支持审核任务的创建、查询和处理
- **Trace 埋点**：在实体处理过程中添加 trace 埋点，记录处理过程和结果

**文件结构**：

- `entity/extractor.py`：实体抽取器，使用 spaCy 或基于规则的回退实现
- `entity/linker.py`：实体链接器，将实体映射到标准信息
- `entity/entity_processor.py`：实体处理器，整合抽取和链接功能，支持 trace 埋点
- `entity/mappings.py`：映射字典，包含风味映射和双语映射
- `entity/build_entity_resources.py`：资源构建脚本，从数据库生成资源文件
- `entity/entity_patterns.json`：实体模式文件
- `entity/entity_lexicon.json`：实体词典文件
- `entity/review_manager.py`：审核任务管理器，处理需要审核的实体

### 2. 意图分析系统

**核心功能**：

- **意图分类**：识别用户的查询意图，支持 recipe_search、recipe_structure、ingredient_neighbors、substitute_recommendation、general_chat 等意图
- **双路径分类**：先使用 LLM 分类，失败时回退到基于规则的分类
- **配置管理**：从配置文件读取 LLM 相关配置
- **Trace 埋点**：在意图判断过程中添加 trace 埋点，记录分类过程和结果

**文件结构**：

- `intent/intent_router.py`：意图路由器，整合 LLM 和规则分类，支持 trace 埋点
- `intent/llm_intent_router.py`：LLM 意图分类器，使用 DeepSeek 模型进行意图分类

### 3. 后端服务

**核心功能**：

- **食谱搜索**：根据食谱名称搜索食谱信息
- **食谱结构**：获取食谱的食材和结构信息
- **食材邻域**：获取与食材邻近的其他食材（已修复，现在查询邻近食材而不是相关食谱）
- **食材替代**：获取食材的替代建议
- **通用响应**：生成通用的响应信息
- **数据库连接**：连接 MySQL 和 Neo4j 数据库，支持真实数据库查询（已修复，使用正确的数据库属性名称）
- **日志记录**：记录实体识别、LLM 意图分类和 Neo4j 检索的日志信息
- **Trace 埋点**：在后端服务调用过程中添加 trace 埋点，记录调用过程和结果

**文件结构**：

- `backend_service.py`：后端服务模块，实现与数据库和其他后端服务的连接，支持 trace 埋点

### 4. 用户输入分析器

**核心功能**：

- **综合分析**：结合实体识别和意图分析，对用户输入进行完整分析
- **响应建议**：根据意图和实体生成具体的行动建议
- **后端服务调用**：根据分析结果调用相应的后端服务
- **审核任务创建**：当识别到需要审核的实体时，自动创建审核任务
- **批量分析**：支持批量处理多个用户输入
- **回退机制**：在依赖缺失时仍能正常运行
- **Trace 收集**：创建和管理 trace 数据，记录整个处理流程

**文件结构**：

- `user_input_analyzer.py`：用户输入分析器，整合实体识别、意图分析和后端服务调用，支持 trace 收集
- `trace_collector.py`：Trace 收集器，创建和管理 trace 数据
- `backend/db/trace_db.py`：Trace 数据库模块，处理 trace 数据的数据库操作

## 技术特点

1. **模块化设计**：各个功能模块独立实现，便于维护和扩展
2. **分层处理**：采用三层处理逻辑，确保高精度和高召回
3. **回退机制**：在依赖缺失时提供回退实现，确保系统稳定性
4. **多语言支持**：支持中英文双语输入
5. **可扩展性**：易于添加新的实体类型、意图类型和映射关系
6. **后端集成**：实现与数据库和其他后端服务的连接，支持真实数据查询
7. **审核机制**：支持将需要审核的实体信息写入数据库，便于人工审核和系统优化
8. **模拟实现**：提供模拟数据库连接，确保在真实数据库不可用时仍能正常运行
9. **依赖管理**：确保所有依赖（如 spaCy 和 RapidFuzz）都已正确安装并正常工作
10. **Trace 收集**：实现完整的 trace 收集系统，记录整个处理流程
11. **前端可视化支持**：生成结构化的 trace 数据，支持前端可视化展示
12. **数据库存储**：将 trace 数据保存到数据库，便于后续查询和分析

## 测试结果

**测试文本**：

1. "找一下 Margarita 的配方"
2. "龙舌兰酒可以换成什么"
3. "lime 的邻域有什么食材"

**测试结果**：

- 成功识别意图：recipe_search、substitute_recommendation、ingredient_neighbors
- 成功识别实体：Margarita (RECIPE)、龙舌兰酒 (CANONICAL)、lime (INGREDIENT)
- 生成合适的响应建议：search_recipe、get_substitute、get_ingredient_neighbors
- 成功调用后端服务：搜索食谱、获取替代建议、获取食材邻域
- 数据库连接成功：能够连接到 MySQL 和 Neo4j 数据库并执行真实查询
- 依赖安装成功：spacy 和 RapidFuzz 都已安装并正常工作
- 日志记录功能：成功记录系统运行日志
- 多语言支持：能够处理中英文输入
- Trace 收集功能：成功收集和保存 trace 数据
- 前端可视化支持：生成结构化的 trace 数据，支持前端可视化展示
- 数据库存储：成功将 trace 数据保存到数据库

## 最近修复的问题

1. **数据库查询修复**：
   - 修复了 Neo4j 数据库查询，使用正确的属性名称（name_norm 和 canonical_name）
   - 确保能够正确找到食材和规范实体
2. **食材邻域查询修复**：
   - 修改了食材邻域查询逻辑，现在查询邻近的食材而不是相关的食谱
   - 能够成功获取食材的邻近食材信息
3. **依赖安装**：
   - 确保 spacy 和 RapidFuzz 都已正确安装
   - 确保 spacy 中文和英文模型都已安装
4. **日志记录**：
   - 确保系统能够正确记录实体识别、LLM 意图分类和 Neo4j 检索的日志信息

## 前端使用指南

### 1. 服务启动

#### Agent 服务（端口 5000）

**启动命令**：
```bash
cd agent/app
python main.py
```

或使用 uvicorn 直接启动：
```bash
cd agent/app
uvicorn main:app --host 0.0.0.0 --port 5000 --reload
```

#### Backend 服务（端口 8000）

**启动命令**：
```bash
cd backend
python app.py
```

### 2. API 接口说明

#### Agent 服务接口（端口 5000）

##### 2.1 发送消息

**接口**：`POST /api/chat/send`

**请求参数**：
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| message | string | 是 | 用户输入的消息 |
| session_id | string | 否 | 会话ID，用于保持对话上下文 |

**请求示例**：
```json
{
  "message": "找一下 Margarita 的配方",
  "session_id": "session_12345"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "intent": "recipe_search",
    "entities": [
      {
        "text": "Margarita",
        "type": "RECIPE",
        "normalized": "Margarita"
      }
    ],
    "response": "为您找到 Margarita 的配方..."
  },
  "trace_id": "trace_abc123",
  "processing_time": 1.234
}
```

##### 2.2 获取历史记录

**接口**：`GET /api/history`

**请求参数**：
| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 10 | 每页数量 |

**请求示例**：
```
GET http://localhost:5000/api/history?page=1&page_size=10
```

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "trace_id": "trace_abc123",
      "user_input": "找一下 Margarita 的配方",
      "final_answer": "为您找到 Margarita 的配方...",
      "created_at": "2026-04-02T12:34:56"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 10
}
```

##### 2.3 获取 Trace 详情

**接口**：`GET /api/trace/{trace_id}`

**请求示例**：
```
GET http://localhost:5000/api/trace/trace_abc123
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "trace_id": "trace_abc123",
    "user_input": "找一下 Margarita 的配方",
    "intent_name": "recipe_search",
    "trace_json": {
      "steps": [
        {
          "step": 1,
          "name": "input_analysis",
          "title": "输入分析",
          "status": "success"
        }
      ]
    }
  }
}
```

##### 2.4 健康检查

**接口**：`GET /health`

**响应示例**：
```json
{
  "status": "healthy",
  "debug": true
}
```

#### Backend 服务接口（端口 8000）

Backend 服务提供管理功能，包括：
- 实体审核
- 系统概览
- 数据分析
- 用户管理

**基础 URL**：`http://localhost:8000/api`

### 3. 前端配置

#### 3.1 修改 Agent 服务 API 地址

**文件**：`frontend/src/api/chatApi.js`

**修改前**：
```javascript
const BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:8080/api';
```

**修改后**（指向 Agent 服务）：
```javascript
const BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000/api';
```

#### 3.2 修改 Backend 服务 API 地址

**文件**：`frontend/src/api/recipeApi.js` 和 `frontend/src/api/entityApi.js`

**保持不变**：
```javascript
const API_BASE_URL = 'http://127.0.0.1:8000/api';
```

#### 3.3 环境变量设置

**Windows**：
```bash
set VUE_APP_API_BASE_URL=http://localhost:5000/api
set VUE_APP_BACKEND_API_BASE_URL=http://127.0.0.1:8000/api
```

**Linux/Mac**：
```bash
export VUE_APP_API_BASE_URL=http://localhost:5000/api
export VUE_APP_BACKEND_API_BASE_URL=http://127.0.0.1:8000/api
```

### 4. 跨域支持

#### Agent 服务 CORS 配置

Agent 服务已配置 CORS，允许所有来源访问。如需限制特定域名，修改 `agent/app/main.py`：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],  # 修改为前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Backend 服务 CORS 配置

Backend 服务已配置 CORS，允许所有来源访问。如需限制特定域名，修改 `backend/app.py`：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081"],  # 修改为前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. 支持的意图类型

| 意图名称 | 说明 | 示例 |
|----------|------|------|
| recipe_search | 搜索食谱 | "找一下 Margarita 的配方" |
| recipe_structure | 查询食谱结构 | "Margarita 需要什么材料" |
| ingredient_neighbors | 食材邻域查询 | "lime 的邻域有什么食材" |
| substitute_recommendation | 替代建议 | "龙舌兰酒可以换成什么" |
| general_chat | 通用对话 | "你好" |

### 6. 支持的实体类型

| 实体类型 | 说明 | 示例 |
|----------|------|------|
| RECIPE | 食谱名称 | Margarita, Mojito |
| INGREDIENT | 食材名称 | lime, tequila |
| CANONICAL | 规范实体 | 龙舌兰酒 |
| FLAVOR | 风味描述 | 酸甜, 苦味 |
| ROLE | 角色/身份 | 调酒师 |

## 下一步工作建议

### 1. 功能增强

- **扩展实体类型**：添加更多实体类型，如杯型、制作方法、场合等
- **增强风味词映射**：扩展风味词词典，支持更多风味描述词
- **改进模糊匹配**：实现 RapidFuzz 和 embedding 检索，提高模糊匹配的准确性
- **添加上下文理解**：考虑对话历史，提高意图识别的准确性
- **中英文映射**：添加中英文食材名称映射，以支持中文输入如 "龙舌兰酒" 映射到 "tequila"

### 2. 性能优化

- **优化资源加载**：减少资源文件的加载时间
- **缓存机制**：添加缓存，避免重复计算
- **并行处理**：支持并行分析多个用户输入
- **模型优化**：优化 spaCy 模型的使用，提高实体识别的速度

### 3. 集成与部署

- **API 接口**：实现 RESTful API 接口，便于前端调用
- **容器化部署**：使用 Docker 容器化部署，提高部署的一致性
- **监控与日志**：添加监控和日志系统，便于问题排查
- **CI/CD 流程**：建立持续集成和持续部署流程

### 4. 数据管理

- **数据库同步**：实现资源文件与数据库的自动同步
- **数据质量**：提高数据质量，减少噪声数据
- **数据可视化**：添加数据可视化工具，便于分析实体和意图的分布

### 5. 用户体验

- **自然语言理解**：提高系统对自然语言的理解能力
- **多轮对话**：支持多轮对话，提高用户体验
- **个性化推荐**：根据用户历史输入，提供个性化的响应建议
- **错误处理**：改进错误处理，提供更友好的错误提示

## 总结

当前实现的 agent 系统已经具备了完整的自然语言理解能力，能够识别用户的意图和实体，并生成合适的响应建议。系统采用了分层处理逻辑，确保了高精度和高召回，同时提供了回退机制，确保系统的稳定性。

系统已经成功连接到数据库并执行真实查询，能够正确获取食谱信息、食材邻域和替代建议。所有依赖都已正确安装并正常工作，系统运行稳定。

系统采用双后端架构，Agent 服务负责自然语言理解，Backend 服务负责数据管理，前端需要同时连接两个服务。下一步可以通过扩展功能、优化性能、改进集成与部署、加强数据管理和提升用户体验等方面，进一步完善系统，使其成为一个更加强大和可靠的自然语言理解系统。
