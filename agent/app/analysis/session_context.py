#!/usr/bin/env python3
"""
会话上下文管理模块

实现四层架构中的第2层：结构化会话状态管理
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class SessionContext:
    """会话上下文数据结构"""
    
    def __init__(self, session_id: str):
        """
        初始化会话上下文
        
        Args:
            session_id: 会话ID
        """
        self.session_id: str = session_id
        self.current_recipe_id: Optional[int] = None
        self.current_recipe_name: Optional[str] = None
        self.current_canonical_id: Optional[int] = None
        self.current_canonical_name: Optional[str] = None
        self.current_step: Optional[str] = None
        self.last_intent: Optional[str] = None
        self.last_action: Optional[str] = None
        self.last_entities: Dict[str, Any] = {}
        self.recent_recipes: List[Dict[str, Any]] = []
        self.recent_ingredients: List[Dict[str, Any]] = []
        self.updated_at: str = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "current_recipe_id": self.current_recipe_id,
            "current_recipe_name": self.current_recipe_name,
            "current_canonical_id": self.current_canonical_id,
            "current_canonical_name": self.current_canonical_name,
            "current_step": self.current_step,
            "last_intent": self.last_intent,
            "last_action": self.last_action,
            "last_entities": self.last_entities,
            "recent_recipes": self.recent_recipes,
            "recent_ingredients": self.recent_ingredients,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionContext':
        """从字典创建 SessionContext"""
        ctx = cls(data.get("session_id", ""))
        ctx.current_recipe_id = data.get("current_recipe_id")
        ctx.current_recipe_name = data.get("current_recipe_name")
        ctx.current_canonical_id = data.get("current_canonical_id")
        ctx.current_canonical_name = data.get("current_canonical_name")
        ctx.current_step = data.get("current_step")
        ctx.last_intent = data.get("last_intent")
        ctx.last_action = data.get("last_action")
        ctx.last_entities = data.get("last_entities", {})
        ctx.recent_recipes = data.get("recent_recipes", [])
        ctx.recent_ingredients = data.get("recent_ingredients", [])
        ctx.updated_at = data.get("updated_at", datetime.now().isoformat())
        return ctx
    
    def add_recent_recipe(self, recipe_id: Optional[int], recipe_name: Optional[str]):
        """
        添加最近配方
        
        Args:
            recipe_id: 配方ID
            recipe_name: 配方名称
        """
        if not recipe_id and not recipe_name:
            return
        
        # 移除已存在的相同配方
        self.recent_recipes = [
            r for r in self.recent_recipes 
            if r.get("id") != recipe_id and r.get("name") != recipe_name
        ]
        
        # 添加新配方到前面
        self.recent_recipes.insert(0, {
            "id": recipe_id,
            "name": recipe_name
        })
        
        # 最多保留5个
        self.recent_recipes = self.recent_recipes[:5]
        
        # 更新当前配方
        self.current_recipe_id = recipe_id
        self.current_recipe_name = recipe_name
        self.updated_at = datetime.now().isoformat()
    
    def add_recent_ingredient(self, canonical_id: Optional[int], canonical_name: Optional[str]):
        """
        添加最近食材
        
        Args:
            canonical_id: 规范食材ID
            canonical_name: 规范食材名称
        """
        if not canonical_id and not canonical_name:
            return
        
        # 移除已存在的相同食材
        self.recent_ingredients = [
            i for i in self.recent_ingredients 
            if i.get("id") != canonical_id and i.get("name") != canonical_name
        ]
        
        # 添加新食材到前面
        self.recent_ingredients.insert(0, {
            "id": canonical_id,
            "name": canonical_name
        })
        
        # 最多保留5个
        self.recent_ingredients = self.recent_ingredients[:5]
        
        # 更新当前食材
        self.current_canonical_id = canonical_id
        self.current_canonical_name = canonical_name
        self.updated_at = datetime.now().isoformat()
    
    def update_after_execution(self, intent: str, action: str, entities: Dict[str, Any]):
        """
        执行任务后更新上下文
        
        Args:
            intent: 当前意图
            action: 当前动作
            entities: 识别的实体
        """
        self.last_intent = intent
        self.last_action = action
        self.last_entities = entities
        self.current_step = intent
        self.updated_at = datetime.now().isoformat()
        
        # 从实体中更新配方和食材
        if "recipe" in entities:
            recipe = entities["recipe"]
            if isinstance(recipe, dict):
                self.add_recent_recipe(recipe.get("id"), recipe.get("name"))
            else:
                self.add_recent_recipe(None, str(recipe))
        
        if "ingredient" in entities:
            ingredient = entities["ingredient"]
            if isinstance(ingredient, dict):
                self.add_recent_ingredient(ingredient.get("id"), ingredient.get("name"))
            else:
                self.add_recent_ingredient(None, str(ingredient))


class SessionContextManager:
    """会话上下文管理器"""
    
    def __init__(self):
        """初始化会话上下文管理器"""
        self._contexts: Dict[str, SessionContext] = {}
    
    def get_or_create(self, session_id: str) -> SessionContext:
        """
        获取或创建会话上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            SessionContext: 会话上下文
        """
        if session_id not in self._contexts:
            self._contexts[session_id] = SessionContext(session_id)
        return self._contexts[session_id]
    
    def get(self, session_id: str) -> Optional[SessionContext]:
        """
        获取会话上下文
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[SessionContext]: 会话上下文，如果不存在返回 None
        """
        return self._contexts.get(session_id)
    
    def save(self, context: SessionContext):
        """
        保存会话上下文
        
        Args:
            context: 会话上下文
        """
        self._contexts[context.session_id] = context
    
    def remove(self, session_id: str):
        """
        删除会话上下文
        
        Args:
            session_id: 会话ID
        """
        if session_id in self._contexts:
            del self._contexts[session_id]
    
    def clear(self):
        """清空所有会话上下文"""
        self._contexts.clear()


# 创建全局会话上下文管理器实例
session_context_manager = SessionContextManager()
