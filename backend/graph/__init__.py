"""
Graph 模块初始化文件
"""
import neomodel

from django.conf import settings

neomodel.config.DATABASE_URL = settings.NEOMODEL_NEO4J_BOLT_URL
