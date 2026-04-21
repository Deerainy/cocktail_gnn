class ThreeLayerAnalyzer:
    """三层分析架构实现"""
    
    def __init__(self):
        # 第一层：规则和词典
        self.keyword_rules = {
            'recipe_query': ['配方', '做法', '制作', '步骤'],
            'ingredient_substitute': ['替代', '替换', '换成'],
            'recommendation': ['推荐', '建议', '适合'],
            'flavor_explanation': ['风味', '味道', '口感']
        }
        self.ingredient_dict = {'gin': '金酒', 'vodka': '伏特加', 'rum': '朗姆酒'}
        self.recipe_dict = {'margarita': '玛格丽特', 'martini': '马天尼'}
    
    def analyze(self, user_input: str) -> dict:
        """三层分析核心实现"""
        # 第一层：规则和词典基础匹配
        layer1_result = self._layer1_analysis(user_input)
        
        # 第二层：语义分析判断
        layer2_result = self._layer2_analysis(user_input, layer1_result)
        
        # 第三层：LLM增强理解
        layer3_result = self._layer3_analysis(user_input, layer1_result, layer2_result)
        
        # 综合判断
        final_intent = self._determine_final_intent(layer1_result, layer2_result, layer3_result)
        entities = self._extract_entities(user_input)
        
        return {
            'input': user_input,
            'final_intent': final_intent,
            'entities': entities,
            'layers': {
                'layer1': layer1_result,
                'layer2': layer2_result,
                'layer3': layer3_result
            }
        }
    
    def _layer1_analysis(self, text: str) -> dict:
        """第一层：规则和词典基础匹配"""
        matched_intents = []
        for intent, keywords in self.keyword_rules.items():
            for keyword in keywords:
                if keyword in text:
                    matched_intents.append(intent)
                    break
        
        # 匹配实体
        matched_entities = self._extract_entities(text)
        
        return {
            'matched_intents': matched_intents,
            'matched_entities': matched_entities,
            'confidence': 0.7 if matched_intents else 0.3
        }
    
    def _layer2_analysis(self, text: str, layer1_result: dict) -> dict:
        """第二层：语义分析判断"""
        # 检查是否需要深层分析
        needs_deep_analysis = False
        
        # 如果第一层没有匹配到意图，需要深层分析
        if not layer1_result['matched_intents']:
            needs_deep_analysis = True
        
        # 检查是否包含复杂表达
        complex_patterns = [r'如果.*?会怎样', r'如何.*?才能', r'为什么.*?']
        for pattern in complex_patterns:
            if re.search(pattern, text):
                needs_deep_analysis = True
                break
        
        return {
            'needs_deep_analysis': needs_deep_analysis,
            'reason': '复杂表达' if needs_deep_analysis else '简单表达'
        }
    
    def _layer3_analysis(self, text: str, layer1_result: dict, layer2_result: dict) -> dict:
        """第三层：LLM增强理解"""
        if not layer2_result['needs_deep_analysis']:
            return {
                'used': False,
                'enhanced_intent': layer1_result['matched_intents'][0] if layer1_result['matched_intents'] else 'general_chat'
            }
        
        # 模拟LLM分析（实际项目中调用真实LLM API）
        enhanced_intent = 'general_chat'
        if '推荐' in text and '适合' in text:
            enhanced_intent = 'recommendation'
        elif '替代' in text:
            enhanced_intent = 'ingredient_substitute'
        elif '怎么做' in text:
            enhanced_intent = 'recipe_query'
        
        return {
            'used': True,
            'enhanced_intent': enhanced_intent,
            'confidence': 0.85
        }
    
    def _determine_final_intent(self, layer1: dict, layer2: dict, layer3: dict) -> str:
        """综合判断最终意图"""
        if layer3['used']:
            return layer3['enhanced_intent']
        elif layer1['matched_intents']:
            return layer1['matched_intents'][0]
        else:
            return 'general_chat'
    
    def _extract_entities(self, text: str) -> list:
        """提取实体"""
        entities = []
        # 提取食材
        for eng_name, chn_name in self.ingredient_dict.items():
            if eng_name.lower() in text.lower() or chn_name in text:
                entities.append({'name': chn_name, 'type': 'ingredient'})
        # 提取配方
        for eng_name, chn_name in self.recipe_dict.items():
            if eng_name.lower() in text.lower() or chn_name in text:
                entities.append({'name': chn_name, 'type': 'recipe'})
        return entities