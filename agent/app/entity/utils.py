#!/usr/bin/env python3
"""
工具函数模块

包含文本规范化、别名处理等工具函数
"""

import re
import string
from functools import lru_cache

@lru_cache(maxsize=10000)
def normalize_text(text: str) -> str:
    """文本规范化函数
    
    处理文本的规范化，包括：
    1. 去掉多余空格
    2. 去掉标点
    3. 处理复数尾缀
    4. 连字符和下划线统一为空格
    5. 中英文全半角统一
    6. 常见缩写展开
    7. 转为小写
    
    Args:
        text: 待规范化的文本
        
    Returns:
        str: 规范化后的文本
    """
    if not text:
        return ""
    
    # 1. 全半角统一
    text = full_to_half(text)
    
    # 2. 连字符和下划线统一为空格
    text = re.sub(r'[-_]', ' ', text)
    
    # 3. 去掉标点
    text = text.translate(str.maketrans('', '', string.punctuation))
    
    # 4. 去掉多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 5. 处理复数尾缀
    text = handle_plural(text)
    
    # 6. 展开常见缩写
    text = expand_abbreviations(text)
    
    # 7. 转为小写
    text = text.lower()
    
    return text

def full_to_half(text: str) -> str:
    """全角转半角
    
    Args:
        text: 包含全角字符的文本
        
    Returns:
        str: 转换为半角的文本
    """
    result = []
    for char in text:
        code = ord(char)
        if code == 0x3000:
            # 全角空格
            result.append(' ')
        elif 0xFF01 <= code <= 0xFF5E:
            # 全角字符（除空格）
            result.append(chr(code - 0xFEE0))
        else:
            # 其他字符保持不变
            result.append(char)
    return ''.join(result)

def handle_plural(text: str) -> str:
    """处理复数尾缀
    
    Args:
        text: 可能包含复数尾缀的文本
        
    Returns:
        str: 处理后的文本
    """
    # 常见复数规则
    plural_rules = [
        (r'(.*)ies$', r'\1y'),      # babies -> baby
        (r'(.*)es$', r'\1'),        # tomatoes -> tomato
        (r'(.+)s$', r'\1'),          # apples -> apple
    ]
    
    # 特殊情况处理
    special_cases = {
        'limes': 'lime',
        'lemons': 'lemon',
        'oranges': 'orange',
    }
    
    # 检查特殊情况
    if text in special_cases:
        return special_cases[text]
    
    # 应用一般规则
    for pattern, replacement in plural_rules:
        if re.search(pattern, text):
            result = re.sub(pattern, replacement, text)
            # 确保结果不为空
            if result:
                return result
            break
    
    return text

def expand_abbreviations(text: str) -> str:
    """展开常见缩写
    
    Args:
        text: 可能包含缩写的文本
        
    Returns:
        str: 展开后的文本
    """
    abbreviations = {
        'ml': 'milliliter',
        'oz': 'ounce',
        'tbsp': 'tablespoon',
        'tsp': 'teaspoon',
        'cup': 'cup',
        'glass': 'glass',
        'shot': 'shot',
        'dash': 'dash',
        'pinch': 'pinch',
        'piece': 'piece',
        'slice': 'slice',
        'wedge': 'wedge',
        'leaf': 'leaf',
        'sprig': 'sprig',
    }
    
    # 展开缩写
    for abbr, full in abbreviations.items():
        # 确保匹配完整的单词
        pattern = rf'\b{abbr}\b'
        text = re.sub(pattern, full, text, flags=re.IGNORECASE)
    
    return text

# 从 mappings.py 导入双语映射
from .mappings import bilingual_mapping

def map_bilingual(text: str) -> str:
    """中英文映射
    
    Args:
        text: 可能是中文的文本
        
    Returns:
        str: 映射后的英文文本
    """
    normalized = normalize_text(text)
    return bilingual_mapping.get(normalized, normalized)
