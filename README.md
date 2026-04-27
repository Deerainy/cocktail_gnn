# 🍹 鸡尾酒配方创新与分析系统

<div align="center">
  <img src="./frontend/src/assets/logo.png" alt="Logo" width="200" height="200">
  <p>基于AI的鸡尾酒配方创新与分析平台</p>

  <div style="display: flex; gap: 10px; justify-content: center; margin: 20px 0;">
    <img src="https://img.shields.io/badge/Vue-3-green" alt="Vue 3">
    <img src="https://img.shields.io/badge/Django-REST-orange" alt="Django REST">
    <img src="https://img.shields.io/badge/Python-3.8+-blue" alt="Python 3.8+">
    <img src="https://img.shields.io/badge/Neo4j-Graph%20DB-purple" alt="Neo4j">
    <img src="https://img.shields.io/badge/MySQL-Database-yellow" alt="MySQL">
  </div>
</div>

## 📋 项目简介

本项目是一个基于结构分析的鸡尾酒配方创新与分析系统，旨在通过人工智能技术和数据驱动的方法，为用户提供个性化的鸡尾酒配方推荐和分析。系统不仅支持传统配方的管理和展示，还能基于用户输入的基础原料、应用场景和风味偏好，智能生成新的配方组合。

## ✨ 核心功能

### 1. 创新风味组合生成

- 🎯 基于用户输入的基础原料、应用场景和风味偏好，生成个性化的鸡尾酒配方
- 📊 通过ECharts实现风味偏好可视化
- 🔍 支持原料搜索、分类筛选和选择
- 🧠 智能算法分析原料关系，生成平衡的配方组合

### 2. 配方分析模块

- 📈 对现有配方进行结构分析和风味评估
- ⚖️ 评估风味平衡度和创新程度
- 📋 生成详细的配方分析报告

### 3. 原料关系网络

- 🔗 使用Neo4j构建和查询原料之间的关系网络
- 🤝 分析原料之间的协同效应
- 💡 基于图算法的原料推荐

### 4. 实体识别与审核

- 🔍 智能识别配方和原料实体
- ✅ 人工审核和纠正实体识别结果
- 📚 构建和维护实体库

## 🛠️ 技术栈

### 前端技术

| 技术             | 版本      | 用途         |
| -------------- | ------- | ---------- |
| Vue 3          | ^3.2.13 | 前端框架       |
| Ant Design Vue | ^4.2.6  | UI组件库      |
| ECharts        | ^5.4.3  | 数据可视化      |
| Axios          | ^1.14.0 | HTTP请求     |
| marked         | ^17.0.5 | Markdown渲染 |
| Vue Router     | ^4.0.3  | 路由管理       |
| Vuex           | ^4.0.0  | 状态管理       |

### 后端技术

| 技术                    | 用途          |
| --------------------- | ----------- |
| Django                | Web框架       |
| Django REST Framework | API构建       |
| Python                | 核心算法和数据分析   |
| Neo4j                 | 存储和查询原料关系网络 |
| MySQL                 | 存储用户数据和配方信息 |

### 智能代理

- 基于LLM的用户意图分析
- 智能会话管理
- 个性化推荐服务

## 🚀 快速开始

### 环境要求

- Node.js >= 14
- Python >= 3.8
- MySQL
- Neo4j

### 前端安装与运行

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run serve

# 构建生产版本
npm run build
```

### 后端安装与运行

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 启动服务器
python manage.py runserver
```

### 智能代理运行

```bash
# 进入agent目录
cd agent

# 安装依赖
pip install -r requirements.txt

# 启动代理服务
python -m agent.app.main
```

## 📁 项目结构

```
├── agent/             # 智能代理系统
│   ├── app/           # 代理核心代码
│   └── data/          # 代理数据
├── backend/           # 后端代码
│   ├── backend/       # Django项目配置
│   ├── cocktail/      # 鸡尾酒相关API
│   ├── entity/        # 实体识别与审核
│   └── graph/         # 原料关系网络
├── frontend/          # 前端代码
│   ├── public/        # 静态资源
│   └── src/           # 源代码
│       ├── api/       # API调用
│       ├── assets/    # 资源文件
│       ├── components/ # 组件
│       └── views/     # 页面
├── .gitignore         # Git忽略文件
└── README.md          # 项目文档
```

## 🌐 API文档

### 原料相关API

- `GET /api/ingredients`：获取原料列表
- `GET /api/ingredients/{id}`：获取原料详情
- `GET /api/ingredients/categories`：获取原料分类

### 配方相关API

- `GET /api/recipes`：获取配方列表
- `GET /api/recipes/{id}`：获取配方详情
- `POST /api/recipes`：创建新配方

### 创新生成API

- `POST /api/innovation/generate`：生成新配方
- `POST /api/innovation/analyze`：分析配方

### 实体相关API

- `POST /api/entity/process`：处理单个文本的实体识别
- `POST /api/entity/batch_process`：批量处理文本的实体识别
- `POST /api/entity/review`：提交审核结果
- `GET /api/entity/review_tasks`：获取审核任务列表

## 🎨 界面预览

### 创新配方生成

![创新配方生成](https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cocktail%20recipe%20generator%20interface%20with%20ingredient%20selection%20and%20flavor%20preferences%20sliders\&image_size=landscape_16_9)

### 配方分析

![配方分析](https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cocktail%20recipe%20analysis%20dashboard%20with%20flavor%20balance%20charts\&image_size=landscape_16_9)

### 原料关系网络

![原料关系网络](https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=interactive%20ingredient%20relationship%20graph%20visualization\&image_size=landscape_16_9)

## 🔬 核心算法

### 1. 配方生成算法

- **基于规则的生成**：根据鸡尾酒结构理论，确保配方包含必要的成分类型
- **基于相似度的推荐**：分析现有配方，推荐相似但有创新的组合
- **基于优化的调整**：根据用户的风味偏好，调整原料比例

### 2. 风味评估算法

- **平衡度计算**：评估配方中各风味维度的平衡程度
- **创新度计算**：分析配方与传统配方的差异程度
- **协同效应分析**：评估原料之间的相互作用效果

### 3. 实体识别算法

- **词典/规则优先**：使用pattern词典、alias映射和标准实体库进行高精度识别
- **模糊匹配/检索兜底**：处理第一层未命中的实体
- **LLM候选分析**：对前两层都无法处理的实体，使用LLM进行候选分析

## 📖 使用指南

### 生成新配方

1. 在首页选择基础原料（如伏特加、金酒等）
2. 选择应用场景（如派对、约会、休闲等）
3. 调整风味偏好滑块（酸味、甜味、苦味等）
4. 点击"生成配方"按钮
5. 浏览生成的配方列表，查看详细信息

### 分析现有配方

1. 进入"配方分析"页面
2. 输入或选择现有配方
3. 系统会自动分析配方的结构和风味
4. 查看分析结果和改进建议

### 探索原料关系

1. 进入"原料网络"页面
2. 搜索或选择原料
3. 查看该原料与其他原料的关系
4. 探索推荐的原料组合

## 🌟 技术亮点

1. **智能配方生成**：基于原料关系网络和用户偏好，生成个性化配方
2. **数据可视化**：通过ECharts实现风味偏好和配方分析的可视化
3. **响应式设计**：适配不同屏幕尺寸，提供良好的移动端体验
4. **实时反馈**：通过动画和交互效果，提供实时的用户反馈
5. **模块化架构**：清晰的代码结构，便于维护和扩展
6. **多模态AI**：结合规则引擎和LLM，实现更准确的实体识别
7. **图数据库应用**：使用Neo4j构建复杂的原料关系网络

## 📈 未来规划

- [ ] **用户个性化**：基于用户历史偏好，提供更个性化的推荐
- [ ] **社区功能**：允许用户分享和评价配方
- [ ] **多语言支持**：支持中英文切换
- [ ] **移动端应用**：开发iOS和Android应用
- [ ] **增强现实**：使用AR技术展示鸡尾酒制作过程
- [ ] **智能调酒助手**：基于语音交互的调酒指导
- [ ] **商业版功能**：为酒吧和餐厅提供专业版功能

## 🤝 贡献指南

欢迎贡献代码、提出问题和建议！请遵循以下步骤：

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启Pull Request

## 📄 许可证

本项目采用MIT许可证。详见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

- **项目维护者**：Deerainy
- **邮箱**：[yuxinlu0410@gmail.com](mailto:contact@cocktail-innovation.com)

***

<div align="center">
  <p>✨ Why don’t we grab a drink together?  ✨</p>
</div>
