"""
Graph API 接口层

提供与 Neo4j 图数据库交互的 REST API 接口
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.recipe_service import RecipeService
from .services.substitute_service import SubstituteService
from .services.canonical_service import CanonicalService
from neomodel import db
from django.http import JsonResponse
class TestNeo4jConnectionView(APIView):
    """
    测试 Neo4j 连接
    """
    def get(self, request):
        try:
            # 执行 Cypher 查询，这里简单查询所有节点
            results, meta = db.cypher_query("MATCH (n) RETURN n LIMIT 10")
            data = []
            for record in results:
                node = record[0]
                node_data = dict(node.items())
                data.append(node_data)
            return JsonResponse({'data': data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)





class RecipeSubgraphView(APIView):
    """
    获取食谱子图
    """
    def get(self, request, recipe_id):
        try:
            result = RecipeService.get_recipe_subgraph(recipe_id)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GlobalSubstitutesView(APIView):
    """
    获取全局替代候选
    """
    def get(self, request, canonical_id):
        try:
            top_k = int(request.query_params.get('top_k', 10))
            result = SubstituteService.get_global_substitutes(canonical_id, top_k)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecipeSubstituteResultsView(APIView):
    """
    获取食谱替代结果
    """
    def get(self, request, recipe_id):
        try:
            result = RecipeService.get_recipe_substitute_results(recipe_id)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CanonicalNeighborsView(APIView):
    """
    获取规范食材邻域
    """
    def get(self, request, canonical_id):
        try:
            limit = int(request.query_params.get('limit', 20))
            result = CanonicalService.get_canonical_neighbors(canonical_id, limit)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecipeBasicInfoView(APIView):
    """
    获取食谱基本信息
    """
    def get(self, request, recipe_id):
        try:
            result = RecipeService.get_recipe_basic_info(recipe_id)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecipeIngredientsView(APIView):
    """
    获取食谱食材
    """
    def get(self, request, recipe_id):
        try:
            result = RecipeService.get_recipe_ingredients(recipe_id)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RecipeCanonicalsView(APIView):
    """
    获取食谱规范食材
    """
    def get(self, request, recipe_id):
        try:
            result = RecipeService.get_recipe_canonicals(recipe_id)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CanonicalBasicInfoView(APIView):
    """
    获取规范食材基本信息
    """
    def get(self, request, canonical_id):
        try:
            result = CanonicalService.get_canonical_basic_info(canonical_id)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchRecipeView(APIView):
    """
    根据名称搜索食谱
    """
    def get(self, request):
        try:
            keyword = request.query_params.get('keyword', '')
            result = RecipeService.search_recipe_by_name(keyword)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SearchCanonicalView(APIView):
    """
    根据名称搜索规范食材
    """
    def get(self, request):
        try:
            keyword = request.query_params.get('keyword', '')
            result = CanonicalService.search_canonical_by_name(keyword)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
