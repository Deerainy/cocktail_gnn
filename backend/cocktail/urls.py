from django.urls import path
from .views_recipe import (
    RecipeDetailView, RecipeIngredientsView, RecipeSqeView, 
    RecipeBalanceView, RecipeKeyNodesView, RecipeGraphView, 
    RecipeSubstitutesView, RecipeListView
)

urlpatterns = [
    path('api/recipes', RecipeListView.as_view(), name='recipe-list'),
    path('api/recipes/<str:recipe_id>', RecipeDetailView.as_view(), name='recipe-detail'),
    path('api/recipes/<str:recipe_id>/ingredients', RecipeIngredientsView.as_view(), name='recipe-ingredients'),
    path('api/recipes/<str:recipe_id>/sqe', RecipeSqeView.as_view(), name='recipe-sqe'),
    path('api/recipes/<str:recipe_id>/balance', RecipeBalanceView.as_view(), name='recipe-balance'),
    path('api/recipes/<str:recipe_id>/key-nodes', RecipeKeyNodesView.as_view(), name='recipe-key-nodes'),
    path('api/recipes/<str:recipe_id>/graph', RecipeGraphView.as_view(), name='recipe-graph'),
    path('api/recipes/<str:recipe_id>/substitutes', RecipeSubstitutesView.as_view(), name='recipe-substitutes'),
]
