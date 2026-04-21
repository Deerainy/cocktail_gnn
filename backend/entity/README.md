# Entity 应用 - 实现说明

## 1. 系统概述

本应用实现了一个完整的实体识别与处理系统，用于鸡尾酒知识图谱系统的 NLU 前置处理。系统基于 Django 框架开发，提供了用户认证、实体管理、审核管理和实体处理等核心功能。

## 2. 核心功能模块

### 2.1 用户认证模块
- **用户注册**：`POST /api/auth/register` - 注册新用户
- **用户登录**：`POST /api/auth/login` - 登录获取 JWT 令牌
- **获取用户信息**：`GET /api/auth/me` - 获取当前登录用户信息

### 2.2 实体管理模块
- **实体列表**：`GET /api/entity` - 获取实体列表，支持分页和标签过滤
- **实体详情**：`GET /api/entity/{id}` - 获取实体详细信息
- **创建实体**：`POST /api/entity` - 创建新实体
- **更新实体**：`PUT /api/entity/{id}` - 更新实体信息
- **删除实体**：`DELETE /api/entity/{id}` - 删除实体
- **实体别名管理**：
  - 获取别名：`GET /api/entity/{id}/aliases`
  - 添加别名：`POST /api/entity/{id}/aliases`
  - 删除别名：`DELETE /api/entity/aliases/{id}`

### 2.3 审核管理模块
- **审核任务列表**：`GET /api/entity/review/tasks` - 获取审核任务列表
- **审核任务详情**：`GET /api/entity/review/tasks/{id}` - 获取审核任务详细信息
- **提交审核结果**：`POST /api/entity/review` - 提交审核结果，支持添加新别名

### 2.4 实体处理模块
- **单个文本处理**：`POST /api/entity/process` - 处理单个文本，识别实体
- **批量文本处理**：`POST /api/entity/batch_process` - 批量处理多个文本

## 3. 数据库设计

### 3.1 主要表结构
- **users**：用户表，存储用户信息
- **entities**：实体表，存储标准实体信息
- **aliases**：别名表，存储实体的别名
- **review_tasks**：审核任务表，存储需要审核的任务
- **review_entities**：审核实体表，存储需要审核的实体
- **candidates**：候选实体表，存储实体的候选选项
- **review_results**：审核结果表，存储审核结果

### 3.2 关系图
```
users (user_id) <-- review_results (review_id)
entities (entity_id) <-- aliases (entity_id)
review_tasks (review_id) <-- review_entities (review_id)
review_entities (review_entity_id) <-- candidates (review_entity_id)
review_tasks (review_id) <-- review_results (review_id)
```

## 4. 技术实现

### 4.1 认证机制
- 使用 JWT (JSON Web Token) 进行用户认证
- 集成 djangorestframework-simplejwt 库
- 支持令牌过期和刷新

### 4.2 API 设计
- 基于 Django REST Framework 开发
- 使用 ViewSet 组织相关接口
- 支持 RESTful API 设计规范
- 实现了完整的错误处理和响应格式

### 4.3 实体处理流程
1. **词典/规则优先**：使用 pattern 词典、alias 映射和标准实体库进行高精度识别
2. **模糊匹配/检索兜底**：处理第一层未命中的实体，包括文本规范化、去标点、alias 变体处理等
3. **LLM 候选分析**：对前两层都无法处理的实体，使用 LLM 进行候选分析和类型判断

## 5. 接口文档

### 5.1 认证接口

#### 注册
- **Endpoint**: `/api/auth/register`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "username": "testuser",
    "password": "123456"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "注册成功",
    "data": {
      "user_id": 1,
      "username": "testuser",
      "role": "user"
    }
  }
  ```

#### 登录
- **Endpoint**: `/api/auth/login`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "username": "testuser",
    "password": "123456"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "message": "登录成功",
    "data": {
      "user_id": 1,
      "username": "testuser",
      "role": "user",
      "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
  ```

### 5.2 实体处理接口

#### 单个处理
- **Endpoint**: `/api/entity/process`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "text": "I want a smoky Margarita with lime juice and mezcal."
  }
  ```
- **Response**:
  ```json
  {
    "text": "I want a smoky Margarita with lime juice and mezcal.",
    "entities": [
      {
        "text": "smoky",
        "label": "FLAVOR",
        "start": 9,
        "end": 14,
        "processing_level": "lexicon_rule",
        "confidence": 1.0,
        "normalized_flavor": "aroma"
      },
      {
        "text": "Margarita",
        "label": "RECIPE",
        "start": 15,
        "end": 24,
        "processing_level": "lexicon_rule",
        "confidence": 1.0,
        "entity_id": 723,
        "normalized_name": "Margarita"
      }
    ],
    "processing_level": "lexicon_rule"
  }
  ```

## 6. 测试账号

为了方便测试，系统已创建测试账号：
- **用户名**：testuser2
- **密码**：123456

## 7. 注意事项

1. **权限管理**：除了登录、注册和实体处理接口外，其他接口都需要认证
2. **数据安全**：密码使用 Django 的密码哈希机制存储
3. **API 限流**：建议在生产环境中添加 API 限流机制
4. **错误处理**：系统已实现完整的错误处理机制，返回标准化的错误信息

## 8. 部署说明

1. 运行数据库迁移：`python manage.py migrate`
2. 启动开发服务器：`python manage.py runserver`
3. 在生产环境中，建议使用 Gunicorn 或 uWSGI 作为 WSGI 服务器

## 9. 技术栈

- **后端框架**：Django 5.2
- **API 框架**：Django REST Framework
- **认证**：JWT (djangorestframework-simplejwt)
- **数据库**：MySQL
- **开发工具**：Python 3.9+

## 10. 未来扩展

1. **实体识别算法优化**：集成更先进的 NLP 模型
2. **多语言支持**：扩展支持更多语言
3. **实时处理**：添加实时实体处理功能
4. **监控系统**：添加系统监控和日志分析
5. **自动化审核**：实现基于机器学习的自动审核系统
