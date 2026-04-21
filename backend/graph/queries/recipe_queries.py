"""
食谱相关的 Cypher 查询
"""

from typing import List, Dict, Optional, Any


class RecipeQueries:
    """
    食谱相关的 Cypher 查询
    """

    @staticmethod
    def get_recipe_subgraph_query(recipe_id: str) -> str:
        """
        获取食谱子图的 Cypher 查询
        Args:
            recipe_id: 食谱 ID
        Returns: Cypher 查询语句
        """
        return """
        MATCH (r:Recipe)
        WHERE r.recipe_id = $recipe_id OR r.recipe_id = toInteger($recipe_id)
        OPTIONAL MATCH (r)-[ru:USES]->(i:Ingredient)
        OPTIONAL MATCH (i)-[im:MAPS_TO_CANONICAL]->(ci:CanonicalIngredient)
        OPTIONAL MATCH (r)-[rci:USES_CANONICAL]->(ci2:CanonicalIngredient)
        OPTIONAL MATCH (ci3:CanonicalIngredient)<-[:USES_CANONICAL]-(r)-[:USES_CANONICAL]->(ci4:CanonicalIngredient)
        OPTIONAL MATCH (ci3)-[rel:CO_OCCUR|FLAVOR_SIM|FLAVOR_COMPAT]->(ci4)
        RETURN r.recipe_id, r.name, 
               i.name_norm, 
               ci.canonical_id, ci.canonical_name, 
               ci2.canonical_id, ci2.canonical_name, 
               ci3.canonical_id, ci3.canonical_name, 
               ci4.canonical_id, ci4.canonical_name, 
               type(rel) as relationship_type
        """



    @staticmethod
    def get_recipe_basic_info_query(recipe_id: str) -> str:
        """
        获取食谱基本信息的 Cypher 查询
        Args:
            recipe_id: 食谱 ID
        Returns: Cypher 查询语句
        """
        return """
        MATCH (r:Recipe)
        WHERE r.recipe_id = $recipe_id OR r.recipe_id = toInteger($recipe_id)
        RETURN r.recipe_id, r.name
        """


    @staticmethod
    def get_recipe_ingredients_query(recipe_id: str) -> str:
        """
        获取食谱食材的 Cypher 查询
        Args:
            recipe_id: 食谱 ID
        Returns: Cypher 查询语句
        """
        return """
        MATCH (r:Recipe)
        WHERE r.recipe_id = $recipe_id OR r.recipe_id = toInteger($recipe_id)
        MATCH (r)-[ru:USES]->(i:Ingredient)
        RETURN i.name_norm
        """


    @staticmethod
    def get_recipe_canonicals_query(recipe_id: str) -> str:
        """
        获取食谱规范食材的 Cypher 查询
        Args:
            recipe_id: 食谱 ID
        Returns: Cypher 查询语句
        """
        return """
        MATCH (r:Recipe)
        WHERE r.recipe_id = $recipe_id OR r.recipe_id = toInteger($recipe_id)
        MATCH (r)-[rci:USES_CANONICAL]->(ci:CanonicalIngredient)
        RETURN ci.canonical_id, ci.canonical_name
        """



    @staticmethod
    def get_recipe_substitute_results_query(recipe_id: str) -> str:
        """
        获取食谱替代结果的 Cypher 查询
        Args:
            recipe_id: 食谱 ID
        Returns: Cypher 查询语句
        """
        return """
        MATCH (r:Recipe)
        WHERE r.recipe_id = $recipe_id OR r.recipe_id = toInteger($recipe_id)
        OPTIONAL MATCH (r)-[hr:HAS_SUBSTITUTE_RESULT]->(sr:SubstituteResult)
        OPTIONAL MATCH (sr)-[tr:TARGET]->(t:CanonicalIngredient)
        OPTIONAL MATCH (sr)-[cr:CANDIDATE]->(c:CanonicalIngredient)
        RETURN r.recipe_id, r.name, 
               properties(sr) as substitute_result, 
               t.canonical_id, t.canonical_name as target_ingredient, 
               c.canonical_id, c.canonical_name as candidate_ingredient
        """



    @staticmethod
    def search_recipe_by_name_query(keyword: str) -> str:
        """
        根据名称搜索食谱的 Cypher 查询
        Args:
            keyword: 搜索关键词
        Returns: Cypher 查询语句
        """
        return """
        MATCH (r:Recipe)
        WHERE LOWER(r.name) CONTAINS LOWER($keyword)
        RETURN r
        LIMIT 20
        """

