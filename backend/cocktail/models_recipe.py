from django.db import models

class Recipe(models.Model):
    recipe_id = models.CharField(primary_key=True, max_length=100)
    source = models.CharField(max_length=100)
    source_recipe_key = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    instructions = models.TextField()
    glass = models.CharField(max_length=100)
    tags = models.JSONField()
    image_url = models.URLField()
    is_alcoholic = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipe'

class Ingredient(models.Model):
    ingredient_id = models.CharField(primary_key=True, max_length=100)
    name_norm = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    abv = models.FloatField(null=True)
    is_alcoholic = models.BooleanField()
    notes = models.TextField(null=True)
    llm_canonical_id = models.CharField(max_length=100, null=True)

    class Meta:
        db_table = 'ingredient'

class LlmCanonicalMap(models.Model):
    src_ingredient_id = models.IntegerField()
    src_name_norm = models.CharField(max_length=255)
    canonical_id = models.IntegerField()
    canonical_name = models.CharField(max_length=255)
    confidence = models.FloatField()
    provider = models.CharField(max_length=100)
    model = models.CharField(max_length=100, null=True)
    rationale = models.TextField(null=True)
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    src_image_path = models.CharField(max_length=500, null=True)

    class Meta:
        db_table = 'llm_canonical_map'

class RecipeIngredient(models.Model):
    id = models.AutoField(primary_key=True)
    recipe_id = models.CharField(max_length=100)
    ingredient_id = models.CharField(max_length=100)
    line_no = models.IntegerField()
    amount = models.FloatField()
    unit = models.CharField(max_length=50)
    role = models.CharField(max_length=100)
    raw_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recipe_ingredient'
        unique_together = ('recipe_id', 'ingredient_id')

class IngredientFlavorAnchor(models.Model):
    ingredient_id = models.CharField(max_length=100)
    ingredient_name = models.CharField(max_length=255)
    canonical_id = models.CharField(max_length=100)
    canonical_name = models.CharField(max_length=255)
    anchor_name = models.CharField(max_length=255)
    anchor_form = models.CharField(max_length=100)
    anchor_source = models.CharField(max_length=100)
    match_confidence = models.FloatField()
    is_direct_match = models.BooleanField()
    review_status = models.CharField(max_length=50)
    notes = models.TextField(null=True)

    class Meta:
        db_table = 'ingredient_flavor_anchor'

class IngredientFlavorFeature(models.Model):
    ingredient_id = models.CharField(max_length=100)
    anchor_name = models.CharField(max_length=255)
    sour = models.FloatField()
    sweet = models.FloatField()
    bitter = models.FloatField()
    aroma = models.FloatField()
    fruity = models.FloatField()
    body = models.FloatField()
    feature_source = models.CharField(max_length=100)
    feature_confidence = models.FloatField()
    derivation_method = models.CharField(max_length=100)
    review_status = models.CharField(max_length=50)
    notes = models.TextField(null=True)

    class Meta:
        db_table = 'ingredient_flavor_feature'

class CanonicalFreqV2(models.Model):
    snapshot_id = models.CharField(max_length=100)
    canonical_id = models.CharField(max_length=100)
    freq = models.IntegerField()
    computed_at = models.DateTimeField()
    method_note = models.TextField()

    class Meta:
        db_table = 'canonical_freq_v2'

class RecipeBalanceFeature(models.Model):
    id = models.AutoField(primary_key=True)
    recipe_id = models.CharField(max_length=100)
    snapshot_id = models.CharField(max_length=100)
    family = models.CharField(max_length=100)
    f_sour = models.FloatField()
    f_sweet = models.FloatField()
    f_bitter = models.FloatField()
    f_aroma = models.FloatField()
    f_fruity = models.FloatField()
    f_body = models.FloatField()
    r_base = models.FloatField()
    r_acid = models.FloatField()
    r_sweetener = models.FloatField()
    r_modifier = models.FloatField()
    r_bitters = models.FloatField()
    r_garnish = models.FloatField()
    r_dilution = models.FloatField()
    r_other = models.FloatField()
    flavor_dist = models.FloatField()
    role_dist = models.FloatField()
    flavor_balance_score = models.FloatField()
    role_balance_score = models.FloatField()
    final_balance_score = models.FloatField()
    computed_at = models.DateTimeField()

    class Meta:
        db_table = 'recipe_balance_feature'

class SqeRecipeScore(models.Model):
    snapshot_id = models.CharField(max_length=100)
    recipe_id = models.CharField(max_length=100)
    param_version = models.CharField(max_length=100)
    model_version = models.CharField(max_length=100)
    phaseA_synergy_raw = models.FloatField()
    phaseA_conflict_raw = models.FloatField()
    phaseA_balance_raw = models.FloatField()
    phaseA_synergy_norm = models.FloatField()
    phaseA_conflict_norm = models.FloatField()
    phaseA_balance_norm = models.FloatField()
    phaseA_total = models.FloatField()
    phaseB_synergy_score = models.FloatField()
    phaseB_conflict_score = models.FloatField()
    phaseB_balance_score = models.FloatField()
    phaseB_total = models.FloatField()
    phaseC_residual = models.FloatField()
    phaseC_pred_score = models.FloatField()
    phaseC_margin = models.FloatField()
    phaseC_confidence = models.FloatField()
    final_sqe_total = models.FloatField()
    rank_in_snapshot = models.IntegerField()
    is_valid = models.BooleanField()
    note = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sqe_recipe_score'

class SqeNodeImportance(models.Model):
    snapshot_id = models.CharField(max_length=100)
    recipe_id = models.CharField(max_length=100)
    model_version = models.CharField(max_length=100)
    embedding_version = models.CharField(max_length=100)
    param_version = models.CharField(max_length=100)
    canonical_id = models.CharField(max_length=100)
    ingredient_name = models.CharField(max_length=255)
    role = models.CharField(max_length=100)
    amount_unit = models.CharField(max_length=100)
    order_no = models.IntegerField()
    base_score = models.FloatField()
    learned_contribution = models.FloatField()
    normalized_contribution = models.FloatField()
    contribution_ratio = models.FloatField()
    residual_effect = models.FloatField()
    attention_weight = models.FloatField()
    degree_value = models.FloatField()
    neighbor_count = models.IntegerField()
    synergy_contrib = models.FloatField()
    conflict_contrib = models.FloatField()
    balance_contrib = models.FloatField()
    rank_no = models.IntegerField()
    is_key_node = models.BooleanField()
    threshold_flag = models.CharField(max_length=50)
    node_embedding_json = models.JSONField()
    explanation = models.TextField()
    note = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sqe_node_importance'

class GraphEdgeStatsV2(models.Model):
    snapshot_id = models.CharField(max_length=100)
    i_id = models.CharField(max_length=100)
    j_id = models.CharField(max_length=100)
    co_count = models.IntegerField()
    pmi = models.FloatField()
    weight = models.FloatField()
    computed_at = models.DateTimeField()
    weight_method = models.CharField(max_length=100)

    class Meta:
        db_table = 'graph_edge_stats_v2'

class GraphFlavorEdgeStats(models.Model):
    snapshot_id = models.CharField(max_length=100)
    i_id = models.CharField(max_length=100)
    j_id = models.CharField(max_length=100)
    sim_cosine = models.FloatField()
    dist_l2 = models.FloatField()
    weight = models.FloatField()
    weight_method = models.CharField(max_length=100)
    computed_at = models.DateTimeField()
    is_exact_match = models.BooleanField()

    class Meta:
        db_table = 'graph_flavor_edge_stats'

class GraphFlavorCompatEdgeStats(models.Model):
    snapshot_id = models.CharField(max_length=100)
    i_canonical_id = models.CharField(max_length=100)
    j_canonical_id = models.CharField(max_length=100)
    compat_score = models.FloatField()
    role_bonus = models.FloatField()
    taste_complement_score = models.FloatField()
    anchor_bonus = models.FloatField()
    cooccur_bonus = models.FloatField()
    penalty_score = models.FloatField()
    weight = models.FloatField()
    weight_method = models.CharField(max_length=100)
    rule_version = models.CharField(max_length=100)
    note = models.TextField(null=True)
    computed_at = models.DateTimeField()

    class Meta:
        db_table = 'graph_flavor_compat_edge_stats'

class RecipeSubstituteResult(models.Model):
    snapshot_id = models.CharField(max_length=100)
    recipe_id = models.CharField(max_length=100)
    target_canonical_id = models.CharField(max_length=100)
    candidate_canonical_id = models.CharField(max_length=100)
    target_role = models.CharField(max_length=100)
    candidate_role = models.CharField(max_length=100)
    old_sqe_total = models.FloatField()
    new_sqe_total = models.FloatField()
    delta_sqe = models.FloatField()
    old_synergy_score = models.FloatField()
    new_synergy_score = models.FloatField()
    delta_synergy = models.FloatField()
    old_conflict_score = models.FloatField()
    new_conflict_score = models.FloatField()
    delta_conflict = models.FloatField()
    old_balance_score = models.FloatField()
    new_balance_score = models.FloatField()
    delta_balance = models.FloatField()
    accept_flag = models.BooleanField()
    rank_no = models.IntegerField()
    reason_code = models.CharField(max_length=100)
    explanation = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipe_substitute_result'
