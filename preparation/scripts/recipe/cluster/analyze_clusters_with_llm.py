# -*- coding: utf-8 -*-
"""
使用 LLM 分析聚类结果并为每个簇生成标签和描述

功能：
1. 加载聚类结果
2. 为每个簇生成 LLM 提示
3. 调用 LLM 分析每个簇
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
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

# 加载环境变量
_llm_env = os.path.join(_root, "config", "llm.env")
load_dotenv(_llm_env)

# 获取 API 密钥
api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("Missing DEEPSEEK_API_KEY or OPENAI_API_KEY")

# 创建 OpenAI 客户端
client = OpenAI(
    api_key=api_key,
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
)


class ClusterAnalyzer:
    def __init__(self, cluster_summaries_file: str):
        """
        初始化 ClusterAnalyzer 类
        """
        self.cluster_summaries_file = cluster_summaries_file
        self.cluster_summaries = []
        self.analysis_results = {}
    
    def load_cluster_summaries(self):
        """
        加载聚类结果
        """
        with open(self.cluster_summaries_file, "r", encoding="utf-8") as f:
            self.cluster_summaries = json.load(f)
        
        print(f"[INFO] 加载了 {len(self.cluster_summaries)} 个簇的摘要")
    
    def generate_prompt(self, cluster_summary: Dict) -> str:
        """
        为每个簇生成 LLM 提示
        """
        cluster_id = cluster_summary["cluster_id"]
        size = cluster_summary["size"]
        avg_flavor = cluster_summary["avg_flavor"]
        avg_role = cluster_summary["avg_role"]
        top_ingredients = cluster_summary["top_ingredients"]
        representative_recipes = cluster_summary["representative_recipes"]
        
        prompt = f"""
你是一位专业的鸡尾酒分类专家，擅长分析鸡尾酒配方的风味特征和结构特点。

请分析以下鸡尾酒配方簇的特征，并为其生成以下信息：
1. candidate_label: 一个简洁的标签，描述这个簇的主要特点
2. description: 详细描述这个簇的风味特点、结构特点和典型特征
3. possible_classic_family_alignment: 这个簇可能属于哪个经典鸡尾酒家族（如 sour、old fashioned、martini、daiquiri、margarita 等）
4. confidence_note: 对分类结果的置信度评估和说明

簇信息：
- 簇 ID: {cluster_id}
- 簇大小: {size} 个配方
- 平均风味向量: {avg_flavor}
- 平均角色分布: {avg_role}
- 高频原料: {top_ingredients}
- 代表配方 ID: {representative_recipes}

请以 JSON 格式输出结果，包含以下字段：
candidate_label, description, possible_classic_family_alignment, confidence_note
"""
        
        return prompt
    
    def analyze_cluster(self, cluster_summary: Dict) -> Dict:
        """
        分析单个簇
        """
        cluster_id = cluster_summary["cluster_id"]
        prompt = self.generate_prompt(cluster_summary)
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一位专业的鸡尾酒分类专家，擅长分析鸡尾酒配方的风味特征和结构特点。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            # 解析响应
            content = response.choices[0].message.content
            result = json.loads(content)
            
            print(f"[INFO] 成功分析簇 {cluster_id}")
            return result
        except Exception as e:
            print(f"[ERROR] 分析簇 {cluster_id} 时出错: {e}")
            return {
                "candidate_label": "Unknown",
                "description": "Error analyzing cluster",
                "possible_classic_family_alignment": "Unknown",
                "confidence_note": "Analysis failed"
            }
    
    def analyze_all_clusters(self):
        """
        分析所有簇
        """
        for cluster_summary in self.cluster_summaries:
            cluster_id = cluster_summary["cluster_id"]
            result = self.analyze_cluster(cluster_summary)
            self.analysis_results[cluster_id] = result
        
        print(f"[INFO] 完成所有簇的分析")
    
    def save_results(self, output_file: str):
        """
        保存分析结果
        """
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # 保存分析结果
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 分析结果已保存到: {output_file}")
    
    def print_results(self):
        """
        打印分析结果
        """
        for cluster_id, result in self.analysis_results.items():
            print(f"\n簇 {cluster_id} 分析结果:")
            print(f"标签: {result['candidate_label']}")
            print(f"描述: {result['description']}")
            print(f"经典家族对齐: {result['possible_classic_family_alignment']}")
            print(f"置信度说明: {result['confidence_note']}")


def main():
    """
    主函数
    """
    # 加载聚类结果
    cluster_summaries_file = os.path.join(_root, "data", "clustering_results", "cluster_summaries.json")
    
    # 初始化分析器
    analyzer = ClusterAnalyzer(cluster_summaries_file)
    
    # 加载簇摘要
    analyzer.load_cluster_summaries()
    
    # 分析所有簇
    analyzer.analyze_all_clusters()
    
    # 保存结果
    output_file = os.path.join(_root, "data", "clustering_results", "cluster_analysis_results.json")
    analyzer.save_results(output_file)
    
    # 打印结果
    analyzer.print_results()


if __name__ == "__main__":
    main()
