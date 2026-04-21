from rest_framework import serializers
from .models import AgentTrace, AgentTraceStep


class AgentTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTrace
        fields = [
            'id', 'trace_id', 'session_id', 'user_input', 'normalized_input',
            'language', 'intent_name', 'intent_source', 'action_name',
            'backend_type', 'status', 'final_answer', 'error_message',
            'trace_json', 'created_at'
        ]


class AgentTraceStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTraceStep
        fields = [
            'id', 'trace_id', 'step_no', 'step_name', 'step_title',
            'status', 'data_json', 'created_at'
        ]
