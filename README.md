# 鸡尾酒配方创新与分析系统

## 项目概述

本项目是一个基于结构分析的鸡尾酒配方创新与分析系统，旨在通过人工智能技术和数据驱动的方法，为用户提供个性化的鸡尾酒配方推荐和分析。系统不仅支持传统配方的管理和展示，还能基于用户输入的基础原料、应用场景和风味偏好，智能生成新的配方组合。

## 理论基础

### 1. 鸡尾酒结构理论

鸡尾酒的结构通常由以下几个部分组成：

- **基酒 (Base)**: 鸡尾酒的主要成分，通常是烈酒，如伏特加、金酒、朗姆酒等
- **辅料 (Modifier)**: 调整基酒风味的成分，如利口酒、果汁、糖浆等
- **装饰 (Garnish)**: 提升视觉效果和风味层次的成分，如柠檬片、橄榄等
- **稀释剂 (Diluent)**: 调整酒精度和口感的成分，如苏打水、冰块等

本系统基于这一结构理论，通过分析原料之间的相互作用，生成平衡的配方组合。

### 2. 风味轮理论

风味轮是一种用于描述和分类风味的工具，本系统使用了扩展的风味轮模型，包括以下维度：

- **酸味 (Sour)**: 如柠檬汁、酸橙汁等带来的酸味
- **甜味 (Sweet)**: 如糖浆、利口酒等带来的甜味
- **苦味 (Bitter)**: 如苦精、某些利口酒等带来的苦味
- **香气 (Aroma)**: 如香草、香料等带来的香气
- **果香 (Fruity)**: 如各种水果带来的果味
- **酒体 (Body)**: 描述酒的浓稠度和口感

用户可以通过调整这些维度的强度，获得符合个人口味的配方。

### 3. 原料相互作用理论

原料之间的相互作用是影响鸡尾酒风味的关键因素，主要包括：

- **协同作用 (Synergy)**: 两种或多种原料组合后，风味大于各自单独使用时的总和
- **对比作用 (Contrast)**: 原料之间的风味对比，如酸甜平衡
- **补充作用 (Complement)**: 一种原料增强另一种原料的风味
- **抑制作用 (Suppression)**: 一种原料减弱另一种原料的风味

系统通过分析这些相互作用，生成和谐的原料组合。

## 技术实现

### 前端技术栈

- **Vue 3**: 使用 Composition API 构建组件
- **Ant Design Vue**: 提供UI组件库
- **ECharts**: 实现数据可视化图表
- **marked**: 渲染Markdown格式内容
- **Axios**: 处理HTTP请求

### 后端技术栈

- **Spring Boot**: 构建RESTful API
- **Python**: 实现核心算法和数据分析
- **Neo4j**: 存储和查询原料关系网络
- **MySQL**: 存储用户数据和配方信息

### 核心模块

#### 1. 创新风味组合生成模块

**功能**：基于用户输入的基础原料、应用场景和风味偏好，生成个性化的鸡尾酒配方。

**实现细节**：

- 使用Vue 3 Composition API管理状态
- 通过ECharts实现风味偏好饼图可视化
- 调用后端API进行智能配方生成
- 支持原料搜索、分类筛选和选择

**关键代码**：

```javascript
const generateCombinations = async () => {
  if (selectedIngredients.value.length === 0) {
    message.error('请至少选择一个基础原料');
    return;
  }
  
  loading.value = true;
  
  try {
    // 准备请求参数
    const requestData = {
      base_ingredients: selectedIngredients.value.map(ing => ing.id.replace('c_', '')),
      scene: scene.value,
      flavor_preferences: flavorPreferences.value
    };
    
    // 调用后端创新生成API
    const apiUrl = 'http://localhost:8000/api/innovation/generate';
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData)
    });
    
    const data = await response.json();
    
    if (data.code === 0) {
      // 使用后端返回的真实数据
      combinations.value = data.data.generated_combinations || [];
      message.success('酒单生成成功！');
    } else {
      message.error('生成失败: ' + (data.message || '未知错误'));
    }
  } catch (error) {
    console.error('生成失败:', error);
    message.error('生成失败，请重试');
  } finally {
    loading.value = false;
  }
};
```

#### 2. 配方分析模块

**功能**：对现有配方进行结构分析和风味评估。

**实现细节**：

- 分析配方的原料组成和比例
- 评估风味平衡度和创新程度
- 生成可视化的风味分析图表

#### 3. 原料关系网络模块

**功能**：构建和查询原料之间的关系网络。

**实现细节**：

- 使用Neo4j存储原料之间的关系
- 实现基于图算法的原料推荐
- 分析原料之间的协同效应

### 数据流程

1. **用户输入**：用户选择基础原料、应用场景和调整风味偏好
2. **数据处理**：前端处理用户输入，准备请求参数
3. **API调用**：调用后端创新生成API
4. **算法处理**：后端算法分析原料关系，生成配方组合
5. **结果返回**：后端返回生成的配方数据
6. **前端展示**：前端展示生成的配方详情

### 算法实现

#### 1. 配方生成算法

- **基于规则的生成**：根据鸡尾酒结构理论，确保配方包含必要的成分类型
- **基于相似度的推荐**：分析现有配方，推荐相似但有创新的组合
- **基于优化的调整**：根据用户的风味偏好，调整原料比例

#### 2. 风味评估算法

- **平衡度计算**：评估配方中各风味维度的平衡程度
- **创新度计算**：分析配方与传统配方的差异程度
- **协同效应分析**：评估原料之间的相互作用效果

## 项目结构

```
├── frontend/            # 前端代码
│   ├── src/
│   │   ├── components/  # 组件
│   │   │   ├── innovation/  # 创新生成组件
│   │   │   └── common/  # 通用组件
│   │   ├── views/       # 页面
│   │   ├── api/         # API调用
│   │   └── assets/      # 静态资源
├── backend/             # 后端代码
│   ├── src/
│   │   ├── main/java/   # Java代码
│   │   └── main/resources/  # 配置文件
│   └── python/          # Python算法
├── database/            # 数据库脚本
└── docs/                # 文档
```

## 核心API

### 1. 原料相关API

- **GET /api/ingredients**：获取原料列表
- **GET /api/ingredients/{id}**：获取原料详情
- **GET /api/ingredients/categories**：获取原料分类

### 2. 配方相关API

- **GET /api/recipes**：获取配方列表
- **GET /api/recipes/{id}**：获取配方详情
- **POST /api/recipes**：创建新配方

### 3. 创新生成API

- **POST /api/innovation/generate**：生成新配方
- **POST /api/innovation/analyze**：分析配方

## 技术亮点

1. **智能配方生成**：基于原料关系网络和用户偏好，生成个性化配方
2. **数据可视化**：通过ECharts实现风味偏好和配方分析的可视化
3. **响应式设计**：适配不同屏幕尺寸，提供良好的移动端体验
4. **实时反馈**：通过动画和交互效果，提供实时的用户反馈
5. **模块化架构**：清晰的代码结构，便于维护和扩展

## 未来发展

1. **用户个性化**：基于用户历史偏好，提供更个性化的推荐
2. **社区功能**：允许用户分享和评价配方
3. **多语言支持**：支持中英文切换
4. **移动端应用**：开发iOS和Android应用
5. **增强现实**：使用AR技术展示鸡尾酒制作过程

## 安装与运行

### 前端

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run serve


# 构建生产版本
npm run build
```

### 后端

```bash
# 启动Spring Boot应用
./mvnw spring-boot:run

# 启动Python算法服务
python backend/python/server.py
```

## python -m agent.app.main

python manage.py runserver
