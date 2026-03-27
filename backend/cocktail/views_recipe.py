from rest_framework.views import APIView
from rest_framework.response import Response
from .models_recipe import (
    Recipe, RecipeIngredient, SqeRecipeScore, RecipeBalanceFeature, 
    SqeNodeImportance, GraphEdgeStatsV2, GraphFlavorEdgeStats, 
    GraphFlavorCompatEdgeStats, RecipeSubstituteResult, Ingredient, IngredientFlavorAnchor
)
from .serializers_recipe import (
    RecipeSerializer, SqeRecipeScoreSerializer,
    RecipeBalanceFeatureSerializer, SqeNodeImportanceSerializer, 
    RecipeSubstituteResultSerializer, IngredientSerializer
)

class RecipeDetailView(APIView):
    def get(self, request, recipe_id):
        try:
            recipe = Recipe.objects.get(recipe_id=recipe_id)
            serializer = RecipeSerializer(recipe)
            return Response({
                "code": 0,
                "message": "ok",
                "data": serializer.data
            })
        except Recipe.DoesNotExist:
            return Response({
                "code": 404,
                "message": "recipe not found",
                "data": None
            })

class RecipeIngredientsView(APIView):
    def get(self, request, recipe_id):
        try:
            # 检查配方是否存在
            recipe = Recipe.objects.get(recipe_id=recipe_id)
            # 使用values()方法指定查询字段，避免查询id字段
            ingredients = RecipeIngredient.objects.filter(recipe_id=recipe_id).values(
                'recipe_id', 'ingredient_id', 'line_no', 'amount', 'unit', 'role', 'raw_text', 'created_at'
            )
            # 手动构建响应数据
            result = []
            for ing in ingredients:
                # 获取原料详情
                ingredient = Ingredient.objects.filter(ingredient_id=ing['ingredient_id']).first()
                ing_data = {
                    'ingredient_id': ing['ingredient_id'],
                    'line_no': ing['line_no'],
                    'amount': ing['amount'],
                    'unit': ing['unit'],
                    'role': ing['role'],
                    'raw_text': ing['raw_text'],
                    'ingredient': None
                }
                if ingredient:
                    # 序列化原料数据
                    ing_data['ingredient'] = IngredientSerializer(ingredient).data
                result.append(ing_data)
            return Response({
                "code": 0,
                "message": "ok",
                "data": result
            })
        except Recipe.DoesNotExist:
            return Response({
                "code": 404,
                "message": "recipe not found",
                "data": None
            })
        except Exception as e:
            return Response({
                "code": 500,
                "message": str(e),
                "data": None
            })

class RecipeSqeView(APIView):
    def get(self, request, recipe_id):
        try:
            # 检查配方是否存在
            recipe = Recipe.objects.get(recipe_id=recipe_id)
            sqe_score = SqeRecipeScore.objects.filter(recipe_id=recipe_id).order_by('-created_at').first()
            if sqe_score:
                serializer = SqeRecipeScoreSerializer(sqe_score)
                return Response({
                    "code": 0,
                    "message": "ok",
                    "data": serializer.data
                })
            else:
                return Response({
                    "code": 404,
                    "message": "sqe score not found",
                    "data": None
                })
        except Recipe.DoesNotExist:
            return Response({
                "code": 404,
                "message": "recipe not found",
                "data": None
            })

class RecipeBalanceView(APIView):
    def get(self, request, recipe_id):
        try:
            # 检查配方是否存在
            recipe = Recipe.objects.get(recipe_id=recipe_id)
            balance_feature = RecipeBalanceFeature.objects.filter(recipe_id=recipe_id).order_by('-computed_at').first()
            if balance_feature:
                serializer = RecipeBalanceFeatureSerializer(balance_feature)
                return Response({
                    "code": 0,
                    "message": "ok",
                    "data": serializer.data
                })
            else:
                return Response({
                    "code": 404,
                    "message": "balance feature not found",
                    "data": None
                })
        except Recipe.DoesNotExist:
            return Response({
                "code": 404,
                "message": "recipe not found",
                "data": None
            })

class RecipeKeyNodesView(APIView):
    def get(self, request, recipe_id):
        try:
            # 检查配方是否存在
            recipe = Recipe.objects.get(recipe_id=recipe_id)
            key_nodes = SqeNodeImportance.objects.filter(recipe_id=recipe_id, is_key_node=True).order_by('rank_no')
            serializer = SqeNodeImportanceSerializer(key_nodes, many=True)
            return Response({
                "code": 0,
                "message": "ok",
                "data": serializer.data
            })
        except Recipe.DoesNotExist:
            return Response({
                "code": 404,
                "message": "recipe not found",
                "data": None
            })

class RecipeGraphView(APIView):
    def get(self, request, recipe_id):
        try:
            # 检查配方是否存在
            recipe = Recipe.objects.get(recipe_id=recipe_id)
            
            # 获取配方的原料节点
            recipe_ingredients = RecipeIngredient.objects.filter(recipe_id=recipe_id)
            ingredient_ids = [ri.ingredient_id for ri in recipe_ingredients]
            
            # 获取canonical_id映射
            canonical_map = {}
            for ingredient_id in ingredient_ids:
                anchor = IngredientFlavorAnchor.objects.filter(ingredient_id=ingredient_id).first()
                if anchor:
                    canonical_map[ingredient_id] = anchor.canonical_id
            
            # 构建节点列表
            nodes = []
            for ri in recipe_ingredients:
                anchor = IngredientFlavorAnchor.objects.filter(ingredient_id=ri.ingredient_id).first()
                node_importance = SqeNodeImportance.objects.filter(
                    recipe_id=recipe_id,
                    canonical_id=canonical_map.get(ri.ingredient_id)
                ).first()
                
                node = {
                    "id": canonical_map.get(ri.ingredient_id, ri.ingredient_id),
                    "label": anchor.canonical_name if anchor else ri.ingredient_id,
                    "role": ri.role,
                    "is_key_node": node_importance.is_key_node if node_importance else False,
                    "contribution_ratio": node_importance.contribution_ratio if node_importance else 0.0
                }
                nodes.append(node)
            
            # 构建边列表
            edges = []
            layer = request.query_params.get('layer', 'compat')
            
            # 获取所有唯一的canonical_id对
            canonical_ids = list(canonical_map.values())
            for i in range(len(canonical_ids)):
                for j in range(i + 1, len(canonical_ids)):
                    if layer == 'cooccur' or layer == 'mixed':
                        # 共现边
                        edge = GraphEdgeStatsV2.objects.filter(
                            i_id=canonical_ids[i],
                            j_id=canonical_ids[j]
                        ).first()
                        if edge:
                            edges.append({
                                "source": canonical_ids[i],
                                "target": canonical_ids[j],
                                "type": "cooccur",
                                "weight": edge.weight,
                                "extra": {
                                    "co_count": edge.co_count,
                                    "pmi": edge.pmi
                                }
                            })
                    
                    if layer == 'flavor' or layer == 'mixed':
                        # 风味相似边
                        edge = GraphFlavorEdgeStats.objects.filter(
                            i_id=canonical_ids[i],
                            j_id=canonical_ids[j]
                        ).first()
                        if edge:
                            edges.append({
                                "source": canonical_ids[i],
                                "target": canonical_ids[j],
                                "type": "flavor",
                                "weight": edge.weight,
                                "extra": {
                                    "sim_cosine": edge.sim_cosine,
                                    "dist_l2": edge.dist_l2
                                }
                            })
                    
                    if layer == 'compat' or layer == 'mixed':
                        # 兼容边
                        edge = GraphFlavorCompatEdgeStats.objects.filter(
                            i_canonical_id=canonical_ids[i],
                            j_canonical_id=canonical_ids[j]
                        ).first()
                        if edge:
                            edges.append({
                                "source": canonical_ids[i],
                                "target": canonical_ids[j],
                                "type": "compat",
                                "weight": edge.weight,
                                "extra": {
                                    "compat_score": edge.compat_score,
                                    "role_bonus": edge.role_bonus,
                                    "taste_complement_score": edge.taste_complement_score
                                }
                            })
            
            # 序列化结果
            graph_data = {
                "nodes": nodes,
                "edges": edges
            }
            
            return Response({
                "code": 0,
                "message": "ok",
                "data": graph_data
            })
        except Recipe.DoesNotExist:
            return Response({
                "code": 404,
                "message": "recipe not found",
                "data": None
            })

class RecipeSubstitutesView(APIView):
    def get(self, request, recipe_id):
        try:
            # 检查配方是否存在
            recipe = Recipe.objects.get(recipe_id=recipe_id)
            target_canonical_id = request.query_params.get('target_canonical_id')
            
            if not target_canonical_id:
                return Response({
                    "code": 400,
                    "message": "target_canonical_id is required",
                    "data": None
                })
            
            substitutes = RecipeSubstituteResult.objects.filter(
                recipe_id=recipe_id,
                target_canonical_id=target_canonical_id
            ).order_by('rank_no')
            
            serializer = RecipeSubstituteResultSerializer(substitutes, many=True)
            return Response({
                "code": 0,
                "message": "ok",
                "data": serializer.data
            })
        except Recipe.DoesNotExist:
            return Response({
                "code": 404,
                "message": "recipe not found",
                "data": None
            })


class RecipeListView(APIView):
    def get(self, request):
        try:
            # 获取所有配方
            recipes = Recipe.objects.all()
            serializer = RecipeSerializer(recipes, many=True)
            return Response({
                "code": 0,
                "message": "ok",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "code": 500,
                "message": str(e),
                "data": None
            })