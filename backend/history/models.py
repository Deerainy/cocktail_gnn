from django.db import models
from datetime import datetime


class AgentTrace(models.Model):
    id = models.BigAutoField(primary_key=True)
    trace_id = models.CharField(max_length=64, unique=True, db_index=True)
    session_id = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    user_input = models.TextField()
    normalized_input = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=16, blank=True, null=True)
    intent_name = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    intent_source = models.CharField(max_length=32, blank=True, null=True)
    action_name = models.CharField(max_length=64, blank=True, null=True)
    backend_type = models.CharField(max_length=32, blank=True, null=True)
    status = models.CharField(max_length=16, default='success', db_index=True)
    final_answer = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    trace_json = models.JSONField()
    created_at = models.DateTimeField(default=datetime.now, db_index=True)

    class Meta:
        db_table = 'agent_trace'
        ordering = ['-created_at']


class AgentTraceStep(models.Model):
    id = models.BigAutoField(primary_key=True)
    trace_id = models.CharField(max_length=64, db_index=True)
    step_no = models.IntegerField()
    step_name = models.CharField(max_length=64, db_index=True)
    step_title = models.CharField(max_length=64, blank=True, null=True)
    status = models.CharField(max_length=16, default='success', db_index=True)
    data_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=datetime.now)

    class Meta:
        db_table = 'agent_trace_step'
        ordering = ['trace_id', 'step_no']
