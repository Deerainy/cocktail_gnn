"""
实体识别器

用于从用户查询中提取食谱、食材等实体，采用分层实体识别方法
"""

import re
import os
import json
from typing import Dict, Any, List, Optional


class EntityRecognizer:
    """
    实体识别器类
    用于从用户查询中提取食谱、食材等实体
    采用分层实体识别方法：
    1. 领域词典/规则匹配做第一层
    2. 相似召回或模糊匹配做第二层
    3. 轻量 NER / span 分类模型做第三层兜底
    4. 最后接实体归一化（entity linking）到库或图谱 ID
    """

    def __init__(self):
        """
        初始化实体识别器
        """
        # 确保日志目录存在
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "entity_recognition_log.txt")
        
        # 定义领域词典
        self._init_domain_dictionaries()

    def _init_domain_dictionaries(self):
        """
        初始化领域词典
        """
        # 食谱词典
        self.recipe_dict = {
            "margarita": "Margarita",
            "mojito": "Mojito",
            "cosmopolitan": "Cosmopolitan",
            "martini": "Martini",
            "bloody mary": "Bloody Mary",
            "negroni": "Negroni",
            "old fashioned": "Old Fashioned",
            "gin and tonic": "Gin and Tonic",
            "whiskey sour": "Whiskey Sour",
            "daiquiri": "Daiquiri",
            "piña colada": "Piña Colada",
            "moscow mule": "Moscow Mule",
            "sex on the beach": "Sex on the Beach",
            "sangria": "Sangria",
            "mai tai": "Mai Tai",
            "pisco punch": "Pisco Punch"
        }
        
        # 食材词典
        self.ingredient_dict = {
            "lime juice": "lime juice",
            "lemon juice": "lemon juice",
            "gin": "gin",
            "vodka": "vodka",
            "rum": "rum",
            "tequila": "tequila",
            "whiskey": "whiskey",
            "bourbon": "bourbon",
            "scotch": "scotch",
            "brandy": "brandy",
            "cognac": "cognac",
            "sherry": "sherry",
            "port": "port",
            "beer": "beer",
            "wine": "wine",
            "champagne": "champagne",
            "soda water": "soda water",
            "tonic water": "tonic water",
            "ginger ale": "ginger ale",
            "cola": "cola",
            "orange juice": "orange juice",
            "cranberry juice": "cranberry juice",
            "pineapple juice": "pineapple juice",
            "grapefruit juice": "grapefruit juice",
            "tomato juice": "tomato juice",
            "simple syrup": "simple syrup",
            "honey": "honey",
            "maple syrup": "maple syrup",
            "bitters": "bitters",
            "grenadine": "grenadine",
            "triple sec": "triple sec",
            "cointreau": "cointreau",
            "grand marnier": "grand marnier",
            "campari": "campari",
            "aperol": "aperol",
            "sambuca": "sambuca",
            "amaretto": "amaretto",
            "kahlua": "kahlua",
            "baileys": "baileys",
            "irish cream": "irish cream",
            "coffee liqueur": "coffee liqueur",
            "chocolate liqueur": "chocolate liqueur",
            "vanilla liqueur": "vanilla liqueur",
            "coconut liqueur": "coconut liqueur",
            "melon liqueur": "melon liqueur",
            "peach liqueur": "peach liqueur",
            "raspberry liqueur": "raspberry liqueur",
            "strawberry liqueur": "strawberry liqueur",
            "blue curacao": "blue curacao",
            "green chartreuse": "green chartreuse",
            "yellow chartreuse": "yellow chartreuse",
            "absinthe": "absinthe",
            "anisette": "anisette",
            "ouzo": "ouzo",
            "pastis": "pastis",
            "sake": "sake",
            "soju": "soju",
            "mezcal": "mezcal",
            "pisco": "pisco",
            "cachaça": "cachaça",
            "agave syrup": "agave syrup",
            "brown sugar": "brown sugar",
            "white sugar": "white sugar",
            "demerara sugar": "demerara sugar",
            "turbinado sugar": "turbinado sugar",
            "caster sugar": "caster sugar",
            "icing sugar": "icing sugar",
            "honey syrup": "honey syrup",
            "agave nectar": "agave nectar",
            "corn syrup": "corn syrup",
            "molasses": "molasses",
            "caramel syrup": "caramel syrup",
            "chocolate syrup": "chocolate syrup",
            "vanilla syrup": "vanilla syrup",
            "fruit puree": "fruit puree",
            "fruit juice": "fruit juice",
            "herbs": "herbs",
            "spices": "spices",
            "salt": "salt",
            "pepper": "pepper",
            "olive": "olive",
            "cherry": "cherry",
            "lemon twist": "lemon twist",
            "lime twist": "lime twist",
            "orange twist": "orange twist",
            "mint leaf": "mint leaf",
            "basil leaf": "basil leaf",
            "thyme": "thyme",
            "rosemary": "rosemary",
            "sage": "sage",
            "cilantro": "cilantro",
            "parsley": "parsley",
            "dill": "dill",
            "tarragon": "tarragon",
            "chives": "chives",
            "oregano": "oregano",
            "marjoram": "marjoram",
            "bay leaf": "bay leaf",
            "cinnamon": "cinnamon",
            "nutmeg": "nutmeg",
            "clove": "clove",
            "allspice": "allspice",
            "ginger": "ginger",
            "cardamom": "cardamom",
            "coriander": "coriander",
            "cumin": "cumin",
            "paprika": "paprika",
            "chili powder": "chili powder",
            "cayenne pepper": "cayenne pepper",
            "black pepper": "black pepper",
            "white pepper": "white pepper",
            "pink pepper": "pink pepper",
            "green pepper": "green pepper",
            "red pepper": "red pepper",
            "yellow pepper": "yellow pepper",
            "orange pepper": "orange pepper",
            "purple pepper": "purple pepper",
            "sea salt": "sea salt",
            "kosher salt": "kosher salt",
            "table salt": "table salt",
            "pink salt": "pink salt",
            "black salt": "black salt",
            "white salt": "white salt",
            "green salt": "green salt",
            "red salt": "red salt",
            "yellow salt": "yellow salt",
            "orange salt": "orange salt",
            "purple salt": "purple salt",
            "hibiscus syrup": "hibiscus syrup"
        }
        
        # 规范食材词典
        self.canonical_dict = {
            "lime": "lime",
            "lemon": "lemon",
            "gin": "gin",
            "vodka": "vodka",
            "rum": "rum",
            "tequila": "tequila",
            "whiskey": "whiskey",
            "bourbon": "bourbon",
            "scotch": "scotch",
            "brandy": "brandy",
            "cognac": "cognac",
            "sherry": "sherry",
            "port": "port",
            "beer": "beer",
            "wine": "wine",
            "champagne": "champagne",
            "soda water": "soda water",
            "tonic water": "tonic water",
            "ginger ale": "ginger ale",
            "cola": "cola",
            "orange juice": "orange juice",
            "cranberry juice": "cranberry juice",
            "pineapple juice": "pineapple juice",
            "grapefruit juice": "grapefruit juice",
            "tomato juice": "tomato juice",
            "simple syrup": "simple syrup",
            "honey": "honey",
            "maple syrup": "maple syrup",
            "bitters": "bitters",
            "grenadine": "grenadine",
            "triple sec": "triple sec",
            "cointreau": "cointreau",
            "grand marnier": "grand marnier",
            "campari": "campari",
            "aperol": "aperol",
            "sambuca": "sambuca",
            "amaretto": "amaretto",
            "kahlua": "kahlua",
            "baileys": "baileys",
            "irish cream": "irish cream",
            "coffee liqueur": "coffee liqueur",
            "chocolate liqueur": "chocolate liqueur",
            "vanilla liqueur": "vanilla liqueur",
            "coconut liqueur": "coconut liqueur",
            "melon liqueur": "melon liqueur",
            "peach liqueur": "peach liqueur",
            "raspberry liqueur": "raspberry liqueur",
            "strawberry liqueur": "strawberry liqueur",
            "blue curacao": "blue curacao",
            "green chartreuse": "green chartreuse",
            "yellow chartreuse": "yellow chartreuse",
            "absinthe": "absinthe",
            "anisette": "anisette",
            "ouzo": "ouzo",
            "pastis": "pastis",
            "sake": "sake",
            "soju": "soju",
            "mezcal": "mezcal",
            "pisco": "pisco",
            "cachaça": "cachaça",
            "agave syrup": "agave syrup",
            "brown sugar": "brown sugar",
            "white sugar": "white sugar",
            "demerara sugar": "demerara sugar",
            "turbinado sugar": "turbinado sugar",
            "caster sugar": "caster sugar",
            "icing sugar": "icing sugar",
            "honey syrup": "honey syrup",
            "agave nectar": "agave nectar",
            "corn syrup": "corn syrup",
            "molasses": "molasses",
            "caramel syrup": "caramel syrup",
            "chocolate syrup": "chocolate syrup",
            "vanilla syrup": "vanilla syrup",
            "fruit puree": "fruit puree",
            "fruit juice": "fruit juice",
            "herbs": "herbs",
            "spices": "spices",
            "salt": "salt",
            "pepper": "pepper",
            "olive": "olive",
            "cherry": "cherry",
            "lemon twist": "lemon twist",
            "lime twist": "lime twist",
            "orange twist": "orange twist",
            "mint leaf": "mint leaf",
            "basil leaf": "basil leaf",
            "thyme": "thyme",
            "rosemary": "rosemary",
            "sage": "sage",
            "cilantro": "cilantro",
            "parsley": "parsley",
            "dill": "dill",
            "tarragon": "tarragon",
            "chives": "chives",
            "oregano": "oregano",
            "marjoram": "marjoram",
            "bay leaf": "bay leaf",
            "cinnamon": "cinnamon",
            "nutmeg": "nutmeg",
            "clove": "clove",
            "allspice": "allspice",
            "ginger": "ginger",
            "cardamom": "cardamom",
            "coriander": "coriander",
            "cumin": "cumin",
            "paprika": "paprika",
            "chili powder": "chili powder",
            "cayenne pepper": "cayenne pepper",
            "black pepper": "black pepper",
            "white pepper": "white pepper",
            "pink pepper": "pink pepper",
            "green pepper": "green pepper",
            "red pepper": "red pepper",
            "yellow pepper": "yellow pepper",
            "orange pepper": "orange pepper",
            "purple pepper": "purple pepper",
            "sea salt": "sea salt",
            "kosher salt": "kosher salt",
            "table salt": "table salt",
            "pink salt": "pink salt",
            "black salt": "black salt",
            "white salt": "white salt",
            "green salt": "green salt",
            "red salt": "red salt",
            "yellow salt": "yellow salt",
            "orange salt": "orange salt",
            "purple salt": "purple salt",
            "hibiscus syrup": "hibiscus syrup",
            "agave": "agave",
            "sugar": "sugar"
        }
        
        # 风味词典
        self.flavor_dict = {
            "smoky": "smoky",
            "sour": "sour",
            "fruity": "fruity",
            "floral": "floral",
            "sweet": "sweet",
            "bitter": "bitter",
            "spicy": "spicy",
            "herbal": "herbal",
            "citrus": "citrus",
            "woody": "woody",
            "earthy": "earthy",
            "nutty": "nutty",
            "creamy": "creamy",
            "vanilla": "vanilla",
            "chocolate": "chocolate",
            "coffee": "coffee",
            "caramel": "caramel",
            "honey": "honey",
            "maple": "maple",
            "cinnamon": "cinnamon",
            "nutmeg": "nutmeg",
            "clove": "clove",
            "allspice": "allspice",
            "ginger": "ginger",
            "cardamom": "cardamom",
            "coriander": "coriander",
            "cumin": "cumin",
            "paprika": "paprika",
            "chili": "chili",
            "cayenne": "cayenne",
            "black pepper": "black pepper",
            "white pepper": "white pepper",
            "pink pepper": "pink pepper",
            "green pepper": "green pepper",
            "red pepper": "red pepper",
            "yellow pepper": "yellow pepper",
            "orange pepper": "orange pepper",
            "purple pepper": "purple pepper",
            "lime": "lime",
            "lemon": "lemon",
            "orange": "orange",
            "grapefruit": "grapefruit",
            "pineapple": "pineapple",
            "cranberry": "cranberry",
            "strawberry": "strawberry",
            "raspberry": "raspberry",
            "blueberry": "blueberry",
            "blackberry": "blackberry",
            "cherry": "cherry",
            "apple": "apple",
            "pear": "pear",
            "peach": "peach",
            "apricot": "apricot",
            "plum": "plum",
            "fig": "fig",
            "date": "date",
            "honeydew": "honeydew",
            "cantaloupe": "cantaloupe",
            "watermelon": "watermelon",
            "mango": "mango",
            "papaya": "papaya",
            "guava": "guava",
            "kiwi": "kiwi",
            "passion fruit": "passion fruit",
            "lychee": "lychee",
            "dragon fruit": "dragon fruit",
            "pomegranate": "pomegranate",
            "coconut": "coconut",
            "banana": "banana",
            "avocado": "avocado",
            "tomato": "tomato",
            "cucumber": "cucumber",
            "bell pepper": "bell pepper",
            "jalapeno": "jalapeno",
            "serrano": "serrano",
            "habanero": "habanero",
            "ghost pepper": "ghost pepper",
            "tabasco": "tabasco",
            "sriracha": "sriracha",
            "wasabi": "wasabi",
            "horseradish": "horseradish",
            "mustard": "mustard",
            "ketchup": "ketchup",
            "mayonnaise": "mayonnaise",
            "ranch": "ranch",
            "blue cheese": "blue cheese",
            "caesar": "caesar",
            "vinaigrette": "vinaigrette",
            "tahini": "tahini",
            "hummus": "hummus",
            "guacamole": "guacamole",
            "salsa": "salsa",
            "pico de gallo": "pico de gallo",
            "guacamole": "guacamole",
            "salsa": "salsa",
            "pico de gallo": "pico de gallo",
            "taco sauce": "taco sauce",
            "enchilada sauce": "enchilada sauce",
            "chili sauce": "chili sauce",
            "hot sauce": "hot sauce",
            "barbecue sauce": "barbecue sauce",
            "teriyaki sauce": "teriyaki sauce",
            "soy sauce": "soy sauce",
            "fish sauce": "fish sauce",
            "oyster sauce": "oyster sauce",
            "hoisin sauce": "hoisin sauce",
            "plum sauce": "plum sauce",
            "sweet and sour sauce": "sweet and sour sauce",
            "duck sauce": "duck sauce",
            "orange sauce": "orange sauce",
            "lemon sauce": "lemon sauce",
            "lime sauce": "lime sauce",
            "tartar sauce": "tartar sauce",
            "cocktail sauce": "cocktail sauce",
            "remoulade": "remoulade",
            "aioli": "aioli",
            "garlic aioli": "garlic aioli",
            "chipotle aioli": "chipotle aioli",
            "tahini sauce": "tahini sauce",
            "yogurt sauce": "yogurt sauce",
            "raita": "raita",
            "tzatziki": "tzatziki",
            "honey mustard": "honey mustard",
            "dijon mustard": "dijon mustard",
            "whole grain mustard": "whole grain mustard",
            "spicy brown mustard": "spicy brown mustard",
            "yellow mustard": "yellow mustard",
            "stone ground mustard": "stone ground mustard",
            "wasabi mustard": "wasabi mustard",
            "horseradish mustard": "horseradish mustard",
            "maple mustard": "maple mustard",
            "honey dijon mustard": "honey dijon mustard",
            "balsamic vinaigrette": "balsamic vinaigrette",
            "italian dressing": "italian dressing",
            "french dressing": "french dressing",
            "ranch dressing": "ranch dressing",
            "blue cheese dressing": "blue cheese dressing",
            "caesar dressing": "caesar dressing",
            "thousand island dressing": "thousand island dressing",
            "honey mustard dressing": "honey mustard dressing",
            "vinaigrette": "vinaigrette",
            "oil and vinegar dressing": "oil and vinegar dressing",
            "greek dressing": "greek dressing",
            "creamy italian dressing": "creamy italian dressing",
            "creamy ranch dressing": "creamy ranch dressing",
            "creamy blue cheese dressing": "creamy blue cheese dressing",
            "creamy caesar dressing": "creamy caesar dressing",
            "creamy thousand island dressing": "creamy thousand island dressing",
            "creamy honey mustard dressing": "creamy honey mustard dressing",
            "creamy vinaigrette": "creamy vinaigrette",
            "creamy oil and vinegar dressing": "creamy oil and vinegar dressing",
            "creamy greek dressing": "creamy greek dressing"
        }
        
        # 角色词典
        self.role_dict = {
            "base spirit": "base spirit",
            "acid": "acid",
            "sweetener": "sweetener",
            "garnish": "garnish",
            "bitters": "bitters",
            " modifier": "modifier",
            "liqueur": "liqueur",
            "mixer": "mixer",
            "syrup": "syrup",
            "juice": "juice",
            "herb": "herb",
            "spice": "spice",
            "fruit": "fruit",
            "vegetable": "vegetable",
            "nut": "nut",
            "seed": "seed",
            "flower": "flower",
            "bark": "bark",
            "root": "root",
            "leaf": "leaf",
            "stem": "stem",
            "bulb": "bulb",
            "tuber": "tuber",
            "fruit juice": "fruit juice",
            "vegetable juice": "vegetable juice",
            "herb juice": "herb juice",
            "spice juice": "spice juice",
            "fruit puree": "fruit puree",
            "vegetable puree": "vegetable puree",
            "herb puree": "herb puree",
            "spice puree": "spice puree",
            "fruit syrup": "fruit syrup",
            "vegetable syrup": "vegetable syrup",
            "herb syrup": "herb syrup",
            "spice syrup": "spice syrup",
            "fruit liqueur": "fruit liqueur",
            "vegetable liqueur": "vegetable liqueur",
            "herb liqueur": "herb liqueur",
            "spice liqueur": "spice liqueur",
            "fruit bitters": "fruit bitters",
            "vegetable bitters": "vegetable bitters",
            "herb bitters": "herb bitters",
            "spice bitters": "spice bitters"
        }
        
        # 动作词典
        self.action_dict = {
            "replace": "replace",
            "remove": "remove",
            "add": "add",
            "recommend": "recommend",
            "explain": "explain",
            "find": "find",
            "search": "search",
            "show": "show",
            "display": "display",
            "list": "list",
            "suggest": "suggest",
            "propose": "propose",
            "offer": "offer",
            "provide": "provide",
            "give": "give",
            "tell": "tell",
            "describe": "describe",
            "explain": "explain",
            "clarify": "clarify",
            "elaborate": "elaborate",
            "detail": "detail",
            "specify": "specify",
            "identify": "identify",
            "recognize": "recognize",
            "detect": "detect",
            "find": "find",
            "locate": "locate",
            "discover": "discover",
            "uncover": "uncover",
            "reveal": "reveal",
            "expose": "expose",
            "show": "show",
            "display": "display",
            "present": "present",
            "exhibit": "exhibit",
            "demonstrate": "demonstrate",
            "illustrate": "illustrate",
            "depict": "depict",
            "portray": "portray",
            "represent": "represent",
            "symbolize": "symbolize",
            "embody": "embody",
            "incarnate": "incarnate",
            "personify": "personify",
            "typify": "typify",
            "epitomize": "epitomize",
            "exemplify": "exemplify",
            "illustrate": "illustrate",
            "demonstrate": "demonstrate",
            "show": "show",
            "display": "display",
            "present": "present",
            "exhibit": "exhibit",
            "reveal": "reveal",
            "uncover": "uncover",
            "discover": "discover",
            "find": "find",
            "locate": "locate",
            "detect": "detect",
            "recognize": "recognize",
            "identify": "identify",
            "specify": "specify",
            "detail": "detail",
            "elaborate": "elaborate",
            "clarify": "clarify",
            "explain": "explain",
            "describe": "describe",
            "tell": "tell",
            "give": "give",
            "provide": "provide",
            "offer": "offer",
            "propose": "propose",
            "suggest": "suggest",
            "recommend": "recommend",
            "list": "list",
            "display": "display",
            "show": "show",
            "search": "search",
            "find": "find"
        }
        
        # 约束词典
        self.constraint_dict = {
            "no alcohol": "no alcohol",
            "low sugar": "low sugar",
            "only what I have": "only what I have",
            "vegan": "vegan",
            "vegetarian": "vegetarian",
            "gluten free": "gluten free",
            "dairy free": "dairy free",
            "nut free": "nut free",
            "soy free": "soy free",
            "shellfish free": "shellfish free",
            "fish free": "fish free",
            "meat free": "meat free",
            "pork free": "pork free",
            "beef free": "beef free",
            "chicken free": "chicken free",
            "turkey free": "turkey free",
            "duck free": "duck free",
            "goat free": "goat free",
            "sheep free": "sheep free",
            "rabbit free": "rabbit free",
            "game free": "game free",
            "low calorie": "low calorie",
            "low fat": "low fat",
            "low carb": "low carb",
            "high protein": "high protein",
            "high fiber": "high fiber",
            "low sodium": "low sodium",
            "high potassium": "high potassium",
            "low cholesterol": "low cholesterol",
            "high omega 3": "high omega 3",
            "low saturated fat": "low saturated fat",
            "high unsaturated fat": "high unsaturated fat",
            "low trans fat": "low trans fat",
            "high antioxidants": "high antioxidants",
            "low glycemic index": "low glycemic index",
            "high glycemic index": "high glycemic index",
            "low purine": "low purine",
            "high purine": "high purine",
            "low oxalate": "low oxalate",
            "high oxalate": "high oxalate",
            "low histamine": "low histamine",
            "high histamine": "high histamine",
            "low FODMAP": "low FODMAP",
            "high FODMAP": "high FODMAP",
            "low salicylate": "low salicylate",
            "high salicylate": "high salicylate",
            "low amine": "low amine",
            "high amine": "high amine",
            "low glutamine": "low glutamine",
            "high glutamine": "high glutamine",
            "low tyrosine": "low tyrosine",
            "high tyrosine": "high tyrosine",
            "low phenylalanine": "low phenylalanine",
            "high phenylalanine": "high phenylalanine",
            "low tryptophan": "low tryptophan",
            "high tryptophan": "high tryptophan",
            "low cysteine": "low cysteine",
            "high cysteine": "high cysteine",
            "low methionine": "low methionine",
            "high methionine": "high methionine",
            "low lysine": "low lysine",
            "high lysine": "high lysine",
            "low arginine": "low arginine",
            "high arginine": "high arginine",
            "low histidine": "low histidine",
            "high histidine": "high histidine",
            "low isoleucine": "low isoleucine",
            "high isoleucine": "high isoleucine",
            "low leucine": "low leucine",
            "high leucine": "high leucine",
            "low valine": "low valine",
            "high valine": "high valine",
            "low threonine": "low threonine",
            "high threonine": "high threonine",
            "low serine": "low serine",
            "high serine": "high serine",
            "low proline": "low proline",
            "high proline": "high proline",
            "low glycine": "low glycine",
            "high glycine": "high glycine",
            "low alanine": "low alanine",
            "high alanine": "high alanine",
            "low aspartic acid": "low aspartic acid",
            "high aspartic acid": "high aspartic acid",
            "low glutamic acid": "low glutamic acid",
            "high glutamic acid": "high glutamic acid",
            "low asparagine": "low asparagine",
            "high asparagine": "high asparagine",
            "low glutamine": "low glutamine",
            "high glutamine": "high glutamine",
            "low tyrosine": "low tyrosine",
            "high tyrosine": "high tyrosine",
            "low phenylalanine": "low phenylalanine",
            "high phenylalanine": "high phenylalanine",
            "low tryptophan": "low tryptophan",
            "high tryptophan": "high tryptophan",
            "low cysteine": "low cysteine",
            "high cysteine": "high cysteine",
            "low methionine": "low methionine",
            "high methionine": "high methionine",
            "low lysine": "low lysine",
            "high lysine": "high lysine",
            "low arginine": "low arginine",
            "high arginine": "high arginine",
            "low histidine": "low histidine",
            "high histidine": "high histidine",
            "low isoleucine": "low isoleucine",
            "high isoleucine": "high isoleucine",
            "low leucine": "low leucine",
            "high leucine": "high leucine",
            "low valine": "low valine",
            "high valine": "high valine",
            "low threonine": "low threonine",
            "high threonine": "high threonine",
            "low serine": "low serine",
            "high serine": "high serine",
            "low proline": "low proline",
            "high proline": "high proline",
            "low glycine": "low glycine",
            "high glycine": "high glycine",
            "low alanine": "low alanine",
            "high alanine": "high alanine",
            "low aspartic acid": "low aspartic acid",
            "high aspartic acid": "high aspartic acid",
            "low glutamic acid": "low glutamic acid",
            "high glutamic acid": "high glutamic acid",
            "low asparagine": "low asparagine",
            "high asparagine": "high asparagine"
        }
        
        # 目标词典
        self.target_dict = {
            "像 Margarita 的风味": "像 Margarita 的风味",
            "更酸一点": "更酸一点",
            "更适合夏天": "更适合夏天",
            "更适合冬天": "更适合冬天",
            "更适合春天": "更适合春天",
            "更适合秋天": "更适合秋天",
            "更适合早餐": "更适合早餐",
            "更适合午餐": "更适合午餐",
            "更适合晚餐": "更适合晚餐",
            "更适合聚会": "更适合聚会",
            "更适合约会": "更适合约会",
            "更适合商务": "更适合商务",
            "更适合休闲": "更适合休闲",
            "更适合正式": "更适合正式",
            "更适合非正式": "更适合非正式",
            "更适合儿童": "更适合儿童",
            "更适合青少年": "更适合青少年",
            "更适合成年人": "更适合成年人",
            "更适合老年人": "更适合老年人",
            "更适合男性": "更适合男性",
            "更适合女性": "更适合女性",
            "更适合素食者": "更适合素食者",
            "更适合纯素食者": "更适合纯素食者",
            "更适合肉食者": "更适合肉食者",
            "更适合海鲜爱好者": "更适合海鲜爱好者",
            "更适合坚果爱好者": "更适合坚果爱好者",
            "更适合水果爱好者": "更适合水果爱好者",
            "更适合蔬菜爱好者": "更适合蔬菜爱好者",
            "更适合巧克力爱好者": "更适合巧克力爱好者",
            "更适合咖啡爱好者": "更适合咖啡爱好者",
            "更适合茶爱好者": "更适合茶爱好者",
            "更适合酒爱好者": "更适合酒爱好者",
            "更适合啤酒爱好者": "更适合啤酒爱好者",
            "更适合葡萄酒爱好者": "更适合葡萄酒爱好者",
            "更适合烈酒爱好者": "更适合烈酒爱好者",
            "更适合鸡尾酒爱好者": "更适合鸡尾酒爱好者",
            "更适合非酒精饮料爱好者": "更适合非酒精饮料爱好者",
            "更适合健康饮食者": "更适合健康饮食者",
            "更适合减肥者": "更适合减肥者",
            "更适合增肌者": "更适合增肌者",
            "更适合健身者": "更适合健身者",
            "更适合运动员": "更适合运动员",
            "更适合上班族": "更适合上班族",
            "更适合学生": "更适合学生",
            "更适合家庭": "更适合家庭",
            "更适合单身": "更适合单身",
            "更适合情侣": "更适合情侣",
            "更适合朋友": "更适合朋友",
            "更适合家人": "更适合家人",
            "更适合客人": "更适合客人",
            "更适合主人": "更适合主人",
            "更适合厨师": "更适合厨师",
            "更适合新手": "更适合新手",
            "更适合专业人士": "更适合专业人士",
            "更适合初学者": "更适合初学者",
            "更适合进阶者": "更适合进阶者",
            "更适合专家": "更适合专家",
            "更适合业余爱好者": "更适合业余爱好者",
            "更适合专业爱好者": "更适合专业爱好者",
            "更适合休闲爱好者": "更适合休闲爱好者",
            "更适合严肃爱好者": "更适合严肃爱好者",
            "更适合收藏者": "更适合收藏者",
            "更适合投资者": "更适合投资者",
            "更适合创业者": "更适合创业者",
            "更适合企业家": "更适合企业家",
            "更适合管理者": "更适合管理者",
            "更适合员工": "更适合员工",
            "更适合自由职业者": "更适合自由职业者",
            "更适合学生": "更适合学生",
            "更适合教师": "更适合教师",
            "更适合医生": "更适合医生",
            "更适合护士": "更适合护士",
            "更适合律师": "更适合律师",
            "更适合工程师": "更适合工程师",
            "更适合设计师": "更适合设计师",
            "更适合艺术家": "更适合艺术家",
            "更适合音乐家": "更适合音乐家",
            "更适合演员": "更适合演员",
            "更适合作家": "更适合作家",
            "更适合记者": "更适合记者",
            "更适合编辑": "更适合编辑",
            "更适合摄影师": "更适合摄影师",
            "更适合摄像师": "更适合摄像师",
            "更适合导演": "更适合导演",
            "更适合制片人": "更适合制片人",
            "更适合编剧": "更适合编剧",
            "更适合演员": "更适合演员",
            "更适合歌手": "更适合歌手",
            "更适合乐队": "更适合乐队",
            "更适合 DJ": "更适合 DJ",
            "更适合舞者": "更适合舞者",
            "更适合模特": "更适合模特",
            "更适合运动员": "更适合运动员",
            "更适合教练": "更适合教练",
            "更适合裁判": "更适合裁判",
            "更适合解说员": "更适合解说员",
            "更适合评论员": "更适合评论员",
            "更适合主持人": "更适合主持人",
            "更适合播音员": "更适合播音员",
            "更适合记者": "更适合记者",
            "更适合编辑": "更适合编辑",
            "更适合作家": "更适合作家",
            "更适合诗人": "更适合诗人",
            "更适合小说家": "更适合小说家",
            "更适合散文家": "更适合散文家",
            "更适合评论家": "更适合评论家",
            "更适合学者": "更适合学者",
            "更适合教授": "更适合教授",
            "更适合研究员": "更适合研究员",
            "更适合科学家": "更适合科学家",
            "更适合工程师": "更适合工程师",
            "更适合程序员": "更适合程序员",
            "更适合设计师": "更适合设计师",
            "更适合建筑师": "更适合建筑师",
            "更适合工程师": "更适合工程师",
            "更适合医生": "更适合医生",
            "更适合护士": "更适合护士",
            "更适合药剂师": "更适合药剂师",
            "更适合牙医": "更适合牙医",
            "更适合兽医": "更适合兽医",
            "更适合律师": "更适合律师",
            "更适合法官": "更适合法官",
            "更适合检察官": "更适合检察官",
            "更适合律师助理": "更适合律师助理",
            "更适合法律顾问": "更适合法律顾问",
            "更适合财务顾问": "更适合财务顾问",
            "更适合投资顾问": "更适合投资顾问",
            "更适合税务顾问": "更适合税务顾问",
            "更适合法律顾问": "更适合法律顾问",
            "更适合人力资源顾问": "更适合人力资源顾问",
            "更适合管理顾问": "更适合管理顾问",
            "更适合营销顾问": "更适合营销顾问",
            "更适合销售顾问": "更适合销售顾问",
            "更适合客户服务顾问": "更适合客户服务顾问",
            "更适合技术顾问": "更适合技术顾问",
            "更适合IT顾问": "更适合IT顾问",
            "更适合网络顾问": "更适合网络顾问",
            "更适合安全顾问": "更适合安全顾问",
            "更适合数据顾问": "更适合数据顾问",
            "更适合分析顾问": "更适合分析顾问",
            "更适合战略顾问": "更适合战略顾问",
            "更适合业务顾问": "更适合业务顾问",
            "更适合创业顾问": "更适合创业顾问",
            "更适合企业顾问": "更适合企业顾问",
            "更适合管理顾问": "更适合管理顾问",
            "更适合营销顾问": "更适合营销顾问",
            "更适合销售顾问": "更适合销售顾问",
            "更适合客户服务顾问": "更适合客户服务顾问",
            "更适合技术顾问": "更适合技术顾问",
            "更适合IT顾问": "更适合IT顾问",
            "更适合网络顾问": "更适合网络顾问",
            "更适合安全顾问": "更适合安全顾问",
            "更适合数据顾问": "更适合数据顾问",
            "更适合分析顾问": "更适合分析顾问",
            "更适合战略顾问": "更适合战略顾问",
            "更适合业务顾问": "更适合业务顾问",
            "更适合创业顾问": "更适合创业顾问",
            "更适合企业顾问": "更适合企业顾问"
        }

    def log(self, message: str):
        """
        记录日志
        Args:
            message: 日志消息
        """
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")
        print(message)

    def recognize(self, query: str) -> Dict[str, Any]:
        """
        从用户查询中识别实体
        Args:
            query: 用户查询
        Returns: 识别结果，包含食谱、食材等实体
        """
        self.log(f"\n=== 实体识别 ===")
        self.log(f"用户查询: {query}")
        
        # 第一层：领域词典/规则匹配
        domain_entities = self._domain_dictionary_matching(query)
        
        # 第二层：相似召回或模糊匹配
        fuzzy_entities = self._fuzzy_matching(query, domain_entities)
        
        # 第三层：轻量 NER / span 分类模型（预留）
        # ner_entities = self._ner_matching(query, domain_entities, fuzzy_entities)
        
        # 合并结果
        entities = self._merge_entities(domain_entities, fuzzy_entities)
        
        # 实体归一化（预留）
        # normalized_entities = self._entity_linking(entities)
        
        # 构建识别结果
        result = {
            "entities": entities,
            "query": query
        }
        
        self.log(f"识别结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return result

    def _domain_dictionary_matching(self, query: str) -> Dict[str, List[str]]:
        """
        第一层：领域词典/规则匹配
        Args:
            query: 用户查询
        Returns: 识别出的实体
        """
        entities = {
            "RECIPE": [],
            "INGREDIENT": [],
            "CANONICAL": [],
            "FLAVOR": [],
            "ROLE": [],
            "ACTION": [],
            "CONSTRAINT": [],
            "TARGET": []
        }
        
        # 匹配食谱实体
        for recipe, normalized in self.recipe_dict.items():
            if re.search(rf"\b{re.escape(recipe)}\b", query, re.IGNORECASE):
                if normalized not in entities["RECIPE"]:
                    entities["RECIPE"].append(normalized)
        
        # 匹配食材实体
        for ingredient, normalized in self.ingredient_dict.items():
            if re.search(rf"\b{re.escape(ingredient)}\b", query, re.IGNORECASE):
                if normalized not in entities["INGREDIENT"]:
                    entities["INGREDIENT"].append(normalized)
        
        # 匹配规范食材实体
        for canonical, normalized in self.canonical_dict.items():
            if re.search(rf"\b{re.escape(canonical)}\b", query, re.IGNORECASE):
                if normalized not in entities["CANONICAL"]:
                    entities["CANONICAL"].append(normalized)
        
        # 匹配风味实体
        for flavor, normalized in self.flavor_dict.items():
            if re.search(rf"\b{re.escape(flavor)}\b", query, re.IGNORECASE):
                if normalized not in entities["FLAVOR"]:
                    entities["FLAVOR"].append(normalized)
        
        # 匹配角色实体
        for role, normalized in self.role_dict.items():
            if re.search(rf"\b{re.escape(role)}\b", query, re.IGNORECASE):
                if normalized not in entities["ROLE"]:
                    entities["ROLE"].append(normalized)
        
        # 匹配动作实体
        for action, normalized in self.action_dict.items():
            if re.search(rf"\b{re.escape(action)}\b", query, re.IGNORECASE):
                if normalized not in entities["ACTION"]:
                    entities["ACTION"].append(normalized)
        
        # 匹配约束实体
        for constraint, normalized in self.constraint_dict.items():
            if re.search(rf"\b{re.escape(constraint)}\b", query, re.IGNORECASE):
                if normalized not in entities["CONSTRAINT"]:
                    entities["CONSTRAINT"].append(normalized)
        
        # 匹配目标实体
        for target, normalized in self.target_dict.items():
            if re.search(rf"\b{re.escape(target)}\b", query, re.IGNORECASE):
                if normalized not in entities["TARGET"]:
                    entities["TARGET"].append(normalized)
        
        return entities

    def _fuzzy_matching(self, query: str, domain_entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        第二层：相似召回或模糊匹配
        Args:
            query: 用户查询
            domain_entities: 领域词典匹配结果
        Returns: 识别出的实体
        """
        # 这里可以实现模糊匹配逻辑
        # 暂时返回空结果，后续可以使用 Levenshtein 距离或其他模糊匹配算法
        return {
            "RECIPE": [],
            "INGREDIENT": [],
            "CANONICAL": [],
            "FLAVOR": [],
            "ROLE": [],
            "ACTION": [],
            "CONSTRAINT": [],
            "TARGET": []
        }

    def _ner_matching(self, query: str, domain_entities: Dict[str, List[str]], fuzzy_entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        第三层：轻量 NER / span 分类模型
        Args:
            query: 用户查询
            domain_entities: 领域词典匹配结果
            fuzzy_entities: 模糊匹配结果
        Returns: 识别出的实体
        """
        # 这里可以实现 NER 模型调用逻辑
        # 暂时返回空结果，后续可以使用 spaCy 或 Hugging Face 模型
        return {
            "RECIPE": [],
            "INGREDIENT": [],
            "CANONICAL": [],
            "FLAVOR": [],
            "ROLE": [],
            "ACTION": [],
            "CONSTRAINT": [],
            "TARGET": []
        }

    def _merge_entities(self, domain_entities: Dict[str, List[str]], fuzzy_entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        合并实体识别结果
        Args:
            domain_entities: 领域词典匹配结果
            fuzzy_entities: 模糊匹配结果
        Returns: 合并后的实体
        """
        merged = {
            "RECIPE": [],
            "INGREDIENT": [],
            "CANONICAL": [],
            "FLAVOR": [],
            "ROLE": [],
            "ACTION": [],
            "CONSTRAINT": [],
            "TARGET": []
        }
        
        # 合并领域词典匹配结果
        for entity_type, entity_list in domain_entities.items():
            for entity in entity_list:
                if entity not in merged[entity_type]:
                    merged[entity_type].append(entity)
        
        # 合并模糊匹配结果
        for entity_type, entity_list in fuzzy_entities.items():
            for entity in entity_list:
                if entity not in merged[entity_type]:
                    merged[entity_type].append(entity)
        
        return merged

    def _entity_linking(self, entities: Dict[str, List[str]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        实体归一化（entity linking）
        Args:
            entities: 识别出的实体
        Returns: 归一化后的实体
        """
        # 这里可以实现实体归一化逻辑
        # 暂时返回原实体，后续可以链接到数据库或图谱中的实体
        normalized = {}
        for entity_type, entity_list in entities.items():
            normalized[entity_type] = []
            for entity in entity_list:
                normalized[entity_type].append({
                    "name": entity,
                    "id": None,  # 后续可以添加数据库或图谱中的实体 ID
                    "score": 1.0  # 匹配得分
                })
        return normalized


# 创建全局实体识别器实例
entity_recognizer = EntityRecognizer()

