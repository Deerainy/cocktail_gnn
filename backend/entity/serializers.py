from rest_framework import serializers
from .models import User, Entity, Alias, ReviewTask, ReviewEntity, Candidate, ReviewResult

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'username', 'role', 'created_at']

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class UserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ['entity_id', 'name', 'label', 'normalized_name', 'description']

class AliasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alias
        fields = ['alias_id', 'entity_id', 'alias_name']

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['text', 'label', 'confidence', 'source']

class ReviewEntitySerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)
    
    class Meta:
        model = ReviewEntity
        fields = ['entity_id', 'text', 'label', 'start_pos', 'end_pos', 'processing_level', 'confidence', 'context', 'candidates']

class ReviewTaskSerializer(serializers.ModelSerializer):
    entities = ReviewEntitySerializer(many=True, read_only=True)
    
    class Meta:
        model = ReviewTask
        fields = ['review_id', 'original_text', 'status', 'processing_level', 'created_at', 'entities']

class ReviewSubmitSerializer(serializers.Serializer):
    review_id = serializers.CharField(required=True)
    entity_id = serializers.CharField(required=True)
    original_text = serializers.CharField(required=True)
    approved_candidate = serializers.DictField(required=True)
    add_as_alias = serializers.BooleanField(required=True)

class ProcessTextSerializer(serializers.Serializer):
    text = serializers.CharField(required=True)

class BatchProcessSerializer(serializers.Serializer):
    texts = serializers.ListField(child=serializers.CharField(), required=True)

class AddAliasSerializer(serializers.Serializer):
    alias_name = serializers.CharField(required=True)
