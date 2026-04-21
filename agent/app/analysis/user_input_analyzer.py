#!/usr/bin/env python3
"""
用户输入分析器

综合实体识别和意图分析，对用户输入进行完整分析
"""

from typing import Dict, Any, List
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入配置
from config import settings

# 尝试导入实体处理器，如果失败则提供回退实现
try:
    from entity.entity_processor import entity_processor
    ENTITY_PROCESSOR_AVAILABLE = True
except ImportError:
    print("警告: 实体处理器不可用，使用回退实现")
    ENTITY_PROCESSOR_AVAILABLE = False

# 导入意图路由器
from intent.intent_router import intent_router

# 导入后端服务
from services.backend_service import backend_service

# 导入审核任务管理器
from entity.review_manager import review_manager

# 导入调酒师 LLM 服务
from services.bartender_llm import bartender_llm

# 导入推荐服务
from services.recommendation_service import recommendation_service

# 导入解析结果结构
from .parsed_query import ParsedQuery

# 导入会话上下文管理
from .session_context import session_context_manager, SessionContext

# 导入当前轮解析器（已移动到 parser 模块）
from parser.current_turn_parser import current_turn_parser, CurrentTurnParser

# 导入trace收集器
from tracing.trace_collector import create_trace

# 导入trace数据库模块
try:
    from app.backend.db.trace_db import save_trace_to_db, create_trace_tables
    TRACE_DB_AVAILABLE = True
    # 确保表结构存在
    create_trace_tables()
except ImportError:
    print("警告: trace数据库模块不可用，使用回退实现")
    TRACE_DB_AVAILABLE = False

class UserInputAnalyzer:
    def __init__(self):
        """初始化用户输入分析器"""
        pass
    
    def analyze(self, text: str, session_id=None, trace=None) -> Dict[str, Any]:
        """分析用户输入
        
        Args:
            text: 用户输入的文本
            session_id: 会话ID
            trace: 已存在的 trace 对象（可选）
            
        Returns:
            Dict: 分析结果，包含实体识别、意图分析的结果和结构化推理轨迹
        """
        # 使用传入的 trace 或创建新的 trace
        if trace is None:
            trace = create_trace(text, session_id)
        
        # 获取或创建会话上下文（第2层：结构化会话状态）
        session_ctx = None
        if session_id:
            session_ctx = session_context_manager.get_or_create(session_id)
            print(f"获取会话上下文: {session_ctx.session_id}")
        
        # 当前轮解析（第3层：显式解析 + 上下文补全）
        turn_result = current_turn_parser.parse(text, session_ctx)
        print(f"当前轮解析结果: {turn_result}")
        
        # 1. 输入理解
        trace.add_step(
            name="input_analysis",
            title="输入理解",
            status="success",
            data={
                "language": "zh" if any("\u4e00" <= char <= "\u9fff" for char in text) else "en",
                "normalized_text": text,
                "has_context": session_ctx is not None,
                "turn_result": turn_result
            }
        )
        
        # 2. 先检查是否包含需要检索增强的关键词（从配置文件加载）
        retrieval_keywords = settings.get_retrieval_keywords()
        needs_retrieval = False
        print(f"用户输入: {text}")
        
        # 检查是否包含检索增强关键词
        for keyword in retrieval_keywords:
            if keyword in text:
                needs_retrieval = True
                print(f"命中关键词: {keyword}")
                break
        
        # 处理编码问题：如果输入包含英文食材名称和乱码（可能是中文关键词的编码问题），也应该需要检索增强
        english_ingredients = settings.get_english_ingredients()
        if any(ingredient in text.lower() for ingredient in english_ingredients) and "????" in text:
            needs_retrieval = True
            print("命中英文食材+乱码组合")
        
        # 强制处理：如果包含英文食材名称和中文关键词的组合，也应该需要检索增强
        if any(ingredient in text.lower() for ingredient in english_ingredients) and any(keyword in text for keyword in ["替换", "替代", "换成"]):
            needs_retrieval = True
            print("命中英文食材+中文关键词组合")
        
        # 如果当前轮解析出意图，也需要检索增强
        if turn_result.get("intent"):
            needs_retrieval = True
            print(f"当前轮解析出意图: {turn_result.get('intent')}")
        
        # 如果不需要检索增强，再判断是否为日常交流
        is_daily_chat = False
        if not needs_retrieval:
            try:
                # 如果有会话上下文，使用会话上下文
                if session_ctx:
                    # 构建上下文提示
                    context_prompt = "【对话上下文】\n"
                    if session_ctx.current_recipe_name:
                        context_prompt += f"当前配方: {session_ctx.current_recipe_name}\n"
                    if session_ctx.current_canonical_name:
                        context_prompt += f"当前食材: {session_ctx.current_canonical_name}\n"
                    context_prompt += f"\n【当前问题】\n用户: {text}\n\n请判断这是否为日常交流，不需要执行复杂的处理流程，直接回答即可。请回答 '是' 或 '否'。"
                    llm_response = bartender_llm.generate_response(context_prompt)
                else:
                    prompt = f"判断以下用户输入是否为日常交流，不需要执行复杂的处理流程，直接回答即可：\n\n用户输入：{text}\n\n请回答 '是' 或 '否'。"
                    llm_response = bartender_llm.generate_response(prompt)
                
                print(f"日常交流判断结果: {llm_response}")
                if "是" in llm_response and "否" not in llm_response:
                    is_daily_chat = True
            except Exception as e:
                print(f"判断是否为日常交流失败: {e}")
        print(f"is_daily_chat: {is_daily_chat}")
        print(f"needs_retrieval: {needs_retrieval}")
        
        # 如果是日常交流，直接使用 LLM 生成回答
        if is_daily_chat:
            summary = self._generate_llm_response(text, session_ctx, is_daily_chat=True)
            return self._build_simple_analysis_result(text, summary, trace, is_daily_chat=True)
        
        # 如果不需要检索增强，直接使用 LLM 生成回答
        if not needs_retrieval:
            summary = self._generate_llm_response(text, session_ctx)
            return self._build_simple_analysis_result(text, summary, trace, needs_retrieval=False)
        
        # 3. 实体识别和处理
        import concurrent.futures
        
        # 并行执行实体识别和意图分析
        entity_result = None
        intent_result = None
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # 提交实体识别任务
            entity_future = executor.submit(self._process_entity, text, trace)
            # 提交意图分析任务
            intent_future = executor.submit(self._process_intent, text, trace)
            
            # 获取结果
            entity_result = entity_future.result()
            intent_result = intent_future.result()
        
        entities = entity_result.get("entities", [])
        processing_level = entity_result.get("processing_level", "unprocessed")
        
        # 4. 综合分析结果
        needs_review = self._check_needs_review(entities)
        
        # 优先使用意图路由器的结果，因为它更准确
        intent = intent_result.get("intent", "general_chat")
        intent_confidence = intent_result.get("confidence", 0.0)
        
        # 只有当意图路由器识别为 general_chat 时，才考虑解析器的结果
        if intent == "general_chat":
            if isinstance(turn_result.get("intent"), dict):
                parsed_intent = turn_result["intent"]["value"]
                if parsed_intent != "general_chat":
                    intent = parsed_intent
                    intent_confidence = turn_result["intent"]["confidence"]
            else:
                # 对于 memory_query 意图，优先使用解析器结果
                parsed_intent = turn_result.get("intent")
                if parsed_intent == "memory_query":
                    intent = parsed_intent
                    intent_confidence = 0.7  # 给一个合理的置信度
        
        # 构建综合分析结果，优先使用解析器的结果
        analysis_result = {
            "text": text,
            "entities": entities,
            "processing_level": entity_result.get("processing_level", "unprocessed"),
            "intent": intent,
            "intent_confidence": intent_confidence,
            "intent_method": intent_result.get("method", "unknown"),
            "needs_review": needs_review,
            "turn_result": turn_result,  # 添加解析器结果
            "parse_result": turn_result  # 新的解析结果格式
        }
        
        # 5. 根据意图和实体生成响应建议，传入解析器结果和会话上下文
        suggestion = self._generate_response_suggestion(analysis_result, turn_result, session_ctx)
        analysis_result["response_suggestion"] = suggestion
        
        trace.add_step(
            name="action_planning",
            title="动作规划",
            status="success",
            data={
                "action": suggestion.get("action"),
                "params": {
                    "target": suggestion.get("target"),
                    "message": suggestion.get("message")
                }
            }
        )
        
        # 6. 调用后端服务
        backend_response = self._call_backend_service(analysis_result, trace)
        analysis_result["backend_response"] = backend_response
        
        # 7. 答案生成（使用增强的提示词）
        summary = ""
        if backend_response.get("success"):
            action = suggestion.get("action")
            
            # 构建上下文信息
            context_info = ""
            if session_ctx:
                if session_ctx.current_recipe_name:
                    context_info += f"当前讨论的配方: {session_ctx.current_recipe_name}\n"
                if session_ctx.current_canonical_name:
                    context_info += f"当前讨论的食材: {session_ctx.current_canonical_name}\n"
            
            if action == "search_recipe":
                recipe = backend_response.get('data', {})
                
                # 构建详细的食谱信息
                recipe_basic_info = f"食谱名称: {recipe.get('name', '')}"
                recipe_description = recipe.get('description', '暂无描述')
                recipe_instructions = recipe.get('instructions', '暂无制作步骤')
                recipe_structure = ""
                
                # 如果有结构信息，添加到结构部分
                if 'ingredients' in recipe:
                    ingredients = recipe['ingredients']
                    recipe_structure = f"包含 {len(ingredients)} 个食材："
                    for i, ing in enumerate(ingredients, 1):
                        recipe_structure += f"\n{i}. {ing.get('ingredient', '')} ({ing.get('amount', '')} {ing.get('unit', '')})"
                
                # 使用增强的提示词
                try:
                    prompt_template = settings.get_enhanced_prompt("recipe_search_enhanced")
                    if prompt_template:
                        prompt = prompt_template.format(
                            recipe_name=recipe.get('name', ''),
                            recipe_basic_info=recipe_basic_info,
                            recipe_description=recipe_description,
                            recipe_instructions=recipe_instructions,
                            recipe_structure=recipe_structure
                        )
                    else:
                        # 回退到简单提示词
                        prompt = f"用户询问关于食谱 '{recipe.get('name', '')}' 的信息，以下是检索到的信息：\n{recipe_basic_info}\n{recipe_description}\n{recipe_instructions}\n{recipe_structure}\n请基于这些信息，以调酒师的身份生成一个友好、专业的回答。"
                    
                    summary = bartender_llm.generate_response(prompt)
                    
                    # 检查是否是回退响应
                    fallback_responses = [
                        "你好！欢迎来到我的酒吧，有什么可以帮你的吗？",
                        "很高兴为你服务！请问你想了解关于鸡尾酒的什么信息，或者需要我为你推荐一款适合的饮品吗？"
                    ]
                    
                    if any(fallback in summary for fallback in fallback_responses):
                        # 使用基于食谱信息的回退回答
                        summary = f"为你找到食谱: {recipe.get('name', '')}"
                        if recipe.get('description'):
                            summary += f"\n\n描述: {recipe.get('description')}"
                        if recipe.get('instructions'):
                            summary += f"\n\n制作步骤: {recipe.get('instructions')}"
                except Exception as e:
                    print(f"生成调酒师响应失败: {e}")
                    # 使用回退响应
                    summary = f"为你找到食谱: {recipe.get('name', '')}"
                    if recipe.get('description'):
                        summary += f"\n\n描述: {recipe.get('description')}"
                    if recipe.get('instructions'):
                        summary += f"\n\n制作步骤: {recipe.get('instructions')}"
            elif action == "get_recipe_structure":
                ingredients = backend_response.get('data', {}).get('ingredients', [])
                ingredient_count = len(ingredients)
                
                # 构建详细的食材信息
                ingredients_list = f"食谱包含 {ingredient_count} 个食材"
                ingredients_details = ""
                for i, ingredient in enumerate(ingredients, 1):
                    ingredient_name = ingredient.get('ingredient', '')
                    amount = ingredient.get('amount', '')
                    unit = ingredient.get('unit', '')
                    role = ingredient.get('role', '')
                    
                    detail = f"{i}. {ingredient_name}"
                    if amount and unit:
                        detail += f" - 用量: {amount} {unit}"
                    if role:
                        detail += f" - 作用: {role}"
                    ingredients_details += detail + "\n"
                
                # 使用增强的提示词
                try:
                    prompt_template = settings.get_enhanced_prompt("recipe_structure_enhanced")
                    if prompt_template:
                        prompt = prompt_template.format(
                            recipe_name=suggestion.get("target", "未知食谱"),
                            ingredients_list=ingredients_list,
                            ingredients_details=ingredients_details
                        )
                    else:
                        # 回退到简单提示词
                        prompt = f"用户询问食谱的结构，以下是检索到的食材信息：\n{ingredients_list}\n{ingredients_details}\n请基于这些信息，以调酒师的身份生成一个友好、专业的回答。"
                    
                    summary = bartender_llm.generate_response(prompt)
                except Exception as e:
                    print(f"生成调酒师响应失败: {e}")
                    # 使用回退响应
                    summary = f"为你找到食谱结构，包含 {ingredient_count} 个食材"
                    if ingredients:
                        summary += '\n\n具体食材：'
                        for i, ingredient in enumerate(ingredients, 1):
                            ingredient_name = ingredient.get('ingredient', '')
                            amount = ingredient.get('amount', '')
                            unit = ingredient.get('unit', '')
                            if amount and unit:
                                summary += f'\n{i}. {ingredient_name} ({amount} {unit})'
                            else:
                                summary += f'\n{i}. {ingredient_name}'
            elif action == "get_ingredient_neighbors":
                neighbors = backend_response.get('data', {}).get('neighbors', [])
                neighbor_count = len(neighbors)
                
                # 构建详细的邻域信息
                neighbors_list = f"找到 {neighbor_count} 个邻近食材"
                relationships = ""
                for i, neighbor in enumerate(neighbors, 1):
                    neighbor_name = neighbor.get('neighbor_name', '')
                    relationship_type = neighbor.get('relationship_type', '')
                    relationships += f"{i}. {neighbor_name}"
                    if relationship_type:
                        relationships += f" - 关系: {relationship_type}"
                    relationships += "\n"
                
                # 使用增强的提示词
                try:
                    prompt_template = settings.get_enhanced_prompt("ingredient_neighbors_enhanced")
                    if prompt_template:
                        prompt = prompt_template.format(
                            ingredient_name=suggestion.get("target", "未知食材"),
                            neighbors_list=neighbors_list,
                            relationships=relationships
                        )
                    else:
                        # 回退到简单提示词
                        prompt = f"用户询问食材的邻域信息，以下是检索到的邻近食材：\n{neighbors_list}\n{relationships}\n请基于这些信息，以调酒师的身份生成一个友好、专业的回答。"
                    
                    summary = bartender_llm.generate_response(prompt)
                except Exception as e:
                    print(f"生成调酒师响应失败: {e}")
                    # 使用回退响应
                    summary = f"为你找到 {neighbor_count} 个邻近食材"
                    if neighbors:
                        summary += '\n\n具体邻近食材：'
                        for i, neighbor in enumerate(neighbors, 1):
                            neighbor_name = neighbor.get('neighbor_name', '')
                            relationship_type = neighbor.get('relationship_type', '')
                            if relationship_type:
                                summary += f'\n{i}. {neighbor_name} ({relationship_type})'
                            else:
                                summary += f'\n{i}. {neighbor_name}'
            elif action == "get_substitute":
                substitutes = backend_response.get('data', {}).get('substitutes', [])
                substitute_count = len(substitutes)
                
                # 构建详细的替代信息
                substitutes_list = f"找到 {substitute_count} 个可替代原料"
                similarity_info = ""
                for i, substitute in enumerate(substitutes, 1):
                    substitute_name = substitute.get('substitute_name', '')
                    similarity_score = substitute.get('similarity_score', '')
                    similarity_info += f"{i}. {substitute_name}"
                    if similarity_score:
                        similarity_info += f" - 相似度: {similarity_score}"
                    similarity_info += "\n"
                
                # 使用增强的提示词
                try:
                    prompt_template = settings.get_enhanced_prompt("substitute_enhanced")
                    if prompt_template:
                        prompt = prompt_template.format(
                            original_ingredient=suggestion.get("target", "未知食材"),
                            substitutes_list=substitutes_list,
                            similarity_info=similarity_info
                        )
                    else:
                        # 回退到简单提示词
                        prompt = f"用户询问食材的替代建议，以下是检索到的替代原料：\n{substitutes_list}\n{similarity_info}\n请基于这些信息，以调酒师的身份生成一个友好、专业的回答。"
                    
                    summary = bartender_llm.generate_response(prompt)
                except Exception as e:
                    print(f"生成调酒师响应失败: {e}")
                    # 使用回退响应
                    summary = f"为你找到 {substitute_count} 个可替代原料"
                    if substitutes:
                        summary += '\n\n具体替代原料：'
                        for i, substitute in enumerate(substitutes, 1):
                            substitute_name = substitute.get('substitute_name', '')
                            similarity_score = substitute.get('similarity_score', '')
                            if similarity_score:
                                summary += f'\n{i}. {substitute_name} (相似度: {similarity_score})'
                            else:
                                summary += f'\n{i}. {substitute_name}'
            elif action == "get_recommendation":
                # 处理推荐结果
                recommendations = backend_response.get('data', {}).get('recommendations', [])
                user_needs = text
                
                # 构建推荐结果列表
                recommendations_list = ""
                for i, rec in enumerate(recommendations, 1):
                    name = rec.get('recipe_name_zh', rec.get('name', '未知饮品'))
                    alcohol_content = rec.get('alcohol_content', '未知酒精度')
                    description = rec.get('description', '暂无描述')
                    recommendations_list += f"{i}. {name} - 酒精度: {alcohol_content}\n   描述: {description}\n"
                
                # 构建推荐理由
                recommendation_reasons = "我感觉这几款你会喜欢的："
                
                # 检查推荐结果是否为空
                if not recommendations:
                    summary = "抱歉，没找到合适的饮品呢……（扣扣脑袋）"
                else:
                    # 检查LLM客户端是否可用
                    if not bartender_llm.client:
                        # 直接生成基于数据库的推荐响应
                        summary = "看看这几款怎么样，我觉得会很适合你哦：\n"
                        for i, rec in enumerate(recommendations, 1):
                            name = rec.get('recipe_name_zh', rec.get('name', '未知饮品'))
                            summary += f"{i}. {name}\n"
                    else:
                        # 使用增强的推荐提示词，让LLM润色推荐结果
                        try:
                            # 构建消息列表
                            messages = [
                                {"role": "system", "content": bartender_llm.role_info}
                            ]
                            
                            # 构建用户消息
                            user_message = f"用户说：{user_needs}\n\n基于数据库推荐结果，为用户生成一个友好、专业的推荐回答：\n"
                            for i, rec in enumerate(recommendations, 1):
                                name = rec.get('recipe_name_zh', rec.get('name', '未知饮品'))
                                description = rec.get('description', '暂无描述')
                                instructions = rec.get('instructions', '暂无制作步骤')
                                user_message += f"{i}. {name}\n   描述: {description}\n   制作步骤: {instructions}\n\n"
                            
                            messages.append({"role": "user", "content": user_message})
                            
                            # 直接调用LLM API
                            import time
                            start_time = time.time()
                            response = bartender_llm.client.chat.completions.create(
                                model=bartender_llm.model_name,
                                temperature=0.7,
                                max_tokens=1000,
                                messages=messages,
                                timeout=15
                            )
                            end_time = time.time()
                            print(f"LLM 响应时间: {end_time - start_time:.2f} 秒")
                            
                            # 提取响应内容
                            summary = response.choices[0].message.content.strip()
                        except Exception as e:
                            print(f"生成推荐响应失败: {e}")
                            # 回退响应
                            summary = "（翻酒单中）（寻找）（猛地发现）这几款我觉得会适合你：\n"
                            for i, rec in enumerate(recommendations, 1):
                                name = rec.get('recipe_name_zh', rec.get('name', '未知饮品'))
                                summary += f"{i}. {name}\n"
            elif action == "general_response":
                # 使用增强的日常交流提示词
                try:
                    prompt_template = settings.get_enhanced_prompt("daily_chat_enhanced")
                    if prompt_template:
                        prompt = prompt_template.format(
                            user_input=text,
                            context_info=context_info
                        )
                    else:
                        # 回退到简单提示词
                        if session_ctx:
                            prompt = f"【对话上下文】\n{context_info}\n\n【当前问题】\n用户: {text}\n\n请以调酒师的身份回答这个问题。"
                        else:
                            prompt = text
                    
                    summary = bartender_llm.generate_response(prompt)
                except Exception as e:
                    print(f"生成调酒师响应失败: {e}")
                    # 使用回退响应
                    summary = "你好！欢迎来到酒吧玩呀，有什么能帮到你吗？（搓手）"
        else:
            # 使用调酒师 LLM 生成错误响应
            error_message = backend_response.get('message', '未知错误')
            try:
                prompt = f"用户的请求处理失败，错误信息是：{error_message}\n请以调酒师的身份生成一个友好、专业的错误响应，表达歉意并提供一些建议。"
                summary = bartender_llm.generate_response(prompt)
            except Exception as e:
                print(f"生成调酒师响应失败: {e}")
                # 使用回退响应
                summary = f"处理失败: {error_message}\n\n嗷嗷很抱歉，我还没学会该怎么做这个〒▽〒。你可以尝试重新输入，或者询问其他问题。"
        
        trace.add_step(
            name="answer_generation",
            title="答案生成",
            status="success",
            data={
                "summary": summary
            }
        )
        
        # 将summary添加到analysis_result的顶层字段
        analysis_result["summary"] = summary
        
        # 8. 更新会话上下文
        if session_ctx:
            # 构建实体字典
            entities_dict = {}
            for entity in entities:
                label = entity.get("label", "").lower()
                if "recipe" in label:
                    entities_dict["recipe"] = entity.get("text")
                elif "ingredient" in label or "canonical" in label:
                    entities_dict["ingredient"] = entity.get("canonical_name") or entity.get("text")
            
            # 如果是推荐动作，并且有推荐结果，更新实体字典为第一个推荐的饮品
            if suggestion.get("action") == "get_recommendation" and backend_response.get("success"):
                recommendations = backend_response.get('data', {}).get('recommendations', [])
                if recommendations:
                    first_recipe = recommendations[0]
                    recipe_id = first_recipe.get('recipe_id')
                    recipe_name = first_recipe.get('recipe_name_zh', first_recipe.get('name'))
                    if recipe_id and recipe_name:
                        entities_dict["recipe"] = recipe_name
            
            # 如果当前轮解析有结果，合并到实体字典
            if "slots" in turn_result:
                # 新接口：从 slots 中提取
                slots = turn_result.get("slots", {})
                if slots.get("recipe", {}).get("value"):
                    entities_dict["recipe"] = slots["recipe"]["value"]
                if slots.get("ingredient", {}).get("value"):
                    entities_dict["ingredient"] = slots["ingredient"]["value"]
                if slots.get("candidate_substitute", {}).get("value"):
                    entities_dict["candidate_substitute"] = slots["candidate_substitute"]["value"]
            else:
                # 旧接口：直接获取
                if turn_result.get("recipe"):
                    entities_dict["recipe"] = turn_result["recipe"]
                if turn_result.get("ingredient"):
                    entities_dict["ingredient"] = turn_result["ingredient"]
                if turn_result.get("candidate_substitute"):
                    entities_dict["candidate_substitute"] = turn_result["candidate_substitute"]
            
            # 更新会话上下文
            if isinstance(turn_result.get("intent"), dict):
                update_intent = turn_result.get("intent", {}).get("value", intent_result.get("intent", "general_chat"))
            else:
                update_intent = turn_result.get("intent", intent_result.get("intent", "general_chat"))
            
            session_ctx.update_after_execution(
                intent=update_intent,
                action=suggestion.get("action", "general_response"),
                entities=entities_dict
            )
        
        # 9. 如果需要审核，创建审核任务
        if needs_review:
            review_result = review_manager.create_review_task(text, entities)
            analysis_result["review_task"] = review_result
        
        # 10. 生成统一的解析结果结构
        parsed_query = ParsedQuery.from_analysis_result(analysis_result)
        analysis_result["parsed_query"] = parsed_query.to_dict()
        
        # 11. 添加思考流程轨迹
        trace_dict = trace.to_dict()
        analysis_result["trace"] = trace_dict
        
        # 保存trace到数据库
        if TRACE_DB_AVAILABLE:
            save_trace_to_db(trace)
        
        return analysis_result
    
    def _generate_llm_response(self, text: str, session_ctx=None, is_daily_chat=False):
        """生成LLM响应
        
        Args:
            text: 用户输入
            session_ctx: 会话上下文
            is_daily_chat: 是否为日常交流
            
        Returns:
            str: LLM响应
        """
        try:
            # 如果有会话上下文，使用会话上下文
            if session_ctx:
                # 构建上下文提示
                context_prompt = "【对话上下文】\n"
                if session_ctx.current_recipe_name:
                    context_prompt += f"当前配方: {session_ctx.current_recipe_name}\n"
                if session_ctx.current_canonical_name:
                    context_prompt += f"当前食材: {session_ctx.current_canonical_name}\n"
                context_prompt += f"\n【当前问题】\n用户: {text}\n\n请以调酒师的身份回答这个问题。"
                return bartender_llm.generate_response(context_prompt)
            else:
                return bartender_llm.generate_response(text)
        except Exception as e:
            print(f"生成调酒师响应失败: {e}")
            # 使用回退响应
            return "你好！欢迎来到我的酒吧，有什么可以帮你的吗？"
    
    def _build_simple_analysis_result(self, text: str, summary: str, trace, is_daily_chat=False, needs_retrieval=False):
        """构建简单的分析结果
        
        Args:
            text: 用户输入
            summary: LLM响应
            trace: 跟踪对象
            is_daily_chat: 是否为日常交流
            needs_retrieval: 是否需要检索增强
            
        Returns:
            dict: 分析结果
        """
        # 添加答案生成步骤
        trace.add_step(
            name="answer_generation",
            title="答案生成",
            status="success",
            data={
                "summary": summary,
                "is_daily_chat": is_daily_chat,
                "needs_retrieval": needs_retrieval
            }
        )
        
        # 更新可视化步骤，将未执行的步骤标记为跳过
        trace.visualization_steps["entity_recognition"]["status"] = "skipped"
        trace.visualization_steps["intent_classification"]["status"] = "skipped"
        trace.visualization_steps["action_execution"]["status"] = "skipped"
        trace.visualization_steps["retrieval_and_generation"]["status"] = "success"
        trace.visualization_steps["retrieval_and_generation"]["data"]["final_answer"] = summary
        
        # 构建分析结果
        analysis_result = {
            "text": text,
            "is_daily_chat": is_daily_chat,
            "needs_retrieval": needs_retrieval,
            "backend_response": {
                "success": True,
                "data": {
                    "message": summary
                }
            }
        }
        
        # 添加思考流程轨迹
        trace_dict = trace.to_dict()
        analysis_result["trace"] = trace_dict
        
        # 保存trace到数据库
        if TRACE_DB_AVAILABLE:
            save_trace_to_db(trace)
        
        return analysis_result
    
    def _process_entity(self, text: str, trace) -> Dict[str, Any]:
        """处理实体识别
        
        Args:
            text: 用户输入
            trace: 跟踪对象
            
        Returns:
            dict: 实体识别结果
        """
        if ENTITY_PROCESSOR_AVAILABLE:
            try:
                # 打印分词结果
                import jieba
                words = list(jieba.cut(text))
                print(f"分词结果: {words}")
                
                entity_result = entity_processor.process(text, trace)
                return entity_result
            except Exception as e:
                print(f"实体处理失败: {str(e)}")
                entity_result = {"entities": [], "processing_level": "error"}
                trace.add_step(
                    name="entity_recognition",
                    title="实体识别",
                    status="error",
                    data={
                        "error": str(e),
                        "processing_level": "error"
                    }
                )
                return entity_result
        else:
            # 回退实现：简单的基于规则的实体识别
            entity_result = self._fallback_entity_process(text)
            entities = entity_result.get("entities", [])
            processing_level = "fallback"
            
            # 转换实体格式以适应trace schema
            trace_entities = []
            for entity in entities:
                trace_entity = {
                    "text": entity.get("text"),
                    "type": entity.get("label"),
                    "confidence": entity.get("confidence", 0.0)
                }
                trace_entities.append(trace_entity)
            
            trace.add_step(
                name="entity_recognition",
                title="实体识别",
                status="success",
                data={
                    "entities": trace_entities,
                    "processing_level": "fallback"
                }
            )
            return entity_result
    
    def _process_intent(self, text: str, trace) -> Dict[str, Any]:
        """处理意图分析
        
        Args:
            text: 用户输入
            trace: 跟踪对象
            
        Returns:
            dict: 意图分析结果
        """
        try:
            intent_result = intent_router.classify(text, trace)
            return intent_result
        except Exception as e:
            print(f"意图分析失败: {str(e)}")
            intent_result = {
                "intent": "general_chat",
                "confidence": 0.5,
                "method": "error"
            }
            trace.add_step(
                name="intent_classification",
                title="意图判断",
                status="error",
                data={
                    "error": str(e),
                    "intent": "general_chat",
                    "confidence": 0.5,
                    "router": "error"
                }
            )
            return intent_result
        
        # 优先使用意图路由器的结果，因为它更准确
        intent = intent_result.get("intent", "general_chat")
        intent_confidence = intent_result.get("confidence", 0.0)
        
        # 只有当意图路由器识别为 general_chat 时，才考虑解析器的结果
        if intent == "general_chat":
            if isinstance(turn_result.get("intent"), dict):
                parsed_intent = turn_result["intent"]["value"]
                if parsed_intent != "general_chat":
                    intent = parsed_intent
                    intent_confidence = turn_result["intent"]["confidence"]
            else:
                # 对于 memory_query 意图，优先使用解析器结果
                parsed_intent = turn_result.get("intent")
                if parsed_intent == "memory_query":
                    intent = parsed_intent
                    intent_confidence = 0.7  # 给一个合理的置信度
        
        # 构建综合分析结果，优先使用解析器的结果
        analysis_result = {
            "text": text,
            "entities": entities,
            "processing_level": entity_result.get("processing_level", "unprocessed"),
            "intent": intent,
            "intent_confidence": intent_confidence,
            "intent_method": intent_result.get("method", "unknown"),
            "needs_review": needs_review,
            "turn_result": turn_result,  # 添加解析器结果
            "parse_result": turn_result  # 新的解析结果格式
        }
        
        # 6. 根据意图和实体生成响应建议，传入解析器结果和会话上下文
        suggestion = self._generate_response_suggestion(analysis_result, turn_result, session_ctx)
        analysis_result["response_suggestion"] = suggestion
        
        trace.add_step(
            name="action_planning",
            title="动作规划",
            status="success",
            data={
                "action": suggestion.get("action"),
                "params": {
                    "target": suggestion.get("target"),
                    "message": suggestion.get("message")
                }
            }
        )
        
        # 7. 调用后端服务
        backend_response = self._call_backend_service(analysis_result, trace)
        analysis_result["backend_response"] = backend_response
        
        # 调试信息：打印backend_response的内容
        print(f"backend_response success: {backend_response.get('success')}")
        print(f"backend_response message: {backend_response.get('message')}")
        if backend_response.get('data'):
            print(f"backend_response data keys: {backend_response.get('data').keys()}")
        
        # 8. 答案生成（使用增强的提示词）
        summary = ""
        print(f"DEBUG: 开始答案生成，backend_response.success: {backend_response.get('success')}")
        if backend_response.get("success"):
            action = suggestion.get("action")
            print(f"DEBUG: suggestion: {suggestion}")
            print(f"DEBUG: action: {action}")
            
            # 构建上下文信息
            context_info = ""
            if session_ctx:
                if session_ctx.current_recipe_name:
                    context_info += f"当前讨论的配方: {session_ctx.current_recipe_name}\n"
                if session_ctx.current_canonical_name:
                    context_info += f"当前讨论的食材: {session_ctx.current_canonical_name}\n"
            
            if action == "search_recipe":
                print(f"DEBUG: 进入search_recipe处理逻辑")
                recipe = backend_response.get('data', {})
                print(f"DEBUG: recipe数据: {recipe}")
                
                # 构建详细的食谱信息
                recipe_basic_info = f"食谱名称: {recipe.get('name', '')}"
                recipe_description = recipe.get('description', '暂无描述')
                recipe_instructions = recipe.get('instructions', '暂无制作步骤')
                recipe_structure = ""
                
                # 如果有结构信息，添加到结构部分
                if 'ingredients' in recipe:
                    ingredients = recipe['ingredients']
                    recipe_structure = f"包含 {len(ingredients)} 个食材："
                    for i, ing in enumerate(ingredients, 1):
                        recipe_structure += f"\n{i}. {ing.get('ingredient', '')} ({ing.get('amount', '')} {ing.get('unit', '')})"
                
                # 使用增强的提示词
                try:
                    print(f"DEBUG: 准备生成LLM响应")
                    prompt_template = settings.get_enhanced_prompt("recipe_search_enhanced")
                    if prompt_template:
                        prompt = prompt_template.format(
                            recipe_name=recipe.get('name', ''),
                            recipe_basic_info=recipe_basic_info,
                            recipe_description=recipe_description,
                            recipe_instructions=recipe_instructions,
                            recipe_structure=recipe_structure
                        )
                    else:
                        # 回退到简单提示词
                        prompt = f"用户询问关于食谱 '{recipe.get('name', '')}' 的信息，以下是检索到的信息：\n{recipe_basic_info}\n{recipe_description}\n{recipe_instructions}\n{recipe_structure}\n请基于这些信息，以调酒师的身份生成一个友好、专业的回答。"
                    
                    print(f"DEBUG: 调用LLM生成响应，提示词: {prompt}")
                    summary = bartender_llm.generate_response(prompt)
                    print(f"DEBUG: LLM响应: {summary}")
                    
                    # 检查是否是回退响应
                    fallback_responses = [
                        "你好！欢迎来到我的酒吧，有什么可以帮你的吗？",
                        "很高兴为你服务！请问你想了解关于鸡尾酒的什么信息，或者需要我为你推荐一款适合的饮品吗？"
                    ]
                    
                    if any(fallback in summary for fallback in fallback_responses):
                        print(f"DEBUG: LLM返回了回退响应，使用基于食谱信息的回退回答")
                        # 使用基于食谱信息的回退回答
                        summary = f"为你找到食谱: {recipe.get('name', '')}"
                        if recipe.get('description'):
                            summary += f"\n\n描述: {recipe.get('description')}"
                        if recipe.get('instructions'):
                            summary += f"\n\n制作步骤: {recipe.get('instructions')}"
                    else:
                        print(f"DEBUG: LLM响应生成成功: {summary}")
                except Exception as e:
                    print(f"生成调酒师响应失败: {e}")
                    import traceback
                    print(f"DEBUG: 错误堆栈: {traceback.format_exc()}")
                    # 使用回退响应
                    summary = f"为你找到食谱: {recipe.get('name', '')}"
                    if recipe.get('description'):
                        summary += f"\n\n描述: {recipe.get('description')}"
                    if recipe.get('instructions'):
                        summary += f"\n\n制作步骤: {recipe.get('instructions')}"
                print(f"DEBUG: search_recipe处理完成，summary: {summary}")
                        
            elif action == "get_recipe_structure":
                ingredients = backend_response.get('data', {}).get('ingredients', [])
                ingredient_count = len(ingredients)
                
                # 构建详细的食材信息
                ingredients_list = f"食谱包含 {ingredient_count} 个食材"
                ingredients_details = ""
                for i, ingredient in enumerate(ingredients, 1):
                    ingredient_name = ingredient.get('ingredient', '')
                    amount = ingredient.get('amount', '')
                    unit = ingredient.get('unit', '')
                    role = ingredient.get('role', '')
                    
                    detail = f"{i}. {ingredient_name}"
                    if amount and unit:
                        detail += f" - 用量: {amount} {unit}"
                    if role:
                        detail += f" - 作用: {role}"
                    ingredients_details += detail + "\n"
                
                # 使用增强的提示词
                try:
                    prompt_template = settings.get_enhanced_prompt("recipe_structure_enhanced")
                    if prompt_template:
                        prompt = prompt_template.format(
                            recipe_name=suggestion.get("target", "未知食谱"),
                            ingredients_list=ingredients_list,
                            ingredients_details=ingredients_details
                        )
                    else:
                        # 回退到简单提示词
                        prompt = f"用户询问食谱的结构，以下是检索到的食材信息：\n{ingredients_list}\n{ingredients_details}\n请基于这些信息，以调酒师的身份生成一个友好、专业的回答。"
                    
                    summary = bartender_llm.generate_response(prompt)
                except Exception as e:
                    print(f"生成调酒师响应失败: {e}")
                    # 使用回退响应
                    summary = f"为你找到食谱结构，包含 {ingredient_count} 个食材"
                    if ingredients:
                        summary += '\n\n具体食材：'
                        for i, ingredient in enumerate(ingredients, 1):
                            ingredient_name = ingredient.get('ingredient', '')
                            amount = ingredient.get('amount', '')
                            unit = ingredient.get('unit', '')
                            if amount and unit:
                                summary += f'\n{i}. {ingredient_name} ({amount} {unit})'
                            else:
                                summary += f'\n{i}. {ingredient_name}'
                                
            elif action == "get_ingredient_neighbors":
                neighbors = backend_response.get('data', {}).get('neighbors', [])
                neighbor_count = len(neighbors)
                
                # 构建详细的邻域信息
                neighbors_list = f"找到 {neighbor_count} 个邻近食材"
                relationships = ""
                for i, neighbor in enumerate(neighbors, 1):
                    neighbor_name = neighbor.get('neighbor_name', '')
                    relationship_type = neighbor.get('relationship_type', '')
                    relationships += f"{i}. {neighbor_name}"
                    if relationship_type:
                        relationships += f" - 关系: {relationship_type}"
                    relationships += "\n"
                
                # 使用增强的提示词
                try:
                    prompt_template = settings.get_enhanced_prompt("ingredient_neighbors_enhanced")
                    if prompt_template:
                        prompt = prompt_template.format(
                            ingredient_name=suggestion.get("target", "未知食材"),
                            neighbors_list=neighbors_list,
                            relationships=relationships
                        )
                    else:
                        # 回退到简单提示词
                        prompt = f"用户询问食材的邻域信息，以下是检索到的邻近食材：\n{neighbors_list}\n{relationships}\n请基于这些信息，以调酒师的身份生成一个友好、专业的回答。"
                    
                    summary = bartender_llm.generate_response(prompt)
                except Exception as e:
                    print(f"生成调酒师响应失败: {e}")
                    # 使用回退响应
                    summary = f"为你找到 {neighbor_count} 个邻近食材"
                    if neighbors:
                        summary += '\n\n具体邻近食材：'
                        for i, neighbor in enumerate(neighbors, 1):
                            neighbor_name = neighbor.get('neighbor_name', '')
                            relationship_type = neighbor.get('relationship_type', '')
                            if relationship_type:
                                summary += f'\n{i}. {neighbor_name} ({relationship_type})'
                            else:
                                summary += f'\n{i}. {neighbor_name}'
                                
            elif action == "get_substitute":
                substitutes = backend_response.get('data', {}).get('substitutes', [])
                substitute_count = len(substitutes)
                
                # 构建详细的替代信息
                substitutes_list = f"找到 {substitute_count} 个可替代原料"
                similarity_info = ""
                for i, substitute in enumerate(substitutes, 1):
                    substitute_name = substitute.get('substitute_name', '')
                    similarity_score = substitute.get('similarity_score', '')
                    similarity_info += f"{i}. {substitute_name}"
                    if similarity_score:
                        similarity_info += f" - 相似度: {similarity_score}"
                    similarity_info += "\n"
                
                # 使用增强的提示词
                try:
                    prompt_template = settings.get_enhanced_prompt("substitute_enhanced")
                    if prompt_template:
                        prompt = prompt_template.format(
                            original_ingredient=suggestion.get("target", "未知食材"),
                            substitutes_list=substitutes_list,
                            similarity_info=similarity_info
                        )
                    else:
                        # 回退到简单提示词
                        prompt = f"用户询问食材的替代建议，以下是检索到的替代原料：\n{substitutes_list}\n{similarity_info}\n请基于这些信息，以调酒师的身份生成一个友好、专业的回答。"
                    
                    summary = bartender_llm.generate_response(prompt)
                except Exception as e:
                    print(f"生成调酒师响应失败: {e}")
                    # 使用回退响应
                    summary = f"为你找到 {substitute_count} 个可替代原料"
                    if substitutes:
                        summary += '\n\n具体替代原料：'
                        for i, substitute in enumerate(substitutes, 1):
                            substitute_name = substitute.get('substitute_name', '')
                            similarity_score = substitute.get('similarity_score', '')
                            if similarity_score:
                                summary += f'\n{i}. {substitute_name} (相似度: {similarity_score})'
                            else:
                                summary += f'\n{i}. {substitute_name}'
                                
            elif action == "get_recommendation":
                # 处理推荐结果
                recommendations = backend_response.get('data', {}).get('recommendations', [])
                user_needs = text
                
                # 构建推荐结果列表
                recommendations_list = ""
                for i, rec in enumerate(recommendations, 1):
                    name = rec.get('recipe_name_zh', rec.get('name', '未知饮品'))
                    alcohol_content = rec.get('alcohol_content', '未知酒精度')
                    description = rec.get('description', '暂无描述')
                    recommendations_list += f"{i}. {name} - 酒精度: {alcohol_content}\n   描述: {description}\n"
                
                # 构建推荐理由
                recommendation_reasons = "我感觉这几款你会喜欢的："
                
                # 检查推荐结果是否为空
                if not recommendations:
                    summary = "抱歉，没找到合适的饮品呢……（扣扣脑袋）"
                else:
                    # 检查LLM客户端是否可用
                    if not bartender_llm.client:
                        print("LLM客户端不可用，使用基于数据库的推荐响应")
                        # 直接生成基于数据库的推荐响应
                        summary = "看看这几款怎么样，我觉得会很适合你哦：\n"
                        for i, rec in enumerate(recommendations, 1):
                            name = rec.get('recipe_name_zh', rec.get('name', '未知饮品'))
                            summary += f"{i}. {name}\n"
                    else:
                        # 使用增强的推荐提示词，让LLM润色推荐结果
                        try:
                            # 构建消息列表
                            messages = [
                                {"role": "system", "content": bartender_llm.role_info}
                            ]
                            
                            # 构建用户消息
                            user_message = f"用户说：{user_needs}\n\n基于数据库推荐结果，为用户生成一个友好、专业的推荐回答：\n"
                            for i, rec in enumerate(recommendations, 1):
                                name = rec.get('recipe_name_zh', rec.get('name', '未知饮品'))
                                description = rec.get('description', '暂无描述')
                                instructions = rec.get('instructions', '暂无制作步骤')
                                user_message += f"{i}. {name}\n   描述: {description}\n   制作步骤: {instructions}\n\n"
                            
                            messages.append({"role": "user", "content": user_message})
                            
                            # 直接调用LLM API
                            import time
                            start_time = time.time()
                            response = bartender_llm.client.chat.completions.create(
                                model=bartender_llm.model_name,
                                temperature=0.7,
                                max_tokens=1000,
                                messages=messages,
                                timeout=15
                            )
                            end_time = time.time()
                            print(f"LLM 响应时间: {end_time - start_time:.2f} 秒")
                            
                            # 提取响应内容
                            summary = response.choices[0].message.content.strip()
                        except Exception as e:
                            print(f"生成推荐响应失败: {e}")
                            # 回退响应
                            summary = "（翻酒单中）（寻找）（猛地发现）这几款我觉得会适合你：\n"
                            for i, rec in enumerate(recommendations, 1):
                                name = rec.get('recipe_name_zh', rec.get('name', '未知饮品'))
                                summary += f"{i}. {name}\n"
            
            elif action == "general_response":
                # 使用增强的日常交流提示词
                try:
                    prompt_template = settings.get_enhanced_prompt("daily_chat_enhanced")
                    if prompt_template:
                        prompt = prompt_template.format(
                            user_input=text,
                            context_info=context_info
                        )
                    else:
                        # 回退到简单提示词
                        if session_ctx:
                            prompt = f"【对话上下文】\n{context_info}\n\n【当前问题】\n用户: {text}\n\n请以调酒师的身份回答这个问题。"
                        else:
                            prompt = text
                    
                    summary = bartender_llm.generate_response(prompt)
                except Exception as e:
                    print(f"生成调酒师响应失败: {e}")
                    # 使用回退响应
                    summary = "你好！欢迎来到酒吧玩呀，有什么能帮到你吗？（搓手）"
        else:
            # 使用调酒师 LLM 生成错误响应
            error_message = backend_response.get('message', '未知错误')
            try:
                prompt = f"用户的请求处理失败，错误信息是：{error_message}\n请以调酒师的身份生成一个友好、专业的错误响应，表达歉意并提供一些建议。"
                summary = bartender_llm.generate_response(prompt)
            except Exception as e:
                print(f"生成调酒师响应失败: {e}")
                # 使用回退响应
                summary = f"处理失败: {error_message}\n\n嗷嗷很抱歉，我还没学会该怎么做这个〒▽〒。你可以尝试重新输入，或者询问其他问题。"

        
        trace.add_step(
            name="answer_generation",
            title="答案生成",
            status="success",
            data={
                "summary": summary
            }
        )
        
        # 将summary添加到analysis_result的顶层字段
        analysis_result["summary"] = summary
        
        # 9. 更新会话上下文（Step 3：执行后更新上下文）
        if session_ctx:
            # 构建实体字典
            entities_dict = {}
            for entity in entities:
                label = entity.get("label", "").lower()
                if "recipe" in label:
                    entities_dict["recipe"] = entity.get("text")
                elif "ingredient" in label or "canonical" in label:
                    entities_dict["ingredient"] = entity.get("canonical_name") or entity.get("text")
            
            # 如果是推荐动作，并且有推荐结果，更新实体字典为第一个推荐的饮品
            if suggestion.get("action") == "get_recommendation" and backend_response.get("success"):
                recommendations = backend_response.get('data', {}).get('recommendations', [])
                if recommendations:
                    first_recipe = recommendations[0]
                    recipe_id = first_recipe.get('recipe_id')
                    recipe_name = first_recipe.get('recipe_name_zh', first_recipe.get('name'))
                    if recipe_id and recipe_name:
                        entities_dict["recipe"] = recipe_name
                        print(f"将推荐的饮品添加到实体字典: {recipe_name}")
            
            # 如果当前轮解析有结果，合并到实体字典
            # 支持新旧两种接口格式
            if "slots" in turn_result:
                # 新接口：从 slots 中提取
                slots = turn_result.get("slots", {})
                if slots.get("recipe", {}).get("value"):
                    entities_dict["recipe"] = slots["recipe"]["value"]
                if slots.get("ingredient", {}).get("value"):
                    entities_dict["ingredient"] = slots["ingredient"]["value"]
                if slots.get("candidate_substitute", {}).get("value"):
                    entities_dict["candidate_substitute"] = slots["candidate_substitute"]["value"]
            else:
                # 旧接口：直接获取
                if turn_result.get("recipe"):
                    entities_dict["recipe"] = turn_result["recipe"]
                if turn_result.get("ingredient"):
                    entities_dict["ingredient"] = turn_result["ingredient"]
                if turn_result.get("candidate_substitute"):
                    entities_dict["candidate_substitute"] = turn_result["candidate_substitute"]
            
            # 更新会话上下文
            # 支持新旧两种接口格式获取 intent
            if isinstance(turn_result.get("intent"), dict):
                update_intent = turn_result.get("intent", {}).get("value", intent_result.get("intent", "general_chat"))
            else:
                update_intent = turn_result.get("intent", intent_result.get("intent", "general_chat"))
            
            session_ctx.update_after_execution(
                intent=update_intent,
                action=suggestion.get("action", "general_response"),
                entities=entities_dict
            )
            print(f"更新会话上下文: {session_ctx.to_dict()}")
        
        # 10. 如果需要审核，创建审核任务
        if needs_review:
            review_result = review_manager.create_review_task(text, entities)
            analysis_result["review_task"] = review_result
        
        # 11. 生成统一的解析结果结构
        parsed_query = ParsedQuery.from_analysis_result(analysis_result)
        analysis_result["parsed_query"] = parsed_query.to_dict()
        
        # 12. 添加思考流程轨迹
        trace_dict = trace.to_dict()
        analysis_result["trace"] = trace_dict
        
        # 保存trace到数据库
        if TRACE_DB_AVAILABLE:
            save_trace_to_db(trace)
        
        return analysis_result
    
    def _fallback_entity_process(self, text: str) -> Dict[str, Any]:
        """回退实体处理实现（从数据库动态加载）
        
        Args:
            text: 用户输入的文本
            
        Returns:
            Dict: 实体处理结果
        """
        entities = []
        
        try:
            # 尝试从MySQL数据库加载实体
            try:
                from app.backend.db.mysql import get_mysql_connection
                
                conn = get_mysql_connection()
                cursor = conn.cursor()
                
                # 获取热门食谱（限制数量以提高性能）
                cursor.execute("""
                    SELECT name, recipe_name_zh 
                    FROM recipe 
                    WHERE name IS NOT NULL OR recipe_name_zh IS NOT NULL
                    ORDER BY RAND() 
                    LIMIT 30
                """)
                recipes_db = cursor.fetchall()
                
                # 获取常见食材（限制数量以提高性能）
                cursor.execute("""
                    SELECT name_norm 
                    FROM ingredient 
                    WHERE name_norm IS NOT NULL
                    ORDER BY RAND() 
                    LIMIT 50
                """)
                ingredients_db = cursor.fetchall()
                
                cursor.close()
                conn.close()
                
                print(f"从数据库加载了 {len(recipes_db)} 个食谱和 {len(ingredients_db)} 个食材")
                
                # 识别食谱
                for recipe in recipes_db:
                    name = recipe[0]
                    name_zh = recipe[1]
                    
                    # 识别英文名称
                    if name and name.lower() in text.lower():
                        start = text.lower().find(name.lower())
                        if start != -1:
                            entities.append({
                                "text": text[start:start+len(name)],
                                "label": "RECIPE",
                                "start": start,
                                "end": start+len(name),
                                "processing_level": "fallback",
                                "confidence": 0.7,
                                "source": "database"
                            })
                            # 避免重复识别
                            text = text[:start] + " " * len(name) + text[start+len(name):]
                    
                    # 识别中文名称
                    if name_zh and name_zh in text:
                        start = text.find(name_zh)
                        if start != -1:
                            entities.append({
                                "text": text[start:start+len(name_zh)],
                                "label": "RECIPE",
                                "start": start,
                                "end": start+len(name_zh),
                                "processing_level": "fallback",
                                "confidence": 0.7,
                                "source": "database"
                            })
                            # 避免重复识别
                            text = text[:start] + " " * len(name_zh) + text[start+len(name_zh):]
                
                # 识别食材（按照长度从长到短排序，避免短食材被长食材包含）
                ingredients_list = [ing[0] for ing in ingredients_db if ing[0]]
                ingredients_list.sort(key=lambda x: len(x), reverse=True)
                
                for ingredient in ingredients_list:
                    if ingredient.lower() in text.lower():
                        start = text.lower().find(ingredient.lower())
                        if start != -1:
                            entities.append({
                                "text": text[start:start+len(ingredient)],
                                "label": "INGREDIENT",
                                "start": start,
                                "end": start+len(ingredient),
                                "processing_level": "fallback",
                                "confidence": 0.7,
                                "source": "database"
                            })
                            # 避免重复识别
                            text = text[:start] + " " * len(ingredient) + text[start+len(ingredient):]
                
                print(f"回退实体识别：从数据库识别了 {len(entities)} 个实体")
                
            except Exception as db_error:
                print(f"从数据库加载实体失败: {db_error}，使用配置文件作为回退")
                raise db_error
                
        except Exception as e:
            print(f"数据库加载失败，使用配置文件和硬编码列表作为最终回退: {e}")
            
            # 最终回退：使用配置文件中的风味词和少量硬编码列表
            entities = []
            
            # 从配置文件获取风味词
            try:
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
                from config import settings
                
                flavor_terms = settings.get_flavor_terms()
                
                # 识别风味词
                for flavor in flavor_terms:
                    if flavor.lower() in text.lower():
                        start = text.lower().find(flavor.lower())
                        if start != -1:
                            entities.append({
                                "text": text[start:start+len(flavor)],
                                "label": "FLAVOR",
                                "start": start,
                                "end": start+len(flavor),
                                "processing_level": "fallback",
                                "confidence": 0.7,
                                "source": "config"
                            })
                            # 避免重复识别
                            text = text[:start] + " " * len(flavor) + text[start+len(flavor):]
                
                print(f"从配置文件加载了 {len(flavor_terms)} 个风味词")
                
            except Exception as config_error:
                print(f"从配置文件加载风味词失败: {config_error}")
            
            # 使用少量硬编码的常见食谱和食材作为最终回退
            recipes = ["Margarita", "Negroni", "Martini", "Cosmopolitan", "Mojito"]
            for recipe in recipes:
                if recipe.lower() in text.lower():
                    start = text.lower().find(recipe.lower())
                    if start != -1:
                        entities.append({
                            "text": text[start:start+len(recipe)],
                            "label": "RECIPE",
                            "start": start,
                            "end": start+len(recipe),
                            "processing_level": "fallback",
                            "confidence": 0.7,
                            "source": "hardcoded"
                        })
            
            ingredients = ["柠檬", "lemon", "青柠", "lime", "伏特加", "vodka", "金酒", "gin", "龙舌兰", "tequila", "威士忌", "whiskey", "朗姆酒", "rum", "白兰地", "brandy", "利口酒", "liqueur", "苦精", "bitters"]
            ingredients.sort(key=lambda x: len(x), reverse=True)
            for ingredient in ingredients:
                if ingredient.lower() in text.lower():
                    start = text.lower().find(ingredient.lower())
                    if start != -1:
                        entities.append({
                            "text": text[start:start+len(ingredient)],
                            "label": "INGREDIENT",
                            "start": start,
                            "end": start+len(ingredient),
                            "processing_level": "fallback",
                            "confidence": 0.7,
                            "source": "hardcoded"
                        })
                        # 避免重复识别
                        text = text[:start] + " " * len(ingredient) + text[start+len(ingredient):]
            
            # 硬编码的风味词
            flavors = ["smoky", "sweet", "sour", "bitter", "fruity", "清爽", "醇厚", "酸甜", "酸", "甜", "苦", "香", "辣", "咸", "鲜", "浓郁", "清淡"]
            for flavor in flavors:
                if flavor.lower() in text.lower():
                    start = text.lower().find(flavor.lower())
                    if start != -1:
                        entities.append({
                            "text": text[start:start+len(flavor)],
                            "label": "FLAVOR",
                            "start": start,
                            "end": start+len(flavor),
                            "processing_level": "fallback",
                            "confidence": 0.7,
                            "source": "hardcoded"
                        })
            
            # 硬编码的心情词
            mood_terms = ["心情", "开心", "高兴", "快乐", "愉快", "兴奋", "激动", "难过", "悲伤", "伤心", "沮丧", "疲惫", "累", "压力", "紧张", "焦虑", "放松", "平静", "舒服", "好", "不好"]
            for mood in mood_terms:
                if mood.lower() in text.lower():
                    start = text.lower().find(mood.lower())
                    if start != -1:
                        entities.append({
                            "text": text[start:start+len(mood)],
                            "label": "MOOD",
                            "start": start,
                            "end": start+len(mood),
                            "processing_level": "fallback",
                            "confidence": 0.7,
                            "source": "hardcoded"
                        })
            
            print(f"最终回退：识别了 {len(entities)} 个实体")
        
        return {
            "entities": entities,
            "processing_level": "fallback"
        }
    
    def _check_needs_review(self, entities: List[Dict[str, Any]]) -> bool:
        """检查是否需要人工审核
        
        Args:
            entities: 识别的实体列表
            
        Returns:
            bool: 是否需要人工审核
        """
        for entity in entities:
            if entity.get("processing_level") in ["llm_analysis", "unrecognized", "fallback"]:
                return True
        return False
    
    def _generate_response_suggestion(self, analysis_result: Dict[str, Any], turn_result: Dict[str, Any], session_ctx=None) -> Dict[str, Any]:
        """生成响应建议
        
        Args:
            analysis_result: 分析结果
            turn_result: 解析器结果
            session_ctx: 会话上下文
            
        Returns:
            Dict: 响应建议
        """
        intent = analysis_result.get("intent")
        entities = analysis_result.get("entities", [])
        text = analysis_result.get("text", "")
        
        # 提取关键实体
        recipe_entities = [e for e in entities if e.get("label") == "RECIPE"]
        ingredient_entities = [e for e in entities if e.get("label") in ["INGREDIENT", "CANONICAL"]]
        flavor_entities = [e for e in entities if e.get("label") == "FLAVOR"]
        constraint_entities = [e for e in entities if e.get("label") == "CONSTRAINT"]
        
        # 处理代词（如"他"、"它"、"这个"等）
        # 检查文本是否包含代词
        pronouns = ["他", "它", "这个", "那个", "这杯", "那杯"]
        has_pronoun = any(pronoun in text for pronoun in pronouns)
        
        # 如果包含代词，并且会话上下文中有当前配方，使用会话上下文中的配方
        if has_pronoun and session_ctx and session_ctx.current_recipe_name:
            print(f"检测到代词，使用会话上下文中的配方: {session_ctx.current_recipe_name}")
            # 将会话上下文中的配方添加到实体列表
            recipe_entities.append({
                "text": session_ctx.current_recipe_name,
                "label": "RECIPE",
                "source": "session_context"
            })
            # 调整意图为recipe_search，因为用户可能在询问之前推荐的饮品的详细信息
            if intent == "general_chat" or intent == "other":
                intent = "recipe_search"
        
        # 从解析器结果中获取配方和食材（支持新旧两种接口）
        if "slots" in turn_result:
            # 新接口：从 slots 中提取
            slots = turn_result.get("slots", {})
            parsed_recipe = slots.get("recipe", {}).get("value")
            parsed_ingredient = slots.get("ingredient", {}).get("value")
        else:
            # 旧接口：直接获取
            parsed_recipe = turn_result.get("recipe")
            parsed_ingredient = turn_result.get("ingredient")
        
        suggestion = {
            "intent": intent,
            "key_entities": {
                "recipes": recipe_entities,
                "ingredients": ingredient_entities,
                "flavors": flavor_entities,
                "constraints": constraint_entities
            }
        }
        
        # 根据意图生成具体建议
        if intent == "recipe_search" or intent == "recipe_query":
            if parsed_recipe:
                suggestion["action"] = "search_recipe"
                suggestion["target"] = parsed_recipe
                print(f"使用解析器结果: 配方={parsed_recipe}")
            elif recipe_entities:
                suggestion["action"] = "search_recipe"
                suggestion["target"] = recipe_entities[0].get("text")
                print(f"使用实体识别结果: 配方={recipe_entities[0].get('text')}")
            else:
                # 对于recipe_search意图，尝试从用户输入中提取食谱名称
                # 移除常见的查询词和标点符号
                import re
                recipe_name = re.sub(r'的配方是|配方|是|什么|\?|\？|!|！|。|，', '', text).strip()
                if recipe_name:
                    suggestion["action"] = "search_recipe"
                    suggestion["target"] = recipe_name
                    print(f"使用用户输入提取的配方名称: {recipe_name}")
                else:
                    suggestion["action"] = "ask_recipe"
                    suggestion["message"] = "可以说说你想了解的酒单名字吗？"
        
        elif intent == "recipe_structure":
            if parsed_recipe:
                suggestion["action"] = "get_recipe_structure"
                suggestion["target"] = parsed_recipe
                print(f"使用解析器结果: 配方={parsed_recipe}")
            elif recipe_entities:
                suggestion["action"] = "get_recipe_structure"
                suggestion["target"] = recipe_entities[0].get("text")
                print(f"使用实体识别结果: 配方={recipe_entities[0].get('text')}")
            else:
                suggestion["action"] = "ask_recipe"
                suggestion["message"] = "可以说说你想了解的酒单名字吗？"
        
        elif intent == "ingredient_neighbors":
            if parsed_ingredient:
                suggestion["action"] = "get_ingredient_neighbors"
                suggestion["target"] = parsed_ingredient
                print(f"使用解析器结果: 食材={parsed_ingredient}")
            elif ingredient_entities:
                suggestion["action"] = "get_ingredient_neighbors"
                suggestion["target"] = ingredient_entities[0].get("text")
                print(f"使用实体识别结果: 食材={ingredient_entities[0].get('text')}")
            else:
                suggestion["action"] = "ask_ingredient"
                suggestion["message"] = "你想问的是什么原料呢？"
        
        elif intent == "substitute_recommendation" or intent == "ingredient_substitute":
            if parsed_ingredient:
                suggestion["action"] = "get_substitute"
                suggestion["target"] = parsed_ingredient
                print(f"使用解析器结果: 食材={parsed_ingredient}")
            elif ingredient_entities:
                suggestion["action"] = "get_substitute"
                suggestion["target"] = ingredient_entities[0].get("text")
                print(f"使用实体识别结果: 食材={ingredient_entities[0].get('text')}")
            else:
                # 特殊处理：尝试从文本中提取食材名称
                # 常见的食材名称列表
                common_ingredients = ["lemon", "lime", "vodka", "gin", "tequila", "mezcal", "rum", "whiskey", "bourbon", "scotch", "brandy", "cognac", "sherry", "port", "vermouth", "bitters", "syrup", "juice", "soda", "tonic"]
                
                print(f"尝试从文本中提取食材，文本: {text}")
                
                # 尝试从文本中提取食材名称
                extracted_ingredient = None
                
                # 首先尝试从实体处理器获取实体
                try:
                    if ENTITY_PROCESSOR_AVAILABLE:
                        entity_result = entity_processor.process(text)
                        entities = entity_result.get("entities", [])
                        
                        # 查找食材实体
                        for entity in entities:
                            if entity.get("label") == "INGREDIENT":
                                extracted_ingredient = entity.get("text")
                                print(f"从实体处理器提取到食材: {extracted_ingredient}")
                                break
                except Exception as e:
                    print(f"实体处理器调用失败: {e}")
                
                # 如果实体处理器没有找到食材，尝试从常见食材列表中匹配
                if not extracted_ingredient:
                    # 从 entity_lexicon.json 中加载食材列表
                    import json
                    import os
                    lexicon_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entity", "entity_lexicon.json")
                    ingredients = []
                    
                    try:
                        with open(lexicon_file, 'r', encoding='utf-8') as f:
                            lexicon = json.load(f)
                        ingredient_lexicon = lexicon.get("ingredient", {})
                        ingredients = list(ingredient_lexicon.keys())
                        print(f"从 entity_lexicon.json 加载了 {len(ingredients)} 个食材")
                    except Exception as e:
                        print(f"加载 entity_lexicon.json 失败: {e}")
                        # 使用默认食材列表作为回退，包含中英文食材名称
                        ingredients = ["柠檬", "lemon", "青柠", "lime", "伏特加", "vodka", "金酒", "gin", "龙舌兰", "tequila", "威士忌", "whiskey", "朗姆酒", "rum", "白兰地", "brandy", "利口酒", "liqueur", "苦精", "bitters"]
                    
                    # 按照食材长度从长到短排序，避免短食材被长食材包含
                    ingredients.sort(key=lambda x: len(x), reverse=True)
                    
                    for ingredient in ingredients:
                        if ingredient.lower() in text.lower():
                            # 直接使用食材名称
                            extracted_ingredient = ingredient
                            print(f"从食材列表提取到食材: {extracted_ingredient}")
                            break
                
                if extracted_ingredient:
                    suggestion["action"] = "get_substitute"
                    suggestion["target"] = extracted_ingredient
                    print(f"设置target为: {extracted_ingredient}")
                else:
                    suggestion["action"] = "ask_ingredient"
                    suggestion["message"] = "请提供需要替代的食材名称"
                    print("未提取到食材，使用ask_ingredient")
        
        elif intent == "memory_query":
            # 直接返回记忆中的配方信息
            if parsed_recipe:
                suggestion["action"] = "general_response"
                suggestion["message"] = f"当然记得啦！可不要小瞧我！（叉腰）我们要做的酒是 {parsed_recipe}。"
                print(f"使用解析器结果: 记忆查询={parsed_recipe}")
            elif session_ctx and session_ctx.current_recipe_name:
                # 从会话上下文获取配方
                recipe_name = session_ctx.current_recipe_name
                suggestion["action"] = "general_response"
                suggestion["message"] = f"当然记得啦！可不要小瞧我！（叉腰）我们要做的酒是 {recipe_name}。"
                print(f"使用会话上下文: 记忆查询={recipe_name}")
            else:
                suggestion["action"] = "general_response"
                suggestion["message"] = "啊抱歉，我不太记得我们要做的酒的名字了（扣扣脑袋）。你可以再告诉我一下嘛？"
                print("未找到记忆中的配方")
        
        elif intent == "general_chat":
            # 检查是否包含推荐相关的关键词
            has_recommendation_keywords = any(keyword in text for keyword in ["推荐", "想喝", "适合", "材料", "心情", "场合", "季节"])
            if has_recommendation_keywords or flavor_entities or constraint_entities:
                suggestion["action"] = "get_recommendation"
                suggestion["message"] = "这几杯我感觉你会喜欢的！（星星眼）"
            else:
                suggestion["action"] = "general_response"
                suggestion["message"] = "你好呀，有什么可以帮到你吗？（搓手）"
        
        # 推荐意图处理
        elif intent == "recommendation" or intent == "drink_recommendation":
            suggestion["action"] = "get_recommendation"
            suggestion["message"] = "这几杯应该符合要求！请查收！"
        
        # 其他意图处理
        elif intent == "other":
            suggestion["action"] = "general_response"
            suggestion["message"] = "你好呀，有什么可以帮到你吗？（搓手）"
        
        return suggestion
    
    def _call_backend_service(self, analysis_result: Dict[str, Any], trace) -> Dict[str, Any]:
        """调用后端服务
        
        Args:
            analysis_result: 分析结果
            trace: trace对象
            
        Returns:
            Dict: 后端服务响应
        """
        suggestion = analysis_result.get("response_suggestion", {})
        action = suggestion.get("action")
        target = suggestion.get("target")
        message = suggestion.get("message")
        
        try:
            if action == "search_recipe" and target:
                return backend_service.search_recipe(target, trace)
            elif action == "recipe_search" and target:
                return backend_service.search_recipe(target, trace)
            elif action == "get_recipe_structure" and target:
                return backend_service.get_recipe_structure(target, trace)
            elif action == "get_ingredient_neighbors" and target:
                return backend_service.get_ingredient_neighbors(target, trace)
            elif action == "get_substitute" and target:
                return backend_service.get_substitute(target, trace)
            elif action == "get_recommendation":
                entities = analysis_result.get("entities", [])
                constraints = [e for e in entities if e.get("label") == "CONSTRAINT"]
                return recommendation_service.recommend(
                    analysis_result.get("text", ""),
                    entities,
                    constraints
                )
            elif action == "general_response":
                return backend_service.general_response(message or analysis_result.get("text"), trace)
            elif action == "ask_recipe" or action == "ask_ingredient":
                return {"success": True, "data": {"message": message or "请提供具体信息"}}
            else:
                return {"success": False, "message": "无法调用后端服务"}
        except Exception as e:
            print(f"调用后端服务失败: {str(e)}")
            return {"success": False, "message": f"调用后端服务失败: {str(e)}"}
    
    def batch_analyze(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量分析用户输入
        
        Args:
            texts: 用户输入的文本列表
            
        Returns:
            List[Dict]: 分析结果列表
        """
        results = []
        for text in texts:
            result = self.analyze(text)
            results.append(result)
        return results

# 创建全局用户输入分析器实例
user_input_analyzer = UserInputAnalyzer()
