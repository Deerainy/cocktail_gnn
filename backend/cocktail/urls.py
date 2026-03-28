from django.urls import path
from .views_recipe import (
    RecipeDetailView, RecipeIngredientsView, RecipeSqeView, 
    RecipeBalanceView, RecipeKeyNodesView, RecipeGraphView, 
    RecipeSubstitutesView, RecipeListView
)
from .views_flavor_graph import (
    FlavorGraphView, FlavorNodeDetailView, FlavorEdgeDetailView, FlavorGraphStatsView
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
    path('api/flavor-graph/graph', FlavorGraphView.as_view(), name='flavor-graph'),
    path('api/flavor-graph/nodes/<str:node_id>', FlavorNodeDetailView.as_view(), name='flavor-node-detail'),
    path('api/flavor-graph/edges/detail', FlavorEdgeDetailView.as_view(), name='flavor-edge-detail'),
    path('api/flavor-graph/stats', FlavorGraphStatsView.as_view(), name='flavor-graph-stats'),
]
