# 实体处理模块 (Entity Module)

## 模块概述

实体处理模块负责识别和处理用户输入中的实体，包括食谱、食材、风味等。它提供了多层实体识别机制，支持词典/规则识别、模糊匹配和LLM辅助分析。

## 目录结构

```
entity/
├── build_entity_resources.py    # 构建实体资源
├── entity_lexicon.json         # 实体词典
├── entity_patterns.json        # 实体模式
├── entity_processor.py         # 实体处理器
├── extractor.py                # 实体提取器
├── linker.py                   # 实体链接器
├── mappings.py                 # 实体映射
├── patterns.py                 # 实体模式定义
├── populate_entity_tables.py   # 填充实体表
├── review_manager.py           # 实体审核管理器
├── schema.py                   # 实体模式定义
└── utils.py                    # 工具函数
```

## 核心功能

### 1. 实体提取

- **食谱识别**：从用户输入中识别食谱名称
- **食材识别**：从用户输入中识别食材名称
- **风味识别**：从用户输入中识别风味词
- **约束条件识别**：识别用户输入中的约束条件

### 2. 实体处理

- **词典/规则识别**：使用预定义的词典和规则识别实体
- **模糊匹配**：处理近似匹配的实体
- **LLM辅助分析**：使用LLM分析复杂或未知的实体
- **实体链接**：将识别的实体链接到规范形式

### 3. 实体管理

- **实体资源构建**：构建和更新实体资源
- **实体表填充**：填充数据库中的实体表
- **实体审核**：管理实体的审核和验证

## 使用方法

### 实体提取

```python
from app.entity.extractor import EntityExtractor

# 创建实体提取器
extractor = EntityExtractor()

# 提取实体
text = "我想喝酸甜的鸡尾酒"
entities = extractor.extract_entities(text)
print(f"提取的实体: {entities}")
```

### 实体处理

```python
from app.entity.entity_processor import EntityProcessor

# 创建实体处理器
processor = EntityProcessor()

# 处理实体
text = "我想喝酸甜的鸡尾酒"
processed_entities = processor.process_entities(text)
print(f"处理后的实体: {processed_entities}")
```

## 配置

实体处理的配置在以下文件中定义：

- `entity_lexicon.json` - 实体词典
- `entity_patterns.json` - 实体模式
- `config/llm_prompts.yaml` - LLM提示词配置

## 常见问题

### 1. 实体识别不准确

可以通过以下方式改进：

- 更新 `entity_lexicon.json` 文件，添加新的实体
- 调整 `entity_patterns.json` 文件中的实体模式
- 增加 LLM 提示词的准确性

### 2. 实体链接失败

检查实体映射是否正确，确保规范实体名称存在于数据库中。