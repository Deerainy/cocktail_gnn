from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import mysql.connector
import json
from datetime import datetime

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'cocktail_graph',
    'charset': 'utf8mb4',
    'ssl_disabled': True
}

def get_db_connection():
    """获取数据库连接"""
    return mysql.connector.connect(**DB_CONFIG)


class HistoryViewSet(viewsets.ViewSet):
    permission_classes = []
    def list(self, request):
        """获取历史记录列表"""
        try:
            # 获取查询参数
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 10))
            start_time = request.query_params.get('start_time')
            end_time = request.query_params.get('end_time')

            # 连接数据库
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # 构建查询
            query = "SELECT * FROM agent_trace"
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

            # 按创建时间倒序
            query += " ORDER BY created_at DESC"

            # 获取总数
            count_query = "SELECT COUNT(*) as total FROM agent_trace"
            if 'WHERE' in query:
                count_query += query.split('WHERE')[1].split('ORDER')[0]
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            # 分页
            offset = (page - 1) * page_size
            query += " LIMIT %s OFFSET %s"
            params.extend([page_size, offset])

            # 执行查询
            cursor.execute(query, params)
            results = cursor.fetchall()

            # 转换JSON字段
            for result in results:
                if result.get('trace_json'):
                    result['trace_json'] = json.loads(result['trace_json'])

            # 构造响应数据
            data = {
                'list': results,
                'total': total,
                'page': page,
                'page_size': page_size
            }

            # 关闭连接
            cursor.close()
            conn.close()

            return Response({
                'success': True,
                'data': data,
                'message': '获取历史记录成功'
            })
        except Exception as e:
            return Response({
                'success': False,
                'data': None,
                'message': f'获取历史记录失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, pk=None):
        """获取历史记录详情"""
        try:
            # 获取trace_id
            trace_id = pk

            # 连接数据库
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # 查询主记录
            cursor.execute("SELECT * FROM agent_trace WHERE trace_id = %s", (trace_id,))
            trace = cursor.fetchone()

            if not trace:
                cursor.close()
                conn.close()
                return Response({
                    'success': False,
                    'data': None,
                    'message': '历史记录不存在'
                }, status=status.HTTP_404_NOT_FOUND)

            # 转换JSON字段
            if trace.get('trace_json'):
                trace['trace_json'] = json.loads(trace['trace_json'])

            # 查询步骤记录
            cursor.execute("SELECT * FROM agent_trace_step WHERE trace_id = %s ORDER BY step_no ASC", (trace_id,))
            steps = cursor.fetchall()

            # 转换JSON字段
            for step in steps:
                if step.get('data_json'):
                    step['data_json'] = json.loads(step['data_json'])

            # 构造响应数据
            data = {
                **trace,
                'steps': steps
            }

            # 关闭连接
            cursor.close()
            conn.close()

            return Response({
                'success': True,
                'data': data,
                'message': '获取历史记录详情成功'
            })
        except Exception as e:
            return Response({
                'success': False,
                'data': None,
                'message': f'获取历史记录详情失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, pk=None):
        """删除历史记录"""
        try:
            # 获取trace_id
            trace_id = pk

            # 连接数据库
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
                return Response({
                    'success': False,
                    'data': None,
                    'message': '历史记录不存在'
                }, status=status.HTTP_404_NOT_FOUND)

            # 提交事务
            conn.commit()

            # 关闭连接
            cursor.close()
            conn.close()

            return Response({
                'success': True,
                'data': None,
                'message': '删除历史记录成功'
            })
        except Exception as e:
            return Response({
                'success': False,
                'data': None,
                'message': f'删除历史记录失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def sessions(self, request):
        """获取所有会话列表（按最后一条消息时间排序）"""
        try:
            # 获取查询参数
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            
            # 连接数据库
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
            
            return Response({
                'success': True,
                'data': {
                    'sessions': paginated_sessions,
                    'total': total,
                    'page': page,
                    'page_size': page_size
                },
                'message': '获取会话列表成功'
            })
        except Exception as e:
            return Response({
                'success': False,
                'data': None,
                'message': f'获取会话列表失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def session_detail(self, request, pk=None):
        """获取指定 session_id 的完整对话历史"""
        try:
            session_id = pk
            # 连接数据库
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
            for trace in traces:
                if trace.get('trace_json'):
                    trace['trace_json'] = json.loads(trace['trace_json'])
            
            # 关闭连接
            cursor.close()
            conn.close()
            
            return Response({
                'success': True,
                'data': {
                    'session_id': session_id,
                    'messages': traces,
                    'count': len(traces)
                },
                'message': '获取会话历史成功'
            })
        except Exception as e:
            return Response({
                'success': False,
                'data': None,
                'message': f'获取会话历史失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def analysis(self, request):
        """获取数据分析统计数据"""
        try:
            # 连接数据库
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
            
            return Response({
                'success': True,
                'data': data,
                'message': '获取数据分析统计数据成功'
            })
        except Exception as e:
            return Response({
                'success': False,
                'data': None,
                'message': f'获取数据分析统计数据失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
