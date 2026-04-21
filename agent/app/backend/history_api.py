#!/usr/bin/env python3
"""
历史记录 API 服务

提供历史记录的查询、详情和删除功能
"""

from flask import Flask, request, jsonify
import mysql.connector
import json
from datetime import datetime

app = Flask(__name__)

# 导入配置
from app.config import settings

# 数据库连接配置
DB_CONFIG = {
    'host': settings.MYSQL_HOST,
    'user': settings.MYSQL_USER,
    'password': settings.MYSQL_PASSWORD,
    'database': settings.MYSQL_DATABASE,
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    return mysql.connector.connect(**DB_CONFIG)


@app.route('/api/history', methods=['GET'])
def get_history():
    """获取历史记录列表"""
    try:
        # 获取查询参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')

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

        return jsonify({
            'success': True,
            'data': data,
            'message': '获取历史记录成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': None,
            'message': f'获取历史记录失败: {str(e)}'
        }), 500


@app.route('/api/history/<trace_id>', methods=['GET'])
def get_history_detail(trace_id):
    """获取历史记录详情"""
    try:
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 查询主记录
        cursor.execute("SELECT * FROM agent_trace WHERE trace_id = %s", (trace_id,))
        trace = cursor.fetchone()

        if not trace:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'data': None,
                'message': '历史记录不存在'
            }), 404

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

        return jsonify({
            'success': True,
            'data': data,
            'message': '获取历史记录详情成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': None,
            'message': f'获取历史记录详情失败: {str(e)}'
        }), 500


@app.route('/api/history/<trace_id>', methods=['DELETE'])
def delete_history(trace_id):
    """删除历史记录"""
    try:
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
            return jsonify({
                'success': False,
                'data': None,
                'message': '历史记录不存在'
            }), 404

        # 提交事务
        conn.commit()

        # 关闭连接
        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': None,
            'message': '删除历史记录成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': None,
            'message': f'删除历史记录失败: {str(e)}'
        }), 500


@app.route('/api/history/sessions', methods=['GET'])
def get_sessions():
    """获取所有会话列表（按最后一条消息时间排序）"""
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

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

        offset = (page - 1) * page_size
        paginated_sessions = all_sessions[offset:offset + page_size]

        cursor.close()
        conn.close()

        return jsonify({
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
        return jsonify({
            'success': False,
            'data': None,
            'message': f'获取会话列表失败: {str(e)}'
        }), 500


@app.route('/api/history/<session_id>/session_detail', methods=['GET'])
def get_session_detail(session_id):
    """获取指定 session_id 的完整对话历史"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM agent_trace
            WHERE session_id = %s
            ORDER BY created_at ASC
        """, (session_id,))

        traces = cursor.fetchall()

        for trace in traces:
            if trace.get('trace_json'):
                trace['trace_json'] = json.loads(trace['trace_json'])

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id,
                'messages': traces,
                'count': len(traces)
            },
            'message': '获取会话历史成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'data': None,
            'message': f'获取会话历史失败: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
