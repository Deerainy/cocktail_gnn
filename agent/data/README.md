# 数据模块 (Data Module)

## 模块概述

数据模块存储系统运行所需的数据文件，包括缓存数据、词典数据和用户偏好数据。它为系统提供数据支持，确保系统能够正常运行。

## 目录结构

```
data/
├── cache.json             # 缓存数据
├── lexicon.json           # 词典数据
└── user_preferences.json  # 用户偏好数据
```

## 核心文件

### 1. cache.json

**功能**：存储系统的缓存数据，提高系统性能。

**内容**：
- LLM响应缓存
- 数据库查询结果缓存
- 其他需要缓存的数据

### 2. lexicon.json

**功能**：存储实体词典数据，用于实体识别。

**内容**：
- 食谱名称
- 食材名称
- 风味词
- 其他实体

### 3. user_preferences.json

**功能**：存储用户偏好数据，用于个性化推荐。

**内容**：
- 用户ID
- 偏好的风味
- 偏好的酒精浓度
- 历史推荐记录

## 使用方法

### 读取数据

```python
import json

# 读取缓存数据
with open('data/cache.json', 'r', encoding='utf-8') as f:
    cache_data = json.load(f)

# 读取词典数据
with open('data/lexicon.json', 'r', encoding='utf-8') as f:
    lexicon_data = json.load(f)

# 读取用户偏好数据
with open('data/user_preferences.json', 'r', encoding='utf-8') as f:
    user_preferences = json.load(f)
```

### 写入数据

```python
import json

# 写入缓存数据
cache_data = {"key": "value"}
with open('data/cache.json', 'w', encoding='utf-8') as f:
    json.dump(cache_data, f, ensure_ascii=False, indent=2)

# 写入用户偏好数据
user_preferences = {"user_id": "123", "preferences": {"flavor": "sweet"}}
with open('data/user_preferences.json', 'w', encoding='utf-8') as f:
    json.dump(user_preferences, f, ensure_ascii=False, indent=2)
```

## 常见问题

### 1. 数据文件损坏

检查文件格式是否正确，确保JSON格式有效。

### 2. 数据加载失败

确保文件路径正确，并且文件存在。