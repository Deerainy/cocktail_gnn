# 工具模块 (Tools Module)

## 模块概述

工具模块提供各种工具函数和类，用于辅助系统的运行和维护。它包含后端图数据库工具、图谱API工具和其他辅助工具。

## 目录结构

```
tools/
├── backend_graph_tools.py    # 后端图数据库工具
├── graph_api_tools.py        # 图谱API工具
└── sqe_tools.py              # 其他辅助工具
```

## 核心功能

### 1. 后端图数据库工具

- **搜索食谱**：根据关键词搜索食谱
- **搜索规范食材**：根据关键词搜索规范食材
- **获取食谱子图**：获取食谱的局部图谱信息
- **获取规范食材邻域**：获取规范食材的邻域结构
- **获取全局替代候选**：获取全局替代候选
- **获取食谱替代结果**：获取食谱在具体配方上下文中的替代结果

### 2. 图谱API工具

- **图谱API调用**：调用后端图谱API
- **数据格式化**：格式化API返回的数据
- **错误处理**：处理API调用错误

### 3. 其他辅助工具

- **数据处理**：处理和转换数据
- **工具函数**：提供各种辅助函数

## 使用方法

### 后端图数据库工具

```python
from app.tools.backend_graph_tools import backend_graph_tools

# 搜索食谱
result = backend_graph_tools.search_recipe("Margarita")
print(f"搜索结果: {result}")

# 获取食谱子图
result = backend_graph_tools.get_recipe_subgraph("1")
print(f"食谱子图: {result}")
```

### 图谱API工具

```python
from app.tools.graph_api_tools import graph_api_tools

# 搜索食谱
result = graph_api_tools.search_recipe("Margarita")
print(f"搜索结果: {result}")
```

## 配置

工具模块的配置在 `app/config.py` 文件中定义，支持从环境变量读取：

- `GRAPH_API_BASE_URL` - 图谱API基础URL

## 常见问题

### 1. API调用失败

检查API基础URL是否正确，以及网络连接是否正常。

### 2. 数据格式错误

确保API返回的数据格式正确，并且工具能够正确解析。