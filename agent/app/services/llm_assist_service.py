#!/usr/bin/env python3
"""
LLM辅助分析服务
当硬编码无法覆盖时，使用LLM进行智能分析
"""

from typing import List, Dict, Any, Optional
import sys
import os
import json
import re

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import settings


class LLMAssistService:
    """LLM辅助分析服务"""
    
    def __init__(self):
        """初始化LLM辅助服务"""
        self.client = None
        self.model_name = None
        self._init_llm_client()
        
        # 缓存LLM分析结果，避免重复调用
        self.analysis_cache = {}
    
    def _init_llm_client(self):
        """初始化LLM客户端"""
        try:
            from openai import OpenAI
            
            self.client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
            self.model_name = settings.MODEL_NAME
            print("成功初始化LLM客户端")
        except Exception as e:
            print(f"初始化LLM客户端失败: {e}")
            self.client = None
            self.model_name = None
    
    def _fallback_extract_mood(self, response_text: str) -> Dict[str, Any]:
        """
        回退方法：手动提取心情
        
        Args:
            response_text: LLM响应文本
            
        Returns:
            Dict: 心情分析结果
        """
        # 尝试从文本中提取心情
        mood_keywords = ["开心", "难过", "放松", "兴奋", "疲惫", "焦虑"]
        for keyword in mood_keywords:
            if keyword in response_text:
                return {
                    "mood": keyword,
                    "confidence": 0.5,
                    "source": "llm_fallback"
                }
        
        return {
            "mood": "",
            "confidence": 0.0,
            "source": "llm_fallback"
        }
    
    def analyze_mood(self, user_input: str, fallback_keywords: List[str]) -> Dict[str, Any]:
        """
        分析用户心情
        
        Args:
            user_input: 用户输入
            fallback_keywords: 硬编码关键词列表
            
        Returns:
            Dict: 分析结果，包含mood和confidence
        """
        # 检查缓存
        cache_key = f"mood_{user_input}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # 首先尝试硬编码匹配
        user_input_lower = user_input.lower()
        for keyword in fallback_keywords:
            if keyword in user_input_lower:
                result = {
                    "mood": keyword,
                    "confidence": 0.9,
                    "source": "hardcoded"
                }
                self.analysis_cache[cache_key] = result
                return result
        
        # 硬编码无法匹配，使用LLM分析
        if self.client:
            try:
                prompt = f"""
请分析以下用户输入中的心情：
用户输入："{user_input}"

请返回JSON格式的分析结果，包含：
1. mood: 用户的心情（从以下选择：开心、难过、放松、兴奋、疲惫、焦虑，如果都不匹配，请根据内容推断最接近的心情）
2. confidence: 置信度（0-1之间的浮点数）
3. reasoning: 简短的分析理由

只返回JSON，不要其他内容。
"""
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                response_text = response.choices[0].message.content
                
                # 提取JSON - 使用更强大的方法
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        result["source"] = "llm"
                        self.analysis_cache[cache_key] = result
                        return result
                    except json.JSONDecodeError as e:
                        print(f"JSON解析失败: {e}, 原始内容: {response_text[:200]}")
                        # 尝试手动提取
                        return self._fallback_extract_mood(response_text)
                
            except Exception as e:
                print(f"LLM分析心情失败: {e}")
        
        # LLM也失败，返回默认值
        return {
            "mood": "",
            "confidence": 0.0,
            "source": "fallback"
        }
    
    def analyze_flavors(self, user_input: str, fallback_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        分析用户的风味偏好
        
        Args:
            user_input: 用户输入
            fallback_mapping: 硬编码风味映射
            
        Returns:
            List[Dict]: 风味列表，每个包含text和flavor_type
        """
        # 检查缓存
        cache_key = f"flavors_{user_input}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # 首先尝试硬编码匹配
        user_input_lower = user_input.lower()
        flavors = []
        
        for flavor_text, flavor_type in fallback_mapping.items():
            if flavor_text in user_input_lower:
                flavors.append({
                    "text": flavor_text,
                    "flavor_type": flavor_type,
                    "confidence": 0.9,
                    "source": "hardcoded"
                })
        
        if flavors:
            self.analysis_cache[cache_key] = flavors
            return flavors
        
        # 硬编码无法匹配，使用LLM分析
        if self.client:
            try:
                prompt = f"""
请分析以下用户输入中的风味偏好：
用户输入："{user_input}"

请返回JSON格式的分析结果，包含：
1. flavors: 风味列表，每个风味包含：
   - text: 风味词（如"酸"、"甜"、"苦"等）
   - flavor_type: 风味类型（从以下选择：sour, sweet, bitter, aroma, fruity, body）
   - confidence: 置信度（0-1之间的浮点数）

只返回JSON，不要其他内容。
"""
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                response_text = response.choices[0].message.content
                
                # 提取JSON
                json_match = re.search(r'\{[^}]+\}', response_text)
                if json_match:
                    result = json.loads(json_match.group())
                    for flavor in result.get("flavors", []):
                        flavor["source"] = "llm"
                    self.analysis_cache[cache_key] = result.get("flavors", [])
                    return result.get("flavors", [])
                
            except Exception as e:
                print(f"LLM分析风味失败: {e}")
        
        # LLM也失败，返回空列表
        return []
    
    def analyze_ingredients(self, user_input: str) -> List[str]:
        """
        分析用户提到的材料
        
        Args:
            user_input: 用户输入
            
        Returns:
            List[str]: 材料列表
        """
        # 检查缓存
        cache_key = f"ingredients_{user_input}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # 检查是否有材料相关的关键词
        material_keywords = ["材料", "只有", "有", "包含", "加上", "添加"]
        has_material = any(keyword in user_input for keyword in material_keywords)
        
        if not has_material:
            return []
        
        # 使用LLM提取材料
        if self.client:
            try:
                prompt = f"""
请从以下用户输入中提取酒类制作材料：
用户输入："{user_input}"

请返回JSON格式的分析结果，包含：
1. ingredients: 材料列表（如"柠檬"、"伏特加"、"糖浆"等）

只返回JSON，不要其他内容。
"""
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                response_text = response.choices[0].message.content
                
                # 提取JSON
                json_match = re.search(r'\{[^}]+\}', response_text)
                if json_match:
                    result = json.loads(json_match.group())
                    ingredients = result.get("ingredients", [])
                    self.analysis_cache[cache_key] = ingredients
                    return ingredients
                
            except Exception as e:
                print(f"LLM分析材料失败: {e}")
        
        # LLM也失败，返回空列表
        return []
    
    def analyze_constraints(self, user_input: str) -> List[Dict[str, Any]]:
        """
        分析用户的约束条件
        
        Args:
            user_input: 用户输入
            
        Returns:
            List[Dict]: 约束条件列表
        """
        # 检查缓存
        cache_key = f"constraints_{user_input}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # 使用LLM分析约束条件
        if self.client:
            try:
                prompt = f"""
请分析以下用户输入中的约束条件：
用户输入："{user_input}"

请返回JSON格式的分析结果，包含：
1. constraints: 约束条件列表，每个约束包含：
   - constraint_type: 约束类型（从以下选择：alcohol, occasion, time, other）
   - text: 约束文本
   - confidence: 置信度（0-1之间的浮点数）

约束类型说明：
- alcohol: 酒精含量相关（如"无酒精"、"低度"、"高度"）
- occasion: 场合相关（如"聚会"、"约会"、"商务"）
- time: 时间/季节相关（如"夏天"、"晚上"、"冬天"）
- other: 其他约束

只返回JSON，不要其他内容。
"""
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                response_text = response.choices[0].message.content
                
                # 提取JSON
                json_match = re.search(r'\{[^}]+\}', response_text)
                if json_match:
                    result = json.loads(json_match.group())
                    constraints = result.get("constraints", [])
                    for constraint in constraints:
                        constraint["source"] = "llm"
                    self.analysis_cache[cache_key] = constraints
                    return constraints
                
            except Exception as e:
                print(f"LLM分析约束条件失败: {e}")
        
        # LLM也失败，返回空列表
        return []
    
    def analyze_comprehensive(self, user_input: str, entities: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        综合分析用户需求
        
        Args:
            user_input: 用户输入
            entities: 已识别的实体
            
        Returns:
            Dict: 综合分析结果
        """
        # 检查缓存
        cache_key = f"comprehensive_{user_input}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        # 使用LLM进行综合分析
        if self.client:
            try:
                prompt = f"""
请综合分析以下用户的需求：
用户输入："{user_input}"
已识别实体：{json.dumps(entities, ensure_ascii=False) if entities else "无"}

请返回JSON格式的分析结果，包含：
1. has_ingredients: 是否提到材料（true/false）
2. ingredients: 材料列表（如果有）
3. has_mood: 是否提到心情（true/false）
4. mood: 心情（如果有）
5. has_flavors: 是否提到风味偏好（true/false）
6. flavors: 风味列表（如果有），每个包含text和flavor_type
7. has_constraints: 是否有其他约束条件（true/false）
8. constraints: 约束条件列表（如果有）
9. reasoning: 分析理由

只返回JSON，不要其他内容。
"""
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3
                )
                
                response_text = response.choices[0].message.content
                
                # 提取JSON
                json_match = re.search(r'\{[^}]+\}', response_text)
                if json_match:
                    result = json.loads(json_match.group())
                    result["source"] = "llm"
                    self.analysis_cache[cache_key] = result
                    return result
                
            except Exception as e:
                print(f"LLM综合分析失败: {e}")
        
        # LLM也失败，返回默认值
        return {
            "has_ingredients": False,
            "ingredients": [],
            "has_mood": False,
            "mood": "",
            "has_flavors": False,
            "flavors": [],
            "has_constraints": False,
            "constraints": [],
            "source": "fallback"
        }


# 创建全局LLM辅助服务实例
llm_assist_service = LLMAssistService()
