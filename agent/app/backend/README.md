# 后端模块 (Backend Module)

## 模块概述

后端模块负责数据库连接和操作，为智能体提供数据支持。它包含数据库连接管理和历史记录API。

## 目录结构

```
backend/
├── db/        # 数据库连接
│   ├── __init__.py
│   ├── mysql.py      # MySQL数据库连接和操作
│   ├── neo4j.py      # Neo4j图数据库连接和操作
│   └── trace_db.py   # Trace数据存储和查询
├── __init__.py
└── history_api.py    # 历史记录API
```

## 核心功能

### 1. 数据库连接管理

- **MySQL连接**：管理MySQL数据库连接，提供食材、食谱等数据的查询
- **Neo4j连接**：管理Neo4j图数据库连接，提供图谱数据的查询和分析
- **Trace数据库**：存储和查询处理轨迹数据，用于调试和分析

### 2. 历史记录API

- **获取历史记录**：查询用户的对话历史
- **删除历史记录**：删除指定的对话历史
- **获取会话列表**：获取所有会话的列表
- **获取会话详情**：获取指定会话的完整历史

## 使用方法

### 数据库连接

```python
from app.backend.db.mysql import get_mysql_connection
from app.backend.db.neo4j import get_neo4j_driver

# 获取MySQL连接
mysql_conn = get_mysql_connection()

# 获取Neo4j驱动
neo4j_driver = get_neo4j_driver()
```

### 历史记录API

```python
from app.backend.history_api import get_history, delete_history, get_sessions, get_session_detail

# 获取历史记录
history = get_history()

# 删除历史记录
delete_history(trace_id)

# 获取会话列表
sessions = get_sessions()

# 获取会话详情
session_detail = get_session_detail(session_id)
```

## 配置

数据库连接配置在 `app/config.py` 文件中定义，支持从环境变量读取：

- `MYSQL_HOST` - MySQL主机地址
- `MYSQL_USER` - MySQL用户名
- `MYSQL_PASSWORD` - MySQL密码
- `MYSQL_DATABASE` - MySQL数据库名
- `NEO4J_URI` - Neo4j连接URI
- `NEO4J_USER` - Neo4j用户名
- `NEO4J_PASSWORD` - Neo4j密码

## 常见问题

### 1. 数据库连接失败

检查数据库服务是否正在运行，以及连接配置是否正确。

### 2. 历史记录查询失败

检查数据库表结构是否正确，以及权限是否足够。