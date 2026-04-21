"""
领域智能体主入口文件

该文件是领域智能体的主入口，包括：
- FastAPI 应用初始化
- API 路由定义
- 工作流调用逻辑
- 错误处理中间件

领域智能体功能：
- 实体识别与处理
- 意图分析
- 后端服务调用
- Trace 收集与可视化
"""

import os
import sys
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

# 添加当前目录和项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入配置
try:
    from config import settings
except ImportError:
    print("警告: 无法导入配置模块，使用默认配置")
    class Settings:
        DEBUG = True
    settings = Settings()

# 导入核心模块
from analysis.user_input_analyzer import UserInputAnalyzer
from tracing.trace_collector import create_trace
from services.backend_service import backend_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理

    启动时初始化资源，关闭时清理资源
    """
    print("领域智能体启动中...")
    yield
    print("领域智能体关闭中...")


# 创建 FastAPI 应用
app = FastAPI(
    title="领域智能体 API",
    description="基于实体识别和意图分析的烹饪领域智能体",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建用户输入分析器实例
analyzer = UserInputAnalyzer()


@app.get("/")
async def root():
    """
    根路径

    返回 API 基本信息
    """
    return {
        "name": "领域智能体 API",
        "version": "1.0.0",
        "description": "基于实体识别和意图分析的烹饪领域智能体"
    }


@app.get("/health")
async def health_check():
    """
    健康检查

    返回服务健康状态
    """
    return {
        "status": "healthy",
        "debug": settings.DEBUG
    }


from pydantic import BaseModel
from typing import Optional


class MessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[int] = None


@app.post("/api/chat/send")
async def send_message(request: MessageRequest, background_tasks: BackgroundTasks):
    """
    发送消息接口

    处理用户消息，返回智能体的回答

    Args:
        request: 包含消息和会话ID的请求对象
        background_tasks: 后台任务管理器，用于异步执行保存 trace 到数据库的操作

    Returns:
        包含处理结果的响应
    """
    try:
        message = request.message
        session_id = request.session_id
        user_id = request.user_id

        # 如果 session_id 为 None，生成一个新的 session_id
        if session_id is None:
            import uuid
            session_id = str(uuid.uuid4())

        # 创建 trace
        trace = create_trace(message, session_id)

        # 直接处理消息
        from analysis.user_input_analyzer import user_input_analyzer
        analysis_result = user_input_analyzer.analyze(message, session_id=session_id, trace=trace)

        # 从分析结果中获取最终回答
        final_answer = ""
        
        # 首先检查 backend_response 是否成功
        backend_response = analysis_result.get("backend_response", {})
        suggestion = analysis_result.get("response_suggestion", {})
        action = suggestion.get("action")
        
        if backend_response.get("success"):
            # 如果是general_response，优先使用analysis_result.summary
            if action == "general_response" and analysis_result.get("summary"):
                final_answer = analysis_result.get("summary")
            else:
                # 其他情况，从 data 中获取 message
                final_answer = backend_response.get("data", {}).get("message")
            
            # 如果没有 message，但有 substitutes（替代建议），生成包含上下文的回复
            if not final_answer and backend_response.get("data", {}).get("substitutes"):
                ingredient = backend_response.get("data", {}).get("ingredient", "")
                substitutes = backend_response.get("data", {}).get("substitutes", [])
                
                # 获取当前配方上下文
                recipe_name = None
                turn_result = analysis_result.get("turn_result", {})
                if turn_result and "slots" in turn_result:
                    recipe_slot = turn_result.get("slots", {}).get("recipe", {})
                    recipe_name = recipe_slot.get("value")
                
                # 构建替代建议列表（包含中英文对照）
                substitutes_list = ""
                for i, sub in enumerate(substitutes[:5], 1):
                    sub_name = sub.get("substitute_name", "")
                    score = sub.get("similarity_score", 0)
                    # 尝试获取中文名称映射
                    try:
                        from services.backend_service import backend_service
                        chinese_name = backend_service._get_chinese_name(sub_name)  # 使用正确的方法获取中文名称
                        if chinese_name != sub_name:
                            substitutes_list += f"{i}. **{sub_name}** ({chinese_name})"
                        else:
                            substitutes_list += f"{i}. **{sub_name}**"
                    except:
                        substitutes_list += f"{i}. **{sub_name}**"
                    if score:
                        substitutes_list += f" (相似度: {score})"
                    substitutes_list += "\n"
                
                # 构建LLM提示词
                if recipe_name:
                    prompt = f"用户询问在 '{recipe_name}' 中 '{ingredient}' 的替代品。以下是替代建议：\n{substitutes_list}\n请以调酒师的身份生成一个友好、专业的回答，包含中英文对照的替代建议。"
                else:
                    prompt = f"用户询问 '{ingredient}' 的替代品。以下是替代建议：\n{substitutes_list}\n请以调酒师的身份生成一个友好、专业的回答，包含中英文对照的替代建议。"
                
                # 调用LLM生成回答
                try:
                    from services.bartender_llm import bartender_llm
                    final_answer = bartender_llm.generate_response(prompt)
                except:
                    # 如果LLM调用失败，使用默认格式
                    if recipe_name:
                        final_answer = f"在 **{recipe_name}** 中，**{ingredient}** 可以替换为：\n\n"
                    else:
                        final_answer = f"**{ingredient}** 可以替换为：\n\n"
                    final_answer += substitutes_list
                    final_answer += "\n这些替代品都可以根据您的口味和可用性进行选择。"
        else:
            # 如果失败，先尝试从trace步骤中获取LLM生成的错误响应
            final_answer = ""
            if trace.steps:
                # 查找包含LLM响应的步骤
                for step in reversed(trace.steps):
                    if hasattr(step, 'data') and isinstance(step.data, dict):
                        # 检查是否有LLM生成的响应
                        if step.data.get("llm_response"):
                            final_answer = step.data.get("llm_response")
                            break
                        # 检查是否有summary
                        elif step.data.get("summary"):
                            final_answer = step.data.get("summary")
                            break
            
            # 如果没有找到LLM响应，使用错误消息
            if not final_answer:
                final_answer = f"处理失败: {backend_response.get('message', '未知错误')}"
        
        # 如果仍然没有获取到最终回答，尝试从分析结果中获取 summary
        if not final_answer:
            # 优先从 analysis_result 中获取 summary
            final_answer = analysis_result.get("summary", "")
            
            # 如果仍然没有，尝试从 steps 中获取 summary
            if not final_answer and trace.steps:
                last_step = trace.steps[-1]
                if hasattr(last_step, 'data') and isinstance(last_step.data, dict) and last_step.data.get("summary"):
                    final_answer = last_step.data.get("summary")
            
            # 如果仍然没有，使用默认值
            if not final_answer:
                final_answer = "你好呀，我能帮你些什么呢？（搓手）"
        
        # 标记 trace 为完成
        trace.set_final_answer(final_answer)

        # 异步保存 trace 到数据库
        def save_trace_async():
            try:
                from backend.db.trace_db import save_trace_to_db
                save_trace_to_db(trace.to_dict(), session_id=session_id, user_id=user_id)
            except Exception as db_error:
                if settings.DEBUG:
                    print(f"保存 trace 到数据库失败: {db_error}")

        background_tasks.add_task(save_trace_async)

        # 直接返回结果
        return {
            "success": True,
            "message": final_answer,
            "trace_id": trace.trace_id,
            "session_id": session_id,
            "analysis_result": analysis_result
        }

    except Exception as e:
        if settings.DEBUG:
            print(f"消息处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trace/{trace_id}/status")
async def get_trace_status(trace_id: str):
    """
    获取 trace 状态接口

    根据 trace_id 获取 trace 实时状态和进度
    第一次调用时开始处理消息，分步执行以支持进度条

    Args:
        trace_id: trace ID

    Returns:
        包含 trace 状态和当前步骤的响应
    """
    try:
        from tracing.trace_collector import get_trace
        trace = get_trace(trace_id)
        
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        
        # 检查是否已经开始处理
        if trace.status == "running" and len(trace.steps) == 0:
            # 第一次调用，开始处理消息
            try:
                # 使用已经创建的 analyzer 实例
                from analysis.user_input_analyzer import user_input_analyzer
                
                # 使用用户输入分析器处理消息
                analysis_result = user_input_analyzer.analyze(trace.user_query, trace=trace)
                
                # 从分析结果中获取最终回答
                final_answer = ""
                
                # 首先检查 backend_response 是否成功
                backend_response = analysis_result.get("backend_response", {})
                if backend_response.get("success"):
                    # 如果成功，从 data 中获取 message
                    final_answer = backend_response.get("data", {}).get("message")
                else:
                    # 如果失败，使用错误消息
                    final_answer = f"处理失败: {backend_response.get('message', '未知错误')}"
                
                # 如果仍然没有获取到最终回答，尝试从分析结果中获取 summary
                if not final_answer:
                    # 尝试从 steps 中获取 summary
                    if trace.steps:
                        last_step = trace.steps[-1]
                        if hasattr(last_step, 'data') and isinstance(last_step.data, dict) and last_step.data.get("summary"):
                            final_answer = last_step.data.get("summary")
                    
                    # 如果仍然没有，使用默认值
                    if not final_answer:
                        final_answer = "你好呀，有什么可以帮到你吗？（搓手）"
                
                # 标记 trace 为完成
                trace.set_final_answer(final_answer)
            except Exception as e:
                if settings.DEBUG:
                    print(f"处理消息失败: {e}")
                # 标记 trace 为错误
                trace.set_error(str(e))
        
        # 计算进度
        total_steps = max(6, len(trace.steps) if trace.steps else 6)  # 总步骤数，至少为 6
        current_steps = len(trace.steps)
        progress = min(100, int(current_steps / total_steps * 100))
        
        # 返回当前 trace 状态
        return {
            "success": True,
            "data": trace.to_dict(),
            "is_completed": trace.status in ["success", "error"],
            "progress": progress  # 添加进度信息
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if settings.DEBUG:
            print(f"获取 trace 状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trace/{trace_id}")
async def get_trace(trace_id: str):
    """
    获取 trace 接口

    根据 trace_id 获取 trace 数据

    Args:
        trace_id: Trace ID

    Returns:
        Trace 数据
    """
    try:
        # 从数据库获取 trace 数据
        from app.backend.db.trace_db import get_trace_by_id
        trace_data = get_trace_by_id(trace_id)

        if not trace_data:
            raise HTTPException(status_code=404, detail="Trace not found")

        return {
            "success": True,
            "data": trace_data
        }

    except HTTPException:
        raise
    except Exception as e:
        if settings.DEBUG:
            print(f"获取 trace 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history(page: int = 1, page_size: int = 10, start_time: str = None, end_time: str = None):
    """
    获取历史记录接口

    获取历史对话记录

    Args:
        page: 页码
        page_size: 每页数量
        start_time: 开始时间
        end_time: 结束时间

    Returns:
        历史记录列表
    """
    try:
        # 从数据库获取历史记录
        from app.backend.db.trace_db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 构建查询
        query = "SELECT trace_id, user_input, final_answer, created_at FROM agent_trace"
        params = []

        # 时间范围过滤
        if start_time:
            query += " WHERE created_at >= %s"
            params.append(start_time)
        if end_time:
            if 'WHERE' in query:
                query += " AND created_at <= %s"
            else:
                query += " WHERE created_at <= %s"
            params.append(end_time)

        # 排序和分页
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        offset = (page - 1) * page_size
        params.extend([page_size, offset])

        # 查询历史记录
        cursor.execute(query, params)
        results = cursor.fetchall()

        # 查询总记录数
        count_query = "SELECT COUNT(*) as total FROM agent_trace"
        if 'WHERE' in query:
            count_query += query.split('WHERE')[1].split('ORDER')[0]
        cursor.execute(count_query, params[:-2])  # 移除分页参数

        total = cursor.fetchone()['total']

        cursor.close()
        conn.close()

        return {
            "success": True,
            "data": results,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    except Exception as e:
        if settings.DEBUG:
            print(f"获取历史记录失败: {e}")
        # 提供回退实现，返回空列表
        return {
            "success": True,
            "data": [],
            "total": 0,
            "page": page,
            "page_size": page_size
        }


@app.delete("/api/history/{trace_id}")
async def delete_history(trace_id: str):
    """
    删除历史记录接口

    根据 trace_id 删除历史记录

    Args:
        trace_id: trace ID

    Returns:
        删除结果
    """
    try:
        # 从数据库删除历史记录
        from app.backend.db.trace_db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # 删除步骤记录
        cursor.execute("DELETE FROM agent_trace_step WHERE trace_id = %s", (trace_id,))

        # 删除主记录
        cursor.execute("DELETE FROM agent_trace WHERE trace_id = %s", (trace_id,))

        # 检查是否删除成功
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="历史记录不存在")

        # 提交事务
        conn.commit()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "message": "删除历史记录成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        if settings.DEBUG:
            print(f"删除历史记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/history/session/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话接口

    根据 session_id 删除整个会话的所有记录

    Args:
        session_id: 会话 ID

    Returns:
        删除结果
    """
    try:
        # 从数据库删除会话的所有记录
        from app.backend.db.trace_db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # 先获取该会话的所有 trace_id
        cursor.execute("SELECT trace_id FROM agent_trace WHERE session_id = %s", (session_id,))
        trace_ids = [row[0] for row in cursor.fetchall()]

        if not trace_ids:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="会话不存在")

        # 删除步骤记录
        for trace_id in trace_ids:
            cursor.execute("DELETE FROM agent_trace_step WHERE trace_id = %s", (trace_id,))

        # 删除主记录
        cursor.execute("DELETE FROM agent_trace WHERE session_id = %s", (session_id,))

        # 提交事务
        conn.commit()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "message": "删除会话成功",
            "data": {
                "deleted_count": len(trace_ids)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        if settings.DEBUG:
            print(f"删除会话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/chat/stats")
async def get_chat_stats():
    """
    获取对话统计信息接口

    获取用户的对话统计信息，包括总对话数、成功数和失败数

    Returns:
        对话统计信息
    """
    try:
        # 从数据库获取统计信息
        from app.backend.db.trace_db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 查询总对话数
        cursor.execute("SELECT COUNT(*) as total FROM agent_trace")
        total_result = cursor.fetchone()
        total = total_result.get('total', 0)

        # 查询成功数
        cursor.execute("SELECT COUNT(*) as success FROM agent_trace WHERE status = 'success'")
        success_result = cursor.fetchone()
        success = success_result.get('success', 0)

        # 查询失败数
        cursor.execute("SELECT COUNT(*) as error FROM agent_trace WHERE status = 'error'")
        error_result = cursor.fetchone()
        error = error_result.get('error', 0)

        cursor.close()
        conn.close()

        return {
            "success": True,
            "data": {
                "total": total,
                "success": success,
                "error": error
            }
        }

    except Exception as e:
        if settings.DEBUG:
            print(f"获取对话统计信息失败: {e}")
        # 提供回退实现，返回默认值
        return {
            "success": True,
            "data": {
                "total": 0,
                "success": 0,
                "error": 0
            }
        }


@app.get("/api/history/sessions")
async def get_sessions(page: int = 1, page_size: int = 20):
    """
    获取所有会话列表接口

    获取所有会话列表，按最后一条消息时间排序

    Args:
        page: 页码
        page_size: 每页数量

    Returns:
        会话列表
    """
    try:
        # 从数据库获取会话列表
        from app.backend.db.trace_db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询所有不同的 session 及其最后一条消息信息
        cursor.execute("""
            SELECT 
                t1.session_id,
                t1.user_input as last_user_input,
                t1.final_answer as last_system_response,
                t1.created_at as last_message_time,
                t1.status
            FROM agent_trace t1
            INNER JOIN (
                SELECT session_id, MAX(created_at) as max_created_at
                FROM agent_trace
                WHERE session_id IS NOT NULL AND session_id != ''
                GROUP BY session_id
            ) t2 ON t1.session_id = t2.session_id AND t1.created_at = t2.max_created_at
            WHERE t1.session_id IS NOT NULL AND t1.session_id != ''
            ORDER BY t1.created_at DESC
        """)
        
        all_sessions = cursor.fetchall()
        total = len(all_sessions)
        
        # 分页
        offset = (page - 1) * page_size
        paginated_sessions = all_sessions[offset:offset + page_size]
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "data": {
                "sessions": paginated_sessions,
                "total": total,
                "page": page,
                "page_size": page_size
            },
            "message": "获取会话列表成功"
        }
    except Exception as e:
        if settings.DEBUG:
            print(f"获取会话列表失败: {e}")
        return {
            "success": False,
            "data": None,
            "message": f"获取会话列表失败: {e}"
        }


@app.get("/api/history/{session_id}/session_detail")
async def get_session_detail(session_id: str):
    """
    获取指定会话的完整历史接口

    Args:
        session_id: 会话ID

    Returns:
        会话历史
    """
    try:
        # 从数据库获取会话历史
        from app.backend.db.trace_db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 查询指定 session 的所有 trace，按创建时间升序排列
        cursor.execute("""
            SELECT * FROM agent_trace 
            WHERE session_id = %s 
            ORDER BY created_at ASC
        """, (session_id,))
        
        traces = cursor.fetchall()
        
        # 转换 JSON 字段
        import json
        for trace in traces:
            if trace.get('trace_json'):
                trace['trace_json'] = json.loads(trace['trace_json'])
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "messages": traces,
                "count": len(traces)
            },
            "message": "获取会话历史成功"
        }
    except Exception as e:
        if settings.DEBUG:
            print(f"获取会话历史失败: {e}")
        return {
            "success": False,
            "data": None,
            "message": f"获取会话历史失败: {e}"
        }


@app.get("/api/history/analysis")
async def get_analysis_stats():
    """
    获取数据分析统计数据接口

    Returns:
        数据分析统计数据
    """
    try:
        # 从数据库获取统计信息
        from app.backend.db.trace_db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. 总对话数
        cursor.execute("SELECT COUNT(*) as total FROM agent_trace")
        total_conversations = cursor.fetchone()['total']
        
        # 2. 成功率
        cursor.execute("SELECT COUNT(*) as success_count FROM agent_trace WHERE status = 'success'")
        success_count = cursor.fetchone()['success_count']
        success_rate = (success_count / total_conversations * 100) if total_conversations > 0 else 0
        
        # 3. 平均响应时间（这里使用模拟数据，实际项目中需要从数据库中获取）
        avg_response_time = 856
        
        # 4. 活跃用户数（这里使用模拟数据，实际项目中需要从数据库中获取）
        active_users = 156
        
        # 5. 对话趋势数据（模拟数据）
        trend_data = {
            'labels': ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
            'conversations': [120, 132, 101, 134, 90, 230, 210],
            'success': [110, 120, 91, 124, 85, 220, 200]
        }
        
        # 6. 意图分布数据（模拟数据）
        intent_data = [
            {"value": 1048, "name": "查询配方"},
            {"value": 735, "name": "推荐组合"},
            {"value": 580, "name": "调整风味"},
            {"value": 484, "name": "生成创新"},
            {"value": 300, "name": "其他"}
        ]
        
        # 7. 响应时间分布数据（模拟数据）
        response_time_data = {
            'labels': ['<500ms', '500-1000ms', '1000-2000ms', '2000-3000ms', '>3000ms'],
            'data': [320, 200, 150, 80, 70]
        }
        
        # 8. 实体识别统计数据（模拟数据）
        entity_data = [
            {"value": 256, "name": "酒类"},
            {"value": 189, "name": "水果"},
            {"value": 156, "name": "调味品"},
            {"value": 123, "name": "饮料"},
            {"value": 98, "name": "其他"}
        ]
        
        # 构造响应数据
        data = {
            'totalConversations': total_conversations,
            'successRate': success_rate,
            'avgResponseTime': avg_response_time,
            'activeUsers': active_users,
            'trendData': trend_data,
            'intentData': intent_data,
            'responseTimeData': response_time_data,
            'entityData': entity_data
        }
        
        # 关闭连接
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'data': data,
            'message': '获取数据分析统计数据成功'
        }
    except Exception as e:
        if settings.DEBUG:
            print(f"获取数据分析统计数据失败: {e}")
        return {
            'success': False,
            'data': None,
            'message': f'获取数据分析统计数据失败: {e}'
        }


if __name__ == "__main__":
    try:
        import uvicorn
        print("启动uvicorn服务器...")
        # 从外部运行时，使用正确的模块路径
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=5000,
            reload=settings.DEBUG
        )
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
