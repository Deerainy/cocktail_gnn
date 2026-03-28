# -*- coding: utf-8 -*-
"""
Phase B 最优权重搜索脚本

功能：
1. 读取 pairwise dataset
2. 自动搜索最优 SQE 权重组合
3. 评估不同权重组合的性能
4. 输出 top-k 最优权重
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.stats import dirichlet
from typing import List, Dict, Tuple
from tqdm import tqdm

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_script_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 搜索参数
    NUM_SAMPLES = 100  # 随机采样次数
    TOP_K = 10  # 输出 top-k 最优权重
    
    # 目标函数参数
    ALPHA = 0.1  # margin 权重
    BETA = 0.1   # 极端性惩罚权重
    GAMMA = 0.05 # 子类型不平衡惩罚权重
    
    # 输入输出
    INPUT_FILE = os.path.join(_project_root, "data", "phaseB_pairwise_dataset_v3_valid.csv")
    OUTPUT_FILE = os.path.join(_project_root, "data", "phaseB_weight_search_results.csv")

# =========================================================
# 工具函数
# =========================================================

def load_pairwise_dataset() -> pd.DataFrame:
    """
    加载 pairwise 数据集
    """
    if not os.path.exists(Config.INPUT_FILE):
        raise FileNotFoundError(f"Pairwise 数据集不存在: {Config.INPUT_FILE}")
    
    df = pd.read_csv(Config.INPUT_FILE)
    print(f"[INFO] 加载了 {len(df)} 条成对训练数据")
    return df

def generate_weights(n_samples: int) -> List[Tuple[float, float, float]]:
    """
    使用 Dirichlet 分布生成权重组合
    """
    # 使用 Dirichlet 分布生成权重，参数设为 (1,1,1) 表示均匀分布
    weights = dirichlet.rvs([1, 1, 1], size=n_samples)
    return [(w[0], w[1], w[2]) for w in weights]

def calculate_sqe(syn_norm: float, conf_good: float, bal_norm: float, weights: Tuple[float, float, float]) -> float:
    """
    计算 SQE 总分
    """
    lambda_syn, lambda_conf, lambda_bal = weights
    return lambda_syn * syn_norm + lambda_conf * conf_good + lambda_bal * bal_norm

def calculate_accuracy(df: pd.DataFrame, weights: Tuple[float, float, float]) -> float:
    """
    计算 pairwise accuracy
    """
    correct = 0
    total = len(df)
    
    for _, row in df.iterrows():
        # 计算正样本和负样本的 SQE 分数
        pos_sqe = calculate_sqe(
            row['syn_pos_norm'],
            1 - row['conf_pos_norm'],  # conf_good
            row['bal_pos_norm'],
            weights
        )
        
        neg_sqe = calculate_sqe(
            row['syn_neg_norm'],
            1 - row['conf_neg_norm'],  # conf_good
            row['bal_neg_norm'],
            weights
        )
        
        # 正样本分数应该高于负样本
        if pos_sqe > neg_sqe:
            correct += 1
    
    return correct / total if total > 0 else 0

def calculate_average_margin(df: pd.DataFrame, weights: Tuple[float, float, float]) -> float:
    """
    计算平均 margin
    """
    margins = []
    
    for _, row in df.iterrows():
        # 计算正样本和负样本的 SQE 分数
        pos_sqe = calculate_sqe(
            row['syn_pos_norm'],
            1 - row['conf_pos_norm'],  # conf_good
            row['bal_pos_norm'],
            weights
        )
        
        neg_sqe = calculate_sqe(
            row['syn_neg_norm'],
            1 - row['conf_neg_norm'],  # conf_good
            row['bal_neg_norm'],
            weights
        )
        
        # 计算 margin
        margin = pos_sqe - neg_sqe
        margins.append(margin)
    
    return np.mean(margins) if margins else 0

def calculate_extremeness_penalty(weights: Tuple[float, float, float]) -> float:
    """
    计算极端性惩罚
    """
    lambda_syn, lambda_conf, lambda_bal = weights
    # 使用方差作为极端性的度量
    variance = np.var([lambda_syn, lambda_conf, lambda_bal])
    # 方差越大，惩罚越大
    return variance

def calculate_subtype_accuracy(df: pd.DataFrame, weights: Tuple[float, float, float]) -> Dict[str, float]:
    """
    计算各扰动类型的 accuracy
    """
    perturb_types = df['perturb_type'].unique()
    subtype_accuracy = {}
    
    for perturb_type in perturb_types:
        subtype_df = df[df['perturb_type'] == perturb_type]
        accuracy = calculate_accuracy(subtype_df, weights)
        subtype_accuracy[perturb_type] = accuracy
    
    return subtype_accuracy

def calculate_subtype_imbalance(subtype_accuracy: Dict[str, float]) -> float:
    """
    计算子类型不平衡度
    """
    accuracies = list(subtype_accuracy.values())
    if not accuracies:
        return 0
    # 使用标准差作为不平衡度的度量
    return np.std(accuracies)

def calculate_objective(df: pd.DataFrame, weights: Tuple[float, float, float]) -> Dict:
    """
    计算综合目标函数
    """
    # 计算各项指标
    accuracy = calculate_accuracy(df, weights)
    margin = calculate_average_margin(df, weights)
    extremeness = calculate_extremeness_penalty(weights)
    subtype_accuracy = calculate_subtype_accuracy(df, weights)
    subtype_imbalance = calculate_subtype_imbalance(subtype_accuracy)
    
    # 计算综合目标
    objective = (
        accuracy + 
        Config.ALPHA * margin - 
        Config.BETA * extremeness - 
        Config.GAMMA * subtype_imbalance
    )
    
    return {
        "weights": weights,
        "accuracy": accuracy,
        "margin": margin,
        "extremeness": extremeness,
        "subtype_accuracy": subtype_accuracy,
        "subtype_imbalance": subtype_imbalance,
        "objective": objective
    }

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("Phase B 最优权重搜索...")
    
    # 加载数据
    df = load_pairwise_dataset()
    
    # 生成权重组合
    print(f"[INFO] 生成 {Config.NUM_SAMPLES} 组权重组合...")
    weight_combinations = generate_weights(Config.NUM_SAMPLES)
    
    # 评估所有权重组合
    print(f"[INFO] 评估权重组合...")
    results = []
    
    # 使用 tqdm 添加进度条
    for weights in tqdm(weight_combinations, total=Config.NUM_SAMPLES, desc="评估权重组合"):
        # 计算目标函数
        result = calculate_objective(df, weights)
        results.append(result)
    
    # 按目标函数值排序
    results.sort(key=lambda x: x["objective"], reverse=True)
    
    # 提取 top-k 结果
    top_results = results[:Config.TOP_K]
    
    # 准备输出数据
    output_data = []
    for i, result in enumerate(top_results):
        lambda_syn, lambda_conf, lambda_bal = result["weights"]
        row = {
            "rank": i + 1,
            "lambda_synergy": lambda_syn,
            "lambda_conflict": lambda_conf,
            "lambda_balance": lambda_bal,
            "accuracy": result["accuracy"],
            "average_margin": result["margin"],
            "extremeness_penalty": result["extremeness"],
            "subtype_imbalance": result["subtype_imbalance"],
            "objective": result["objective"]
        }
        
        # 添加各扰动类型的 accuracy
        for perturb_type, acc in result["subtype_accuracy"].items():
            row[f"accuracy_{perturb_type}"] = acc
        
        output_data.append(row)
    
    # 转换为 DataFrame
    output_df = pd.DataFrame(output_data)
    
    # 保存结果
    os.makedirs(os.path.dirname(Config.OUTPUT_FILE), exist_ok=True)
    output_df.to_csv(Config.OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"[INFO] 搜索结果已保存到: {Config.OUTPUT_FILE}")
    
    # 打印最优权重
    print("\n[INFO] 最优权重组合:")
    best_result = top_results[0]
    lambda_syn, lambda_conf, lambda_bal = best_result["weights"]
    print(f"[INFO] Lambda Synergy: {lambda_syn:.4f}")
    print(f"[INFO] Lambda Conflict: {lambda_conf:.4f}")
    print(f"[INFO] Lambda Balance: {lambda_bal:.4f}")
    print(f"[INFO] Accuracy: {best_result['accuracy']:.4f}")
    print(f"[INFO] Average Margin: {best_result['margin']:.4f}")
    print(f"[INFO] Objective: {best_result['objective']:.4f}")
    
    # 打印各扰动类型的表现
    print("\n[INFO] 各扰动类型的表现:")
    for perturb_type, acc in best_result["subtype_accuracy"].items():
        print(f"[INFO]   {perturb_type}: {acc:.4f}")

if __name__ == "__main__":
    main()
