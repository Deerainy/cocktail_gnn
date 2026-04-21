#!/usr/bin/env python3
"""
审核任务管理模块

实现审核任务的创建、查询和处理功能
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Any, List

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入配置
from app.config import settings

# 导入数据库连接模块
try:
    from backend.db.mysql import get_mysql_connection
except ImportError:
    print("警告: 无法导入数据库连接模块，使用模拟实现")
    # 模拟数据库连接
    class MockMySQLConnection:
        def cursor(self):
            return MockCursor()
        def close(self):
            pass
    
    class MockCursor:
        def execute(self, query, params=None):
            print(f"执行查询: {query}")
            if params:
                print(f"参数: {params}")
        def fetchall(self):
            return []
        def close(self):
            pass
    
    def get_mysql_connection():
        return MockMySQLConnection()

class ReviewManager:
    def __init__(self):
        """初始化审核任务管理器"""
        pass
    
    def create_review_task(self, text: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建审核任务
        
        Args:
            text: 原始文本
            entities: 需要审核的实体列表
            
        Returns:
            Dict: 审核任务信息
        """
        print(f"创建审核任务，文本: {text}")
        
        # 生成审核任务ID
        review_id = str(uuid.uuid4())
        
        # 连接数据库
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            
            # 插入审核任务
            task_query = """
            INSERT INTO review_tasks (review_id, original_text, status, processing_level, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            now = datetime.now()
            cursor.execute(task_query, (
                review_id,
                text,
                'pending',
                'llm_analysis',
                now,
                now
            ))
            
            # 插入审核实体
            for entity in entities:
                if entity.get("processing_level") in ["llm_analysis", "unrecognized", "fallback"]:
                    entity_id = str(uuid.uuid4())
                    entity_query = """
                    INSERT INTO review_entities (
                        review_id, entity_id, text, label, start_pos, end_pos, 
                        processing_level, confidence, context
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(entity_query, (
                        review_id,
                        entity_id,
                        entity.get("text"),
                        entity.get("label"),
                        entity.get("start"),
                        entity.get("end"),
                        entity.get("processing_level"),
                        entity.get("confidence", 0.0),
                        text
                    ))
                    
                    # 插入候选实体（如果有）
                    if "candidates" in entity:
                        for candidate in entity["candidates"]:
                            candidate_query = """
                            INSERT INTO candidates (
                                review_entity_id, text, label, confidence, source
                            ) VALUES (%s, %s, %s, %s, %s)
                            """
                            # 获取刚插入的 review_entity_id
                            cursor.execute("SELECT LAST_INSERT_ID()")
                            review_entity_id = cursor.fetchone()[0]
                            
                            cursor.execute(candidate_query, (
                                review_entity_id,
                                candidate.get("text"),
                                candidate.get("label"),
                                candidate.get("confidence", 0.0),
                                candidate.get("source", "LLM")
                            ))
            
            # 提交事务
            conn.commit()
            
            return {
                "success": True,
                "review_id": review_id,
                "message": f"审核任务创建成功，ID: {review_id}"
            }
        except Exception as e:
            print(f"创建审核任务失败: {str(e)}")
            conn.rollback()
            return {
                "success": False,
                "message": f"创建审核任务失败: {str(e)}"
            }
        finally:
            conn.close()
    
    def get_review_tasks(self, status: str = None, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """获取审核任务列表
        
        Args:
            status: 任务状态 (pending, processed)
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            Dict: 审核任务列表
        """
        print(f"获取审核任务列表，状态: {status}, 限制: {limit}, 偏移: {offset}")
        
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            
            # 构建查询
            query = "SELECT review_id, original_text, status, processing_level, created_at FROM review_tasks"
            params = []
            
            if status:
                query += " WHERE status = %s"
                params.append(status)
            
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            tasks = []
            for row in cursor.fetchall():
                tasks.append({
                    "review_id": row[0],
                    "original_text": row[1],
                    "status": row[2],
                    "processing_level": row[3],
                    "created_at": row[4]
                })
            
            # 获取总数
            count_query = "SELECT COUNT(*) FROM review_tasks"
            if status:
                count_query += " WHERE status = %s"
            
            cursor.execute(count_query, params[:1] if status else [])
            total = cursor.fetchone()[0]
            
            return {
                "success": True,
                "total": total,
                "tasks": tasks
            }
        except Exception as e:
            print(f"获取审核任务列表失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取审核任务列表失败: {str(e)}"
            }
        finally:
            conn.close()
    
    def get_review_task(self, review_id: str) -> Dict[str, Any]:
        """获取审核任务详情
        
        Args:
            review_id: 审核任务ID
            
        Returns:
            Dict: 审核任务详情
        """
        print(f"获取审核任务详情，ID: {review_id}")
        
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            
            # 获取任务基本信息
            task_query = """
            SELECT review_id, original_text, status, processing_level, created_at
            FROM review_tasks
            WHERE review_id = %s
            """
            cursor.execute(task_query, (review_id,))
            task_row = cursor.fetchone()
            
            if not task_row:
                return {
                    "success": False,
                    "message": "审核任务不存在"
                }
            
            task = {
                "review_id": task_row[0],
                "original_text": task_row[1],
                "status": task_row[2],
                "processing_level": task_row[3],
                "created_at": task_row[4],
                "entities": []
            }
            
            # 获取审核实体
            entity_query = """
            SELECT entity_id, text, label, start_pos, end_pos, processing_level, confidence, context
            FROM review_entities
            WHERE review_id = %s
            """
            cursor.execute(entity_query, (review_id,))
            for entity_row in cursor.fetchall():
                entity = {
                    "entity_id": entity_row[0],
                    "text": entity_row[1],
                    "label": entity_row[2],
                    "start": entity_row[3],
                    "end": entity_row[4],
                    "processing_level": entity_row[5],
                    "confidence": entity_row[6],
                    "context": entity_row[7],
                    "candidates": []
                }
                
                # 获取候选实体
                candidate_query = """
                SELECT text, label, confidence, source
                FROM candidates
                WHERE review_entity_id = %s
                """
                # 这里需要获取 review_entity_id，暂时使用占位符
                # 实际实现中需要调整
                candidate_query = """
                SELECT c.text, c.label, c.confidence, c.source
                FROM candidates c
                JOIN review_entities re ON c.review_entity_id = re.review_entity_id
                WHERE re.review_id = %s AND re.entity_id = %s
                """
                cursor.execute(candidate_query, (review_id, entity["entity_id"]))
                for candidate_row in cursor.fetchall():
                    entity["candidates"].append({
                        "text": candidate_row[0],
                        "label": candidate_row[1],
                        "confidence": candidate_row[2],
                        "source": candidate_row[3]
                    })
                
                task["entities"].append(entity)
            
            return {
                "success": True,
                "data": task
            }
        except Exception as e:
            print(f"获取审核任务详情失败: {str(e)}")
            return {
                "success": False,
                "message": f"获取审核任务详情失败: {str(e)}"
            }
        finally:
            conn.close()
    
    def submit_review_result(self, review_id: str, entity_id: str, original_text: str, 
                            approved_candidate: Dict[str, Any], add_as_alias: bool = False) -> Dict[str, Any]:
        """提交审核结果
        
        Args:
            review_id: 审核任务ID
            entity_id: 实体ID
            original_text: 原始文本
            approved_candidate: 批准的候选实体
            add_as_alias: 是否添加为别名
            
        Returns:
            Dict: 审核结果处理信息
        """
        print(f"提交审核结果，任务ID: {review_id}, 实体ID: {entity_id}")
        
        conn = get_mysql_connection()
        try:
            cursor = conn.cursor()
            
            # 插入审核结果
            result_query = """
            INSERT INTO review_results (
                review_id, entity_id, original_text, approved_candidate_text, 
                approved_candidate_label, add_as_alias, action, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            action = "add_alias" if add_as_alias else "update_entity"
            cursor.execute(result_query, (
                review_id,
                entity_id,
                original_text,
                approved_candidate.get("text"),
                approved_candidate.get("label"),
                add_as_alias,
                action,
                datetime.now()
            ))
            
            # 如果需要添加为别名
            if add_as_alias:
                # 查找对应的实体ID
                entity_query = "SELECT entity_id FROM entities WHERE name = %s"
                cursor.execute(entity_query, (approved_candidate.get("text"),))
                result = cursor.fetchone()
                
                if result:
                    target_entity_id = result[0]
                    # 插入别名
                    alias_query = "INSERT INTO aliases (entity_id, alias_name, created_at) VALUES (%s, %s, %s)"
                    cursor.execute(alias_query, (
                        target_entity_id,
                        original_text,
                        datetime.now()
                    ))
            
            # 更新审核任务状态
            update_query = "UPDATE review_tasks SET status = %s, updated_at = %s WHERE review_id = %s"
            cursor.execute(update_query, ("processed", datetime.now(), review_id))
            
            # 提交事务
            conn.commit()
            
            return {
                "success": True,
                "message": "审核结果提交成功",
                "data": {
                    "review_id": review_id,
                    "entity_id": entity_id,
                    "action": action,
                    "alias": original_text if add_as_alias else None,
                    "canonical_id": approved_candidate.get("entity_id"),
                    "canonical_name": approved_candidate.get("text")
                }
            }
        except Exception as e:
            print(f"提交审核结果失败: {str(e)}")
            conn.rollback()
            return {
                "success": False,
                "message": f"提交审核结果失败: {str(e)}"
            }
        finally:
            conn.close()

# 创建全局审核任务管理器实例
review_manager = ReviewManager()
