#!/usr/bin/env python3
"""
Trace数据库模块

用于处理trace数据的数据库操作
"""

import mysql.connector
from mysql.connector import errors
import json
from typing import Dict, Any, List
from datetime import datetime

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
    try:
        # 尝试连接数据库
        return mysql.connector.connect(**DB_CONFIG)
    except errors.ProgrammingError as e:
        raise

def create_trace_tables():
    """创建trace相关的表结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 创建agent_trace表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_trace (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            trace_id VARCHAR(64) NOT NULL UNIQUE,
            session_id VARCHAR(64),
            user_input TEXT NOT NULL,
            normalized_input TEXT,
            language VARCHAR(16),
            intent_name VARCHAR(64),
            intent_source VARCHAR(32),
            action_name VARCHAR(64),
            backend_type VARCHAR(32),
            status VARCHAR(16) NOT NULL DEFAULT 'success',
            final_answer TEXT,
            error_message TEXT,
            trace_json JSON NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_trace_session (session_id),
            INDEX idx_trace_intent (intent_name),
            INDEX idx_trace_status (status),
            INDEX idx_trace_created (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        # 创建agent_trace_step表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_trace_step (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            trace_id VARCHAR(64) NOT NULL,
            step_no INT NOT NULL,
            step_name VARCHAR(64) NOT NULL,
            step_title VARCHAR(64),
            status VARCHAR(16) NOT NULL DEFAULT 'success',
            data_json JSON,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_step_trace (trace_id),
            INDEX idx_step_name (step_name),
            INDEX idx_step_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ''')
        
        conn.commit()
        print("Trace tables created successfully!")
    except Exception as e:
        print(f"Error creating trace tables: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def save_user_trace_map(user_id, trace_id):
    """保存用户与trace的对应关系到user_trace_map表
    
    Args:
        user_id: 用户ID
        trace_id: trace的唯一标识
    
    Returns:
        bool: 是否保存成功
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 保存到user_trace_map表
        cursor.execute('''
        INSERT INTO user_trace_map (user_id, trace_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            user_id = VALUES(user_id),
            trace_id = VALUES(trace_id)
        ''', (user_id, trace_id))
        
        conn.commit()
        print(f"User trace map saved successfully! user_id: {user_id}, trace_id: {trace_id}")
        return True
    except Exception as e:
        print(f"Error saving user trace map: {str(e)}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def save_trace_to_db(trace, session_id: str = None, user_id: int = None):
    """保存trace数据到数据库
    
    Args:
        trace: trace对象或字典
        session_id: 会话ID
        user_id: 用户ID
    
    Returns:
        bool: 是否保存成功
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查trace是否是对象，如果是，转换为字典
        if hasattr(trace, 'to_dict'):
            trace_data = trace.to_dict()
        else:
            trace_data = trace
        
        # 提取trace信息
        trace_id = trace_data.get('trace_id')
        user_query = trace_data.get('user_query')
        created_at = trace_data.get('created_at')
        steps = trace_data.get('steps', [])
        
        # 提取session_id，如果传入了session_id，则使用传入的，否则从trace_data中获取
        if session_id is None:
            session_id = trace_data.get('session_id')
        
        # 提取额外信息
        language = None
        intent_name = None
        intent_source = None
        action_name = None
        backend_type = None
        status = 'success'
        final_answer = None
        error_message = None
        
        # 从步骤中提取信息
        for step in steps:
            step_name = step.get('name')
            step_data = step.get('data', {})
            
            if step_name == 'input_analysis':
                language = step_data.get('language')
            elif step_name == 'intent_classification':
                intent_name = step_data.get('intent')
                intent_source = step_data.get('router')
            elif step_name == 'action_planning':
                action_name = step_data.get('action')
            elif step_name == 'tool_execution':
                backend_type = step_data.get('backend')
                if step.get('status') == 'error':
                    status = 'error'
                    error_message = step_data.get('message')
            elif step_name == 'answer_generation':
                final_answer = step_data.get('summary')
        
        # 保存到agent_trace表（使用ON DUPLICATE KEY UPDATE避免重复键错误）
        cursor.execute('''
        INSERT INTO agent_trace (
            trace_id, session_id, user_input, normalized_input, 
            language, intent_name, intent_source, action_name, 
            backend_type, status, final_answer, error_message, trace_json
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            session_id = VALUES(session_id),
            user_input = VALUES(user_input),
            normalized_input = VALUES(normalized_input),
            language = VALUES(language),
            intent_name = VALUES(intent_name),
            intent_source = VALUES(intent_source),
            action_name = VALUES(action_name),
            backend_type = VALUES(backend_type),
            status = VALUES(status),
            final_answer = VALUES(final_answer),
            error_message = VALUES(error_message),
            trace_json = VALUES(trace_json)
        ''', (
            trace_id, session_id, user_query, user_query,  # normalized_input暂时使用user_query
            language, intent_name, intent_source, action_name,
            backend_type, status, final_answer, error_message, json.dumps(trace_data, ensure_ascii=False)
        ))
        
        # 先删除现有的步骤记录，避免重复
        cursor.execute('DELETE FROM agent_trace_step WHERE trace_id = %s', (trace_id,))
        
        # 保存到agent_trace_step表
        for step in steps:
            step_no = step.get('step')
            step_name = step.get('name')
            step_title = step.get('title')
            step_status = step.get('status')
            step_data = step.get('data', {})
            
            cursor.execute('''
            INSERT INTO agent_trace_step (
                trace_id, step_no, step_name, step_title, status, data_json
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                trace_id, step_no, step_name, step_title, step_status, json.dumps(step_data, ensure_ascii=False)
            ))
        
        # 如果提供了user_id，保存用户与trace的对应关系
        if user_id is not None:
            save_user_trace_map(user_id, trace_id)
        
        conn.commit()
        print(f"Trace {trace_id} saved to database successfully!")
        return True
    except Exception as e:
        print(f"Error saving trace to database: {str(e)}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_trace_by_id(trace_id: str) -> Dict[str, Any]:
    """根据trace_id获取trace数据
    
    Args:
        trace_id: trace的唯一标识
    
    Returns:
        Dict: trace数据字典
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute('''
        SELECT * FROM agent_trace WHERE trace_id = %s
        ''', (trace_id,))
        
        result = cursor.fetchone()
        if result:
            # 转换JSON字段
            if result.get('trace_json'):
                result['trace_json'] = json.loads(result['trace_json'])
            return result
        return None
    except Exception as e:
        print(f"Error getting trace by id: {str(e)}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_trace_steps(trace_id: str) -> List[Dict[str, Any]]:
    """获取trace的所有步骤
    
    Args:
        trace_id: trace的唯一标识
    
    Returns:
        List[Dict]: 步骤列表
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute('''
        SELECT * FROM agent_trace_step 
        WHERE trace_id = %s 
        ORDER BY step_no ASC
        ''', (trace_id,))
        
        results = cursor.fetchall()
        # 转换JSON字段
        for result in results:
            if result.get('data_json'):
                result['data_json'] = json.loads(result['data_json'])
        return results
    except Exception as e:
        print(f"Error getting trace steps: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # 创建表结构
    create_trace_tables()
    print("Trace database module initialized successfully!")
