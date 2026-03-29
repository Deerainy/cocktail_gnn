import os
import sys
import csv
import json
import base64
import urllib.request
import traceback
import datetime
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 日志函数，只写入日志文件，不输出到控制台
def log(message):
    """记录日志"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    
    # 只写入日志文件，不输出到控制台
    log_file = "generate_recipe_images.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")

# 手动加载环境变量文件的函数
def load_env_file(file_path):
    """从.env文件手动加载环境变量"""
    if not os.path.exists(file_path):
        log(f"警告: 未找到环境变量配置文件: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释行
            if not line or line.startswith('#'):
                continue
            # 解析键值对
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # 移除引号
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                os.environ[key] = value
    log(f"已手动加载环境变量配置文件: {file_path}")

# 加载环境变量（从项目配置文件）
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_llm_env = os.path.join(_root, "config", "llm.env")
load_env_file(_llm_env)

# 清空之前的日志
open("generate_recipe_images.log", "w").close()

# 配置
CSV_PATH = "d:/items/cocktail_gnn/preparation/data/recipes_export.csv"
OUTPUT_DIR = "d:/items/cocktail_gnn/frontend/src/assets/recipe_image"
SD_API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"

# 摄影风格配置
STYLE_MODE = "bright_tabletop"  # 可选值: bright_tabletop, dark_bar

# 固定摄影风格模板
def get_photo_style():
    if STYLE_MODE == "bright_tabletop":
        return (
            "bright natural daylight, soft editorial beverage photography, "
            "clean tabletop setting, light neutral background, "
            "soft fabric on table, fresh lifestyle scene, "
            "shallow depth of field, high detail, realistic condensation, "
            "premium drink photography"
        )
    elif STYLE_MODE == "dark_bar":
        return (
            "dim warm bar lighting, wooden bar counter, real bar background, "
            "cinematic beverage photography, shallow depth of field, high detail"
        )
    else:
        return (
            "bright natural daylight, soft editorial beverage photography, "
            "clean tabletop setting, light neutral background, "
            "soft fabric on table, fresh lifestyle scene, "
            "shallow depth of field, high detail, realistic condensation, "
            "premium drink photography"
        )

# LLM配置
LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
LLM_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 记录初始日志
log("=== 脚本开始执行 ===")
log(f"Python版本: {sys.version}")
log(f"工作目录: {os.getcwd()}")
log(f"LLM_API_KEY是否配置: {'是' if LLM_API_KEY else '否'}")
log(f"LLM_API_KEY前10位: {LLM_API_KEY[:10]}..." if LLM_API_KEY else "无API密钥")
log(f"LLM_BASE_URL: {LLM_BASE_URL}")
log(f"LLM_MODEL: {LLM_MODEL}")

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


def read_recipe_ingredients(csv_path: str) -> Dict[int, str]:
    """从CSV文件读取recipe的原料信息"""
    recipe_ingredients = {}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            recipe_id = int(row['recipe_id'])
            if recipe_id not in recipe_ingredients:
                recipe_ingredients[recipe_id] = []
            canonical_name = row['canonical_name']
            if canonical_name not in recipe_ingredients[recipe_id]:
                recipe_ingredients[recipe_id].append(canonical_name)
    
    # 将原料列表转换为字符串
    for recipe_id in recipe_ingredients:
        recipe_ingredients[recipe_id] = ', '.join(recipe_ingredients[recipe_id])
    
    return recipe_ingredients


def read_recipes_from_csv(csv_path: str, ingredients_csv_path: str) -> Dict[int, Dict[str, str]]:
    """从CSV文件读取recipe数据，包括原料信息"""
    recipes = {}
    
    # 读取原料信息
    ingredients = read_recipe_ingredients(ingredients_csv_path)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            recipe_id = int(row['id'])
            recipes[recipe_id] = {
                'name': row['name'],
                'instructions': row['instructions'],
                'ingredients': ingredients.get(recipe_id, '')
            }
    return recipes


def call_llm_for_prompts(recipe_name: str, recipe_instructions: str, recipe_ingredients: str) -> Dict[str, Any]:
    """调用LLM获取鸡尾酒核心属性，然后使用固定摄影模板生成最终prompt"""
    # 确保所有参数是字符串
    recipe_instructions = str(recipe_instructions) if recipe_instructions else ""
    recipe_ingredients = str(recipe_ingredients) if recipe_ingredients else ""
    
    log(f"=== 调用LLM获取鸡尾酒核心属性 ===")
    log(f"recipe_name: {recipe_name}")
    log(f"recipe_instructions: {recipe_instructions[:100]}...")
    log(f"recipe_ingredients: {recipe_ingredients}")
    
    # 检查API密钥是否配置
    if not LLM_API_KEY:
        log("错误: 未配置LLM API密钥，无法生成高质量prompt")
        raise ValueError("LLM API密钥未配置，必须配置API密钥才能生成prompt")
    
    user_prompt = "cocktail_name = \"" + recipe_name + "\"\nrecipe = \"" + recipe_instructions + "\"\ningredients = \"" + recipe_ingredients + "\""
    
    # 最多重试3次
    max_retries = 3
    for retry in range(max_retries):
        log(f"尝试调用LLM (重试 {retry+1}/{max_retries})...")
        log(f"准备调用LLM API，URL: {LLM_BASE_URL}")
        
        try:
            # 构建LLM API请求
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
            
            # 发送请求
            log("发送LLM API请求...")
            req = urllib.request.Request(llm_url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=60) as response:
                log(f"LLM API响应状态码: {response.status}")
                response_data = response.read().decode('utf-8')
                log(f"LLM API响应数据: {response_data}")
                
                resp_json = json.loads(response_data)
                raw = resp_json['choices'][0]['message']['content']
                log(f"LLM返回原始内容: {raw}")
                
                # 解析返回的JSON
                drink_attrs = json.loads(raw)
                log(f"解析后的鸡尾酒属性: {drink_attrs}")
                
                # 新增函数：可见性判定层 - 基于原料和食谱文本对LLM输出进行纠偏
                def postprocess_drink_attrs(drink_attrs, recipe_text, ingredients_text, cocktail_name=""):
                    """对LLM输出的鸡尾酒属性进行可见性判定和纠偏
                    
                    Args:
                        drink_attrs: LLM返回的鸡尾酒属性字典
                        recipe_text: 食谱文本
                        ingredients_text: 原料文本
                        cocktail_name: 鸡尾酒名称
                    
                    Returns:
                        经过纠偏后的鸡尾酒属性字典
                    """
                    # 将所有文本转换为小写，方便匹配
                    text_all_lower = (recipe_text + " " + ingredients_text + " " + cocktail_name).lower()
                    
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
                    
                    # 从食谱名称中提取视觉暗示元素
                    def extract_visual_cues_from_name(name):
                        """从食谱名称中提取视觉暗示元素"""
                        name_lower = name.lower()
                        visual_cues = []
                        
                        # 检查名称中是否有明确的视觉元素
                        if "pineapple" in name_lower:
                            visual_cues.append("pineapple")
                        if "lemon" in name_lower:
                            visual_cues.append("lemon")
                        if "lime" in name_lower:
                            visual_cues.append("lime")
                        if "orange" in name_lower:
                            visual_cues.append("orange")
                        if "mint" in name_lower:
                            visual_cues.append("mint")
                        if "rose" in name_lower:
                            visual_cues.append("rose")
                        if "cherry" in name_lower:
                            visual_cues.append("cherry")
                        if "olive" in name_lower:
                            visual_cues.append("olive")
                        
                        return visual_cues
                    
                    # 提取原料名称列表
                    def extract_ingredient_names(text):
                        """从文本中提取原料名称"""
                        # 简单的分词处理，提取主要原料名称
                        for form in non_visible_form_words:
                            text = text.replace(form, "")
                        # 去除多余空格并分割
                        return [name.strip() for name in text.split() if name.strip()]
                    
                    # 处理单个可见元素列表 - 柔性保留，只删除明确不可见的元素，同时考虑名称暗示
                    def process_visible_elements(elements, element_type, visual_cues):
                        """柔性处理可见元素列表，只删除明确不可见的元素"""
                        if not elements or elements == f"no visible {element_type}":
                            # 如果没有可见元素，但名称有视觉暗示，添加合理的可见元素
                            if visual_cues and element_type == "fruit":
                                # 为名称中的视觉暗示添加合理的可见形式
                                suggested_elements = []
                                for cue in visual_cues:
                                    if cue == "pineapple":
                                        suggested_elements.append("pineapple slice")
                                    elif cue == "lemon":
                                        suggested_elements.append("lemon twist")
                                    elif cue == "lime":
                                        suggested_elements.append("lime wheel")
                                    elif cue == "orange":
                                        suggested_elements.append("orange slice")
                                    elif cue == "cherry":
                                        suggested_elements.append("cherry")
                                    elif cue == "olive":
                                        suggested_elements.append("olive")
                                if suggested_elements:
                                    return ", ".join(suggested_elements)
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
                    
                    # 提取名称中的视觉暗示
                    visual_cues = extract_visual_cues_from_name(cocktail_name)
                    
                    # 1. 处理可见水果元素 - 柔性保留，考虑名称暗示
                    current_fruits = drink_attrs.get("visible_fruit_elements", "no visible fruit")
                    drink_attrs["visible_fruit_elements"] = process_visible_elements(current_fruits, "fruit", visual_cues)
                    
                    # 2. 处理可见草本元素 - 柔性保留
                    current_herbs = drink_attrs.get("visible_herb_elements", "no visible herbs")
                    drink_attrs["visible_herb_elements"] = process_visible_elements(current_herbs, "herbs", visual_cues)
                    
                    # 3. 处理可见装饰 - 柔性保留
                    current_garnishes = drink_attrs.get("visible_garnishes", "no visible garnishes")
                    drink_attrs["visible_garnishes"] = process_visible_elements(current_garnishes, "garnishes", visual_cues)
                    
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
                
                # 兼容处理：为所有字段设置默认值，处理旧格式的garnish字段
                # 设置所有字段的默认值
                default_attrs = {
                    "glass_type": "rocks glass",
                    "cocktail_type": "mixed drink",
                    "drink_color": "clear",
                    "transparency": "clear",
                    "ice_type": "no ice",
                    "carbonation": "non-carbonated",
                    "rim_style": "no rim",
                    "visible_garnishes": "no visible garnishes",
                    "visible_fruit_elements": "no visible fruit",
                    "visible_herb_elements": "no visible herbs",
                    "non_visible_flavor_cues": "",
                    "serving_style": "up"
                }
                
                # 合并LLM返回的字段和默认值
                for key in default_attrs:
                    if key not in drink_attrs:
                        drink_attrs[key] = default_attrs[key]
                
                # 处理旧格式的garnish字段，映射到新字段
                if "garnish" in drink_attrs:
                    old_garnish = drink_attrs["garnish"]
                    if old_garnish and old_garnish != "no garnish":
                        drink_attrs["visible_garnishes"] = old_garnish
                
                # 调用可见性判定层对LLM输出进行纠偏，传入鸡尾酒名称以提取视觉暗示
                drink_attrs = postprocess_drink_attrs(drink_attrs, recipe_instructions, recipe_ingredients, recipe_name)
                
                log("LLM调用成功，返回了有效的鸡尾酒核心属性")
                
                # 获取固定摄影风格
                photo_style = get_photo_style()
                
                # 精确短语匹配 - 杯口样式
                text_all_lower = (recipe_instructions + " " + recipe_ingredients).lower()
                rim_phrases = [
                    ("salt rim", "salted rim"),
                    ("salted rim", "salted rim"),
                    ("sugar rim", "sugared rim"),
                    ("sugared rim", "sugared rim"),
                    ("tajin rim", "tajin rim"),
                    ("tajin", "tajin rim"),
                    ("spiced rim", "spiced rim"),
                ]
                
                for phrase, style in rim_phrases:
                    if phrase in text_all_lower:
                        drink_attrs["rim_style"] = style
                        break  # 只取第一个匹配的杯口样式
                
                # 程序级颜色规则 - 只在LLM没有返回明确颜色或颜色不合理时才使用
                # 建立颜色优先级体系，不简单覆盖
                # 1. 强着色剂规则（优先级最高）
                strong_colorant_rules = [
                    ("hibiscus" in text_all_lower or "洛神花" in text_all_lower, "deep ruby red", "reddish translucent", "hibiscus syrup"),
                    ("blue cura" in text_all_lower or "blue curacao" in text_all_lower, "bright blue", None, None),
                    ("coffee" in text_all_lower or "espresso" in text_all_lower, "dark coffee brown", None, None),
                    ("cranberry" in text_all_lower, "cranberry red", None, "cranberry juice"),
                    ("matcha" in text_all_lower, "vibrant green", None, None),
                    ("beet" in text_all_lower, "deep beet red", None, None),
                    ("blackberry" in text_all_lower, "dark purple", None, None),
                    ("raspberry" in text_all_lower, "raspberry red", None, None),
                    ("blueberry" in text_all_lower, "blue-purple", None, None),
                ]
                
                # 2. 菠萝类饮料规则（优先级中等）
                pineapple_rules = [
                    ("pineapple" in text_all_lower and not any(strong_color in text_all_lower for strong_color in ["hibiscus", "blue cura", "blue curacao", "coffee", "espresso", "cranberry", "matcha", "beet", "blackberry", "raspberry", "blueberry"]), "pale yellow", None, "pineapple syrup"),
                    ("pineapple gomme" in text_all_lower and not any(strong_color in text_all_lower for strong_color in ["hibiscus", "blue cura", "blue curacao", "coffee", "espresso", "cranberry", "matcha", "beet", "blackberry", "raspberry", "blueberry"]), "straw yellow", None, "pineapple gomme"),
                    ("pineapple juice" in text_all_lower and not any(strong_color in text_all_lower for strong_color in ["hibiscus", "blue cura", "blue curacao", "coffee", "espresso", "cranberry", "matcha", "beet", "blackberry", "raspberry", "blueberry"]), "golden yellow", None, "pineapple juice"),
                ]
                
                # 3. 其他果汁/糖浆规则（优先级较低）
                other_fluid_rules = [
                    ("syrup" in text_all_lower and not any(strong_color in text_all_lower for strong_color in ["hibiscus", "blue cura", "blue curacao", "coffee", "espresso", "cranberry", "matcha", "beet", "blackberry", "raspberry", "blueberry", "pineapple"]), "light amber", None, "simple syrup"),
                    ("gomme" in text_all_lower and not any(strong_color in text_all_lower for strong_color in ["hibiscus", "blue cura", "blue curacao", "coffee", "espresso", "cranberry", "matcha", "beet", "blackberry", "raspberry", "blueberry", "pineapple"]), "pale golden", None, "gomme syrup"),
                ]
                
                # 只在LLM返回的颜色是默认值或不合理时才应用颜色规则
                if drink_attrs["drink_color"] in ["clear", "default"]:
                    # 首先检查强着色剂规则
                    for condition, color, transparency, flavor in strong_colorant_rules:
                        if condition:
                            drink_attrs["drink_color"] = color
                            if transparency:
                                drink_attrs["transparency"] = transparency
                            if flavor and flavor not in drink_attrs["non_visible_flavor_cues"]:
                                drink_attrs["non_visible_flavor_cues"] = flavor
                            break
                    else:
                        # 然后检查菠萝类饮料规则
                        for condition, color, transparency, flavor in pineapple_rules:
                            if condition:
                                drink_attrs["drink_color"] = color
                                if transparency:
                                    drink_attrs["transparency"] = transparency
                                if flavor and flavor not in drink_attrs["non_visible_flavor_cues"]:
                                    drink_attrs["non_visible_flavor_cues"] = flavor
                                break
                        else:
                            # 最后检查其他果汁/糖浆规则
                            for condition, color, transparency, flavor in other_fluid_rules:
                                if condition:
                                    drink_attrs["drink_color"] = color
                                    if transparency:
                                        drink_attrs["transparency"] = transparency
                                    if flavor and flavor not in drink_attrs["non_visible_flavor_cues"]:
                                        drink_attrs["non_visible_flavor_cues"] = flavor
                                    break
                
                # 添加透明度推断规则，确保不同类型的鸡尾酒有合适的透明度
                # 检查透明度是否合理，根据鸡尾酒类型和原料调整
                def infer_transparency(cocktail_type, ingredients, drink_color):
                    """根据鸡尾酒类型和原料推断合理的透明度"""
                    ingredients_lower = ingredients.lower()
                    cocktail_type_lower = cocktail_type.lower()
                    
                    # 明确透明的情况
                    if any(keyword in ingredients_lower for keyword in ["vodka", "gin", "rum", "tequila", "whiskey", "scotch", "brandy", "cognac", "vodka", "soda", "tonic", "water"]):
                        return "clear"
                    
                    # 明确半透明的情况
                    if any(keyword in ingredients_lower for keyword in ["juice", "syrup", "liqueur", "wine", "vermouth"]):
                        return "translucent"
                    
                    # 明确不透明的情况
                    if any(keyword in ingredients_lower for keyword in ["cream", "milk", "egg", "yolk", "matcha", "avocado", "mango", "banana", "ice cream"]):
                        return "opaque"
                    
                    # 根据鸡尾酒类型调整
                    if any(type in cocktail_type_lower for type in ["sour", "daiquiri", "margarita", "cosmopolitan"]):
                        return "translucent"
                    elif any(type in cocktail_type_lower for type in ["martini", "negroni", "old fashioned", "manhattan"]):
                        return "clear"
                    elif any(type in cocktail_type_lower for type in ["milk", "cream", "egg"]):
                        return "opaque"
                    
                    # 默认返回clear，除非颜色是深色
                    if drink_color in ["clear", "pale yellow", "light amber", "pale golden"]:
                        return "clear"
                    else:
                        return "translucent"
                
                # 如果LLM返回的透明度不合理，根据规则调整
                current_transparency = drink_attrs["transparency"]
                inferred_transparency = infer_transparency(
                    drink_attrs["cocktail_type"], 
                    recipe_ingredients, 
                    drink_attrs["drink_color"]
                )
                
                # 只有在当前透明度明显不合理时才调整
                if current_transparency in ["opaque", "cloudy"] and inferred_transparency in ["clear", "translucent"]:
                    drink_attrs["transparency"] = inferred_transparency
                elif current_transparency == "clear" and inferred_transparency == "opaque":
                    drink_attrs["transparency"] = inferred_transparency
                
                # 生成正提示词，使用固定摄影模板，加强颜色约束
                glass_type = drink_attrs["glass_type"]
                cocktail_type = drink_attrs["cocktail_type"]
                drink_color = drink_attrs["drink_color"]
                transparency = drink_attrs["transparency"]
                ice_type = drink_attrs["ice_type"]
                carbonation = drink_attrs["carbonation"]
                rim_style = drink_attrs["rim_style"]
                visible_fruit_elements = drink_attrs["visible_fruit_elements"]
                visible_herb_elements = drink_attrs["visible_herb_elements"]
                visible_garnishes = drink_attrs["visible_garnishes"]
                
                # 构建基础提示词
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
                
                # 只添加通过校验的可见元素
                if visible_fruit_elements and visible_fruit_elements != "no visible fruit":
                    positive_prompt_parts.append(visible_fruit_elements)
                
                if visible_herb_elements and visible_herb_elements != "no visible herbs":
                    positive_prompt_parts.append(visible_herb_elements)
                
                if visible_garnishes and visible_garnishes != "no visible garnishes":
                    positive_prompt_parts.append(visible_garnishes)
                
                # 合并所有提示词部分
                positive_prompt = ", ".join(positive_prompt_parts)
                
                # 生成负提示词，只保留防止明显错误的关键约束
                negative_prompt = (
                    "two glasses, multiple drinks, duplicate glass, extra glass, overlapping glasses, "
                    "stacked glasses, mirrored second glass, reflection that looks like a second drink, "
                    "deformed glass, warped glass, twisted rim, uneven rim, broken proportions, "
                    "blurry, low quality, noisy image, "
                    "text, watermark, logo, "
                    "unsupported oversized garnish"
                )
                
                # 返回最终prompt
                final_prompts = {
                    "positive_prompt": positive_prompt,
                    "negative_prompt": negative_prompt
                }
                log(f"生成的最终正提示词: {final_prompts['positive_prompt'][:150]}...")
                log(f"生成的最终负提示词: {final_prompts['negative_prompt'][:150]}...")
                return final_prompts
        except json.JSONDecodeError as e:
            # JSON解析错误，记录详细错误信息并重试
            log(f"LLM返回内容JSON解析失败: {e}")
            log(f"原始返回内容: {raw}")
            if retry < max_retries - 1:
                log("将重试调用LLM...")
            continue
        except Exception as e:
            # 其他异常，记录详细错误信息并重试
            log(f"LLM调用发生异常: {e}")
            log(f"异常类型: {type(e).__name__}")
            log(f"异常详情: {traceback.format_exc()}")
            if retry < max_retries - 1:
                log("将重试调用LLM...")
            continue
    
    # 所有重试都失败，抛出异常
    log("错误: LLM调用多次失败，无法生成prompt")
    raise RuntimeError("LLM调用多次失败，无法生成有效的prompt")


def generate_image_with_sd_api(prompt: str, negative_prompt: str) -> bytes:
    """调用SD API生成图片"""
    try:
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "steps": 24,
            "width": 512,
            "height": 768,
            "cfg_scale": 6.5,
            "sampler_name": "DPM++ 2M Karras"
        }
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        payload_json = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(SD_API_URL, data=payload_json, headers=headers, method='POST')
        
        with urllib.request.urlopen(req, timeout=300) as response:
            response_data = response.read().decode('utf-8')
            
            try:
                r = json.loads(response_data)
                
                if isinstance(r, dict):
                    if "images" in r and len(r["images"]) > 0:
                        image_b64 = r["images"][0]
                        image_data = base64.b64decode(image_b64)
                        return image_data
                    elif "error" in r:
                        log(f"SD API错误: {r['error']}")
                
                return None
                
            except json.JSONDecodeError:
                log("SD API响应JSON解析失败")
                return None
                
    except Exception as e:
        log(f"调用SD API生成图片时发生异常: {e}")
        return None


def save_image(image_data: bytes, output_dir: str, recipe_id: int) -> None:
    """保存图片到指定目录"""
    os.makedirs(output_dir, exist_ok=True)
    image_path = os.path.join(output_dir, f"{recipe_id}.png")
    
    with open(image_path, "wb") as f:
        f.write(image_data)
    
    log(f"图片已保存: {image_path}")


def main() -> None:
    """主函数"""
    # 初始化日志
    log("=== 开始正式生成recipe图片 ===")
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    log(f"输出目录: {OUTPUT_DIR}")
    
    # 原料CSV路径
    INGREDIENTS_CSV_PATH = "d:/items/cocktail_gnn/preparation/data/ingredient/recipe_canonical.csv"
    
    # 读取recipe数据
    log(f"正在读取CSV文件: {CSV_PATH}")
    recipes = read_recipes_from_csv(CSV_PATH, INGREDIENTS_CSV_PATH)
    total_recipes = len(recipes)
    log(f"共读取到 {total_recipes} 个recipe")
    
    # 手动实现进度条
    def update_progress(current, total, status=""):
        bar_length = 30
        filled_length = int(round(bar_length * current / float(total)))
        percent = round(100.0 * current / float(total), 1)
        bar = "=" * filled_length + "-" * (bar_length - filled_length)
        sys.stdout.write(f"\r[{bar}] {percent}% ({current}/{total}) {status}")
        sys.stdout.flush()
    
    # 处理每个recipe
    processed_count = 0
    skipped_count = 0
    success_count = 0
    failed_count = 0
    
    update_progress(0, total_recipes, "初始化...")
    
    for i, (recipe_id, recipe) in enumerate(recipes.items(), 1):
        # 检查图片是否已存在，如果已存在则跳过
        image_path = os.path.join(OUTPUT_DIR, f"{recipe_id}.png")
        if os.path.exists(image_path):
            log(f"图片已存在，跳过: {image_path}")
            skipped_count += 1
            processed_count += 1
            update_progress(processed_count, total_recipes, f"已跳过 {skipped_count} 个")
            continue
            
        try:
            # 调用LLM生成prompt
            prompts = call_llm_for_prompts(recipe['name'], recipe['instructions'], recipe['ingredients'])
            
            # 调用SD API生成图片
            image_data = generate_image_with_sd_api(
                prompts["positive_prompt"],
                prompts["negative_prompt"]
            )
            
            if image_data:
                # 保存图片
                save_image(image_data, OUTPUT_DIR, recipe_id)
                success_count += 1
                log(f"✓ 图片生成成功: {image_path}")
            else:
                failed_count += 1
                log(f"✗ 生成图片失败: recipe {recipe_id}")
        except Exception as e:
            failed_count += 1
            log(f"✗ 处理失败: recipe {recipe_id}, 错误: {e}")
        finally:
            processed_count += 1
            update_progress(processed_count, total_recipes, f"成功 {success_count}, 失败 {failed_count}, 跳过 {skipped_count}")
    
    # 完成后的统计信息
    sys.stdout.write("\n")
    log(f"\n=== 所有recipe处理完成 ===")
    log(f"总计: {total_recipes} 个recipe")
    log(f"已处理: {processed_count} 个")
    log(f"跳过: {skipped_count} 个")
    log(f"成功: {success_count} 个")
    log(f"失败: {failed_count} 个")


if __name__ == "__main__":
    main()