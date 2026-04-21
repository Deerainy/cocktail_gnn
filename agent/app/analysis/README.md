# Analysis 模块 - 用户输入分析系统

## 模块概述

本模块实现了**四层架构**的用户输入分析系统，专门用于鸡尾酒/调酒领域的智能对话。通过显式状态管理 + LLM 辅助解析的方式，实现稳定可靠的上下文记忆和指代消解功能。

## 架构设计

### 四层架构模型

```
┌─────────────────────────────────────────────────────────────┐
│ 第4层：任务执行器 (Task Executor)                            │
│  - 调用后端服务执行具体任务                                   │
│  - 查询配方、替代食材、邻域关系等                             │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│ 第3层：当前轮解析器 (Current Turn Parser)                    │
│  Step 1: 显式解析 - 从当前输入提取意图和实体                 │
│  Step 2: 上下文补全 - 结合会话状态补全缺失信息               │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│ 第2层：结构化会话状态 (Session Context)                      │
│  - 维护当前配方、当前食材、最近实体等                        │
│  - 显式状态管理，不依赖 LLM                                  │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│ 第1层：原始对话历史 (Raw History)                            │
│  - 数据库存储的用户输入和系统响应                            │
│  - 用于持久化和审计                                          │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. session_context.py - 会话上下文管理

**功能**：实现第2层结构化会话状态管理

**核心类**：

#### `SessionContext`
会话上下文数据结构，包含以下字段：

```python
{
    "session_id": "会话唯一标识",
    "current_recipe_id": "当前配方ID",
    "current_recipe_name": "当前配方名称",
    "current_canonical_id": "当前规范食材ID",
    "current_canonical_name": "当前规范食材名称",
    "current_step": "当前步骤",
    "last_intent": "上一个意图",
    "last_action": "上一个动作",
    "last_entities": "上一个识别的实体",
    "recent_recipes": "最近讨论的配方列表",
    "recent_ingredients": "最近讨论的食材列表",
    "updated_at": "最后更新时间"
}
```

**主要方法**：
- `add_recent_recipe()`: 添加最近配方，自动去重和限制数量
- `add_recent_ingredient()`: 添加最近食材，自动去重和限制数量
- `update_after_execution()`: 执行任务后更新上下文

#### `SessionContextManager`
会话上下文管理器，提供全局访问点：
- `get_or_create(session_id)`: 获取或创建会话上下文
- `get(session_id)`: 获取会话上下文
- `save(context)`: 保存会话上下文
- `remove(session_id)`: 删除会话上下文

**使用示例**：
```python
from analysis.session_context import session_context_manager

# 获取或创建会话上下文
ctx = session_context_manager.get_or_create("sess_xxx")

# 更新当前配方
ctx.add_recent_recipe(12, "Margarita")

# 更新当前食材
ctx.add_recent_ingredient(45, "lime juice")

# 执行任务后更新上下文
ctx.update_after_execution(
    intent="ingredient_substitute",
    action="get_substitute",
    entities={"recipe": "Margarita", "ingredient": "lime juice"}
)
```

---

### 2. current_turn_parser.py - 当前轮解析器

**功能**：实现第3层显式解析 + 上下文补全

**核心类**：

#### `CurrentTurnParser`
当前轮解析器，包含两个主要步骤：

**Step 1: 显式解析 (`parse_explicit`)**

从用户输入中直接提取信息：
- **意图识别**：替换、配方查询、邻域查询等
- **实体提取**：配方名称、食材名称、候选替代
- **指代检测**：检测"这个"、"那个"、"它"等指代词
- **追问识别**：检测"还能"、"还有"、"继续"等追问词

**返回结构**：
```python
{
    "intent": "识别的意图",
    "recipe": "配方名称（可能为null）",
    "ingredient": "食材名称（可能为null）",
    "candidate_substitute": "候选替代（可能为null）",
    "has_pronoun_reference": "是否包含指代词",
    "reference_text": "指代词文本",
    "is_followup": "是否是追问",
    "is_short_question": "是否是简短问题"
}
```

**Step 2: 上下文补全 (`complete_with_context`)**

结合会话上下文补全缺失信息：
- 如果当前轮没说配方，但有指代词 → 使用 `current_recipe_name`
- 如果当前轮没说食材，但有指代词 → 使用 `current_canonical_name`
- 如果当前轮是追问 → 继承上一个意图和实体
- 从 `last_entities` 中补充缺失的槽位

**使用示例**：
```python
from analysis.current_turn_parser import current_turn_parser
from analysis.session_context import session_context_manager

# 获取会话上下文
ctx = session_context_manager.get_or_create("sess_xxx")

# 解析用户输入
text = "这个里面的青柠可以换成什么？"
result = current_turn_parser.parse(text, ctx)

# 输出：
# {
#     "intent": "ingredient_substitute",
#     "recipe": "Margarita",  # ← 从上下文补全
#     "ingredient": "青柠",
#     "has_pronoun_reference": True,
#     "reference_text": "这个里面"
# }
```

---

### 3. user_input_analyzer.py - 用户输入分析器

**功能**：整合四层架构，协调各组件完成完整分析流程

**核心类**：

#### `UserInputAnalyzer`
用户输入分析器，主入口类。

**分析流程**：

1. **创建/获取 Trace**：记录整个分析过程
2. **获取会话上下文**（第2层）：`session_context_manager.get_or_create()`
3. **当前轮解析**（第3层）：`current_turn_parser.parse()`
4. **输入理解**：记录语言、归一化文本、解析结果
5. **检索增强判断**：检查是否需要查询后端
6. **日常交流判断**：使用 LLM 判断是否为闲聊
7. **实体识别**：识别配方、食材等实体
8. **意图分析**：确定用户意图
9. **调用后端服务**（第4层）：执行具体查询
10. **更新会话上下文**：保存当前状态供下一轮使用
11. **答案生成**：生成最终回复

**使用示例**：
```python
from analysis.user_input_analyzer import user_input_analyzer

# 分析用户输入
result = user_input_analyzer.analyze(
    text="这个里面的青柠可以换成什么？",
    session_id="sess_xxx"
)

# 结果包含：
# - entities: 识别的实体
# - intent: 确定的意图
# - backend_response: 后端查询结果
# - trace: 完整的处理流程
```

---

### 4. parsed_query.py - 解析结果结构

**功能**：定义统一的解析结果数据结构

**核心类**：

#### `ParsedEntity`
解析后的实体结构：
```python
{
    "text": "实体文本",
    "label": "实体标签",
    "entity_id": "实体ID",
    "canonical_name": "规范化名称",
    "confidence": "置信度"
}
```

#### `ParsedQuery`
解析后的查询结构：
```python
{
    "intent": "意图",
    "entities": [ParsedEntity, ...],
    "suggested_action": "建议动作",
    "constraints": "约束条件",
    "top_k": "返回结果数量",
    "need_explanation": "是否需要解释"
}
```

---

## 工作流程示例

### 场景1：配方查询 + 食材替代

**第一轮对话**：
```
用户：Margarita 的配方是什么？
系统：Margarita 的配方如下：
- 2盎司 龙舌兰酒
- 1盎司 君度橙酒
- 1盎司 新鲜青柠汁
- 盐（用于杯口装饰）

制作方法：
1. 在调酒壶中加入冰块
2. 倒入龙舌兰酒、君度橙酒和青柠汁
3. 用力摇晃15-20秒
4. 将混合液倒入装有盐边的杯中
5. 用青柠角装饰
```

**第二轮对话**：
```
用户：这个里面的青柠可以换成什么？
系统：在 Margarita 中，青柠可以替换为：
1. 柠檬：口感更酸，香气更浓郁
2. 酸橙汁：酸度适中，热带风味
3. 葡萄柚汁：带有轻微的苦味，增加层次感

建议使用新鲜果汁以获得最佳口感。
```

**解析过程**：
1. **第一轮**：
   - 解析器识别意图为 `recipe_query`
   - 提取实体 `Margarita`
   - 调用后端查询配方
   - 更新会话上下文，设置 `current_recipe_name` 为 "Margarita"

2. **第二轮**：
   - 解析器识别意图为 `ingredient_substitute`
   - 检测到指代词 "这个"，从上下文补全配方为 "Margarita"
   - 提取实体 "青柠"
   - 调用后端查询替代食材
   - 更新会话上下文，设置 `current_canonical_name` 为 "青柠"

### 场景2：邻域查询 + 追问

**对话示例**：
```
用户：和 Margarita 类似的鸡尾酒有哪些？
系统：与 Margarita 类似的鸡尾酒包括：
1. Daiquiri：朗姆酒基底，同样使用青柠汁
2. Paloma：龙舌兰酒基底，加入西柚汁
3. Tequila Sunrise：龙舌兰酒基底，加入橙汁和石榴糖浆

用户：还有吗？
系统：还有以下类似的鸡尾酒：
4. Margarita Blanco：使用 Blanco 龙舌兰，口感更清爽
5. Tommy's Margarita：使用 agave 糖浆代替君度橙酒
6. Cadillac Margarita：加入 Grand Marnier 提升风味
```

**解析过程**：
1. **第一轮**：
   - 解析器识别意图为 `recipe_neighborhood`
   - 提取实体 `Margarita`
   - 调用后端查询邻域配方
   - 更新会话上下文，记录 `last_intent` 为 "recipe_neighborhood"

2. **第二轮**：
   - 解析器检测到追问词 "还有"
   - 继承上一个意图 `recipe_neighborhood`
   - 从上下文补全实体 `Margarita`
   - 调用后端查询更多邻域配方

---

## 模块集成

### 快速开始

1. **安装依赖**：
   ```bash
   # 确保安装了必要的依赖
   pip install -r requirements.txt
   ```

2. **导入模块**：
   ```python
   from analysis.user_input_analyzer import user_input_analyzer
   ```

3. **使用示例**：
   ```python
   # 分析用户输入
   result = user_input_analyzer.analyze(
       text="我想知道 Mojito 的配方",
       session_id="user_123"
   )
   
   # 处理结果
   if result.get("backend_response"):
       print("查询结果:", result["backend_response"])
   else:
       print("意图:", result["intent"])
       print("实体:", [e["text"] for e in result["entities"]])
   ```

### 配置选项

| 配置项 | 描述 | 默认值 |
|--------|------|--------|
| `MAX_RECENT_RECIPES` | 最近配方列表最大长度 | 5 |
| `MAX_RECENT_INGREDIENTS` | 最近食材列表最大长度 | 5 |
| `LLM_API_URL` | LLM 服务 API 地址 | - |
| `LLM_API_KEY` | LLM 服务 API 密钥 | - |

### 依赖项

- Python 3.7+
- 主要依赖：
  - `requests`：用于调用后端服务
  - `pydantic`：用于数据验证
  - `transformers`（可选）：用于高级 NLP 任务
  - `redis`（可选）：用于分布式会话管理

---

## 扩展指南

### 自定义意图识别

要添加新的意图类型，需要：

1. 在 `current_turn_parser.py` 中扩展 `parse_explicit` 方法
2. 在 `user_input_analyzer.py` 中添加对应的处理逻辑
3. 更新后端服务以支持新意图

### 自定义实体识别

要增强实体识别能力：

1. 在 `parsed_query.py` 中扩展 `ParsedEntity` 类
2. 在 `current_turn_parser.py` 中添加新的实体提取规则
3. 考虑集成外部 NER 模型以提高识别准确率

### 会话管理扩展

要自定义会话管理逻辑：

1. 继承 `SessionContext` 类添加自定义字段
2. 实现 `SessionContextManager` 的自定义存储后端（如数据库、Redis 等）

---

## 故障排除

### 常见问题

1. **指代词解析失败**：
   - 检查会话上下文中是否有足够的历史信息
   - 确保 `current_recipe_name` 和 `current_canonical_name` 已正确设置

2. **意图识别错误**：
   - 检查输入文本是否清晰明确
   - 考虑调整 `parse_explicit` 中的规则

3. **后端服务调用失败**：
   - 检查网络连接和服务可用性
   - 验证 API 配置是否正确

### 调试工具

- **Trace 日志**：分析过程中会生成详细的 trace 日志，可用于调试
- **会话状态检查**：使用 `session_context_manager.get(session_id)` 查看当前会话状态
- **解析结果检查**：打印 `current_turn_parser.parse()` 的返回结果以验证解析逻辑

---

## 总结

Analysis 模块通过四层架构实现了智能、稳定的用户输入分析系统，特别针对鸡尾酒/调酒领域的对话场景进行了优化。其核心优势包括：

- **显式状态管理**：不依赖 LLM 的上下文理解能力，确保稳定可靠的对话体验
- **上下文补全**：智能处理指代词和追问，提供流畅的对话体验
- **模块化设计**：各组件职责清晰，易于扩展和维护
- **可扩展性**：支持自定义意图、实体和会话管理逻辑

该模块为鸡尾酒智能助手提供了强大的语言理解能力，能够准确识别用户意图，提取关键实体，并结合上下文提供个性化的响应。