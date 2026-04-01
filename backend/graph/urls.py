"""
Graph API 路由配置
"""

from django.urls import path
from .views import (
    RecipeSubgraphView,
    GlobalSubstitutesView,
    RecipeSubstituteResultsView,
    CanonicalNeighborsView,
    RecipeBasicInfoView,
    RecipeIngredientsView,
    RecipeCanonicalsView,
    CanonicalBasicInfoView,
    SearchRecipeView,
    SearchCanonicalView,
    TestNeo4jConnectionView
)

urlpatterns = [
    # 核心工具接口
    path('recipe/subgraph/<str:recipe_id>/', RecipeSubgraphView.as_view(), name='recipe_subgraph'),
    path('canonical/substitutes/<str:canonical_id>/', GlobalSubstitutesView.as_view(), name='global_substitutes'),
    path('recipe/substitute-results/<str:recipe_id>/', RecipeSubstituteResultsView.as_view(), name='recipe_substitute_results'),
    path('canonical/neighbors/<str:canonical_id>/', CanonicalNeighborsView.as_view(), name='canonical_neighbors'),
    
    # 辅助接口
    path('recipe/basic/<str:recipe_id>/', RecipeBasicInfoView.as_view(), name='recipe_basic_info'),
    path('recipe/ingredients/<str:recipe_id>/', RecipeIngredientsView.as_view(), name='recipe_ingredients'),
    path('recipe/canonicals/<str:recipe_id>/', RecipeCanonicalsView.as_view(), name='recipe_canonicals'),
    path('canonical/basic/<str:canonical_id>/', CanonicalBasicInfoView.as_view(), name='canonical_basic_info'),
    path('search/recipe/', SearchRecipeView.as_view(), name='search_recipe'),
    path('search/canonical/', SearchCanonicalView.as_view(), name='search_canonical'),
    path('test-neo4j-connection/', TestNeo4jConnectionView.as_view(), name='test_neo4j_connection'),
]
