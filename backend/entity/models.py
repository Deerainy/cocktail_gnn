from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True, null=False)
    password_hash = models.CharField(max_length=255, null=False)
    role = models.CharField(max_length=20, default='user')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def set_password(self, password):
        self.password_hash = make_password(password)

    def check_password(self, password):
        return check_password(password, self.password_hash)

    def __str__(self):
        return self.username

class Entity(models.Model):
    entity_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True, null=False)
    label = models.CharField(max_length=50, null=False)
    normalized_name = models.CharField(max_length=255, null=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'entities'

class Alias(models.Model):
    alias_id = models.AutoField(primary_key=True)
    entity_id = models.ForeignKey(Entity, on_delete=models.CASCADE, db_column='entity_id')
    alias_name = models.CharField(max_length=255, unique=True, null=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'aliases'

class ReviewTask(models.Model):
    review_id = models.CharField(max_length=100, primary_key=True)
    original_text = models.TextField(null=False)
    status = models.CharField(max_length=20, default='pending')
    processing_level = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'review_tasks'

class ReviewEntity(models.Model):
    review_entity_id = models.AutoField(primary_key=True)
    review_id = models.ForeignKey(ReviewTask, on_delete=models.CASCADE, related_name='entities', db_column='review_id')
    entity_id = models.CharField(max_length=100, null=False)
    text = models.CharField(max_length=255, null=False)
    label = models.CharField(max_length=50, null=False)
    start_pos = models.IntegerField(null=False)
    end_pos = models.IntegerField(null=False)
    processing_level = models.CharField(max_length=50, null=False)
    confidence = models.FloatField(null=False)
    context = models.TextField(blank=True)

    class Meta:
        db_table = 'review_entities'

class Candidate(models.Model):
    candidate_id = models.AutoField(primary_key=True)
    review_entity_id = models.ForeignKey(ReviewEntity, on_delete=models.CASCADE, db_column='review_entity_id', related_name='candidates')
    text = models.CharField(max_length=255, null=False)
    label = models.CharField(max_length=50, null=False)
    confidence = models.FloatField(null=False)
    source = models.CharField(max_length=50, null=False)

    class Meta:
        db_table = 'candidates'

class ReviewResult(models.Model):
    result_id = models.AutoField(primary_key=True)
    review_id = models.ForeignKey(ReviewTask, on_delete=models.CASCADE, db_column='review_id')
    entity_id = models.CharField(max_length=100, null=False)
    original_text = models.CharField(max_length=255, null=False)
    approved_candidate_text = models.CharField(max_length=255, null=False)
    approved_candidate_label = models.CharField(max_length=50, null=False)
    add_as_alias = models.BooleanField(default=False)
    action = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'review_results'
