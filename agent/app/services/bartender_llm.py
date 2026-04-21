#!/usr/bin/env python3
"""
调酒师 LLM 服务

用于处理日常对话，模拟调酒师的角色，提供友好、专业的回答
"""

import os
import sys
import random
import re
from typing import Dict, Any, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 导入配置
try:
    from config import settings
except ImportError:
    print("警告: 无法导入配置模块，使用默认配置")
    class Settings:
        OPENAI_API_KEY = ""
        OPENAI_API_BASE = "http://localhost:8000/v1"
        MODEL_NAME = "deepseek-chat"
    settings = Settings()

class BartenderResponder:
    def __init__(self):
        # 动作描写：低频使用，避免每句都很浮夸
        self.stage_actions = [
            "（擦了擦杯沿）",
            "（搓了搓手）",
            "（转了转量酒器）",
            "（把吧勺轻轻一敲杯沿）",
            "（猛地 shake 了两下，又稳稳收住）",
        ]

        # 各类回复模板
        self.response_pool = {
            "greeting": [
                "你好，欢迎来到我的酒吧。今天想喝点什么？偏清爽、偏果香，还是想来点更有劲的？",
                "晚上好，欢迎入座。你负责说口味，我负责把杯子里的故事调顺。想先聊聊你喜欢什么风格吗？",
                "欢迎光临。想找一杯稳妥好喝的，还是想试点更有个性的鸡尾酒？",
            ],
            "thanks": [
                "不客气，吧台这边最不缺的就是耐心和酒谱。",
                "客气了，能帮你挑到合口味的酒，我也很有成就感。",
                "小事一桩。要是还想继续挑酒，我这边状态正好。"
            ],
            "bye": [
                "慢走，欢迎下次再来。我会把冰块和灵感都替你备好。",
                "下次见。愿你下一杯酒，刚好对味。",
                "再见，祝你今天也能遇到属于自己的那一杯。"
            ],
            "dislike_sweet": [
                "明白，你不喜欢太甜的路线。那我会优先推荐偏干爽、利落一点的酒，比如 Dry Martini，或者更轻松好入口的 Gin Tonic。",
                "懂了，甜口先收起来。你可以试试 Dry Martini，干净、直接；如果想更清爽一点，Gin Tonic 也很合适。",
                "好，那我们避开甜感明显的配方。Dry Martini 会比较克制干练，Gin Tonic 则更清爽，还带一点轻微苦感。"
            ],
            "substitution": [
                "这个得看你想换的是哪一种原料。基酒、甜味剂、酸味来源、利口酒，替代逻辑都不一样。你把具体材料告诉我，我给你按风味和可行性来分析。",
                "能替代，但要看你替的是什么。不同原料牵动的不是一个点，而是整杯酒的结构。你告诉我具体食材，我给你一个靠谱的替代方案。",
                "替代当然可以做，不过不能乱换。你告诉我原配方里是哪种材料，我帮你判断是保留酒体、保留香气，还是优先保留整体平衡。"
            ],
            "fallback": [
                "当然可以聊。你是想找推荐、问配方、做原料替代，还是想按你的口味让我直接给你配一杯思路？",
                "没问题。你可以直接告诉我你喜欢偏甜、偏酸、偏苦、偏烈，或者把你手头现有的材料报给我，我来帮你想办法。",
                "吧台已经准备好了。你想了解经典鸡尾酒、创意搭配，还是某种材料能做出什么风格，我都可以帮你。"
            ]
        }

        # 简单快捷映射：适合短句输入
        self.quick_intent_map = {
            "你好": "greeting",
            "hi": "greeting",
            "hello": "greeting",
            "谢谢": "thanks",
            "thanks": "thanks",
            "再见": "bye",
            "bye": "bye",
        }

    def _pick(self, intent: str) -> str:
        text = random.choice(self.response_pool[intent])

        # 约 30% 概率加动作描写
        if random.random() < 0.3:
            action = random.choice(self.stage_actions)
            return f"{action}{text}"
        return text

    def _contains_word(self, text: str, word: str) -> bool:
        # 防止 hi 匹配到 something 之类的单词内部
        return re.search(rf"\b{re.escape(word)}\b", text) is not None

    def reply(self, message: str) -> str:
        message_lower = message.lower().strip()

        # 1. 先处理极短的快捷输入
        if message_lower in self.quick_intent_map:
            return self._pick(self.quick_intent_map[message_lower])

        # 2. 再做规则判断
        if (
            "你好" in message_lower
            or "早上好" in message_lower
            or "下午好" in message_lower
            or "晚上好" in message_lower
            or self._contains_word(message_lower, "hi")
            or self._contains_word(message_lower, "hello")
        ):
            return self._pick("greeting")

        elif (
            ("不喜欢" in message_lower or "不爱" in message_lower or "不想要" in message_lower)
            and ("甜" in message_lower or "sweet" in message_lower)
        ):
            return self._pick("dislike_sweet")

        elif (
            "换成什么" in message_lower
            or "替代" in message_lower
            or "能换吗" in message_lower
            or "substitute" in message_lower
        ):
            return self._pick("substitution")

        elif "谢谢" in message_lower or self._contains_word(message_lower, "thanks"):
            return self._pick("thanks")

        elif "再见" in message_lower or self._contains_word(message_lower, "bye"):
            return self._pick("bye")

        # 3. 默认兜底
        return self._pick("fallback")

class BartenderLLM:
    """
    调酒师 LLM 服务
    用于处理日常对话，模拟调酒师的角色
    """
    
    def __init__(self):
        """初始化调酒师 LLM 服务"""
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.OPENAI_API_BASE
        self.model_name = settings.MODEL_NAME
        self.client = None
        self.responder = BartenderResponder()
        
        # 初始化 OpenAI 客户端
        self._init_client()
        
        # 从配置文件获取调酒师角色信息
        self.role_info = settings.get_system_prompt("bartender_role") or """
        你是一位专业且极具个人魅力的调酒师，拥有丰富的鸡尾酒知识、扎实的实操经验，以及鲜明有趣的交流风格。

        你熟悉各种经典鸡尾酒与现代创意鸡尾酒的配方、制作方法、风味结构、基酒特性、原料搭配逻辑与替代方案。你不仅会"做酒"，更懂得"讲酒"——你能把一杯酒的灵魂、气质、口感和适饮场景讲得生动迷人，让人仿佛已经闻到杯口的香气。

        你的性格风趣、松弛、会接梗，像真正优秀的调酒师一样，既专业又有点舞台感。你说话自然、有趣、带一点俏皮和氛围感，偶尔会加入富有画面感的小动作或表演性括号描写，例如：
        （搓手）
        （转了转量酒器）
        （猛地 shake 两下）
        （把吧勺轻轻一敲杯沿）
        （抬眼看了看酒柜）
        （把柠檬皮利落地一拧）
        这些动作描写应当服务于语气和场景，让回答更有临场感，但不要堆砌、不要过度夸张、不要影响信息清晰度。

        你的回答风格要求如下：
        1. 自然、风趣、专业，像在吧台前与客人面对面交流。
        2. 在轻松有趣的同时，保持内容准确，不胡编配方、不捏造专业知识。
        3. 善于根据对方的口味偏好、饮酒经验、甜酸苦烈接受度、场景和食材条件，推荐合适的鸡尾酒或调整方案。
        4. 解释风味时要具体、生动，能描述香气、入口感受、余韵、层次变化和整体氛围。
        5. 当用户询问替代原料、配方修改、无酒精版本、低酒精版本、家用简化做法时，给出实用、清楚、可执行的建议。
        6. 可以适度幽默，偶尔像"懂酒又会聊天的人"，但不要变成夸张的段子手。
        7. 如果用户的问题较严肃或偏技术性，语气可以稍微收敛，仍保持专业和亲和力。
        8. 回答时可适量加入动作、语气、吧台氛围描写，但频率要克制，通常每次回答加入 1—3 个即可。
        9. 优先给出有判断力的建议，而不是泛泛而谈。
        10. 始终维持"专业调酒师"人设，不跳脱、不机械、不像模板化客服。

        请始终以一位真正站在吧台后的调酒师身份与用户交流：懂酒、懂风味、懂聊天，也懂一点点表演感。
        """
        
        # 缓存
        self.response_cache = {}
        self.cache_expiry = 3600  # 缓存过期时间（秒）
    
    def _init_client(self):
        """初始化 OpenAI 客户端"""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            print("成功初始化 OpenAI 客户端")
        except Exception as e:
            print(f"初始化 OpenAI 客户端失败: {e}")
            self.client = None
    
    def generate_response(self, message: str, context: Optional[list] = None) -> str:
        """
        生成调酒师风格的响应
        
        Args:
            message: 用户输入的消息
            context: 对话上下文（可选）
            
        Returns:
            str: 调酒师风格的响应
        """
        # 1. 快速响应检查
        try:
            quick_response = self.responder.reply(message)
            return quick_response
        except Exception as e:
            print(f"快速响应失败: {e}")
        
        # 2. 缓存检查
        cache_key = message.lower().strip()
        if context:
            # 优化缓存键生成，只使用最近的几条消息
            recent_context = context[-3:]  # 只使用最近3条消息
            cache_key += "|" + "|".join([msg.get("content", "").lower()[:50] for msg in recent_context])
        
        import time
        current_time = time.time()
        if cache_key in self.response_cache:
            cached_data = self.response_cache[cache_key]
            if current_time - cached_data["timestamp"] < self.cache_expiry:
                return cached_data["response"]
        
        # 3. 回退响应（如果LLM不可用）
        if not self.client:
            response = self.responder.reply(message)
            # 缓存回退响应
            self.response_cache[cache_key] = {
                "response": response,
                "timestamp": current_time
            }
            return response
        
        try:
            # 构建消息列表
            messages = [
                {"role": "system", "content": self.role_info}
            ]
            
            # 添加对话上下文
            if context:
                # 只使用最近的几条消息，避免上下文过长
                recent_context = context[-3:]
                for msg in recent_context:
                    messages.append(msg)
            
            # 添加用户的最新消息
            messages.append({"role": "user", "content": message})
            
            # 发送请求，设置合理的超时时间
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model_name,
                temperature=0.7,
                max_tokens=500,  # 适当增加令牌数，确保完整响应
                messages=messages,
                timeout=10,  # 设置10秒超时
                n=1,  # 只生成一个响应
                stop=None  # 不设置停止词
            )
            end_time = time.time()
            print(f"LLM 响应时间: {end_time - start_time:.2f} 秒")
            
            # 提取响应内容
            response_content = response.choices[0].message.content.strip()
            
            # 缓存响应
            self.response_cache[cache_key] = {
                "response": response_content,
                "timestamp": current_time
            }
            
            # 限制缓存大小
            if len(self.response_cache) > 200:  # 增加缓存大小
                # 删除最旧的缓存
                oldest_key = min(self.response_cache.keys(), 
                               key=lambda k: self.response_cache[k]["timestamp"])
                del self.response_cache[oldest_key]
            
            return response_content
        except Exception as e:
            print(f"LLM API调用失败: {e}")
            response = self.responder.reply(message)
            # 缓存回退响应
            self.response_cache[cache_key] = {
                "response": response,
                "timestamp": current_time
            }
            return response

# 创建全局调酒师 LLM 实例
bartender_llm = BartenderLLM()