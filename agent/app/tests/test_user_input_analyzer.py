#!/usr/bin/env python3
"""
用户输入分析器测试脚本

测试用户输入分析器的功能，验证实体识别和意图分析的结合
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from user_input_analyzer import user_input_analyzer

# 测试文本
TEST_TEXTS = [
    "找一下 Margarita 的配方",
    "龙舌兰酒可以换成什么",
    "lime 的邻域有什么食材",
    "Margarita 的配方结构是什么样的",
    "你好，有什么推荐的鸡尾酒吗",
    "我想要一杯酸甜的 Margarita",
    "给我一杯龙舌兰酒加青柠",
    "Margareta with lemon juice and vodka"
]

def test_analyzer():
    """测试用户输入分析器"""
    print("开始测试用户输入分析器...")
    print("=" * 80)
    
    # 只测试前3个文本，避免性能问题
    for text in TEST_TEXTS[:3]:
        print(f"\n测试文本: {text}")
        print("-" * 60)
        
        try:
            # 分析用户输入
            result = user_input_analyzer.analyze(text)
            
            # 打印分析结果
            print(f"意图: {result.get('intent')} (置信度: {result.get('intent_confidence'):.2f})")
            print(f"处理层级: {result.get('processing_level')}")
            print(f"需要审核: {result.get('needs_review')}")
            
            # 打印识别的实体
            entities = result.get('entities', [])
            if entities:
                print(f"识别到 {len(entities)} 个实体:")
                for entity in entities:
                    entity_text = entity.get('text')
                    entity_label = entity.get('label')
                    processing_level = entity.get('processing_level')
                    confidence = entity.get('confidence', 0.0)
                    print(f"  - {entity_text} ({entity_label}) - {processing_level} (置信度: {confidence:.2f})")
            else:
                print("未识别到实体")
            
            # 打印响应建议
            suggestion = result.get('response_suggestion', {})
            print(f"响应建议: {suggestion.get('action')}")
            if 'message' in suggestion:
                print(f"建议消息: {suggestion.get('message')}")
            if 'target' in suggestion:
                print(f"目标: {suggestion.get('target')}")
            
            # 打印解析结果结构
            parsed_query = result.get('parsed_query', {})
            if parsed_query:
                print("解析结果结构:")
                print(f"  意图: {parsed_query.get('intent')}")
                print(f"  建议动作: {parsed_query.get('suggested_action')}")
                print(f"  实体数量: {len(parsed_query.get('entities', []))}")
                print(f"  约束条件: {parsed_query.get('constraints')}")
                print(f"  返回结果数量: {parsed_query.get('top_k')}")
                print(f"  需要解释: {parsed_query.get('need_explanation')}")
        except Exception as e:
            print(f"分析出错: {str(e)}")
        
        print("-" * 60)
    
    print("\n" + "=" * 80)
    print("测试完成！")

def test_batch_analyze():
    """测试批量分析功能"""
    print("\n\n开始测试批量分析功能...")
    print("=" * 80)
    
    try:
        results = user_input_analyzer.batch_analyze(TEST_TEXTS[:2])
        
        for i, result in enumerate(results):
            print(f"\n分析结果 {i+1}:")
            print(f"文本: {result.get('text')}")
            print(f"意图: {result.get('intent')}")
            print(f"实体数量: {len(result.get('entities', []))}")
    except Exception as e:
        print(f"批量分析出错: {str(e)}")
    
    print("\n" + "=" * 80)
    print("批量分析测试完成！")

if __name__ == "__main__":
    test_analyzer()
    test_batch_analyze()
