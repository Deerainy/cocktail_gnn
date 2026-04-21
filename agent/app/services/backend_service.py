#!/usr/bin/env python3
"""
后端服务模块

实现与后端函数、数据库查询和 Neo4j 接口的连接
"""

import os
import sys
import time
from typing import Dict, Any, List

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入配置
try:
    from config import settings
except ImportError:
    print("警告: 无法导入配置模块，使用默认配置")
    class Settings:
        MYSQL_HOST = "localhost"
        MYSQL_USER = "root"
        MYSQL_PASSWORD = "123456"
        MYSQL_DATABASE = "cocktail_graph"
        NEO4J_URI = "bolt://localhost:7687"
        NEO4J_USER = "neo4j"
        NEO4J_PASSWORD = "Lyx040410"
    settings = Settings()

# 导入数据库连接模块
try:
    from backend.db.mysql import get_mysql_connection
    from backend.db.neo4j import get_neo4j_driver
except ImportError:
    print("警告: 无法导入数据库连接模块，使用模拟实现")
    # 模拟数据库连接
    class MockMySQLConnection:
        def cursor(self):
            return MockCursor()
        def close(self):
            pass
        def commit(self):
            pass
        def rollback(self):
            pass
    
    class MockCursor:
        def execute(self, query, params=None):
            pass
        def fetchall(self):
            return []
        def close(self):
            pass
    
    class MockNeo4jDriver:
        def session(self):
            return MockNeo4jSession()
        def close(self):
            pass
    
    class MockNeo4jSession:
        def run(self, query, **kwargs):
            return MockNeo4jResult()
        def close(self):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()
    
    class MockNeo4jResult:
        def data(self):
            return []
    
    def get_mysql_connection():
        return MockMySQLConnection()
    
    def get_neo4j_driver():
        return MockNeo4jDriver()

class BackendService:
    def __init__(self):
        """初始化后端服务"""
        # 确保日志目录存在
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.neo4j_log_file = os.path.join(self.log_dir, "neo4j_retrieval_log.txt")
        
        # 缓存数据库连接
        self.neo4j_driver = None
        self.mysql_connection = None
        
        # 缓存常用查询结果
        self.substitute_cache = {}
        self.ingredient_neighbors_cache = {}
        self.recipe_cache = {}
    
    def get_neo4j_driver(self):
        """获取 Neo4j 驱动
        
        Returns:
            Neo4j 驱动实例
        """
        # 每次都返回一个新的驱动实例，避免使用已关闭的驱动
        return get_neo4j_driver()
    
    def log_neo4j(self, message: str):
        """记录 Neo4j 相关日志
        
        Args:
            message: 日志消息
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        with open(self.neo4j_log_file, "a", encoding="utf-8") as f:
            f.write(f"{log_message}\n")
    
    def _get_english_name(self, chinese_name: str) -> str:
        """从 MySQL 数据库查询英文名称映射
        
        Args:
            chinese_name: 中文名称
            
        Returns:
            str: 英文名称，如果没有找到则返回原名称
        """
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            
            # 先查询 recipe 表
            cursor.execute(
                "SELECT name FROM recipe WHERE recipe_name_zh = %s LIMIT 1",
                (chinese_name,)
            )
            result = cursor.fetchone()
            
            if not result:
                # 如果 recipe 表中没有，再查询 llm_canonical_map 表
                cursor.execute(
                    "SELECT canonical_name FROM llm_canonical_map WHERE canonical_name_zh = %s LIMIT 1",
                    (chinese_name,)
                )
                result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                english_name = result[0]
                print(f"找到中英文映射: {chinese_name} -> {english_name}")
                self.log_neo4j(f"找到中英文映射: {chinese_name} -> {english_name}")
                return english_name
            else:
                print(f"未找到中英文映射: {chinese_name}")
                self.log_neo4j(f"未找到中英文映射: {chinese_name}")
                return chinese_name
        except Exception as e:
            print(f"查询中英文映射失败: {e}")
            self.log_neo4j(f"查询中英文映射失败: {e}")
            return chinese_name
    
    def _get_chinese_name(self, english_name: str) -> str:
        """从 MySQL 数据库查询中文名称映射
        
        Args:
            english_name: 英文名称
            
        Returns:
            str: 中文名称，如果没有找到则返回原名称
        """
        try:
            conn = get_mysql_connection()
            cursor = conn.cursor()
            
            # 先查询 recipe 表
            cursor.execute(
                "SELECT recipe_name_zh FROM recipe WHERE name = %s LIMIT 1",
                (english_name,)
            )
            result = cursor.fetchone()
            
            if not result:
                # 如果 recipe 表中没有，再查询 llm_canonical_map 表
                cursor.execute(
                    "SELECT canonical_name_zh FROM llm_canonical_map WHERE canonical_name = %s LIMIT 1",
                    (english_name,)
                )
                result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                chinese_name = result[0]
                print(f"找到英文到中文映射: {english_name} -> {chinese_name}")
                self.log_neo4j(f"找到英文到中文映射: {english_name} -> {chinese_name}")
                return chinese_name
            else:
                print(f"未找到英文到中文映射: {english_name}")
                self.log_neo4j(f"未找到英文到中文映射: {english_name}")
                return english_name
        except Exception as e:
            print(f"查询英文到中文映射失败: {e}")
            self.log_neo4j(f"查询英文到中文映射失败: {e}")
            return english_name
    
    def search_recipe(self, recipe_name: str, trace=None) -> Dict[str, Any]:
        """搜索食谱
        
        Args:
            recipe_name: 食谱名称
            trace: trace对象
            
        Returns:
            Dict: 食谱信息
        """
        # 检查缓存
        if recipe_name in self.recipe_cache:
            print(f"从缓存中获取食谱: {recipe_name}")
            return self.recipe_cache[recipe_name]
        
        # 尝试中英文映射
        mapped_recipe_name = self._get_english_name(recipe_name)
        if mapped_recipe_name != recipe_name:
            print(f"使用映射后的食谱名称: {mapped_recipe_name}")
            # 检查映射后的名称是否在缓存中
            if mapped_recipe_name in self.recipe_cache:
                print(f"从缓存中获取映射后的食谱: {mapped_recipe_name}")
                return self.recipe_cache[mapped_recipe_name]
            recipe_name = mapped_recipe_name
        
        print(f"搜索食谱: {recipe_name}")
        self.log_neo4j(f"\n=== Neo4j 食谱搜索 ===")
        self.log_neo4j(f"搜索食谱: {recipe_name}")
        
        # 添加trace步骤
        if trace:
            trace.add_step(
                name="tool_execution",
                title="数据检索",
                status="running",
                data={
                    "tool": "search_recipe",
                    "backend": "neo4j",
                    "params": {"recipe_name": recipe_name}
                }
            )
        
        # 从 Neo4j 数据库搜索食谱
        driver = self.get_neo4j_driver()
        try:
            with driver.session() as session:
                # 搜索食谱节点
                search_query = """
                MATCH (r:Recipe) 
                WHERE r.name =~ '(?i).*' + $recipe_name + '.*' OR r.recipe_name_zh =~ '(?i).*' + $recipe_name + '.*'
                RETURN r LIMIT 1
                """
                self.log_neo4j(f"执行查询: {search_query}")
                search_result = session.run(search_query, recipe_name=recipe_name)
                recipe_node = search_result.data()
                
                if recipe_node:
                    # 构造食谱信息
                    recipe_data = recipe_node[0]["r"]
                    recipe = {
                        "id": recipe_data.get("id"),
                        "name": recipe_data.get("name"),
                        "recipe_name_zh": recipe_data.get("recipe_name_zh"),
                        "description": recipe_data.get("description"),
                        "instructions": recipe_data.get("instructions"),
                        "difficulty": recipe_data.get("difficulty"),
                        "prep_time": recipe_data.get("prep_time"),
                        "cook_time": recipe_data.get("cook_time"),
                        "total_time": recipe_data.get("total_time"),
                        "servings": recipe_data.get("servings")
                    }
                    self.log_neo4j(f"找到食谱: {recipe.get('name')}")
                    self.log_neo4j(f"食谱详情: {recipe}")
                    
                    # 更新trace步骤
                    if trace:
                        trace.add_step(
                            name="tool_execution",
                            title="数据检索",
                            status="success",
                            data={
                                "tool": "search_recipe",
                                "backend": "neo4j",
                                "result_count": 1,
                                "recipe": recipe.get("name")
                            }
                        )
                    
                    result = {"success": True, "data": recipe}
                    # 缓存结果
                    self.recipe_cache[recipe_name] = result
                    return result
                else:
                    self.log_neo4j("未找到食谱")
                    
                    # 更新trace步骤
                    if trace:
                        trace.add_step(
                            name="tool_execution",
                            title="数据检索",
                            status="success",
                            data={
                                "tool": "search_recipe",
                                "backend": "neo4j",
                                "result_count": 0,
                                "message": "未找到食谱"
                            }
                        )
                    
                    result = {"success": False, "message": "食谱未找到"}
                    # 缓存结果
                    self.recipe_cache[recipe_name] = result
                    return result
        except Exception as e:
            error_msg = f"搜索食谱失败: {str(e)}"
            print(error_msg)
            self.log_neo4j(error_msg)
            
            # 更新trace步骤
            if trace:
                trace.add_step(
                    name="tool_execution",
                    title="数据检索",
                    status="error",
                    data={
                        "tool": "search_recipe",
                        "backend": "neo4j",
                        "error": str(e)
                    }
                )
            
            result = {"success": False, "message": f"搜索失败: {str(e)}"}
            # 缓存结果
            self.recipe_cache[recipe_name] = result
            return result
    
    def get_recipe_structure(self, recipe_name: str, trace=None) -> Dict[str, Any]:
        """获取食谱结构
        
        Args:
            recipe_name: 食谱名称
            trace: trace对象
            
        Returns:
            Dict: 食谱结构信息
        """
        print(f"获取食谱结构: {recipe_name}")
        self.log_neo4j(f"\n=== Neo4j 食谱结构查询 ===")
        self.log_neo4j(f"获取食谱结构: {recipe_name}")
        
        # 添加trace步骤
        if trace:
            trace.add_step(
                name="tool_execution",
                title="数据检索",
                status="running",
                data={
                    "tool": "get_recipe_structure",
                    "backend": "neo4j",
                    "params": {"recipe_name": recipe_name}
                }
            )
        
        # 从 Neo4j 数据库获取食谱结构
        driver = get_neo4j_driver()
        try:
            with driver.session() as session:
                # 搜索食谱节点
                search_query = """
                MATCH (r:Recipe) 
                WHERE r.name =~ '(?i).*' + $recipe_name + '.*' OR r.recipe_name_zh =~ '(?i).*' + $recipe_name + '.*'
                RETURN r LIMIT 1
                """
                self.log_neo4j(f"执行查询: {search_query}")
                search_result = session.run(search_query, recipe_name=recipe_name)
                recipe_node = search_result.data()
                
                if not recipe_node:
                    self.log_neo4j("未找到食谱")
                    
                    # 更新trace步骤
                    if trace:
                        trace.add_step(
                            name="tool_execution",
                            title="数据检索",
                            status="success",
                            data={
                                "tool": "get_recipe_structure",
                                "backend": "neo4j",
                                "result_count": 0,
                                "message": "未找到食谱"
                            }
                        )
                    
                    return {"success": False, "message": "食谱未找到"}
                
                # 获取食谱的食材和关系
                structure_query = """
                MATCH (r:Recipe) 
                WHERE r.name =~ '(?i).*' + $recipe_name + '.*' OR r.recipe_name_zh =~ '(?i).*' + $recipe_name + '.*'
                MATCH (r)-[rel:CONTAINS]->(i:Ingredient)
                RETURN r.name as recipe, i.name_norm as ingredient, rel.amount as amount, rel.unit as unit, rel.role as role
                """
                self.log_neo4j(f"执行查询: {structure_query}")
                structure_result = session.run(structure_query, recipe_name=recipe_name)
                ingredients = []
                for record in structure_result.data():
                    ingredients.append({
                        "ingredient": record.get("ingredient"),
                        "amount": record.get("amount"),
                        "unit": record.get("unit"),
                        "role": record.get("role")
                    })
                
                recipe_name = recipe_node[0]["r"].get("name")
                self.log_neo4j(f"找到食谱结构: {recipe_name}, 包含 {len(ingredients)} 个食材")
                self.log_neo4j(f"食材详情: {ingredients}")
                
                # 更新trace步骤
                if trace:
                    trace.add_step(
                        name="tool_execution",
                        title="数据检索",
                        status="success",
                        data={
                            "tool": "get_recipe_structure",
                            "backend": "neo4j",
                            "result_count": len(ingredients),
                            "recipe": recipe_name
                        }
                    )
                
                return {
                    "success": True,
                    "data": {
                        "recipe": recipe_name,
                        "ingredients": ingredients
                    }
                }
        except Exception as e:
            error_msg = f"获取食谱结构失败: {str(e)}"
            print(error_msg)
            self.log_neo4j(error_msg)
            
            # 更新trace步骤
            if trace:
                trace.add_step(
                    name="tool_execution",
                    title="数据检索",
                    status="error",
                    data={
                        "tool": "get_recipe_structure",
                        "backend": "neo4j",
                        "error": str(e)
                    }
                )
            
            return {"success": False, "message": f"获取失败: {str(e)}"}
        finally:
            driver.close()
    
    def get_ingredient_neighbors(self, ingredient_name: str, trace=None) -> Dict[str, Any]:
        """获取食材邻域
        
        Args:
            ingredient_name: 食材名称
            trace: trace对象
            
        Returns:
            Dict: 食材邻域信息
        """
        # 检查缓存
        if ingredient_name in self.ingredient_neighbors_cache:
            print(f"从缓存中获取食材邻域: {ingredient_name}")
            return self.ingredient_neighbors_cache[ingredient_name]
        
        print(f"获取食材邻域: {ingredient_name}")
        self.log_neo4j(f"\n=== Neo4j 食材邻域查询 ===")
        self.log_neo4j(f"获取食材邻域: {ingredient_name}")
        
        # 添加trace步骤
        if trace:
            trace.add_step(
                name="tool_execution",
                title="数据检索",
                status="running",
                data={
                    "tool": "get_ingredient_neighbors",
                    "backend": "neo4j",
                    "params": {"ingredient_name": ingredient_name}
                }
            )
        
        # 从 Neo4j 数据库获取食材邻域
        driver = self.get_neo4j_driver()
        try:
            with driver.session() as session:
                # 搜索食材节点，使用name_norm和canonical_name属性
                search_query = """
                MATCH (i:Ingredient) 
                WHERE i.name_norm =~ '(?i).*' + $ingredient_name + '.*' OR 
                      i.canonical_name =~ '(?i).*' + $ingredient_name + '.*'
                RETURN i LIMIT 1
                """
                self.log_neo4j(f"执行查询: {search_query}")
                search_result = session.run(search_query, ingredient_name=ingredient_name)
                ingredient_node = search_result.data()
                
                if not ingredient_node:
                    self.log_neo4j("未找到食材，尝试查询中英文映射")
                    print("未找到食材，尝试查询中英文映射")
                    
                    # 尝试从 MySQL 查询英文名称
                    english_name = self._get_english_name(ingredient_name)
                    
                    if english_name != ingredient_name:
                        # 使用英文名称再次查询
                        print(f"使用英文名称再次查询: {english_name}")
                        self.log_neo4j(f"使用英文名称再次查询: {english_name}")
                        search_result = session.run(search_query, ingredient_name=english_name)
                        ingredient_node = search_result.data()
                        
                        print(f"英文名称查询结果: {ingredient_node}")
                        self.log_neo4j(f"英文名称查询结果: {ingredient_node}")
                    
                    if not ingredient_node:
                        self.log_neo4j("仍未找到食材")
                        
                        # 更新trace步骤
                        if trace:
                            trace.add_step(
                                name="tool_execution",
                                title="数据检索",
                                status="success",
                                data={
                                    "tool": "get_ingredient_neighbors",
                                    "backend": "neo4j",
                                    "result_count": 0,
                                    "message": "未找到食材"
                                }
                            )
                        
                        result = {"success": False, "message": "食材未找到"}
                        # 缓存结果
                        self.ingredient_neighbors_cache[ingredient_name] = result
                        return result
                
                # 获取食材的实际名称用于后续查询
                actual_ingredient_name = ingredient_node[0]["i"].get("name_norm")
                self.log_neo4j(f"找到食材: {actual_ingredient_name}")
                
                # 获取与该食材邻近的食材
                neighbors_query = """
                MATCH (i:Ingredient) 
                WHERE i.name_norm = $actual_ingredient_name
                MATCH (i)-[rel]-(n:Ingredient)
                RETURN n.name_norm as neighbor_name, type(rel) as relationship_type
                LIMIT 10
                """
                self.log_neo4j(f"执行查询: {neighbors_query}")
                neighbors_result = session.run(neighbors_query, actual_ingredient_name=actual_ingredient_name)
                neighbors = []
                for record in neighbors_result.data():
                    neighbors.append({
                        "neighbor_name": record.get("neighbor_name"),
                        "relationship_type": record.get("relationship_type")
                    })
                
                self.log_neo4j(f"找到食材邻域: {actual_ingredient_name}, 邻近食材: {len(neighbors)} 个")
                self.log_neo4j(f"邻域详情: {neighbors}")
                
                # 更新trace步骤
                if trace:
                    trace.add_step(
                        name="tool_execution",
                        title="数据检索",
                        status="success",
                        data={
                            "tool": "get_ingredient_neighbors",
                            "backend": "neo4j",
                            "result_count": len(neighbors),
                            "ingredient": actual_ingredient_name
                        }
                    )
                
                result = {
                    "success": True,
                    "data": {
                        "ingredient": ingredient_name,
                        "neighbors": neighbors
                    }
                }
                # 缓存结果
                self.ingredient_neighbors_cache[ingredient_name] = result
                return result
        except Exception as e:
            error_msg = f"获取食材邻域失败: {str(e)}"
            print(error_msg)
            self.log_neo4j(error_msg)
            
            # 更新trace步骤
            if trace:
                trace.add_step(
                    name="tool_execution",
                    title="数据检索",
                    status="error",
                    data={
                        "tool": "get_ingredient_neighbors",
                        "backend": "neo4j",
                        "error": str(e)
                    }
                )
            
            result = {"success": False, "message": f"获取失败: {str(e)}"}
            # 缓存结果
            self.ingredient_neighbors_cache[ingredient_name] = result
            return result
        finally:
            driver.close()
    
    def get_substitute(self, ingredient_name: str, trace=None) -> Dict[str, Any]:
        """获取食材替代建议
        
        Args:
            ingredient_name: 食材名称
            trace: trace对象
            
        Returns:
            Dict: 替代建议信息
        """
        # 暂时禁用缓存，确保每次都执行新查询
        # if ingredient_name in self.substitute_cache:
        #     print(f"从缓存中获取替代建议: {ingredient_name}")
        #     return self.substitute_cache[ingredient_name]
        
        print(f"获取食材替代建议: {ingredient_name}")
        self.log_neo4j(f"\n=== Neo4j 食材替代查询 ===")
        self.log_neo4j(f"获取食材替代建议: {ingredient_name}")
        
        # 添加trace步骤
        if trace:
            trace.add_step(
                name="tool_execution",
                title="数据检索",
                status="running",
                data={
                    "tool": "get_substitute",
                    "backend": "neo4j",
                    "params": {"ingredient_name": ingredient_name}
                }
            )
        
        # 从 Neo4j 数据库获取替代建议
        driver = self.get_neo4j_driver()
        try:
            with driver.session() as session:
                # 搜索食材节点，使用name_norm和canonical_name属性
                search_query = """
                MATCH (i:Ingredient) 
                WHERE i.name_norm =~ '(?i).*' + $ingredient_name + '.*' OR 
                      i.canonical_name =~ '(?i).*' + $ingredient_name + '.*'
                RETURN i LIMIT 1
                """
                print(f"执行查询: {search_query}")
                print(f"查询参数: ingredient_name={ingredient_name}")
                self.log_neo4j(f"执行查询: {search_query}")
                self.log_neo4j(f"查询参数: ingredient_name={ingredient_name}")
                search_result = session.run(search_query, ingredient_name=ingredient_name)
                ingredient_node = search_result.data()
                
                print(f"查询结果: {ingredient_node}")
                self.log_neo4j(f"查询结果: {ingredient_node}")
                
                if not ingredient_node:
                    self.log_neo4j("未找到食材，尝试查询中英文映射")
                    print("未找到食材，尝试查询中英文映射")
                    
                    # 尝试从 MySQL 查询英文名称
                    english_name = self._get_english_name(ingredient_name)
                    
                    if english_name != ingredient_name:
                        # 使用英文名称再次查询
                        print(f"使用英文名称再次查询: {english_name}")
                        self.log_neo4j(f"使用英文名称再次查询: {english_name}")
                        search_result = session.run(search_query, ingredient_name=english_name)
                        ingredient_node = search_result.data()
                        
                        print(f"英文名称查询结果: {ingredient_node}")
                        self.log_neo4j(f"英文名称查询结果: {ingredient_node}")
                    
                    # 如果仍未找到，尝试模糊匹配包含该关键词的食材
                    if not ingredient_node:
                        print(f"尝试模糊匹配包含 '{ingredient_name}' 的食材")
                        self.log_neo4j(f"尝试模糊匹配包含 '{ingredient_name}' 的食材")
                        
                        fuzzy_search_query = """
                        MATCH (i:Ingredient) 
                        WHERE i.name_norm =~ '(?i).*' + $ingredient_name + '.*' OR 
                              i.canonical_name =~ '(?i).*' + $ingredient_name + '.*'
                        RETURN i 
                        ORDER BY size(i.name_norm)
                        LIMIT 1
                        """
                        fuzzy_result = session.run(fuzzy_search_query, ingredient_name=ingredient_name)
                        ingredient_node = fuzzy_result.data()
                        
                        print(f"模糊匹配结果: {ingredient_node}")
                        self.log_neo4j(f"模糊匹配结果: {ingredient_node}")
                    
                    if not ingredient_node:
                        self.log_neo4j("仍未找到食材")
                        
                        # 更新trace步骤
                        if trace:
                            trace.add_step(
                                name="tool_execution",
                                title="数据检索",
                                status="success",
                                data={
                                    "tool": "get_substitute",
                                    "backend": "neo4j",
                                    "result_count": 0,
                                    "message": "未找到食材"
                                }
                            )
                        
                        result = {"success": False, "message": "食材未找到"}
                        # 缓存结果
                        self.substitute_cache[ingredient_name] = result
                        return result
                
                # 获取食材的实际名称用于后续查询
                actual_ingredient_name = ingredient_node[0]["i"].get("name_norm")
                print(f"找到食材: {actual_ingredient_name}")
                print(f"食材属性: {ingredient_node[0]["i"]}")
                self.log_neo4j(f"找到食材: {actual_ingredient_name}")
                self.log_neo4j(f"食材属性: {ingredient_node[0]["i"]}")
                
                # 获取与该食材相关的替代食材
                substitute_query = """
                MATCH (i:Ingredient) 
                WHERE i.name_norm = $actual_ingredient_name
                OPTIONAL MATCH (i)-[:MAPS_TO_CANONICAL]->(ci:CanonicalIngredient)
                OPTIONAL MATCH (ci)-[r:GLOBAL_SUBSTITUTE]->(sub:CanonicalIngredient)
                WHERE ci IS NOT NULL AND sub IS NOT NULL
                RETURN sub.canonical_name as substitute_name, 
                       r.best_rank as similarity_score
                ORDER BY r.best_rank ASC
                LIMIT 5
                """
                print(f"执行查询: {substitute_query}")
                print(f"查询参数: actual_ingredient_name={actual_ingredient_name}")
                self.log_neo4j(f"执行查询: {substitute_query}")
                self.log_neo4j(f"查询参数: actual_ingredient_name={actual_ingredient_name}")
                substitute_result = session.run(substitute_query, actual_ingredient_name=actual_ingredient_name)
                substitute_data = substitute_result.data()
                
                print(f"替代建议查询结果: {substitute_data}")
                self.log_neo4j(f"替代建议查询结果: {substitute_data}")
                
                substitutes = []
                for record in substitute_data:
                    substitutes.append({
                        "substitute_name": record.get("substitute_name"),
                        "similarity_score": record.get("similarity_score")
                    })
                
                if substitutes:
                    print(f"找到 {len(substitutes)} 个替代建议")
                    print(f"替代建议: {substitutes}")
                    self.log_neo4j(f"找到 {len(substitutes)} 个替代建议")
                    self.log_neo4j(f"替代建议详情: {substitutes}")
                    
                    # 更新trace步骤
                    if trace:
                        trace.add_step(
                            name="tool_execution",
                            title="数据检索",
                            status="success",
                            data={
                                "tool": "get_substitute",
                                "backend": "neo4j",
                                "result_count": len(substitutes),
                                "ingredient": actual_ingredient_name,
                                "substitutes": substitutes
                            }
                        )
                    
                    result = {
                        "success": True,
                        "data": {
                            "ingredient": ingredient_name,
                            "substitutes": substitutes
                        }
                    }
                    # 缓存结果
                    self.substitute_cache[ingredient_name] = result
                    return result
                else:
                    print("未找到替代建议")
                    self.log_neo4j("未找到替代建议")
                    
                    # 尝试获取所有与该食材相关的关系，看看是否有其他类型的关系
                    relation_query = """
                    MATCH (i:Ingredient) 
                    WHERE i.name_norm = $actual_ingredient_name
                    MATCH (i)-[rel]->(s)
                    RETURN type(rel) as relation_type, s.name_norm as target_name
                    LIMIT 10
                    """
                    print(f"执行查询: {relation_query}")
                    self.log_neo4j(f"执行查询: {relation_query}")
                    relation_result = session.run(relation_query, actual_ingredient_name=actual_ingredient_name)
                    relation_data = relation_result.data()
                    print(f"关系查询结果: {relation_data}")
                    self.log_neo4j(f"关系查询结果: {relation_data}")
                    
                    # 提供默认的替代建议
                    default_substitutes = []
                    if actual_ingredient_name == "lime juice":
                        default_substitutes = [
                            {"substitute_name": "lemon juice", "similarity_score": 0.8},
                            {"substitute_name": "orange juice", "similarity_score": 0.7},
                            {"substitute_name": "grapefruit juice", "similarity_score": 0.6}
                        ]
                    elif actual_ingredient_name == "lemon juice":
                        default_substitutes = [
                            {"substitute_name": "lime juice", "similarity_score": 0.8},
                            {"substitute_name": "orange juice", "similarity_score": 0.7},
                            {"substitute_name": "grapefruit juice", "similarity_score": 0.6}
                        ]
                    elif actual_ingredient_name == "soda water" or actual_ingredient_name == "club soda":
                        default_substitutes = [
                            {"substitute_name": "sparkling water", "similarity_score": 0.9},
                            {"substitute_name": "tonic water", "similarity_score": 0.8},
                            {"substitute_name": "lemon lime soda", "similarity_score": 0.7}
                        ]
                    
                    if default_substitutes:
                        print(f"使用默认替代建议: {default_substitutes}")
                        self.log_neo4j(f"使用默认替代建议: {default_substitutes}")
                        
                        # 更新trace步骤
                        if trace:
                            trace.add_step(
                                name="tool_execution",
                                title="数据检索",
                                status="success",
                                data={
                                    "tool": "get_substitute",
                                    "backend": "neo4j",
                                    "result_count": len(default_substitutes),
                                    "ingredient": actual_ingredient_name,
                                    "substitutes": default_substitutes,
                                    "message": "使用默认替代建议"
                                }
                            )
                        
                        result = {
                            "success": True,
                            "data": {
                                "ingredient": ingredient_name,
                                "substitutes": default_substitutes
                            }
                        }
                        # 缓存结果
                        self.substitute_cache[ingredient_name] = result
                        return result
                    
                    # 更新trace步骤
                    if trace:
                        trace.add_step(
                            name="tool_execution",
                            title="数据检索",
                            status="success",
                            data={
                                "tool": "get_substitute",
                                "backend": "neo4j",
                                "result_count": 0,
                                "message": "未找到替代建议",
                                "relations": relation_data
                            }
                        )
                    
                    result = {"success": False, "message": "未找到替代建议，该食材可能没有设置替代选项"}
                    # 缓存结果
                    self.substitute_cache[ingredient_name] = result
                    return result
        except Exception as e:
            error_msg = f"获取替代建议失败: {str(e)}"
            print(error_msg)
            self.log_neo4j(error_msg)
            
            # 更新trace步骤
            if trace:
                trace.add_step(
                    name="tool_execution",
                    title="数据检索",
                    status="error",
                    data={
                        "tool": "get_substitute",
                        "backend": "neo4j",
                        "error": str(e)
                    }
                )
            
            result = {"success": False, "message": f"获取失败: {str(e)}"}
            # 缓存结果
            self.substitute_cache[ingredient_name] = result
            return result
        finally:
            driver.close()
    
    def general_response(self, message: str, trace=None) -> Dict[str, Any]:
        """生成通用响应
        
        Args:
            message: 输入消息
            trace: trace对象
            
        Returns:
            Dict: 通用响应信息
        """
        print(f"生成通用响应: {message}")
        self.log_neo4j(f"\n=== 通用响应 ===")
        self.log_neo4j(f"生成通用响应: {message}")
        
        # 添加trace步骤
        if trace:
            trace.add_step(
                name="tool_execution",
                title="数据检索",
                status="running",
                data={
                    "tool": "general_response",
                    "backend": "local",
                    "params": {"message": message}
                }
            )
        
        # 生成通用响应
        response = {
            "success": True,
            "data": {
                "message": message,
                "suggestions": [
                    "您可以搜索食谱，例如：'找一下 Margarita 的配方'",
                    "您可以查询食谱结构，例如：'Margarita 的配方结构是什么样的'",
                    "您可以查询食材邻域，例如：'lime 的邻域有什么食材'",
                    "您可以获取替代建议，例如：'龙舌兰酒可以换成什么'"
                ]
            }
        }
        
        # 更新trace步骤
        if trace:
            trace.add_step(
                name="tool_execution",
                title="数据检索",
                status="success",
                data={
                    "tool": "general_response",
                    "backend": "local",
                    "result_count": 1
                }
            )
        
        self.log_neo4j("生成通用响应完成")
        return response

# 创建全局后端服务实例
backend_service = BackendService()
