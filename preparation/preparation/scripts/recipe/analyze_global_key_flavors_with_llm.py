# -*- coding: utf-8 -*-
"""
使用 LLM 分析全局关键风味数据

功能：
1. 加载全局关键风味数据
2. 生成 LLM 提示
3. 调用 LLM 分析数据
4. 保存分析结果
"""

import os
import sys
import json
from typing import Dict, List
from dotenv import load_dotenv
from openai import OpenAI

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
# 确保 _root 是项目根目录
if os.path.basename(_script_dir) == "recipe":
    _root = os.path.dirname(os.path.dirname(_script_dir))
elif os.path.basename(_script_dir) == "scripts":
    _root = os.path.dirname(_script_dir)
else:
    _root = _script_dir

if _root not in sys.path:
    sys.path.insert(0, _root)

# 加载环境变量
_llm_env = os.path.join(_root, "config", "llm.env")
print(f"[DEBUG] 尝试加载环境变量文件: {_llm_env}")
print(f"[DEBUG] 文件是否存在: {os.path.exists(_llm_env)}")

load_dotenv(_llm_env)

# 获取 API 密钥
api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
print(f"[DEBUG] API Key: {api_key}")

if not api_key:
    # 尝试直接读取文件
    print("[DEBUG] 尝试直接读取 llm.env 文件")
    if os.path.exists(_llm_env):
        with open(_llm_env, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if key == "DEEPSEEK_API_KEY":
                        api_key = value
                        print(f"[DEBUG] 从文件中读取到 API Key: {api_key}")
                        break

if not api_key:
    raise RuntimeError("Missing DEEPSEEK_API_KEY or OPENAI_API_KEY")

# 创建 OpenAI 客户端
client = OpenAI(
    api_key=api_key,
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)


class GlobalKeyFlavorAnalyzer:
    def __init__(self, llm_input_file: str):
        """
        初始化 GlobalKeyFlavorAnalyzer 类
        """
        self.llm_input_file = llm_input_file
        self.llm_input = {}
        self.analysis_result = {}
    
    def load_llm_input(self):
        """
        加载 LLM 输入数据
        """
        with open(self.llm_input_file, "r", encoding="utf-8") as f:
            self.llm_input = json.load(f)
        
        print(f"[INFO] 加载了 LLM 输入数据")
        print(f"[INFO] 总原料数: {self.llm_input['key_statistics']['total_ingredients']}")
        print(f"[INFO] 总配方数: {self.llm_input['key_statistics']['total_recipes']}")
    
    def generate_prompt(self) -> str:
        """
        生成 LLM 提示
        """
        top_flavors = self.llm_input['top_flavors']
        
        # 提取前 10 个关键风味原料
        top_10_flavors = top_flavors[:10]
        
        # 构建原料列表字符串
        flavors_str = "\n".join([
            f"{i+1}. {flavor['name']} (全局关键得分: {flavor['global_key_score']:.4f}, 配方数: {flavor['recipe_count']}, 主要角色: {flavor['dominant_role']})"
            for i, flavor in enumerate(top_10_flavors)
        ])
        
        prompt = f"""
你是一位专业的鸡尾酒风味分析专家，擅长分析鸡尾酒配方的风味特征和结构特点。

请分析以下全局关键风味原料数据，并生成详细的分析报告：

数据概览：
- 总原料数: {self.llm_input['key_statistics']['total_ingredients']}
- 总配方数: {self.llm_input['key_statistics']['total_recipes']}

前 10 个关键风味原料：
{flavors_str}

请从以下几个方面进行分析：
1. 总体趋势：分析这些关键风味原料的整体分布和特点
2. 角色分布：分析不同角色（base_spirit、modifier、sweetener、acid、bitters 等）的关键原料分布
3. 风味特征：分析这些原料的风味特点和它们在鸡尾酒中的作用
4. 结构重要性：分析这些原料对鸡尾酒结构的影响
5. 应用建议：基于分析结果，提供一些鸡尾酒配方设计和优化的建议

请提供详细、专业的分析，帮助理解这些关键风味原料在鸡尾酒配方中的重要性和作用。
"""
        
        return prompt
    
    def analyze_global_key_flavors(self) -> Dict:
        """
        分析全局关键风味
        """
        prompt = self.generate_prompt()
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一位专业的鸡尾酒风味分析专家，擅长分析鸡尾酒配方的风味特征和结构特点。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # 解析响应
            content = response.choices[0].message.content
            
            print("[INFO] 成功分析全局关键风味")
            return {"analysis": content}
        except Exception as e:
            print(f"[ERROR] 分析全局关键风味时出错: {e}")
            return {"analysis": "Error analyzing global key flavors"}
    
    def save_results(self, output_file: str):
        """
        保存分析结果
        """
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 保存分析结果
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.analysis_result, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 分析结果已保存到: {output_file}")
    
    def print_results(self):
        """
        打印分析结果
        """
        print("\n全局关键风味分析结果:")
        print(self.analysis_result.get("analysis", "No analysis available"))


def main():
    """
    主函数
    """
    # 加载 LLM 输入数据
    llm_input_file = os.path.join(_root, "data", "flavor", "llm_input_v3.json")
    
    # 初始化分析器
    analyzer = GlobalKeyFlavorAnalyzer(llm_input_file)
    
    # 加载 LLM 输入数据
    analyzer.load_llm_input()
    
    # 分析全局关键风味
    analyzer.analysis_result = analyzer.analyze_global_key_flavors()
    
    # 保存结果
    output_file = os.path.join(_root, "data", "flavor", "global_key_flavor_analysis.json")
    analyzer.save_results(output_file)
    
    # 打印结果
    analyzer.print_results()


if __name__ == "__main__":
    main()
