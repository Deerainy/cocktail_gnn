from rest_framework import serializers
from .models_recipe import (
    Recipe, RecipeIngredient, Ingredient, IngredientFlavorAnchor, 
    IngredientFlavorFeature, SqeRecipeScore, RecipeBalanceFeature, 
    SqeNodeImportance, GraphEdgeStatsV2, GraphFlavorEdgeStats, 
    GraphFlavorCompatEdgeStats, RecipeSubstituteResult, LlmCanonicalMap
)

class RecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = [
            'recipe_id', 'source', 'source_recipe_key', 'name', 'recipe_name_zh', 'instructions',
            'glass', 'tags', 'image_url', 'is_alcoholic', 'created_at', 'updated_at'
        ]

class FlavorFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientFlavorFeature
        fields = ['sour', 'sweet', 'bitter', 'aroma', 'fruity', 'body']

class IngredientSerializer(serializers.ModelSerializer):
    canonical_id = serializers.SerializerMethodField()
    canonical_name = serializers.SerializerMethodField()
    canonical_name_zh = serializers.SerializerMethodField()
    anchor_name = serializers.SerializerMethodField()
    anchor_form = serializers.SerializerMethodField()
    flavor_feature = serializers.SerializerMethodField()

    def get_canonical_id(self, obj):
        # 尝试从llm_canonical_map中获取映射
        try:
            src_ingredient_id = int(obj.ingredient_id)
            mapping = LlmCanonicalMap.objects.filter(src_ingredient_id=src_ingredient_id, status='ok').first()
            if mapping:
                return str(mapping.canonical_id)
        except:
            pass
        #  fallback到原有的llm_canonical_id
        return obj.llm_canonical_id

    def get_canonical_name(self, obj):
        # 尝试从llm_canonical_map中获取映射
        try:
            src_ingredient_id = int(obj.ingredient_id)
            mapping = LlmCanonicalMap.objects.filter(src_ingredient_id=src_ingredient_id, status='ok').first()
            if mapping:
                return mapping.canonical_name
        except:
            pass
        #  fallback到IngredientFlavorAnchor
        anchor = IngredientFlavorAnchor.objects.filter(ingredient_id=obj.ingredient_id).first()
        return anchor.canonical_name if anchor else None

    def get_canonical_name_zh(self, obj):
        # 尝试从llm_canonical_map中获取映射
        try:
            src_ingredient_id = int(obj.ingredient_id)
            mapping = LlmCanonicalMap.objects.filter(src_ingredient_id=src_ingredient_id, status='ok').first()
            if mapping:
                return mapping.canonical_name_zh
        except:
            pass
        return None

    def get_anchor_name(self, obj):
        anchor = IngredientFlavorAnchor.objects.filter(ingredient_id=obj.ingredient_id).first()
        return anchor.anchor_name if anchor else None

    def get_anchor_form(self, obj):
        anchor = IngredientFlavorAnchor.objects.filter(ingredient_id=obj.ingredient_id).first()
        return anchor.anchor_form if anchor else None

    def get_flavor_feature(self, obj):
        feature = IngredientFlavorFeature.objects.filter(ingredient_id=obj.ingredient_id).first()
        if feature:
            return FlavorFeatureSerializer(feature).data
        return None

    class Meta:
        model = Ingredient
        fields = [
            'ingredient_id', 'name_norm', 'canonical_id', 'canonical_name', 'canonical_name_zh',
            'category', 'abv', 'is_alcoholic', 'anchor_name', 'anchor_form', 'flavor_feature'
        ]

class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = serializers.SerializerMethodField()

    def get_ingredient(self, obj):
        ingredient = Ingredient.objects.filter(ingredient_id=obj.ingredient_id).first()
        if ingredient:
            return IngredientSerializer(ingredient).data
        return None

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient_id', 'line_no', 'amount', 'unit', 'role', 'raw_text', 'ingredient']

class SqeRecipeScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = SqeRecipeScore
        fields = [
            'snapshot_id', 'param_version', 'model_version',
            'phaseA_synergy_raw', 'phaseA_conflict_raw', 'phaseA_balance_raw',
            'phaseA_synergy_norm', 'phaseA_conflict_norm', 'phaseA_balance_norm',
            'phaseA_total', 'phaseB_synergy_score', 'phaseB_conflict_score',
            'phaseB_balance_score', 'phaseB_total', 'phaseC_residual',
            'phaseC_pred_score', 'phaseC_margin', 'phaseC_confidence',
            'final_sqe_total', 'rank_in_snapshot', 'is_valid', 'note'
        ]

class RecipeBalanceFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeBalanceFeature
        fields = [
            'snapshot_id', 'family', 'f_sour', 'f_sweet', 'f_bitter',
            'f_aroma', 'f_fruity', 'f_body', 'r_base', 'r_acid',
            'r_sweetener', 'r_modifier', 'r_bitters', 'r_garnish',
            'r_dilution', 'r_other', 'flavor_dist', 'role_dist',
            'flavor_balance_score', 'role_balance_score', 'final_balance_score'
        ]

class SqeNodeImportanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SqeNodeImportance
        fields = [
            'canonical_id', 'ingredient_name', 'role', 'amount_unit',
            'base_score', 'learned_contribution', 'normalized_contribution',
            'contribution_ratio', 'is_key_node', 'rank_no', 'explanation'
        ]

class NodeSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    role = serializers.CharField()
    is_key_node = serializers.BooleanField()
    contribution_ratio = serializers.FloatField()

class EdgeSerializer(serializers.Serializer):
    source = serializers.CharField()
    target = serializers.CharField()
    type = serializers.CharField()
    weight = serializers.FloatField()
    extra = serializers.DictField()

class GraphSerializer(serializers.Serializer):
    nodes = NodeSerializer(many=True)
    edges = EdgeSerializer(many=True)

class RecipeSubstituteResultSerializer(serializers.ModelSerializer):
    candidate_name = serializers.SerializerMethodField()
    score_breakdown = serializers.SerializerMethodField()

    def get_candidate_name(self, obj):
        anchor = IngredientFlavorAnchor.objects.filter(canonical_id=obj.candidate_canonical_id).first()
        return anchor.canonical_name if anchor else obj.candidate_canonical_id

    def get_score_breakdown(self, obj):
        return {
            'old_sqe_total': obj.old_sqe_total,
            'new_sqe_total': obj.new_sqe_total,
            'delta_sqe': obj.delta_sqe,
            'old_synergy_score': obj.old_synergy_score,
            'new_synergy_score': obj.new_synergy_score,
            'delta_synergy': obj.delta_synergy,
            'old_conflict_score': obj.old_conflict_score,
            'new_conflict_score': obj.new_conflict_score,
            'delta_conflict': obj.delta_conflict,
            'old_balance_score': obj.old_balance_score,
            'new_balance_score': obj.new_balance_score,
            'delta_balance': obj.delta_balance
        }

    class Meta:
        model = RecipeSubstituteResult
        fields = [
            'candidate_canonical_id', 'candidate_name', 'target_role',
            'candidate_role', 'delta_sqe', 'accept_flag', 'rank_no',
            'reason_code', 'explanation', 'score_breakdown'
        ]
