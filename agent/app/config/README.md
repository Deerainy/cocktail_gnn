# 配置模块 (Config Module)

## 模块概述

配置模块负责管理应用的配置信息，包括检索配置、查询模板和LLM提示词等。它提供了灵活的配置管理机制，支持从文件和环境变量加载配置。

## 目录结构

```
config/
├── llm_prompts.yaml     # LLM提示词配置
├── query_templates.yaml # 查询模板配置
└── retrieval_config.yaml # 检索相关配置
```

## 配置文件说明

### 1. retrieval_config.yaml

**功能**：配置检索相关的参数和关键词

**主要配置项**：
- `retrieval_keywords` - 检索关键词列表
- `english_ingredients` - 英文食材列表
- `confidence_thresholds` - 置信度阈值配置
- `daily_chat_keywords` - 日常交流关键词

### 2. query_templates.yaml

**功能**：配置数据库查询模板

**主要配置项**：
- `neo4j_queries` - Neo4j查询模板
- `mysql_queries` - MySQL查询模板

### 3. llm_prompts.yaml

**功能**：配置LLM提示词和相关参数

**主要配置项**：
- `system_prompts` - 系统提示词
- `user_prompts` - 用户提示词
- `example_conversations` - 示例对话
- `flavor_terms` - 风味词配置
- `common_nouns` - 通用名词配置

## 使用方法

### 加载配置

```python
from app.config import settings

# 获取检索关键词
retrieval_keywords = settings.get_retrieval_keywords()

# 获取英文食材列表
english_ingredients = settings.get_english_ingredients()

# 获取系统提示词
system_prompt = settings.get_system_prompt("bartender_role")

# 获取用户提示词
user_prompt = settings.get_user_prompt("intent_classification")

# 获取查询模板
query_template = settings.get_query_template("search_recipe")
```

### 重新加载配置

```python
from app.config import settings

# 重新加载配置
settings.reload_configs()
```

## 环境变量支持

所有配置都可以通过环境变量覆盖，例如：

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

### 1. 配置文件修改不生效

修改配置文件后，需要重启服务或调用 `settings.reload_configs()` 重新加载配置。

### 2. 环境变量覆盖不生效

确保环境变量的名称与配置项名称一致，并且在服务启动前设置。