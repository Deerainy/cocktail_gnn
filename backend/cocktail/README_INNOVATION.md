# 创新页面功能设计与实现

## 1. 功能概述

创新页面是一个基于结构分析的风味组合生成系统，主要功能包括：

- **智能配方生成**：基于用户提供的基础原料，自动生成创意鸡尾酒配方
- **风味平衡分析**：分析配方的风味特征，确保口感平衡
- **场景适配**：根据不同场景（如派对、休闲、正式等）生成适合的配方
- **创意级别调整**：支持低、中、高不同创意级别的配方生成
- **LLM 辅助**：使用大语言模型生成鸡尾酒名称和制作方法
- **比例建议**：为生成的配方提供合理的原料比例建议

## 2. 核心理论基础

### 2.1 风味组合理论

- **风味平衡**：通过分析原料的酸、甜、苦、香、果味和酒体等特征，确保配方的风味平衡
- **原料兼容性**：基于图数据库中的兼容性数据，评估不同原料之间的搭配效果
- **原料多样性**：确保配方中包含不同类型的原料，如烈酒、利口酒、 mixer 等
- **场景适配性**：根据不同场景的需求，选择适合的原料组合

### 2.2 创意评估理论

- **原料组合多样性**：通过计算原料类型的多样性评估创意程度
- **兼容性反转**：适当的低兼容性原料组合可以增加创意性
- **风味特征分布**：通过风味特征的标准差评估配方的独特性

### 2.3 算法理论

- **组合生成算法**：使用递归方法生成不同长度的原料组合
- **评分排序算法**：基于兼容性、多样性和平衡度对组合进行评分
- **比例分配算法**：基于原料角色分配合理的比例

## 3. 技术实现

### 3.1 技术栈

| 技术 | 用途 |
|------|------|
| Python | 后端开发语言 |
| Django | Web 框架 |
| Django REST Framework | API 开发 |
| MySQL | 关系型数据库 |
| Neo4j | 图数据库（存储原料关系） |
| NumPy | 数值计算 |
| OpenAI API | 大语言模型调用 |
| DeepSeek API | 备选大语言模型 |

### 3.2 核心模块

#### 3.2.1 创新生成视图

`InnovationGenerationView` 是创新页面的核心视图类，负责处理配方生成请求。

**主要功能**：
- 接收用户输入的基础原料、风味偏好、场景和创意级别
- 生成候选原料列表
- 生成并评估原料组合
- 使用 LLM 生成鸡尾酒名称和制作方法
- 返回格式化的结果

#### 3.2.2 候选原料生成

`_generate_candidates` 方法负责生成候选原料列表：

- 根据创意级别调整兼容性阈值和候选数量
- 基于图数据库中的兼容性数据查找候选原料
- 考虑原料的重要性和频率
- 根据场景过滤不适合的原料

#### 3.2.3 组合生成与评估

`_generate_combinations` 方法生成原料组合：
- 生成不同长度的原料组合
- 检查组合的有效性（原料多样性和风味平衡）

`_evaluate_combination` 方法评估组合质量：
- 计算原料间的兼容性得分
- 计算风味多样性
- 计算原料类型多样性

#### 3.2.4 LLM 集成

`_generate_with_llm` 方法使用大语言模型生成鸡尾酒名称和制作方法：
- 构建原料列表、风味特征和场景描述
- 生成提示词
- 调用 LLM API
- 处理 API 调用失败的情况

#### 3.2.5 比例生成

`_generate_proportions` 方法为生成的配方提供比例建议：
- 基于原料角色分配比例
- 调整比例确保总和为 100%

### 3.3 数据模型

系统使用以下数据模型：

- **CanonicalFreqV2**：存储原料的使用频率
- **IngredientFlavorAnchor**：存储原料的风味锚点
- **IngredientFlavorFeature**：存储原料的风味特征
- **SqeNodeImportance**：存储原料的重要性
- **GraphFlavorCompatEdgeStats**：存储原料间的兼容性数据
- **LlmCanonicalMap**：存储原料的名称映射

### 3.4 API 设计

#### 3.4.1 创新生成 API

| API 路径 | 方法 | 功能 |
|---------|------|------|
| `/api/innovation/generate/` | POST | 生成创新配方 |

**请求参数**：
- `base_ingredients`：基础原料列表
- `flavor_preferences`：风味偏好
- `scene`：场景（general, party, casual, formal, summer, winter）
- `creativity_level`：创意级别（low, medium, high）
- `max_ingredients`：最大原料数量

**响应数据**：
- `base_ingredients`：基础原料信息
- `generated_combinations`：生成的配方组合
- `meta`：元数据（场景、创意级别等）

## 4. 关键算法实现

### 4.1 组合生成算法

```python
def _generate_k_combinations(self, items, k):
    """生成k元素组合"""
    if k == 0:
        return [[]]
    if not items:
        return []
    
    combinations = []
    for i in range(len(items)):
        current = items[i]
        remaining = items[i+1:]
        for combo in self._generate_k_combinations(remaining, k-1):
            combinations.append([current] + combo)
    
    # 随机选择一些组合，避免过多
    if len(combinations) > 20:
        random.shuffle(combinations)
        combinations = combinations[:20]
    
    return combinations
```

### 4.2 组合评估算法

```python
def _evaluate_combination(self, combo, base_features):
    """评估组合质量"""
    score = 0
    
    # 1. 计算原料间的兼容性得分
    compat_scores = []
    for i in range(len(combo)):
        for j in range(i+1, len(combo)):
            edge = GraphFlavorCompatEdgeStats.objects.filter(
                Q(i_canonical_id=combo[i], j_canonical_id=combo[j]) |
                Q(i_canonical_id=combo[j], j_canonical_id=combo[i])
            ).first()
            if edge:
                compat_scores.append(edge.weight)
    
    if compat_scores:
        score += float(sum(compat_scores) / len(compat_scores)) * 0.5
    
    # 2. 计算风味多样性
    # ... (代码省略) ...
    
    # 3. 计算原料类型多样性
    # ... (代码省略) ...
    
    return score
```

### 4.3 创意评估算法

```python
def _evaluate_creativity(self, combo):
    """评估组合的创意级别"""
    # 基于原料的多样性和兼容性评估创意级别
    # 1. 计算原料类型多样性
    roles = set()
    for cid in combo:
        anchor = IngredientFlavorAnchor.objects.filter(canonical_id=cid).first()
        if anchor:
            roles.add(anchor.anchor_form)
    
    # 2. 计算原料间的平均兼容性
    # ... (代码省略) ...
    
    # 3. 计算创意分数
    creativity_score = float((1 - avg_compat) * 0.6 + role_diversity * 0.4)
    
    # 4. 确定创意级别
    if creativity_score > 0.7:
        return "激进"
    elif creativity_score > 0.4:
        return "适中"
    else:
        return "保守"
```

### 4.4 LLM 调用实现

```python
def _call_llm_api(self, prompt):
    """调用LLM API生成内容"""
    max_retries = 2
    for retry in range(max_retries):
        try:
            # 使用OpenAI客户端调用LLM API
            from openai import OpenAI
            
            # 配置OpenAI客户端
            client = OpenAI(
                api_key="sk-ede8258f75cd47aa90248b99bb1c6a6f",
                base_url="https://api.deepseek.com/v1"
            )
            
            # 发送请求
            response = client.chat.completions.create(
                model="deepseek-chat",
                temperature=0.7,
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": "你是一位专业的调酒师，擅长为鸡尾酒起创意名称和编写详细的制作方法。"},
                    {"role": "user", "content": prompt}
                ],
                timeout=30
            )
            
            # 提取响应内容
            content = response.choices[0].message.content.strip()
            return content
        except Exception as e:
            print(f"LLM API调用失败 (尝试 {retry+1}/{max_retries}): {e}")
            if retry < max_retries - 1:
                import time
                time.sleep(2)  # 等待2秒后重试
            else:
                return ""
```

## 5. 技术流程

1. **请求处理**：接收用户输入的基础原料、风味偏好、场景和创意级别
2. **原料解析**：解析基础原料，提取 canonical_id
3. **特征获取**：获取基础原料的风味特征和锚点信息
4. **候选生成**：基于兼容性数据和场景生成候选原料列表
5. **组合生成**：生成不同长度的原料组合
6. **组合评估**：评估组合的兼容性、多样性和平衡度
7. **LLM 处理**：使用大语言模型生成鸡尾酒名称和制作方法
8. **结果格式化**：格式化结果并返回

## 6. 使用示例

### 6.1 API 调用示例

```python
import requests
import json

url = "http://localhost:8000/api/innovation/generate/"
data = {
    "base_ingredients": ["gin"],
    "flavor_preferences": {
        "sour": 0.6,
        "sweet": 0.4
    },
    "scene": "party",
    "creativity_level": "medium",
    "max_ingredients": 5
}

response = requests.post(url, json=data)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
```

### 6.2 响应示例

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "base_ingredients": [
      {
        "id": "c_gin",
        "name": "gin",
        "name_zh": "金酒",
        "type": "spirit",
        "role": "spirit"
      }
    ],
    "generated_combinations": [
      {
        "ingredients": [
          {
            "id": "c_gin",
            "name": "gin",
            "name_zh": "金酒",
            "type": "spirit",
            "role": "spirit"
          },
          {
            "id": "c_lemon_juice",
            "name": "lemon juice",
            "name_zh": "柠檬汁",
            "type": "fruit",
            "role": "fruit"
          },
          {
            "id": "c_sugar",
            "name": "sugar",
            "name_zh": "糖",
            "type": "sweetener",
            "role": "mixer"
          }
        ],
        "flavor_profile": {
          "sour": 0.5,
          "sweet": 0.4,
          "bitter": 0.2,
          "aroma": 0.7,
          "fruity": 0.5,
          "body": 0.6
        },
        "proportions": [
          {
            "ingredient_id": "c_gin",
            "proportion": 40
          },
          {
            "ingredient_id": "c_lemon_juice",
            "proportion": 30
          },
          {
            "ingredient_id": "c_sugar",
            "proportion": 30
          }
        ],
        "suggested_name": "金柠派对",
        "recipe": "1. 所需材料：金酒 40ml，柠檬汁 30ml，糖 30g，冰块适量\n2. 制作步骤：将所有材料放入调酒壶中，加入冰块，用力摇晃15秒，滤入杯中\n3. 装饰建议：柠檬片\n4. 饮用建议：冰镇饮用",
        "creativity_level": "适中"
      }
    ],
    "meta": {
      "scene": "party",
      "creativity_level": "medium",
      "max_ingredients": 5,
      "flavor_preferences": {
        "sour": 0.6,
        "sweet": 0.4
      }
    }
  }
}
```

## 7. 性能优化

### 7.1 优化策略

- **缓存机制**：缓存频繁使用的原料数据和兼容性数据
- **并行处理**：使用多线程并行处理组合生成和评估
- **结果限制**：限制生成的组合数量，提高响应速度
- **LLM 调用优化**：使用批处理和错误重试机制

### 7.2 性能指标

- **响应时间**：在正常情况下，响应时间应控制在 3-5 秒内
- **成功率**：LLM 调用成功率应达到 95% 以上
- **内存使用**：内存使用应控制在合理范围内，避免内存溢出

## 8. 未来改进方向

### 8.1 功能改进

- **用户偏好学习**：基于用户历史选择学习用户偏好
- **季节性推荐**：根据季节变化推荐适合的配方
- **健康因素**：考虑健康因素，如卡路里、酒精含量等
- **文化因素**：考虑不同文化背景的饮酒偏好

### 8.2 技术改进

- **模型优化**：使用更先进的机器学习模型预测原料兼容性
- **实时数据**：整合实时原料价格和可用性数据
- **多语言支持**：支持多语言的配方生成和描述
- **移动应用**：开发移动应用，提供更便捷的使用体验

### 8.3 集成扩展

- **社交分享**：支持将生成的配方分享到社交媒体
- **用户评价**：允许用户评价和反馈生成的配方
- **专业调酒师审核**：引入专业调酒师审核机制，提高配方质量
- **商业合作**：与酒吧和酒厂合作，推广生成的配方

## 9. 总结

创新页面是一个结合了传统调酒知识和现代人工智能技术的系统，通过分析原料的风味特征和兼容性，生成创意、平衡的鸡尾酒配方。系统不仅考虑了原料的搭配合理性，还考虑了场景适配性和创意级别，为用户提供了个性化的配方推荐。

通过整合图数据库、机器学习和大语言模型等技术，创新页面实现了从原料选择到配方生成的全流程自动化，为鸡尾酒爱好者和专业调酒师提供了一个强大的工具。未来，随着技术的不断发展和数据的积累，系统将能够生成更加个性化、创意性和高质量的鸡尾酒配方。

---

**作者**：项目团队
**日期**：2026-04-06
**版本**：1.0.0