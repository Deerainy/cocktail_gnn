# -*- coding: utf-8 -*-
"""
Phase B 参数学习脚本

功能：
1. 加载 Phase B 成对训练数据集
2. 使用 softmax 参数化方法优化权重
3. 实现 pairwise hinge loss 损失函数
4. 训练权重参数
5. 保存优化后的权重
"""

import os
import sys
import pandas as pd
import numpy as np
from scipy.optimize import minimize

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_script_dir))
if _root not in sys.path:
    sys.path.insert(0, _root)

# 加载成 B 成对训练数据集
def load_pairwise_dataset() -> pd.DataFrame:
    """
    加载 Phase B 成对训练数据集
    """
    dataset_file = os.path.join(_root, "data", "phaseB_pairwise_dataset_v2.csv")
    if not os.path.exists(dataset_file):
        raise FileNotFoundError(f"Phase B 成对训练数据集不存在: {dataset_file}")
    
    df = pd.read_csv(dataset_file)
    print(f"[INFO] 加载了 {len(df)} 条成对训练数据")
    return df

def softmax(theta: np.ndarray) -> np.ndarray:
    """
    Softmax 函数，将参数转换为权重
    """
    exp_theta = np.exp(theta)
    return exp_theta / np.sum(exp_theta)

def pairwise_hinge_loss(theta: np.ndarray, X: pd.DataFrame, margin: float = 0.05) -> float:
    """
    计算 pairwise hinge loss
    """
    weights = softmax(theta)
    loss = 0.0
    
    for _, row in X.iterrows():
        # 计算正样本的 SQE 分数
        sqe_pos = (weights[0] * row['syn_pos_norm'] + 
                   weights[1] * row['conf_pos_good'] + 
                   weights[2] * row['bal_pos_norm'])
        
        # 计算负样本的 SQE 分数
        sqe_neg = (weights[0] * row['syn_neg_norm'] + 
                   weights[1] * row['conf_neg_good'] + 
                   weights[2] * row['bal_neg_norm'])
        
        # 计算 hinge loss
        loss += max(0, margin - (sqe_pos - sqe_neg))
    
    return loss

def gradient(theta: np.ndarray, X: pd.DataFrame, margin: float = 0.05) -> np.ndarray:
    """
    计算损失函数的梯度
    """
    weights = softmax(theta)
    grad = np.zeros_like(theta)
    
    for _, row in X.iterrows():
        # 计算正样本和负样本的 SQE 分数
        sqe_pos = (weights[0] * row['syn_pos_norm'] + 
                   weights[1] * row['conf_pos_good'] + 
                   weights[2] * row['bal_pos_norm'])
        sqe_neg = (weights[0] * row['syn_neg_norm'] + 
                   weights[1] * row['conf_neg_good'] + 
                   weights[2] * row['bal_neg_norm'])
        
        # 只有当损失大于 0 时才计算梯度
        if margin - (sqe_pos - sqe_neg) > 0:
            # 计算 SQE 对权重的导数
            d_sqe_pos = np.array([row['syn_pos_norm'], row['conf_pos_good'], row['bal_pos_norm']])
            d_sqe_neg = np.array([row['syn_neg_norm'], row['conf_neg_good'], row['bal_neg_norm']])
            d_sqe = d_sqe_pos - d_sqe_neg
            
            # 计算权重对 theta 的导数
            d_weights = np.diag(weights) - np.outer(weights, weights)
            
            # 计算损失对 theta 的导数
            grad += -np.dot(d_sqe, d_weights)
    
    return grad

def train_weights(dataset: pd.DataFrame) -> np.ndarray:
    """
    训练权重参数
    """
    # 初始化参数：使用当前人工设置的权重
    initial_weights = np.array([0.4, 0.3, 0.3])
    initial_theta = np.log(initial_weights)
    
    # 优化
    result = minimize(
        pairwise_hinge_loss,
        initial_theta,
        args=(dataset, 0.05),
        method='L-BFGS-B',
        jac=gradient,
        options={'maxiter': 1000, 'disp': True}
    )
    
    # 转换回权重
    optimized_weights = softmax(result.x)
    print(f"[INFO] 优化后的权重: {optimized_weights}")
    print(f"[INFO] 权重和: {np.sum(optimized_weights):.4f}")
    
    return optimized_weights

def save_optimized_weights(weights: np.ndarray, output_file: str):
    """
    保存优化后的权重
    """
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"lambda_synergy,{weights[0]:.6f}\n")
        f.write(f"lambda_conflict,{weights[1]:.6f}\n")
        f.write(f"lambda_balance,{weights[2]:.6f}\n")
    
    print(f"[INFO] 优化后的权重已保存到: {output_file}")

def evaluate_weights(weights: np.ndarray, dataset: pd.DataFrame) -> float:
    """
    评估权重的性能
    """
    correct_pairs = 0
    total_pairs = len(dataset)
    
    for _, row in dataset.iterrows():
        # 计算正样本的 SQE 分数
        sqe_pos = (weights[0] * row['syn_pos_norm'] + 
                   weights[1] * row['conf_pos_good'] + 
                   weights[2] * row['bal_pos_norm'])
        
        # 计算负样本的 SQE 分数
        sqe_neg = (weights[0] * row['syn_neg_norm'] + 
                   weights[1] * row['conf_neg_good'] + 
                   weights[2] * row['bal_neg_norm'])
        
        if sqe_pos > sqe_neg:
            correct_pairs += 1
    
    accuracy = correct_pairs / total_pairs
    print(f"[INFO] 权重性能评估: {accuracy:.2%} ({correct_pairs}/{total_pairs})")
    return accuracy

def main():
    """
    主函数
    """
    print("Phase B 参数学习...")
    
    # 加载成对训练数据集
    dataset = load_pairwise_dataset()
    
    # 训练权重
    optimized_weights = train_weights(dataset)
    
    # 保存结果
    output_file = os.path.join(_root, "data", "phaseB_optimized_weights.csv")
    save_optimized_weights(optimized_weights, output_file)
    
    # 评估优化效果
    print("\n[INFO] 评估优化效果:")
    
    # 初始权重
    initial_weights = np.array([0.4, 0.3, 0.3])
    print("[INFO] 初始权重性能:")
    initial_accuracy = evaluate_weights(initial_weights, dataset)
    
    # 优化后权重
    print("[INFO] 优化后权重性能:")
    optimized_accuracy = evaluate_weights(optimized_weights, dataset)
    
    # 性能提升
    accuracy_improvement = optimized_accuracy - initial_accuracy
    print(f"[INFO] 性能提升: {accuracy_improvement:.2%}")
    
    # 损失比较
    initial_loss = pairwise_hinge_loss(np.log(initial_weights), dataset)
    optimized_loss = pairwise_hinge_loss(np.log(optimized_weights), dataset)
    print(f"[INFO] 初始损失: {initial_loss:.4f}")
    print(f"[INFO] 优化后损失: {optimized_loss:.4f}")
    print(f"[INFO] 损失减少: {((initial_loss - optimized_loss) / initial_loss) * 100:.2f}%")

if __name__ == "__main__":
    main()
