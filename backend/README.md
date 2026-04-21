# 后端系统设计与实现

## 1. 项目概述

本项目是一个基于 Django 的鸡尾酒配方管理与分析系统，结合了传统关系型数据库（MySQL）和图数据库（Neo4j）的优势，实现了鸡尾酒配方的存储、查询、分析和推荐功能。

## 2. 理论基础

### 2.1 系统架构

系统采用前后端分离架构，后端负责数据处理和业务逻辑，前端负责用户界面展示。后端系统基于 Django 框架构建，使用 RESTful API 与前端进行通信。

### 2.2 数据模型设计

系统使用双数据库架构：
- **MySQL**：存储结构化数据，如用户信息、配方基本信息等
- **Neo4j**：存储复杂的关系数据，如配料之间的关联、风味图谱等

### 2.3 核心理论

- **图数据库理论**：利用 Neo4j 图数据库的优势，构建配料之间的关系网络，实现高效的关联查询和推荐
- **RESTful API 设计**：遵循 REST 原则，设计标准化的 API 接口
- **JWT 认证机制**：实现无状态的用户认证，提高系统安全性
- **CORS 跨域处理**：支持前端跨域请求，实现前后端分离

## 3. 技术实现

### 3.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.8+ | 后端开发语言 |
| Django | 5.2 | Web 框架 |
| Django REST Framework | 3.15+ | API 开发 |
| MySQL | 8.0+ | 关系型数据库 |
| Neo4j | 5.0+ | 图数据库 |
| PyNeo4j | 2021.2.3+ | Python 与 Neo4j 的连接库 |
| JWT | - | 用户认证 |
| CORS Headers | - | 跨域请求处理 |

### 3.2 项目结构

```
backend/
├── backend/              # 项目配置目录
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py       # 项目设置
│   ├── urls.py           # 全局 URL 配置
│   └── wsgi.py
├── cocktail/             # 鸡尾酒应用
│   ├── migrations/       # 数据库迁移文件
│   ├── __init__.py
│   ├── admin.py
│   ├── api_documentation.txt
│   ├── apps.py
│   ├── models_recipe.py  # 配方数据模型
│   ├── serializers_flavor_graph.py
│   ├── serializers_recipe.py
│   ├── services_combo_adjust.py
│   ├── tests.py
│   ├── urls.py           # 应用 URL 配置
│   ├── views_combo_adjust.py
│   ├── views_flavor_graph.py
│   ├── views_innovation.py
│   └── views_recipe.py
├── db/                   # 数据库连接
│   ├── __init__.py
│   ├── mysql.py
│   └── neo4j.py
├── entity/               # 实体应用
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── graph/                # 图谱应用
│   ├── queries/          # 图谱查询
│   ├── schemas/
│   ├── services/         # 图谱服务
│   ├── utils/
│   ├── __init__.py
│   ├── client.py
│   ├── urls.py
│   └── views.py
├── history/              # 历史记录应用
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── backend_requirements.txt
├── db.sqlite3
├── generate_recipe_info.py
├── manage.py             # Django 管理脚本
├── test_alcoholic_status.py
└── 前端对接说明.md
```

### 3.3 核心功能模块

#### 3.3.1 配方管理

- **配方列表**：获取所有配方信息，支持分页和筛选
- **配方详情**：获取单个配方的详细信息，包括配料、制作方法等
- **配方搜索**：根据名称、配料等条件搜索配方
- **配方分析**：分析配方的风味特点、配料比例等

#### 3.3.2 风味图谱

- **配料关系**：构建配料之间的关联网络
- **风味分析**：分析配方的风味组成和特点
- **相似度计算**：计算不同配方之间的相似度
- **推荐系统**：基于图谱关系推荐相似配方

#### 3.3.3 创新功能

- **配料替换**：根据用户需求推荐合适的配料替换方案
- **配方调整**：根据用户偏好调整配方的配料比例
- **新品生成**：基于现有配方生成新的配方创意

#### 3.3.4 历史记录

- **用户操作记录**：记录用户的搜索、查看等操作
- **偏好分析**：基于历史记录分析用户偏好
- **个性化推荐**：根据历史记录提供个性化配方推荐

### 3.4 API 设计

#### 3.4.1 配方相关 API

| API 路径 | 方法 | 功能 |
|---------|------|------|
| `/api/recipes/` | GET | 获取配方列表 |
| `/api/recipes/{id}/` | GET | 获取配方详情 |
| `/api/recipes/search/` | GET | 搜索配方 |
| `/api/recipes/analyze/{id}/` | GET | 分析配方 |

#### 3.4.2 风味图谱相关 API

| API 路径 | 方法 | 功能 |
|---------|------|------|
| `/api/graph/flavor/` | GET | 获取风味图谱 |
| `/api/graph/ingredients/` | GET | 获取配料关系 |
| `/api/graph/similar/{id}/` | GET | 获取相似配方 |

#### 3.4.3 创新相关 API

| API 路径 | 方法 | 功能 |
|---------|------|------|
| `/api/innovation/substitute/` | POST | 配料替换推荐 |
| `/api/innovation/adjust/` | POST | 配方调整 |
| `/api/innovation/generate/` | POST | 生成新配方 |

#### 3.4.4 历史相关 API

| API 路径 | 方法 | 功能 |
|---------|------|------|
| `/api/history/` | GET | 获取历史记录 |
| `/api/history/add/` | POST | 添加历史记录 |
| `/api/history/recommend/` | GET | 基于历史的推荐 |

### 3.5 数据库设计

#### 3.5.1 MySQL 数据库

**配方表 (`cocktail_recipe`)**
| 字段名 | 数据类型 | 描述 |
|-------|---------|------|
| `recipe_id` | `INT` | 配方 ID |
| `recipe_name_zh` | `VARCHAR(255)` | 中文名称 |
| `name` | `VARCHAR(255)` | 英文名称 |
| `glass` | `VARCHAR(100)` | 酒杯类型 |
| `is_alcoholic` | `BOOLEAN` | 是否含酒精 |
| `instructions` | `TEXT` | 制作方法 |
| `created_at` | `DATETIME` | 创建时间 |

**配料表 (`cocktail_ingredient`)**
| 字段名 | 数据类型 | 描述 |
|-------|---------|------|
| `ingredient_id` | `INT` | 配料 ID |
| `name` | `VARCHAR(255)` | 配料名称 |
| `category` | `VARCHAR(100)` | 配料类别 |
| `abv` | `FLOAT` | 酒精度 |
| `description` | `TEXT` | 描述 |

**配方配料关联表 (`cocktail_recipe_ingredient`)**
| 字段名 | 数据类型 | 描述 |
|-------|---------|------|
| `id` | `INT` | 关联 ID |
| `recipe_id` | `INT` | 配方 ID |
| `ingredient_id` | `INT` | 配料 ID |
| `amount` | `VARCHAR(100)` | 用量 |
| `unit` | `VARCHAR(50)` | 单位 |

#### 3.5.2 Neo4j 图数据库

**节点类型**
- `Recipe`：配方节点
- `Ingredient`：配料节点
- `Flavor`：风味节点
- `Category`：类别节点

**关系类型**
- `CONTAINS`：配方包含配料
- `HAS_FLAVOR`：配料具有风味
- `BELONGS_TO`：配料属于类别
- `SIMILAR_TO`：配料/配方相似

### 3.6 关键技术实现

#### 3.6.1 双数据库集成

```python
# db/neo4j.py
from neo4j import GraphDatabase

class Neo4jClient:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            return [record.data() for record in result]
```

#### 3.6.2 配方分析服务

```python
# cocktail/services_combo_adjust.py
def analyze_recipe(recipe_id):
    # 获取配方信息
    recipe = Recipe.objects.get(recipe_id=recipe_id)
    
    # 分析配料比例
    ingredients = RecipeIngredient.objects.filter(recipe_id=recipe_id)
    
    # 计算风味分布
    flavor_distribution = calculate_flavor_distribution(ingredients)
    
    # 计算 SQE 评分
    sqe_score = calculate_sqe_score(ingredients)
    
    return {
        'recipe': recipe,
        'ingredients': ingredients,
        'flavor_distribution': flavor_distribution,
        'sqe_score': sqe_score
    }
```

#### 3.6.3 配料替换推荐

```python
# graph/services/substitute_service.py
def get_substitutes(ingredient_id, limit=5):
    # 查询相似配料
    query = """
    MATCH (i:Ingredient {id: $ingredient_id})-[r:SIMILAR_TO]->(s:Ingredient)
    RETURN s.id, s.name, r.score
    ORDER BY r.score DESC
    LIMIT $limit
    """
    
    result = neo4j_client.run_query(query, {"ingredient_id": ingredient_id, "limit": limit})
    return result
```

## 4. 部署与运行

### 4.1 环境要求

- Python 3.8+
- MySQL 8.0+
- Neo4j 5.0+
- Django 5.2+

### 4.2 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd graduation-sys/backend
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r backend_requirements.txt
   ```

4. **配置数据库**
   - 配置 MySQL 数据库，创建 `cocktail_graph` 数据库
   - 配置 Neo4j 数据库，设置用户名和密码
   - 修改 `settings.py` 中的数据库配置

5. **数据库迁移**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **启动服务器**
   ```bash
   python manage.py runserver
   ```

### 4.3 测试

```bash
# 运行测试
python manage.py test

# 测试酒精状态
python test_alcoholic_status.py
```

## 5. 前端对接

前端项目位于 `../frontend` 目录，使用 Vue.js 构建。前端通过 RESTful API 与后端通信，实现数据的展示和交互。

### 5.1 API 调用示例

```javascript
// 前端调用示例
import axios from 'axios';

// 获取配方列表
export const getRecipes = async () => {
  const response = await axios.get('http://localhost:8000/api/recipes/');
  return response.data;
};

// 获取配方详情
export const getRecipeDetail = async (id) => {
  const response = await axios.get(`http://localhost:8000/api/recipes/${id}/`);
  return response.data;
};

// 搜索配方
export const searchRecipes = async (query) => {
  const response = await axios.get(`http://localhost:8000/api/recipes/search/?q=${query}`);
  return response.data;
};
```

## 6. 总结与展望

### 6.1 系统特点

- **双数据库架构**：结合 MySQL 和 Neo4j 的优势，实现高效的数据存储和查询
- **RESTful API**：标准化的 API 设计，便于前端集成
- **智能分析**：基于图数据库的配方分析和推荐
- **创新功能**：支持配料替换、配方调整和新品生成
- **历史记录**：基于用户行为的个性化推荐

### 6.2 未来改进方向

- **机器学习集成**：引入机器学习模型，提高推荐精度
- **用户认证系统**：完善用户注册、登录和权限管理
- **多语言支持**：支持多语言配方和界面
- **移动应用开发**：开发移动端应用，提高用户体验
- **社区功能**：添加用户评论、评分和分享功能

### 6.3 技术价值

本系统展示了如何结合关系型数据库和图数据库构建复杂的应用系统，为类似的项目提供了参考。通过图数据库的优势，实现了高效的关联查询和推荐功能，为鸡尾酒爱好者和专业调酒师提供了有价值的工具。

---

**作者**：项目团队
**日期**：2026-04-06
**版本**：1.0.0