from rest_framework import serializers
from .models_recipe import (
    CanonicalFreqV2, IngredientFlavorAnchor, IngredientFlavorFeature,
    SqeNodeImportance, GraphEdgeStatsV2, GraphFlavorEdgeStats,
    GraphFlavorCompatEdgeStats, LlmCanonicalMap
)


class FlavorGraphNodeSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    label_zh = serializers.CharField(allow_null=True)
    ingredient_type = serializers.CharField(allow_null=True)
    role = serializers.CharField(allow_null=True)
    freq = serializers.IntegerField(allow_null=True)
    importance_score = serializers.FloatField(allow_null=True)
    anchor_name = serializers.CharField(allow_null=True)
    is_key_node = serializers.BooleanField(allow_null=True)


class FlavorGraphEdgeSerializer(serializers.Serializer):
    source = serializers.CharField()
    target = serializers.CharField()
    type = serializers.CharField()
    weight = serializers.FloatField()


class FlavorNodeDetailSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    label_zh = serializers.CharField(allow_null=True)
    ingredient_type = serializers.CharField(allow_null=True)
    role = serializers.CharField(allow_null=True)
    freq = serializers.IntegerField(allow_null=True)
    importance_score = serializers.FloatField(allow_null=True)
    is_key_node = serializers.BooleanField(allow_null=True)
    
    anchor = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    top_neighbors = serializers.SerializerMethodField()
    summary = serializers.CharField(allow_null=True)
    
    def get_anchor(self, obj):
        anchor = IngredientFlavorAnchor.objects.filter(canonical_id=obj['id']).first()
        if anchor:
            return {
                'anchor_name': anchor.anchor_name,
                'anchor_source': anchor.anchor_source,
                'match_confidence': anchor.match_confidence
            }
        return None
    
    def get_features(self, obj):
        feature = IngredientFlavorFeature.objects.filter(anchor_name=obj.get('anchor_name')).first()
        if feature:
            return {
                'sour': feature.sour,
                'sweet': feature.sweet,
                'bitter': feature.bitter,
                'aroma': feature.aroma,
                'fruity': feature.fruity,
                'body': feature.body
            }
        return None
    
    def get_top_neighbors(self, obj):
        node_id = obj['id']
        neighbors = GraphFlavorCompatEdgeStats.objects.filter(
            i_canonical_id=node_id
        ).order_by('-weight')[:5]
        
        result = []
        for neighbor in neighbors:
            other_id = neighbor.j_canonical_id
            label = self._get_label(other_id)
            result.append({
                'id': str(other_id),
                'label': label,
                'weight': float(neighbor.weight),
                'type': 'compat'
            })
        return result
    
    def _get_label(self, canonical_id):
        mapping = LlmCanonicalMap.objects.filter(canonical_id=canonical_id, status='ok').first()
        if mapping:
            return mapping.canonical_name
        return str(canonical_id)


class FlavorEdgeDetailSerializer(serializers.Serializer):
    source = serializers.SerializerMethodField()
    target = serializers.SerializerMethodField()
    type = serializers.CharField()
    weight = serializers.FloatField()
    metrics = serializers.SerializerMethodField()
    summary = serializers.CharField(allow_null=True)
    
    def get_source(self, obj):
        return {
            'id': obj['source_id'],
            'label': obj['source_label'],
            'label_zh': obj.get('source_label_zh')
        }
    
    def get_target(self, obj):
        return {
            'id': obj['target_id'],
            'label': obj['target_label'],
            'label_zh': obj.get('target_label_zh')
        }
    
    def get_metrics(self, obj):
        layer = obj.get('layer')
        if layer == 'compat':
            return {
                'compat_score': obj.get('compat_score'),
                'role_bonus': obj.get('role_bonus'),
                'taste_complement_score': obj.get('taste_complement_score'),
                'anchor_bonus': obj.get('anchor_bonus'),
                'cooccur_bonus': obj.get('cooccur_bonus'),
                'penalty_score': obj.get('penalty_score')
            }
        elif layer == 'cooccur':
            return {
                'co_count': obj.get('co_count'),
                'pmi': obj.get('pmi'),
                'weight': obj.get('weight')
            }
        elif layer == 'flavor':
            return {
                'cosine_sim': obj.get('cosine_sim'),
                'l2_distance': obj.get('l2_distance'),
                'weight': obj.get('weight')
            }
        return {}


class FlavorStatsTopNodeSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    score = serializers.FloatField()


class FlavorStatsTopFreqSerializer(serializers.Serializer):
    id = serializers.CharField()
    label = serializers.CharField()
    freq = serializers.IntegerField()


class FlavorStatsTopAnchorSerializer(serializers.Serializer):
    anchor_name = serializers.CharField()
    count = serializers.IntegerField()


class FlavorGraphStatsSerializer(serializers.Serializer):
    summary = serializers.SerializerMethodField()
    top_nodes = FlavorStatsTopNodeSerializer(many=True)
    top_freq = FlavorStatsTopFreqSerializer(many=True)
    top_anchors = FlavorStatsTopAnchorSerializer(many=True)
    
    def get_summary(self, obj):
        return {
            'node_count': obj.get('node_count'),
            'edge_count': obj.get('edge_count'),
            'avg_degree': obj.get('avg_degree'),
            'max_weight': obj.get('max_weight')
        }
