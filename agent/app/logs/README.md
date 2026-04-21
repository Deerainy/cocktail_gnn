# 日志模块 (Logs Module)

## 模块概述

日志模块存储系统运行过程中产生的日志文件，用于调试和分析。它记录系统的运行状态、错误信息和关键事件，帮助开发人员了解系统的运行情况。

## 目录结构

```
logs/
├── llm_intent_log.txt    # LLM意图分类日志
└── neo4j_retrieval_log.txt # Neo4j检索日志
```

## 核心文件

### 1. llm_intent_log.txt

**功能**：记录LLM意图分类的日志信息。

**内容**：
- 用户输入
- 意图分类结果
- 置信度
- 处理时间
- 错误信息

### 2. neo4j_retrieval_log.txt

**功能**：记录Neo4j检索的日志信息。

**内容**：
- 检索查询
- 检索结果
- 处理时间
- 错误信息

## 使用方法

### 查看日志

```bash
# 查看LLM意图分类日志
cat app/logs/llm_intent_log.txt

# 查看Neo4j检索日志
cat app/logs/neo4j_retrieval_log.txt
```

### 清理日志

```bash
# 清理LLM意图分类日志
echo "" > app/logs/llm_intent_log.txt

# 清理Neo4j检索日志
echo "" > app/logs/neo4j_retrieval_log.txt
```

## 常见问题

### 1. 日志文件过大

定期清理日志文件，或者配置日志轮转。

### 2. 日志内容不完整

检查日志记录代码是否正确，确保所有关键事件都被记录。