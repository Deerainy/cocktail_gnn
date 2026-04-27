from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from .models_recipe import (
    CanonicalFreqV2, IngredientFlavorAnchor, IngredientFlavorFeature,
    SqeNodeImportance, GraphFlavorCompatEdgeStats, LlmCanonicalMap
)
import random
import numpy as np
from collections import defaultdict
import requests
import json


class InnovationGenerationView(APIView):
    permission_classes = []
    """
    基于结构分析的风味组合生成
    """
    
    # 场景规则配置
    SCENE_RULES = {
        'party': ['spirit', 'liqueur', 'soda', 'fruit'],
        'casual': ['spirit', 'mixer', 'fruit', 'herb'],
        'formal': ['spirit', 'liqueur', 'fortified_wine'],
        'summer': ['fruit', 'soda', 'citrus'],
        'winter': ['spice', 'warm', 'fortified_wine']
    }
    
    # 原料角色权重配置
    ROLE_WEIGHTS = {
        'spirit': 40,
        'liqueur': 20,
        'mixer': 30,
        'fruit': 15,
        'herb': 5,
        'bitters': 3,
        'fortified_wine': 25
    }
    
    # 创意级别配置
    CREATIVITY_CONFIG = {
        'low': {'min_weight': 0.7, 'topk': 5},
        'medium': {'min_weight': 0.5, 'topk': 10},
        'high': {'min_weight': 0.3, 'topk': 15}
    }
    
    def post(self, request):
        try:
            # 获取请求参数
            base_ingredients = request.data.get('base_ingredients', [])
            flavor_preferences = request.data.get('flavor_preferences', {})
            scene = request.data.get('scene', 'general')
            creativity_level = request.data.get('creativity_level', 'medium')  # low, medium, high
            max_ingredients = request.data.get('max_ingredients', 5)
            
            # 验证参数
            if not base_ingredients:
                return Response({
                    'code': 400,
                    'message': '至少需要一个基础原料',
                    'data': None
                })
            
            # 1. 解析基础原料
            base_canonical_ids = []
            for ing in base_ingredients:
                if isinstance(ing, dict) and 'id' in ing:
                    # 从ID中提取canonical_id
                    canonical_id = ing['id'].replace('c_', '') if ing['id'].startswith('c_') else ing['id']
                    base_canonical_ids.append(canonical_id)
                elif isinstance(ing, str):
                    # 直接使用字符串作为canonical_id
                    base_canonical_ids.append(ing)
            
            # 2. 获取基础原料的风味特征
            base_features = {}
            base_anchors = {}
            for canonical_id in base_canonical_ids:
                anchor = IngredientFlavorAnchor.objects.filter(canonical_id=canonical_id).first()
                if anchor:
                    base_anchors[canonical_id] = anchor
                    feature = IngredientFlavorFeature.objects.filter(anchor_name=anchor.anchor_name).first()
                    if feature:
                        base_features[canonical_id] = {
                            'sour': feature.sour,
                            'sweet': feature.sweet,
                            'bitter': feature.bitter,
                            'aroma': feature.aroma,
                            'fruity': feature.fruity,
                            'body': feature.body
                        }
            
            # 3. 基于结构分析生成候选原料
            candidate_ingredients = self._generate_candidates(
                base_canonical_ids, 
                base_anchors, 
                creativity_level,
                scene
            )
            
            # 4. 生成组合方案
            combinations = self._generate_combinations(
                base_canonical_ids, 
                candidate_ingredients, 
                base_features,
                max_ingredients,
                flavor_preferences
            )
            
            # 5. 评估并排序组合
            evaluated_combinations = []
            for combo in combinations:
                score = self._evaluate_combination(combo, base_features)
                evaluated_combinations.append((score, combo))
            
            # 按分数排序，取前3个（减少生成数量，提高速度）
            evaluated_combinations.sort(reverse=True)
            top_combinations = [combo for _, combo in evaluated_combinations[:2]]
            
            # 6. 格式化结果
            result = {
                'base_ingredients': self._format_ingredients(base_canonical_ids),
                'generated_combinations': [
                    self._format_combination(combo, scene) for combo in top_combinations
                ],
                'meta': {
                    'scene': scene,
                    'creativity_level': creativity_level,
                    'max_ingredients': max_ingredients,
                    'flavor_preferences': flavor_preferences
                }
            }
            
            return Response({
                'code': 0,
                'message': 'ok',
                'data': result
            })
        
        except Exception as e:
            return Response({
                'code': 500,
                'message': str(e),
                'data': None
            })
    
    def _generate_candidates(self, base_canonical_ids, base_anchors, creativity_level, scene):
        """生成候选原料"""
        candidates = {}
        
        # 根据创意级别调整参数
        config = self.CREATIVITY_CONFIG.get(creativity_level, self.CREATIVITY_CONFIG['medium'])
        min_weight = config['min_weight']
        topk = config['topk']
        
        # 为每个基础原料找到兼容的候选
        for canonical_id in base_canonical_ids:
            # 查找兼容性高的原料
            compat_edges = GraphFlavorCompatEdgeStats.objects.filter(
                Q(i_canonical_id=canonical_id) | Q(j_canonical_id=canonical_id)
            ).filter(weight__gte=min_weight).order_by('-weight')[:topk]
            
            for edge in compat_edges:
                other_id = edge.j_canonical_id if edge.i_canonical_id == canonical_id else edge.i_canonical_id
                
                # 跳过基础原料本身
                if other_id in base_canonical_ids:
                    continue
                
                # 获取原料信息
                anchor = IngredientFlavorAnchor.objects.filter(canonical_id=other_id).first()
                if not anchor:
                    continue
                
                # 根据场景过滤
                if not self._is_suitable_for_scene(anchor, scene):
                    continue
                
                # 计算综合得分
                score = edge.weight
                
                # 考虑原料的重要性
                importance = SqeNodeImportance.objects.filter(canonical_id=other_id).first()
                if importance:
                    score *= (1 + float(importance.normalized_contribution) * 0.5)
                
                # 考虑原料的频率
                freq = CanonicalFreqV2.objects.filter(canonical_id=other_id).first()
                if freq:
                    # 频率适中的原料更适合创新
                    freq_score = min(float(freq.freq) / 100, 1.0)  # 频率过高的原料会降低分数
                    score *= (1 + float(freq_score) * 0.3)
                
                candidates[other_id] = max(candidates.get(other_id, 0), score)
        
        # 如果没有找到候选原料，使用一些默认的原料
        if not candidates:
            # 从数据库中获取一些常见的原料
            default_ingredients = CanonicalFreqV2.objects.order_by('-freq')[:10]
            for ing in default_ingredients:
                # 跳过基础原料本身
                if ing.canonical_id in base_canonical_ids:
                    continue
                
                # 获取原料信息
                anchor = IngredientFlavorAnchor.objects.filter(canonical_id=ing.canonical_id).first()
                if not anchor:
                    continue
                
                # 检查是否适合场景
                if not self._is_suitable_for_scene(anchor, scene):
                    continue
                
                # 计算得分
                score = 0.5  # 默认得分
                
                # 考虑原料频率
                freq_score = min(float(ing.freq) / 100, 1.0)
                score *= (1 + freq_score * 0.3)
                
                candidates[ing.canonical_id] = max(candidates.get(ing.canonical_id, 0), score)
        
        # 按得分排序，取前20个
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:20]
        return [cid for cid, _ in sorted_candidates]
    
    def _is_suitable_for_scene(self, anchor, scene):
        """判断原料是否适合特定场景"""
        if scene not in self.SCENE_RULES:
            return True
        
        suitable_roles = self.SCENE_RULES[scene]
        return anchor.anchor_form in suitable_roles
    
    def _generate_combinations(self, base_canonical_ids, candidate_ingredients, base_features, max_ingredients, flavor_preferences):
        """生成组合方案"""
        combinations = []
        base_count = len(base_canonical_ids)
        remaining_slots = max(1, max_ingredients - base_count)
        
        # 生成不同长度的组合
        for k in range(1, remaining_slots + 1):
            # 从候选原料中选择k个
            if len(candidate_ingredients) >= k:
                # 生成组合
                combos = self._generate_k_combinations(candidate_ingredients, k)
                for combo in combos:
                    # 合并基础原料和候选原料
                    full_combo = base_canonical_ids + list(combo)
                    # 检查组合是否有效
                    if self._is_valid_combination(full_combo, base_features):
                        combinations.append(full_combo)
        
        # 限制组合数量
        return combinations[:50]  # 最多生成50个组合
    
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
    
    def _is_valid_combination(self, combo, base_features):
        """检查组合是否有效"""
        # 1. 检查原料类型多样性
        anchors = {}
        for cid in combo:
            anchor = IngredientFlavorAnchor.objects.filter(canonical_id=cid).first()
            if anchor:
                anchors[cid] = anchor
        
        # 确保有不同类型的原料
        roles = set(anchor.anchor_form for anchor in anchors.values() if anchor)
        if len(roles) < 2:
            return False
        
        # 2. 检查风味平衡
        if len(combo) > 2:
            features = {}
            for cid in combo:
                if cid in base_features:
                    features[cid] = base_features[cid]
                else:
                    anchor = anchors.get(cid)
                    if anchor:
                        feature = IngredientFlavorFeature.objects.filter(anchor_name=anchor.anchor_name).first()
                        if feature:
                            features[cid] = {
                                'sour': feature.sour,
                                'sweet': feature.sweet,
                                'bitter': feature.bitter,
                                'aroma': feature.aroma,
                                'fruity': feature.fruity,
                                'body': feature.body
                            }
            
            if features:
                # 计算风味均值
                mean_features = {}
                for key in ['sour', 'sweet', 'bitter', 'aroma', 'fruity', 'body']:
                    values = [float(f[key]) for f in features.values() if f[key] is not None]
                    if values:
                        mean_features[key] = float(sum(values) / len(values))
                
                # 确保没有极端值
                for key, value in mean_features.items():
                    if value > 0.9 or value < 0.1:
                        return False
        
        return True
    
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
        features = {}
        for cid in combo:
            if cid in base_features:
                features[cid] = base_features[cid]
            else:
                anchor = IngredientFlavorAnchor.objects.filter(canonical_id=cid).first()
                if anchor:
                    feature = IngredientFlavorFeature.objects.filter(anchor_name=anchor.anchor_name).first()
                    if feature:
                        features[cid] = {
                            'sour': feature.sour,
                            'sweet': feature.sweet,
                            'bitter': feature.bitter,
                            'aroma': feature.aroma,
                            'fruity': feature.fruity,
                            'body': feature.body
                        }
        
        if features:
                # 计算风味标准差
                std_scores = []
                for key in ['sour', 'sweet', 'bitter', 'aroma', 'fruity', 'body']:
                    values = [float(f[key]) for f in features.values() if f[key] is not None]
                    if len(values) > 1:
                        std_scores.append(float(np.std(values)))
                
                if std_scores:
                    # 适当的多样性得分更高
                    diversity = float(sum(std_scores) / len(std_scores))
                    score += min(float(diversity * 2), 0.3)  # 多样性贡献最多30%
        
        # 3. 计算原料类型多样性
        roles = set()
        for cid in combo:
            anchor = IngredientFlavorAnchor.objects.filter(canonical_id=cid).first()
            if anchor:
                roles.add(anchor.anchor_form)
        
        role_diversity = len(roles) / 5  # 假设最多5种类型
        score += min(role_diversity, 0.2)  # 类型多样性贡献最多20%
        
        return score
    
    def _format_ingredients(self, canonical_ids):
        """格式化原料信息"""
        ingredients = []
        for cid in canonical_ids:
            anchor = IngredientFlavorAnchor.objects.filter(canonical_id=cid).first()
            mapping = LlmCanonicalMap.objects.filter(canonical_id=cid, status='ok').first()
            
            ingredient = {
                'id': f'c_{cid}',
                'name': mapping.canonical_name if mapping else str(cid),
                'name_zh': mapping.canonical_name_zh if mapping else None,
                'type': anchor.anchor_source if anchor else None,
                'role': anchor.anchor_form if anchor else None
            }
            ingredients.append(ingredient)
        return ingredients
    
    def _format_combination(self, combo, scene):
        """格式化组合信息"""
        ingredients = self._format_ingredients(combo)
        
        # 计算组合的风味特征
        features = {}
        for cid in combo:
            anchor = IngredientFlavorAnchor.objects.filter(canonical_id=cid).first()
            if anchor:
                feature = IngredientFlavorFeature.objects.filter(anchor_name=anchor.anchor_name).first()
                if feature:
                    for key in ['sour', 'sweet', 'bitter', 'aroma', 'fruity', 'body']:
                        if key not in features:
                            features[key] = []
                        if getattr(feature, key) is not None:
                            features[key].append(getattr(feature, key))
        
        # 计算平均风味特征
        avg_features = {}
        for key, values in features.items():
            if values:
                avg_features[key] = float(sum(values) / len(values))
        
        # 生成比例建议
        proportions = self._generate_proportions(combo)
        
        # 使用LLM生成名称和做法
        name, recipe = self._generate_with_llm(ingredients, avg_features, scene)
        
        # 评估创意级别
        creativity_level = self._evaluate_creativity(combo)
        
        return {
            'ingredients': ingredients,
            'flavor_profile': avg_features,
            'proportions': proportions,
            'suggested_name': name,
            'recipe_name': name,
            'recipe': recipe,
            'creativity_level': creativity_level
        }
    
    def _generate_proportions(self, combo):
        """生成比例建议"""
        proportions = []
        total_parts = 100
        
        # 基于原料角色分配比例
        role_weights = self.ROLE_WEIGHTS
        
        # 计算各角色的原料数量
        role_counts = defaultdict(int)
        for cid in combo:
            anchor = IngredientFlavorAnchor.objects.filter(canonical_id=cid).first()
            if anchor:
                role_counts[anchor.anchor_form] += 1
        
        # 分配比例
        allocated = 0
        for cid in combo:
            anchor = IngredientFlavorAnchor.objects.filter(canonical_id=cid).first()
            if anchor:
                role = anchor.anchor_form
                weight = role_weights.get(role, 10)
                count = role_counts.get(role, 1)
                part = weight // count
                proportions.append({
                    'ingredient_id': f'c_{cid}',
                    'proportion': part
                })
                allocated += part
        
        # 调整比例，确保总和为100
        if allocated > 0:
            scale = float(total_parts / allocated)
            for p in proportions:
                p['proportion'] = round(float(p['proportion']) * scale)
        
        # 处理舍入误差
        current_total = sum(p['proportion'] for p in proportions)
        if current_total != total_parts:
            diff = total_parts - current_total
            if diff > 0:
                # 增加到第一个原料
                proportions[0]['proportion'] += diff
            else:
                # 减少从最后一个原料
                proportions[-1]['proportion'] += diff
        
        return proportions
    
    def _call_llm_api(self, prompt):
        """调用LLM API生成内容"""
        max_retries = 2
        for retry in range(max_retries):
            try:
                print(f"开始调用LLM API (尝试 {retry+1}/{max_retries})，提示词长度: {len(prompt)}")
                # 使用OpenAI客户端调用LLM API
                from openai import OpenAI
                import os
                
                # 从环境变量获取API密钥和base_url
                api_key = os.environ.get('DEEPSEEK_API_KEY', 'sk-ede8258f75cd47aa90248b99bb1c6a6f')
                base_url = os.environ.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
                
                # 配置OpenAI客户端
                client = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                
                print("OpenAI客户端初始化成功")
                
                # 发送请求
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    temperature=0.7,
                    max_tokens=1000,  # 增加 max_tokens 到 1000，避免内容被截断
                    messages=[
                        {"role": "system", "content": "你是一位专业的调酒师，擅长为鸡尾酒起创意名称和编写详细的制作方法。"},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=30  # 增加超时时间到30秒
                )
                
                print("LLM API调用成功")
                
                # 提取响应内容
                content = response.choices[0].message.content.strip()
                print(f"LLM生成内容: {content[:100]}...")
                return content
            except Exception as e:
                print(f"LLM API调用失败 (尝试 {retry+1}/{max_retries}): {e}")
                if retry < max_retries - 1:
                    import time
                    time.sleep(2)  # 等待2秒后重试
                else:
                    return ""
    
    def _generate_with_llm(self, ingredients, flavor_profile, scene):
        """使用LLM生成酒单名称和做法"""
        # 构建原料列表
        ingredient_names = []
        for ing in ingredients:
            if ing.get('name_zh'):
                ingredient_names.append(ing['name_zh'])
            else:
                ingredient_names.append(ing['name'])
        
        # 构建风味特征描述
        flavor_desc = []
        for key, value in flavor_profile.items():
            if value > 0.6:
                flavor_desc.append(f"{key}味浓郁")
            elif value > 0.3:
                flavor_desc.append(f"{key}味适中")
            else:
                flavor_desc.append(f"{key}味清淡")
        
        # 构建场景描述
        scene_desc = {
            'general': '通用场合',
            'party': '派对',
            'casual': '休闲场合',
            'formal': '正式场合',
            'summer': '夏季',
            'winter': '冬季'
        }.get(scene, '通用场合')
        
        # 生成名称的提示
        name_prompt = f"为一款由{', '.join(ingredient_names)}制作的鸡尾酒起一个创意、好听的名称，适合{scene_desc}。名字要优雅、有吸引力，能够体现酒的风味特点和原料特色。可以参考经典鸡尾酒的命名风格，但要独特创新。只返回名称，不要其他内容。"
        
        # 调用LLM API生成名称
        name = self._call_llm_api(name_prompt)
        
        # 如果LLM调用失败，使用默认生成方法
        if not name:
            # 回退到默认方法
            canonical_ids = [ing['id'].replace('c_', '') for ing in ingredients]
            name = self._generate_name(canonical_ids)
        
        # 生成做法的提示，将生成的名称作为提示词的一部分，并要求统一格式
        recipe_prompt = f"为一款名为'{name}'的鸡尾酒编写详细的制作方法，这款酒由{', '.join(ingredient_names)}制作，适合{scene_desc}，风味特点是{', '.join(flavor_desc)}。请严格按照以下格式输出：\n\n鸡尾酒名称：{name}\n\n1. 所需材料及准确用量\n...\n\n2. 详细的制作步骤\n...\n\n3. 装饰建议\n...\n\n4. 饮用建议\n...\n\n请提供专业、详细且易于操作的做法，不要添加任何开场白或额外的介绍文字。"
        
        # 调用LLM API生成做法
        recipe = self._call_llm_api(recipe_prompt)
        
        return name, recipe
    
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
        compat_scores = []
        for i in range(len(combo)):
            for j in range(i+1, len(combo)):
                edge = GraphFlavorCompatEdgeStats.objects.filter(
                    Q(i_canonical_id=combo[i], j_canonical_id=combo[j]) |
                    Q(i_canonical_id=combo[j], j_canonical_id=combo[i])
                ).first()
                if edge:
                    compat_scores.append(edge.weight)
        
        avg_compat = float(sum(compat_scores) / len(compat_scores)) if compat_scores else 0.0
        role_diversity = float(len(roles) / 5)  # 假设最多5种类型
        
        # 3. 计算创意分数
        creativity_score = float((1 - avg_compat) * 0.6 + role_diversity * 0.4)
        
        # 4. 确定创意级别
        if creativity_score > 0.7:
            return "激进"
        elif creativity_score > 0.4:
            return "适中"
        else:
            return "保守"
    
    def _generate_name(self, combo):
        """生成组合名称"""
        # 获取原料名称
        names = []
        for cid in combo:
            mapping = LlmCanonicalMap.objects.filter(canonical_id=cid, status='ok').first()
            if mapping and mapping.canonical_name_zh:
                names.append(mapping.canonical_name_zh)
            elif mapping:
                names.append(mapping.canonical_name)
        
        if not names:
            return "创新饮品"
        
        # 生成名称
        if len(names) == 1:
            return f"{names[0]}特调"
        elif len(names) == 2:
            # 使用更有创意的名称组合
            creative_names = [
                f"{names[0]}遇上{names[1]}",
                f"{names[0]}与{names[1]}的邂逅",
                f"{names[0]}与{names[1]}的完美融合",
                f"{names[0]}与{names[1]}的奇妙组合"
            ]
            import random
            return random.choice(creative_names)
        else:
            # 使用更有创意的名称组合
            creative_names = [
                f"{names[0]}等原料的创意碰撞",
                f"{names[0]}等原料的完美融合",
                f"{names[0]}等原料的奇妙组合",
                f"{names[0]}等原料的创新调配"
            ]
            import random
            return random.choice(creative_names)
