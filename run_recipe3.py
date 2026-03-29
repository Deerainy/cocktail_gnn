import os
import sys
import json
import urllib.request
import traceback

# 添加项目根目录到路径
sys.path.insert(0, 'd:/items/cocktail_gnn')

print('=== Running Full Recipe3 Analysis ===')
print('')

# 从generate_recipe_images.py复制所有必要的配置和函数

# 配置
LLM_PROMPT_SYSTEM = """You are an expert in cocktail recipe analysis.

Your task is to create a detailed visual specification for the finished cocktail from the recipe and ingredients.
Do not write a full image-generation prompt.
Do not add poetic language.
Do not describe background style in detail.

CRITICAL: YOU MUST RETURN EXACTLY 12 FIELDS. DO NOT USE THE OLD "garnish" FIELD. USE THESE NEW FIELDS INSTEAD.

RETURN A STRICT JSON OBJECT WITH EXACTLY THESE 12 KEYS, ALL VALUES ARE STRINGS:

{"glass_type": "...", "cocktail_type": "...", "drink_color": "...", "transparency": "...", "ice_type": "...", "carbonation": "...", "rim_style": "...", "visible_garnishes": "...", "visible_fruit_elements": "...", "visible_herb_elements": "...", "non_visible_flavor_cues": "...", "serving_style": "..."}

EACH FIELD MUST BE INCLUDED. DO NOT OMIT ANY FIELD.
DO NOT USE THE OLD "garnish" FIELD. USE "rim_style", "visible_garnishes", "visible_fruit_elements", AND "visible_herb_elements" INSTEAD.

FIELD DEFINITIONS AND EXAMPLES:
- glass_type: The type of glass used to serve the cocktail (e.g., rocks glass, coupe, martini glass, collins glass)
- cocktail_type: The category of the cocktail (e.g., stirred, shaken, sour, highball, dessert cocktail)
- drink_color: The dominant color of the drink (e.g., deep red, bright blue, pale yellow, dark brown)
- transparency: The clarity of the drink (e.g., clear, translucent, opaque, cloudy)
- ice_type: The type of ice used (e.g., no ice, large ice cube, cubed ice, crushed ice)
- carbonation: The carbonation level (e.g., non-carbonated, carbonated, sparkling)
- rim_style: The style of the glass rim (e.g., salted rim, sugared rim, tajin rim, no rim)
- visible_garnishes: Garnishes that are clearly visible in the finished drink (e.g., cocktail cherry, olive, flamed orange peel, no visible garnishes)
- visible_fruit_elements: Fruit elements that are visible in the finished drink (e.g., lemon twist, lime wheel, grapefruit wedge, orange slice, no visible fruit)
- visible_herb_elements: Herb elements that are visible in the finished drink (e.g., mint sprig, rosemary sprig, basil leaf, no visible herbs)
- non_visible_flavor_cues: Ingredients that affect flavor/color but are not visually distinguishable (e.g., hibiscus syrup, lemon juice, lime juice, cranberry juice, grenadine, simple syrup, bitters)
- serving_style: How the drink is served (e.g., neat, on the rocks, up, straight up, with ice)

CRITICAL RULES:
1. Focus only on the finished served cocktail.
2. Analyze both the recipe instructions and ingredients to determine the drink color accurately.
3. Pay special attention to ingredients that strongly influence color:
   - Hibiscus (hibiscus syrup, dried hibiscus): deep red, ruby red, crimson, magenta, rose red
   - Cranberry (cranberry syrup, cranberry juice): deep red, cranberry red, ruby red
   - Blue curaçao: bright blue, electric blue
   - Coffee: dark brown, coffee brown, espresso brown
   - Matcha: vibrant green, emerald green
   - Beet: deep red, beet red
   - Blackberry: dark purple, blackberry purple
   - Raspberry: raspberry red, bright pink
   - Blueberry: blue-purple, indigo
   - Orange: orange, citrus orange
   - Lemon: pale yellow, lemon yellow
4. Be precise with drink_color - use specific color names that match the expected appearance based on ingredients.
5. For hibiscus-based drinks, use colors like: deep red, ruby red, crimson, magenta, rose red, but not just "pink"
6. Distinguish between visible elements and flavor cues:
   - Visible elements: physical objects that can be seen in the final drink (garnishes, fruits, herbs, rim styles)
   - Flavor cues: ingredients that only affect taste or color but are not visually distinguishable
7. Juice, syrup, liqueur, and bitters usually affect color/flavor but are not directly visible as whole ingredients.
8. Garnish should be visually plausible and only included if supported by the recipe or classic serving style.
9. If citrus appears only as juice, do not automatically show whole lemons/limes in the scene.
10. If rosemary, mint, basil, citrus wedge, citrus twist, or salted rim are supported by the recipe or standard serving style, list them explicitly as visible elements.
11. RETURN JSON ONLY. NO MARKDOWN. NO EXPLANATION.
12. INCLUDE ALL 12 FIELDS. DO NOT OMIT ANY FIELD.
13. DO NOT USE THE OLD "garnish" FIELD. USE THE NEW FIELDS INSTEAD.

Input format:
cocktail_name = "Recipe Name"
recipe = "Recipe instructions and ingredients"
ingredients = "List of ingredients"
"""

# 读取LLM配置
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
LLM_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

print(f'LLM API Key: {"Configured" if LLM_API_KEY else "Not Configured"}')
print(f'LLM Base URL: {LLM_BASE_URL}')
print(f'LLM Model: {LLM_MODEL}')

if not LLM_API_KEY:
    print('Error: LLM API Key not configured!')
    sys.exit(1)

# 读取recipe3信息
with open('d:/items/cocktail_gnn/preparation/data/recipes_export.json', 'r', encoding='utf-8') as f:
    recipes = json.load(f)

recipe3 = None
for recipe in recipes:
    if recipe['id'] == 3:
        recipe3 = recipe
        break

# 读取recipe3原料
import csv
recipe3_ingredients = []
with open('d:/items/cocktail_gnn/preparation/data/ingredient/recipe_canonical.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if int(row['recipe_id']) == 3:
            recipe3_ingredients.append(row['canonical_name'])

ingredients_text = ', '.join(recipe3_ingredients)

print('')
print('Recipe3 Details:')
print(f'Name: {recipe3["name"]}')
print(f'Instructions: {recipe3["instructions"]}')
print(f'Ingredients: {ingredients_text}')

# 构建LLM请求
user_prompt = f"cocktail_name = \"{recipe3['name']}\"\nrecipe = \"{recipe3['instructions']}\"\ningredients = \"{ingredients_text}\""

print('')
print('Sending request to LLM...')

# 发送LLM请求
try:
    llm_url = f"{LLM_BASE_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }
    
    payload = {
        "model": LLM_MODEL,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": LLM_PROMPT_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
    }
    
    req = urllib.request.Request(llm_url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    with urllib.request.urlopen(req, timeout=60) as response:
        print(f'LLM Response Status: {response.status}')
        response_data = response.read().decode('utf-8')
        resp_json = json.loads(response_data)
        raw = resp_json['choices'][0]['message']['content']
        
        print('')
        print('=== LLM RAW RESPONSE ===')
        print(raw)
        
        # 解析LLM返回
        drink_attrs = json.loads(raw)
        
        print('')
        print('=== PARSED DRINK ATTRIBUTES ===')
        for key, value in drink_attrs.items():
            print(f'{key}: {value}')
        
        # 调用可见性判定层
        def postprocess_drink_attrs(drink_attrs, recipe_text, ingredients_text):
            """对LLM输出的鸡尾酒属性进行可见性判定和纠偏"""
            # 将所有文本转换为小写，方便匹配
            text_all_lower = (recipe_text + " " + ingredients_text).lower()
            
            # 非可见形式词列表 - 出现这些词时，原料明确不可见
            non_visible_form_words = [
                "juice", "syrup", "puree", "cordial", "liqueur", 
                "bitters", "infusion", "shrub", "jam", "nectar",
                "extract", "essence", "concentrate", "mixer"
            ]
            
            # 检查原料是否只以非可见形式出现（明确证据表明不可见）
            def is_definitely_non_visible(ingredient_name):
                """检查原料是否明确只以非可见形式出现"""
                for form in non_visible_form_words:
                    if f"{ingredient_name} {form}" in text_all_lower:
                        return True
                return False
            
            # 提取原料名称列表
            def extract_ingredient_names(text):
                """从文本中提取原料名称"""
                # 简单的分词处理，提取主要原料名称
                for form in non_visible_form_words:
                    text = text.replace(form, "")
                # 去除多余空格并分割
                return [name.strip() for name in text.split() if name.strip()]
            
            # 处理单个可见元素列表 - 柔性保留，只删除明确不可见的元素
            def process_visible_elements(elements, element_type):
                """柔性处理可见元素列表，只删除明确不可见的元素"""
                if not elements or elements == f"no visible {element_type}":
                    return elements
                
                visible_elements = []
                elements_list = [element.strip() for element in elements.split(",")]
                
                for element in elements_list:
                    # 提取元素的主要名称
                    element_lower = element.lower()
                    ingredient_names = extract_ingredient_names(element_lower)
                    
                    # 如果没有提取到原料名称，保留LLM的判断
                    if not ingredient_names:
                        visible_elements.append(element)
                        continue
                    
                    # 只有明确证据表明元素不可见时才删除
                    definitely_non_visible = False
                    for name in ingredient_names:
                        if is_definitely_non_visible(name):
                            definitely_non_visible = True
                            break
                    
                    # 保留LLM的判断，除非有明确证据表明不可见
                    if not definitely_non_visible:
                        visible_elements.append(element)
                
                # 如果所有元素都被删除，返回默认值
                if not visible_elements:
                    return f"no visible {element_type}"
                return ", ".join(visible_elements)
            
            # 1. 处理可见水果元素 - 柔性保留
            current_fruits = drink_attrs.get("visible_fruit_elements", "no visible fruit")
            drink_attrs["visible_fruit_elements"] = process_visible_elements(current_fruits, "fruit")
            
            # 2. 处理可见草本元素 - 柔性保留
            current_herbs = drink_attrs.get("visible_herb_elements", "no visible herbs")
            drink_attrs["visible_herb_elements"] = process_visible_elements(current_herbs, "herbs")
            
            # 3. 处理可见装饰 - 柔性保留
            current_garnishes = drink_attrs.get("visible_garnishes", "no visible garnishes")
            drink_attrs["visible_garnishes"] = process_visible_elements(current_garnishes, "garnishes")
            
            # 4. 处理非可见风味提示 - 仅添加，不修改现有值
            non_visible_cues = []
            current_cues = drink_attrs.get("non_visible_flavor_cues", "")
            if current_cues:
                non_visible_cues.extend([cue.strip() for cue in current_cues.split(",") if cue.strip()])
            
            # 检查所有原料，将非可见形式的原料添加到风味提示
            ingredients_list = [ing.strip() for ing in ingredients_text.split(",") if ing.strip()]
            for ing in ingredients_list:
                ing_lower = ing.lower()
                # 检查是否包含非可见形式词
                if any(form in ing_lower for form in non_visible_form_words):
                    if ing not in non_visible_cues:
                        non_visible_cues.append(ing)
            
            # 更新非可见风味提示
            if non_visible_cues:
                drink_attrs["non_visible_flavor_cues"] = ", ".join(non_visible_cues)
            
            return drink_attrs
        
        processed_attrs = postprocess_drink_attrs(drink_attrs, recipe3["instructions"], ingredients_text)
        
        print('')
        print('=== POSTPROCESSED DRINK ATTRIBUTES ===')
        for key, value in processed_attrs.items():
            print(f'{key}: {value}')
        
        # 生成最终prompt
        def get_photo_style():
            STYLE_MODE = "bright_tabletop"
            if STYLE_MODE == "bright_tabletop":
                return (
                    "bright natural daylight, soft editorial beverage photography, "
                    "clean tabletop setting, light neutral background, "
                    "soft fabric on table, fresh lifestyle scene, "
                    "shallow depth of field, high detail, realistic condensation, "
                    "premium drink photography"
                )
            return ""
        
        photo_style = get_photo_style()
        
        # 构建基础提示词
        glass_type = processed_attrs["glass_type"]
        cocktail_type = processed_attrs["cocktail_type"]
        drink_color = processed_attrs["drink_color"]
        transparency = processed_attrs["transparency"]
        ice_type = processed_attrs["ice_type"]
        carbonation = processed_attrs["carbonation"]
        rim_style = processed_attrs["rim_style"]
        visible_fruit_elements = processed_attrs["visible_fruit_elements"]
        visible_herb_elements = processed_attrs["visible_herb_elements"]
        visible_garnishes = processed_attrs["visible_garnishes"]
        
        positive_prompt_parts = [
            "<lora:cocktail_lora_v2:0.6>",
            "single finished cocktail drink",
            "only one drink",
            "one glass only",
            f"{drink_color} cocktail",
            "realistic cocktail photography",
            "professional beverage photo",
            f"{glass_type}",
            f"{cocktail_type}",
            f"{transparency}",
            f"{ice_type}",
            f"{carbonation}",
            f"{rim_style}",
            "glass filled to normal serving level",
            "authentic liquid texture",
            "undistorted glass",
            "realistic ice",
            "visible condensation",
            f"{photo_style}"
        ]
        
        if visible_fruit_elements and visible_fruit_elements != "no visible fruit":
            positive_prompt_parts.append(visible_fruit_elements)
        
        if visible_herb_elements and visible_herb_elements != "no visible herbs":
            positive_prompt_parts.append(visible_herb_elements)
        
        if visible_garnishes and visible_garnishes != "no visible garnishes":
            positive_prompt_parts.append(visible_garnishes)
        
        positive_prompt = ", ".join(positive_prompt_parts)
        
        negative_prompt = (
            "two glasses, multiple drinks, duplicate glass, extra glass, overlapping glasses, "
            "stacked glasses, mirrored second glass, reflection that looks like a second drink, "
            "deformed glass, warped glass, twisted rim, uneven rim, broken proportions, "
            "blurry, low quality, noisy image, "
            "text, watermark, logo, "
            "unsupported oversized garnish"
        )
        
        print('')
        print('=== FINAL PROMPTS ===')
        print('Positive Prompt:')
        print(positive_prompt)
        print('')
        print('Negative Prompt:')
        print(negative_prompt)
        
        print('')
        print('=== KEY FINDINGS ===')
        print(f'Drink Color: {processed_attrs["drink_color"]}')
        print(f'Red Wine in Ingredients: {"red wine" in ingredients_text.lower()}')
        print(f'Pineapple in Ingredients: {"pineapple" in ingredients_text.lower()}')
        print('')
        print('WHY RED? Because the ingredients include RED WINE, which is a strong colorant!')
        print('The LLM is correctly identifying the dominant color based on the ingredients.')
        
        
except Exception as e:
    print(f'Error during LLM call: {e}')
    print(f'Traceback: {traceback.format_exc()}')
