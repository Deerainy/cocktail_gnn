# -*- coding: utf-8 -*-
"""
Recipe-level feature clustering and LLM analysis

功能：
1. Step 1: 做 recipe-level feature clustering
2. Step 2: 提取每个簇的代表特征
3. Step 3: 把簇摘要交给 LLM 进行分析和命名
"""

import os
import sys
import json
import math
import numpy as np
from typing import Dict, List, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_script_dir) if os.path.basename(_script_dir) == "scripts" else _script_dir
if _root not in sys.path:
    sys.path.insert(0, _root)

from src.db import get_engine
import pandas as pd
from sqlalchemy import text

# 数据库引擎
engine = get_engine()

# 风味特征维度
FLAVOR_DIMENSIONS = ["sour", "sweet", "bitter", "aroma", "fruity", "body"]

# 角色类型
ROLE_TYPES = ["base", "acid", "sweetener", "modifier", "bitters", "garnish", "dilution", "other"]


class RecipeClustering:
    def __init__(self, n_clusters: int = 5):
        """
        初始化 RecipeClustering 类
        """
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.cluster_results = {}
    
    def load_data(self) -> pd.DataFrame:
        """
        加载数据
        """
        # 加载 recipe_balance_feature 表
        sql = text("""
        SELECT * FROM recipe_balance_feature
        """)
        
        with engine.begin() as conn:
            df = pd.read_sql(sql, conn)
        
        print(f"[INFO] 加载了 {len(df)} 条 recipe 平衡特征数据")
        return df
    
    def load_ingredient_info(self) -> Dict[int, Dict]:
        """
        加载原料信息
        """
        # 加载 recipe_ingredient 表
        sql = text("""
        SELECT
            recipe_id,
            ingredient_id,
            raw_text
        FROM recipe_ingredient
        """)
        
        with engine.begin() as conn:
            rows = conn.execute(sql).mappings().all()
        
        # 构建 recipe_id 到 ingredients 的映射
        recipe_ingredients = {}
        for row in rows:
            recipe_id = row["recipe_id"]
            if recipe_id not in recipe_ingredients:
                recipe_ingredients[recipe_id] = []
            recipe_ingredients[recipe_id].append({
                "ingredient_id": row["ingredient_id"],
                "raw_text": row["raw_text"]
            })
        
        return recipe_ingredients
    
    def build_feature_vectors(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[int]]:
        """
        构建特征向量
        """
        feature_vectors = []
        recipe_ids = []
        
        for _, row in df.iterrows():
            recipe_id = row["recipe_id"]
            
            # 构建风味向量
            flavor_vector = [
                float(row.get("f_sour", 0.0)),
                float(row.get("f_sweet", 0.0)),
                float(row.get("f_bitter", 0.0)),
                float(row.get("f_aroma", 0.0)),
                float(row.get("f_fruity", 0.0)),
                float(row.get("f_body", 0.0))
            ]
            
            # 构建角色分布向量
            role_vector = [
                float(row.get("r_base", 0.0)),
                float(row.get("r_acid", 0.0)),
                float(row.get("r_sweetener", 0.0)),
                float(row.get("r_modifier", 0.0)),
                float(row.get("r_bitters", 0.0)),
                float(row.get("r_garnish", 0.0)),
                float(row.get("r_dilution", 0.0)),
                float(row.get("r_other", 0.0))
            ]
            
            # 合并特征向量
            feature_vector = flavor_vector + role_vector
            feature_vectors.append(feature_vector)
            recipe_ids.append(recipe_id)
        
        # 标准化特征
        feature_vectors = np.array(feature_vectors)
        feature_vectors = self.scaler.fit_transform(feature_vectors)
        
        return feature_vectors, recipe_ids
    
    def cluster(self, feature_vectors: np.ndarray, recipe_ids: List[int]):
        """
        执行聚类
        """
        # 执行 K-means 聚类
        labels = self.kmeans.fit_predict(feature_vectors)
        
        # 整理聚类结果
        for i, recipe_id in enumerate(recipe_ids):
            cluster_id = int(labels[i])
            if cluster_id not in self.cluster_results:
                self.cluster_results[cluster_id] = {
                    "recipe_ids": [],
                    "feature_vectors": []
                }
            self.cluster_results[cluster_id]["recipe_ids"].append(recipe_id)
            self.cluster_results[cluster_id]["feature_vectors"].append(feature_vectors[i])
        
        print(f"[INFO] 聚类完成，共 {self.n_clusters} 个簇")
        for cluster_id, info in self.cluster_results.items():
            print(f"[INFO] 簇 {cluster_id}: {len(info['recipe_ids'])} 个 recipe")
    
    def extract_cluster_features(self, df: pd.DataFrame, recipe_ingredients: Dict[int, Dict]):
        """
        提取每个簇的代表特征
        """
        for cluster_id, info in self.cluster_results.items():
            recipe_ids = info["recipe_ids"]
            
            # 提取簇中的 recipe 数据
            cluster_df = df[df["recipe_id"].isin(recipe_ids)]
            
            # 计算平均风味向量
            avg_flavor = {}
            for dim in FLAVOR_DIMENSIONS:
                avg_flavor[dim] = float(cluster_df[f"f_{dim}"].mean())
            
            # 计算平均角色分布
            avg_role = {}
            for role in ROLE_TYPES:
                avg_role[role] = float(cluster_df[f"r_{role}"].mean())
            
            # 收集高频 ingredients
            ingredient_counts = {}
            for recipe_id in recipe_ids:
                if recipe_id in recipe_ingredients:
                    for ing in recipe_ingredients[recipe_id]:
                        raw_text = ing["raw_text"]
                        ingredient_counts[raw_text] = ingredient_counts.get(raw_text, 0) + 1
            
            # 排序并取前 10 个高频 ingredients
            top_ingredients = sorted(ingredient_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # 保存簇特征
            self.cluster_results[cluster_id].update({
                "avg_flavor": avg_flavor,
                "avg_role": avg_role,
                "top_ingredients": top_ingredients,
                "representative_recipes": recipe_ids[:5]  # 取前 5 个作为代表
            })
    
    def generate_cluster_summaries(self) -> List[Dict]:
        """
        生成簇摘要
        """
        summaries = []
        
        for cluster_id, info in self.cluster_results.items():
            summary = {
                "cluster_id": cluster_id,
                "size": len(info["recipe_ids"]),
                "avg_flavor": info["avg_flavor"],
                "avg_role": info["avg_role"],
                "top_ingredients": [ing[0] for ing in info["top_ingredients"]],
                "representative_recipes": info["representative_recipes"]
            }
            summaries.append(summary)
        
        return summaries
    
    def save_results(self, summaries: List[Dict], output_dir: str):
        """
        保存结果
        """
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存簇摘要
        summary_file = os.path.join(output_dir, "cluster_summaries.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summaries, f, ensure_ascii=False, indent=2)
        
        # 保存聚类结果
        results_file = os.path.join(output_dir, "clustering_results.json")
        with open(results_file, "w", encoding="utf-8") as f:
            # 转换 numpy 数组为列表
            serializable_results = {}
            for cluster_id, info in self.cluster_results.items():
                serializable_results[cluster_id] = {
                    "recipe_ids": info["recipe_ids"],
                    "feature_vectors": [vec.tolist() for vec in info["feature_vectors"]],
                    "avg_flavor": info["avg_flavor"],
                    "avg_role": info["avg_role"],
                    "top_ingredients": info["top_ingredients"],
                    "representative_recipes": info["representative_recipes"]
                }
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        print(f"[INFO] 结果已保存到: {output_dir}")

def main():
    """
    主函数
    """
    # 初始化聚类器
    clustering = RecipeClustering(n_clusters=5)
    
    # 加载数据
    df = clustering.load_data()
    recipe_ingredients = clustering.load_ingredient_info()
    
    # 构建特征向量
    feature_vectors, recipe_ids = clustering.build_feature_vectors(df)
    
    # 执行聚类
    clustering.cluster(feature_vectors, recipe_ids)
    
    # 提取簇特征
    clustering.extract_cluster_features(df, recipe_ingredients)
    
    # 生成簇摘要
    summaries = clustering.generate_cluster_summaries()
    
    # 保存结果
    output_dir = os.path.join(_root, "data", "clustering_results")
    clustering.save_results(summaries, output_dir)
    
    # 打印簇摘要
    print("\n[INFO] 簇摘要:")
    for summary in summaries:
        print(f"\n簇 {summary['cluster_id']} (大小: {summary['size']}):")
        print(f"平均风味: {summary['avg_flavor']}")
        print(f"平均角色: {summary['avg_role']}")
        print(f"高频原料: {summary['top_ingredients']}")
        print(f"代表 recipe: {summary['representative_recipes']}")


if __name__ == "__main__":
    main()
