# -*- coding: utf-8 -*-
"""
Phase C 损失函数和评估指标脚本

功能：
1. 实现 pairwise ranking loss
2. 实现 residual regularization
3. 实现 total loss
4. 实现评估指标函数
"""

import torch
import torch.nn.functional as F
from typing import Dict, List, Tuple

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 损失权重
    LAMBDA_RES = 0.01  # 残差正则化权重
    LAMBDA_REG = 0.001  # 参数正则化权重

# =========================================================
# 损失函数
# =========================================================

def pairwise_ranking_loss(pos_output: Dict, neg_output: Dict) -> torch.Tensor:
    """
    Pairwise ranking loss
    
    参数:
    pos_output: 正样本的模型输出
    neg_output: 负样本的模型输出
    
    返回:
    损失值
    """
    pos_sqe = pos_output['sqe_c']
    neg_sqe = neg_output['sqe_c']
    
    # 计算分数差
    score_diff = pos_sqe - neg_sqe
    
    # 计算 sigmoid 并取负对数
    loss = -F.logsigmoid(score_diff)
    
    return loss.mean()

def residual_regularization(pos_output: Dict, neg_output: Dict) -> torch.Tensor:
    """
    Residual regularization loss
    
    参数:
    pos_output: 正样本的模型输出
    neg_output: 负样本的模型输出
    
    返回:
    损失值
    """
    # 计算正样本的残差平方和
    pos_delta_syn = pos_output['delta_syn']
    pos_delta_conf = pos_output['delta_conf']
    pos_delta_bal = pos_output['delta_bal']
    pos_res_loss = pos_delta_syn.pow(2) + pos_delta_conf.pow(2) + pos_delta_bal.pow(2)
    
    # 计算负样本的残差平方和
    neg_delta_syn = neg_output['delta_syn']
    neg_delta_conf = neg_output['delta_conf']
    neg_delta_bal = neg_output['delta_bal']
    neg_res_loss = neg_delta_syn.pow(2) + neg_delta_conf.pow(2) + neg_delta_bal.pow(2)
    
    # 求均值
    res_loss = (pos_res_loss + neg_res_loss).mean()
    
    return res_loss

def total_loss(pos_output: Dict, neg_output: Dict, lambda_res: float = Config.LAMBDA_RES) -> torch.Tensor:
    """
    Total loss
    
    参数:
    pos_output: 正样本的模型输出
    neg_output: 负样本的模型输出
    lambda_res: 残差正则化权重
    
    返回:
    损失值
    """
    # 计算 pairwise ranking loss
    rank_loss = pairwise_ranking_loss(pos_output, neg_output)
    
    # 计算 residual regularization loss
    res_loss = residual_regularization(pos_output, neg_output)
    
    # 计算总损失
    total_loss = rank_loss + lambda_res * res_loss
    
    return total_loss

# =========================================================
# 评估指标函数
# =========================================================

def pair_accuracy(pos_output: Dict, neg_output: Dict) -> float:
    """
    计算配对准确率
    
    参数:
    pos_output: 正样本的模型输出
    neg_output: 负样本的模型输出
    
    返回:
    准确率
    """
    pos_sqe = pos_output['sqe_c']
    neg_sqe = neg_output['sqe_c']
    
    # 计算正样本分数大于负样本分数的比例
    correct = (pos_sqe > neg_sqe).float()
    accuracy = correct.mean().item()
    
    return accuracy

def average_margin(pos_output: Dict, neg_output: Dict) -> float:
    """
    计算平均 margin
    
    参数:
    pos_output: 正样本的模型输出
    neg_output: 负样本的模型输出
    
    返回:
    平均 margin
    """
    pos_sqe = pos_output['sqe_c']
    neg_sqe = neg_output['sqe_c']
    
    # 计算分数差
    margin = pos_sqe - neg_sqe
    
    # 计算平均 margin
    avg_margin = margin.mean().item()
    
    return avg_margin

def margin_by_perturb_type(pos_outputs: List[Dict], neg_outputs: List[Dict], perturb_types: List[str]) -> Dict[str, float]:
    """
    按扰动类型计算平均 margin
    
    参数:
    pos_outputs: 正样本的模型输出列表
    neg_outputs: 负样本的模型输出列表
    perturb_types: 扰动类型列表
    
    返回:
    各扰动类型的平均 margin
    """
    # 按扰动类型分组
    type_margins = {}
    type_counts = {}
    
    for pos_output, neg_output, perturb_type in zip(pos_outputs, neg_outputs, perturb_types):
        pos_sqe = pos_output['sqe_c']
        neg_sqe = neg_output['sqe_c']
        
        # 计算 margin
        margin = pos_sqe - neg_sqe
        
        # 处理 batch 情况
        if margin.dim() > 0:
            # 如果是 batch，计算平均值
            margin = margin.mean().item()
        else:
            # 如果是标量，直接获取值
            margin = margin.item()
        
        if perturb_type not in type_margins:
            type_margins[perturb_type] = 0.0
            type_counts[perturb_type] = 0
        
        type_margins[perturb_type] += margin
        type_counts[perturb_type] += 1
    
    # 计算各扰动类型的平均 margin
    avg_margins = {}
    for perturb_type in type_margins:
        if type_counts[perturb_type] > 0:
            avg_margins[perturb_type] = type_margins[perturb_type] / type_counts[perturb_type]
    
    return avg_margins

def compute_metrics(pos_outputs: List[Dict], neg_outputs: List[Dict], perturb_types: List[str] = None) -> Dict:
    """
    计算所有评估指标
    
    参数:
    pos_outputs: 正样本的模型输出列表
    neg_outputs: 负样本的模型输出列表
    perturb_types: 扰动类型列表（可选）
    
    返回:
    包含所有评估指标的字典
    """
    # 计算配对准确率
    accuracies = []
    for pos_output, neg_output in zip(pos_outputs, neg_outputs):
        acc = pair_accuracy(pos_output, neg_output)
        accuracies.append(acc)
    avg_accuracy = sum(accuracies) / len(accuracies)
    
    # 计算平均 margin
    margins = []
    for pos_output, neg_output in zip(pos_outputs, neg_outputs):
        margin = average_margin(pos_output, neg_output)
        margins.append(margin)
    avg_margin = sum(margins) / len(margins)
    
    # 计算按扰动类型的平均 margin
    margin_by_type = {}
    if perturb_types is not None:
        margin_by_type = margin_by_perturb_type(pos_outputs, neg_outputs, perturb_types)
    
    # 构建结果字典
    metrics = {
        'pair_accuracy': avg_accuracy,
        'average_margin': avg_margin,
        'margin_by_perturb_type': margin_by_type
    }
    
    return metrics

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("测试 Phase C 损失函数和评估指标...")
    
    # 创建示例数据
    pos_output = {
        'sqe_c': torch.tensor([0.8, 0.7, 0.9]),
        'delta_syn': torch.tensor([0.1, 0.05, 0.15]),
        'delta_conf': torch.tensor([-0.05, -0.02, -0.08]),
        'delta_bal': torch.tensor([0.02, 0.01, 0.03])
    }
    
    neg_output = {
        'sqe_c': torch.tensor([0.6, 0.8, 0.7]),
        'delta_syn': torch.tensor([-0.1, 0.1, -0.05]),
        'delta_conf': torch.tensor([0.05, -0.1, 0.02]),
        'delta_bal': torch.tensor([-0.02, 0.05, -0.01])
    }
    
    # 测试损失函数
    rank_loss = pairwise_ranking_loss(pos_output, neg_output)
    res_loss = residual_regularization(pos_output, neg_output)
    total = total_loss(pos_output, neg_output)
    
    print(f"[INFO] Pairwise ranking loss: {rank_loss.item():.4f}")
    print(f"[INFO] Residual regularization loss: {res_loss.item():.4f}")
    print(f"[INFO] Total loss: {total.item():.4f}")
    
    # 测试评估指标
    accuracy = pair_accuracy(pos_output, neg_output)
    margin = average_margin(pos_output, neg_output)
    
    print(f"[INFO] Pair accuracy: {accuracy:.4f}")
    print(f"[INFO] Average margin: {margin:.4f}")
    
    # 测试按扰动类型计算 margin
    perturb_types = ['balance_change_role', 'synergy_insert_different_type', 'conflict_acid_sweetener_ratio_break']
    margin_by_type = margin_by_perturb_type([pos_output], [neg_output], perturb_types)
    print(f"[INFO] Margin by perturb type: {margin_by_type}")
    
    # 测试计算所有指标
    metrics = compute_metrics([pos_output], [neg_output], perturb_types)
    print(f"[INFO] All metrics: {metrics}")
    
    print("[INFO] Phase C 损失函数和评估指标测试完成！")

if __name__ == "__main__":
    main()
