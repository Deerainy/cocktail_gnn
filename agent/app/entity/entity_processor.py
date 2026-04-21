#!/usr/bin/env python3
"""
分层实体处理模块

实现三层实体处理逻辑：
1. 第一层：词典/规则优先
2. 第二层：模糊匹配/检索兜底
3. 第三层：LLM做候选分析
"""

from typing import List, Dict, Any, Optional, Tuple
from .extractor import EntityExtractor
from .linker import entity_linker
from .utils import normalize_text, map_bilingual

class EntityProcessor:
    def __init__(self):
        """初始化实体处理器"""
        self.extractor = EntityExtractor()
        # 置信度阈值
        self.confidence_threshold = 0.8
    
    def process(self, text: str, trace=None) -> Dict[str, Any]:
        """处理文本中的实体
        
        Args:
            text: 待处理的文本
            trace: trace对象
            
        Returns:
            Dict: 处理结果，包含识别的实体和处理层级
        """
        # 第一步：抽取实体
        extracted_entities = self.extractor.extract(text)
        
        # 第二步：链接实体
        linked_entities = entity_linker.link_entities(extracted_entities)
        
        # 第三步：分层处理
        processed_entities = []
        processing_level = "lexicon_rule"
        strategy = "rule"
        
        for entity in linked_entities:
            # 第一层：词典/规则优先
            if self._is_high_confidence(entity):
                entity["processing_level"] = "lexicon_rule"
                entity["confidence"] = 1.0
                processed_entities.append(entity)
            else:
                # 第二层：模糊匹配/检索兜底
                fuzzy_result = self._fuzzy_match(entity)
                if fuzzy_result:
                    fuzzy_result["processing_level"] = "fuzzy_match"
                    fuzzy_result["confidence"] = 0.9
                    processed_entities.append(fuzzy_result)
                    processing_level = "fuzzy_match"
                    strategy = "rule + fuzzy"
                else:
                    # 第三层：LLM做候选分析
                    llm_result = self._llm_analysis(entity, context=text)
                    if llm_result:
                        llm_result["processing_level"] = "llm_analysis"
                        llm_result["confidence"] = 0.7
                        processed_entities.append(llm_result)
                        processing_level = "llm_analysis"
                        strategy = "rule + fuzzy + llm"
                    else:
                        # 无法识别的实体
                        entity["processing_level"] = "unrecognized"
                        entity["confidence"] = 0.0
                        processed_entities.append(entity)
        
        # 转换实体格式以适应trace schema
        trace_entities = []
        for entity in processed_entities:
            trace_entity = {
                "text": entity.get("text"),
                "type": entity.get("label"),
                "confidence": entity.get("confidence", 0.0)
            }
            # 添加规范名称和来源（如果有）
            if "canonical_name" in entity:
                trace_entity["canonical_name"] = entity.get("canonical_name")
            if "source" in entity:
                trace_entity["source"] = entity.get("source")
            trace_entities.append(trace_entity)
        
        # 添加trace步骤
        if trace:
            trace.add_step(
                name="entity_recognition",
                title="实体识别",
                status="success",
                data={
                    "entities": trace_entities,
                    "processing_level": processing_level,
                    "strategy": strategy
                }
            )
        
        return {
            "text": text,
            "entities": processed_entities,
            "processing_level": processing_level,
            "strategy": strategy
        }
    
    def _is_high_confidence(self, entity: Dict[str, Any]) -> bool:
        """判断实体是否为高置信度
        
        Args:
            entity: 链接后的实体
            
        Returns:
            bool: 是否为高置信度
        """
        # 检查是否有实体ID或规范ID
        if "entity_id" in entity or "canonical_id" in entity:
            return True
        # 检查是否为风味实体且已映射
        if entity.get("label") == "FLAVOR" and "normalized_flavor" in entity:
            return True
        # 检查是否为通用名词
        if entity.get("label") == "NOUN":
            return True
        return False
    
    def _fuzzy_match(self, entity: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """模糊匹配实体
        
        Args:
            entity: 待匹配的实体
            
        Returns:
            Optional[Dict]: 匹配结果
        """
        text = entity.get("text", "").strip()
        label = entity.get("label", "").lower()
        
        # 文本规范化
        normalized_text = normalize_text(text)
        
        # 双语映射
        mapped_text = map_bilingual(normalized_text)
        if mapped_text != normalized_text:
            # 尝试用映射后的文本重新链接
            mapped_entity = {**entity, "text": mapped_text}
            linked = entity_linker.link(mapped_entity)
            if self._is_high_confidence(linked):
                linked["original_text"] = text
                return linked
        
        # 这里可以添加更多模糊匹配逻辑
        # 例如：RapidFuzz 模糊匹配、embedding 检索等
        
        return None
    
    def _llm_analysis(self, entity: Dict[str, Any], context: str = "") -> Optional[Dict[str, Any]]:
        """使用LLM分析实体
        
        Args:
            entity: 待分析的实体
            context: 用户输入的上下文
            
        Returns:
            Optional[Dict]: 分析结果
        """
        try:
            import json
            import sys
            import os
            
            # 添加父目录到路径
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            
            from services.bartender_llm import bartender_llm
            
            entity_text = entity.get("text", "")
            
            # 构建LLM分析提示词
            prompt = f"""分析以下文本中的实体：

用户输入：{context}
待分析片段：{entity_text}

请判断：
1. 这可能是什么类型的实体？
   - INGREDIENT: 食材或原料（如：柠檬、伏特加、金酒）
   - RECIPE: 鸡尾酒配方名称（如：Margarita、Martini）
   - FLAVOR: 风味或口感描述（如：清爽、酸甜、醇厚、苦、甜）
   - MOOD: 心情或情绪状态（如：开心、难过、放松、心情好、心情不好）
   - OTHER: 其他无关词汇（如：有、的、了、吗）

2. 如果是食材，可能的规范英文名称是什么？
3. 置信度是多少？（0-1）
4. 判断理由是什么？

请严格按照以下JSON格式返回（不要包含其他内容）：
{{
    "type": "INGREDIENT/RECIPE/FLAVOR/MOOD/OTHER",
    "canonical_name": "规范名称或null",
    "confidence": 0.8,
    "reasoning": "判断理由"
}}"""

            # 调用LLM
            response = bartender_llm.generate_response(prompt)
            
            # 解析LLM响应
            try:
                # 尝试提取JSON
                import re
                json_match = re.search(r'\{[^{}]*\}', response)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # 如果没有找到JSON，尝试直接解析
                    result = json.loads(response)
                
                # 验证结果
                if not isinstance(result, dict):
                    print(f"LLM分析结果格式错误: {result}")
                    return None
                
                # 构建返回结果
                llm_result = {
                    **entity,
                    "label": result.get("type", "UNKNOWN"),
                    "canonical_name": result.get("canonical_name"),
                    "confidence": result.get("confidence", 0.5),
                    "processing_level": "llm_analysis",
                    "reasoning": result.get("reasoning", ""),
                    "source": "llm"
                }
                
                print(f"LLM分析实体 '{entity_text}' 成功: {result.get('type')} (置信度: {result.get('confidence')})")
                return llm_result
                
            except json.JSONDecodeError as e:
                print(f"解析LLM响应失败: {e}, 响应内容: {response}")
                return None
            
        except Exception as e:
            print(f"LLM分析实体失败: {e}")
            return None
    
    def batch_process(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量处理文本
        
        Args:
            texts: 待处理的文本列表
            
        Returns:
            List[Dict]: 处理结果列表
        """
        results = []
        for text in texts:
            result = self.process(text)
            results.append(result)
        return results

# 创建全局实体处理器实例
entity_processor = EntityProcessor()
