# -*- coding: utf-8 -*-
"""
Phase B 权重稳健性验证脚本（快速版本）

功能：
1. 加载 valid pairwise 数据集
2. 随机切分成 80% 训练集和 20% 验证集
3. 用训练集搜索最优权重（使用向量化操作加速）
4. 用验证集评估最佳权重的性能
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
    NUM_SAMPLES = 5000  # 随机采样次数
    TOP_K = 5  # 输出 top-k 最优权重
    
    # 目标函数参数
    ALPHA = 0.1  # margin 权重
    BETA = 0.1   # 极端性惩罚权重
    GAMMA = 0.05 # 子类型不平衡惩罚权重
    
    # 输入输出
    INPUT_FILE = os.path.join(_project_root, "data", "phaseB_pairwise_dataset_v3_valid.csv")
    TRAIN_FILE = os.path.join(_project_root, "data", "phaseB_pairwise_train.csv")
    VALID_FILE = os.path.join(_project_root, "data", "phaseB_pairwise_validation.csv")
    OUTPUT_FILE = os.path.join(_project_root, "data", "phaseB_weight_validation_results.csv")

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

def split_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    随机切分数据集为 80% 训练集和 20% 验证集
    """
    # 设置随机种子以确保可重复性
    np.random.seed(42)
    
    # 随机打乱数据
    shuffled_df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # 计算切分点
    split_point = int(len(shuffled_df) * 0.8)
    
    # 切分数据集
    train_df = shuffled_df[:split_point]
    valid_df = shuffled_df[split_point:]
    
    # 保存切分后的数据集
    train_df.to_csv(Config.TRAIN_FILE, index=False, encoding="utf-8")
    valid_df.to_csv(Config.VALID_FILE, index=False, encoding="utf-8")
    
    print(f"[INFO] 训练集大小: {len(train_df)}")
    print(f"[INFO] 验证集大小: {len(valid_df)}")
    
    return train_df, valid_df

def generate_weights(n_samples: int) -> List[Tuple[float, float, float]]:
    """
    使用 Dirichlet 分布生成权重组合
    """
    # 使用 Dirichlet 分布生成权重，参数设为 (1,1,1) 表示均匀分布
    weights = dirichlet.rvs([1, 1, 1], size=n_samples)
    return [(w[0], w[1], w[2]) for w in weights]

def calculate_sqe_vectorized(train_df: pd.DataFrame, weights: Tuple[float, float, float]) -> Tuple[np.ndarray, np.ndarray]:
    """
    向量化计算 SQE 总分
    """
    lambda_syn, lambda_conf, lambda_bal = weights
    
    # 计算正样本 SQE 分数
    pos_sqe = (
        lambda_syn * train_df['syn_pos_norm'].values +
        lambda_conf * (1 - train_df['conf_pos_norm'].values) +
        lambda_bal * train_df['bal_pos_norm'].values
    )
    
    # 计算负样本 SQE 分数
    neg_sqe = (
        lambda_syn * train_df['syn_neg_norm'].values +
        lambda_conf * (1 - train_df['conf_neg_norm'].values) +
        lambda_bal * train_df['bal_neg_norm'].values
    )
    
    return pos_sqe, neg_sqe

def calculate_accuracy_vectorized(train_df: pd.DataFrame, weights: Tuple[float, float, float]) -> float:
    """
    向量化计算 pairwise accuracy
    """
    pos_sqe, neg_sqe = calculate_sqe_vectorized(train_df, weights)
    correct = np.sum(pos_sqe > neg_sqe)
    total = len(train_df)
    return correct / total if total > 0 else 0

def calculate_average_margin_vectorized(train_df: pd.DataFrame, weights: Tuple[float, float, float]) -> float:
    """
    向量化计算平均 margin
    """
    pos_sqe, neg_sqe = calculate_sqe_vectorized(train_df, weights)
    margins = pos_sqe - neg_sqe
    return np.mean(margins) if len(margins) > 0 else 0

def calculate_extremeness_penalty(weights: Tuple[float, float, float]) -> float:
    """
    计算极端性惩罚
    """
    lambda_syn, lambda_conf, lambda_bal = weights
    # 使用方差作为极端性的度量
    variance = np.var([lambda_syn, lambda_conf, lambda_bal])
    # 方差越大，惩罚越大
    return variance

def calculate_subtype_accuracy(train_df: pd.DataFrame, weights: Tuple[float, float, float]) -> Dict[str, float]:
    """
    计算各扰动类型的 accuracy
    """
    perturb_types = train_df['perturb_type'].unique()
    subtype_accuracy = {}
    
    for perturb_type in perturb_types:
        subtype_df = train_df[train_df['perturb_type'] == perturb_type]
        if len(subtype_df) > 0:
            accuracy = calculate_accuracy_vectorized(subtype_df, weights)
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

def calculate_objective(train_df: pd.DataFrame, weights: Tuple[float, float, float]) -> Dict:
    """
    计算综合目标函数
    """
    # 计算各项指标
    accuracy = calculate_accuracy_vectorized(train_df, weights)
    margin = calculate_average_margin_vectorized(train_df, weights)
    extremeness = calculate_extremeness_penalty(weights)
    subtype_accuracy = calculate_subtype_accuracy(train_df, weights)
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
    print("Phase B 权重稳健性验证...")
    
    # 加载数据
    df = load_pairwise_dataset()
    
    # 切分数据集
    train_df, valid_df = split_dataset(df)
    
    # 生成权重组合
    print(f"[INFO] 生成 {Config.NUM_SAMPLES} 组权重组合...")
    weight_combinations = generate_weights(Config.NUM_SAMPLES)
    
    # 评估所有权重组合（使用训练集）
    print(f"[INFO] 评估权重组合...")
    results = []
    
    # 使用 tqdm 添加进度条
    for weights in tqdm(weight_combinations, total=Config.NUM_SAMPLES, desc="评估权重组合"):
        # 计算目标函数
        result = calculate_objective(train_df, weights)
        results.append(result)
    
    # 按目标函数值排序
    results.sort(key=lambda x: x["objective"], reverse=True)
    
    # 提取 top-k 结果
    top_results = results[:Config.TOP_K]
    
    # 使用验证集评估最佳权重
    best_weights = top_results[0]["weights"]
    validation_accuracy = calculate_accuracy_vectorized(valid_df, best_weights)
    validation_margin = calculate_average_margin_vectorized(valid_df, best_weights)
    validation_subtype_accuracy = calculate_subtype_accuracy(valid_df, best_weights)
    
    print(f"\n[INFO] 最佳权重在验证集上的表现:")
    print(f"[INFO] 验证集 Accuracy: {validation_accuracy:.4f}")
    print(f"[INFO] 验证集 Average Margin: {validation_margin:.4f}")
    
    # 打印各扰动类型的表现
    print("\n[INFO] 各扰动类型在验证集上的表现:")
    for perturb_type, acc in validation_subtype_accuracy.items():
        print(f"[INFO]   {perturb_type}: {acc:.4f}")
    
    # 准备输出数据
    output_data = []
    for i, result in enumerate(top_results):
        lambda_syn, lambda_conf, lambda_bal = result["weights"]
        row = {
            "rank": i + 1,
            "lambda_synergy": lambda_syn,
            "lambda_conflict": lambda_conf,
            "lambda_balance": lambda_bal,
            "train_accuracy": result["accuracy"],
            "train_average_margin": result["margin"],
            "train_extremeness_penalty": result["extremeness"],
            "train_subtype_imbalance": result["subtype_imbalance"],
            "train_objective": result["objective"],
            "validation_accuracy": validation_accuracy,
            "validation_average_margin": validation_margin
        }
        
        # 添加各扰动类型的 accuracy
        for perturb_type, acc in result["subtype_accuracy"].items():
            row[f"train_accuracy_{perturb_type}"] = acc
        
        output_data.append(row)
    
    # 转换为 DataFrame
    output_df = pd.DataFrame(output_data)
    
    # 保存结果
    os.makedirs(os.path.dirname(Config.OUTPUT_FILE), exist_ok=True)
    output_df.to_csv(Config.OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"[INFO] 验证结果已保存到: {Config.OUTPUT_FILE}")
    
    # 打印最优权重
    print("\n[INFO] 最优权重组合:")
    best_result = top_results[0]
    lambda_syn, lambda_conf, lambda_bal = best_result["weights"]
    print(f"[INFO] Lambda Synergy: {lambda_syn:.4f}")
    print(f"[INFO] Lambda Conflict: {lambda_conf:.4f}")
    print(f"[INFO] Lambda Balance: {lambda_bal:.4f}")
    print(f"[INFO] 训练集 Accuracy: {best_result['accuracy']:.4f}")
    print(f"[INFO] 验证集 Accuracy: {validation_accuracy:.4f}")
    print(f"[INFO] 训练集 Average Margin: {best_result['margin']:.4f}")
    print(f"[INFO] 验证集 Average Margin: {validation_margin:.4f}")

if __name__ == "__main__":
    main()
