# -*- coding: utf-8 -*-
"""
Phase C 训练主脚本 v2 - 改进版

改进点：
1. 按 group_id（原始 recipe）分组切分训练/验证集，避免数据泄漏
2. 修复 batch_size 配置不一致问题
3. 添加扰动类型统计和均衡性检查
4. 添加跨 recipe 泛化验证
"""

import os
import sys
import json
import csv
import torch
import torch.optim as optim
from torch.utils.data import Subset
from torch_geometric.loader import DataLoader
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from tqdm import tqdm

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 导入模块
from scripts.sqe.phase_C.config_phaseC import Config
from scripts.sqe.phase_C.phaseC_dataset import PhaseCGraphStore, PhaseCPairDataset
from scripts.sqe.phase_C.model_phaseC_residual import ResidualGNNv1
from scripts.sqe.phase_C.loss_phaseC import total_loss, compute_metrics

# =========================================================
# 工具函数
# =========================================================

def create_output_dirs():
    """创建输出目录"""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(Config.CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(Config.LOG_DIR, exist_ok=True)

def save_checkpoint(model, optimizer, epoch, best_metric, filename):
    """保存模型检查点"""
    checkpoint_path = os.path.join(Config.CHECKPOINT_DIR, filename)
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'best_metric': best_metric
    }, checkpoint_path)
    print(f"[INFO] 检查点已保存到: {checkpoint_path}")

def save_logs(logs, filename):
    """保存日志"""
    log_path = os.path.join(Config.LOG_DIR, filename)
    with open(log_path, 'w', encoding='utf-8', newline='') as f:
        if logs:
            fieldnames = logs[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for log in logs:
                writer.writerow(log)
    print(f"[INFO] 日志已保存到: {log_path}")

def save_curves(curves, filename):
    """保存训练曲线"""
    curve_path = os.path.join(Config.LOG_DIR, filename)
    with open(curve_path, 'w', encoding='utf-8') as f:
        json.dump(curves, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 训练曲线已保存到: {curve_path}")

# =========================================================
# 分组切分函数
# =========================================================

def group_based_split(dataset, test_size=0.2, valid_size=0.1, random_seed=42):
    """
    按 group_id 分组切分数据集
    
    参数:
        dataset: PhaseCPairDataset 数据集
        test_size: 测试集比例
        valid_size: 验证集比例（从训练集中再划分）
        random_seed: 随机种子
    
    返回:
        train_indices, valid_indices, test_indices
    """
    import numpy as np
    np.random.seed(random_seed)
    
    # 收集每个 group_id 对应的样本索引
    group_to_indices = defaultdict(list)
    for idx in range(len(dataset)):
        group_id = dataset.pairs.iloc[idx]['group_id']
        group_to_indices[group_id].append(idx)
    
    # 获取所有 group_id 并随机打乱
    all_groups = list(group_to_indices.keys())
    np.random.shuffle(all_groups)
    
    # 计算切分点
    n_groups = len(all_groups)
    n_test = int(n_groups * test_size)
    n_valid = int(n_groups * valid_size)
    n_train = n_groups - n_test - n_valid
    
    # 切分 group
    train_groups = set(all_groups[:n_train])
    valid_groups = set(all_groups[n_train:n_train + n_valid])
    test_groups = set(all_groups[n_train + n_valid:])
    
    # 收集对应的样本索引
    train_indices = []
    valid_indices = []
    test_indices = []
    
    for group_id, indices in group_to_indices.items():
        if group_id in train_groups:
            train_indices.extend(indices)
        elif group_id in valid_groups:
            valid_indices.extend(indices)
        else:
            test_indices.extend(indices)
    
    print(f"[INFO] 分组切分结果:")
    print(f"  总 group 数: {n_groups}")
    print(f"  训练组: {len(train_groups)} 个, 样本数: {len(train_indices)}")
    print(f"  验证组: {len(valid_groups)} 个, 样本数: {len(valid_indices)}")
    print(f"  测试组: {len(test_groups)} 个, 样本数: {len(test_indices)}")
    
    return train_indices, valid_indices, test_indices

def analyze_perturbation_distribution(dataset, indices, split_name):
    """
    分析扰动类型分布
    
    参数:
        dataset: PhaseCPairDataset 数据集
        indices: 样本索引列表
        split_name: 数据集名称（训练/验证/测试）
    """
    perturb_count = defaultdict(int)
    for idx in indices:
        perturb_type = dataset.pairs.iloc[idx]['perturb_type']
        perturb_count[perturb_type] += 1
    
    print(f"\n[INFO] {split_name} 集扰动类型分布:")
    for perturb_type, count in sorted(perturb_count.items()):
        percentage = count / len(indices) * 100
        print(f"  {perturb_type}: {count} ({percentage:.1f}%)")
    
    return perturb_count

# =========================================================
# 训练函数
# =========================================================

def train_one_epoch(model, dataloader, optimizer, epoch):
    """训练一个轮次"""
    model.train()
    total_loss_epoch = 0.0
    total_accuracy = 0.0
    total_margin = 0.0
    
    # 使用 tqdm 添加进度条
    with tqdm(dataloader, desc=f"Epoch {epoch+1} 训练", unit="batch") as pbar:
        for batch_idx, batch in enumerate(pbar):
            from torch_geometric.data import Data
            
            # 由于 PyTorch Geometric DataLoader 的特性，我们需要单独处理每个样本
            # 我们将 batch_size 设置为 1，这样每个批次只包含一个样本对
            # 这样可以避免 edge_index 合并的问题
            
            # 处理正样本数据
            pos_x = batch.pos_x
            pos_edge_index = batch.pos_edge_index
            pos_edge_attr = batch.pos_edge_attr
            pos_z_graph = batch.pos_z_graph
            pos_y_base = batch.pos_y_base
            
            # 确保维度正确
            if pos_x.dim() == 1:
                pos_x = pos_x.unsqueeze(0)
            
            # 处理 edge_index 维度
            # 正确的 edge_index 应该是 2xN 的维度
            num_nodes = pos_x.size(0)
            
            if pos_edge_index.dim() == 1:
                # 如果是 1D 张量，需要重塑
                if pos_edge_index.size(0) % 2 == 0:
                    pos_edge_index = pos_edge_index.view(2, -1)
                else:
                    # 如果长度不是偶数，创建一个空的 edge_index
                    pos_edge_index = torch.tensor([[], []], dtype=torch.long, device=pos_edge_index.device)
            elif pos_edge_index.dim() == 2:
                # 如果是 2D 张量，确保第一个维度是 2
                if pos_edge_index.size(0) != 2:
                    # 检查第二个维度是否是 2
                    if pos_edge_index.size(1) == 2:
                        pos_edge_index = pos_edge_index.t()
                    else:
                        # 如果两个维度都不是 2，创建一个空的 edge_index
                        pos_edge_index = torch.tensor([[], []], dtype=torch.long, device=pos_edge_index.device)
            
            # 确保 edge_index 中的索引值在有效范围内
            if pos_edge_index.size(1) > 0:
                # 检查所有索引值是否都在 [0, num_nodes) 范围内
                max_index = pos_edge_index.max().item()
                if max_index >= num_nodes:
                    # 如果有索引值超出范围，创建一个空的 edge_index
                    pos_edge_index = torch.tensor([[], []], dtype=torch.long, device=pos_edge_index.device)
            
            # 处理 edge_attr 维度
            if pos_edge_attr.dim() == 1:
                pos_edge_attr = pos_edge_attr.unsqueeze(0)
            # 确保 edge_attr 的长度与 edge_index 的边数一致
            if pos_edge_index.size(1) > 0 and pos_edge_attr.size(0) != pos_edge_index.size(1):
                # 如果边数不匹配，创建空的 edge_attr
                pos_edge_attr = torch.zeros(pos_edge_index.size(1), 4, dtype=torch.float, device=pos_edge_attr.device)
            
            # 确保 z_graph 是二维张量
            if pos_z_graph.dim() == 0:
                # 如果是标量，转换为 1x23 张量（与模型初始化时的维度一致）
                pos_z_graph = torch.zeros(1, 23, dtype=torch.float, device=pos_z_graph.device)
            elif pos_z_graph.dim() == 1:
                # 如果是 1D 张量，确保它的长度是 23
                if pos_z_graph.size(0) != 23:
                    # 如果长度不是 23，创建一个 1x23 的零张量
                    pos_z_graph = torch.zeros(1, 23, dtype=torch.float, device=pos_z_graph.device)
                else:
                    # 如果长度是 23，转换为 1x23 张量
                    pos_z_graph = pos_z_graph.unsqueeze(0)
            elif pos_z_graph.dim() == 2:
                # 如果是 2D 张量，确保它的形状是 1x23
                if pos_z_graph.size(1) != 23:
                    # 如果形状不是 1x23，创建一个 1x23 的零张量
                    pos_z_graph = torch.zeros(1, 23, dtype=torch.float, device=pos_z_graph.device)
            
            # 确保 y_base 是二维张量，形状为 (1, 3)
            if pos_y_base.dim() == 0:
                # 如果是标量，转换为 1x3 张量
                pos_y_base = torch.zeros(1, 3, dtype=torch.float, device=pos_y_base.device)
            elif pos_y_base.dim() == 1:
                # 如果是 1D 张量，确保它的长度是 3
                if pos_y_base.size(0) != 3:
                    # 如果长度不是 3，创建一个 1x3 的零张量
                    pos_y_base = torch.zeros(1, 3, dtype=torch.float, device=pos_y_base.device)
                else:
                    # 如果长度是 3，转换为 1x3 张量
                    pos_y_base = pos_y_base.unsqueeze(0)
            elif pos_y_base.dim() == 2:
                # 如果是 2D 张量，确保它的形状是 1x3
                if pos_y_base.size(1) != 3:
                    # 如果形状不是 1x3，创建一个 1x3 的零张量
                    pos_y_base = torch.zeros(1, 3, dtype=torch.float, device=pos_y_base.device)
            
            # 创建正样本 Data 对象
            pos_data = Data(
                x=pos_x,
                edge_index=pos_edge_index,
                edge_attr=pos_edge_attr,
                z_graph=pos_z_graph,
                y_base=pos_y_base
            )
            
            # 处理负样本数据
            neg_x = batch.neg_x
            neg_edge_index = batch.neg_edge_index
            neg_edge_attr = batch.neg_edge_attr
            neg_z_graph = batch.neg_z_graph
            neg_y_base = batch.neg_y_base
            
            # 确保维度正确
            if neg_x.dim() == 1:
                neg_x = neg_x.unsqueeze(0)
            
            # 处理 edge_index 维度
            # 正确的 edge_index 应该是 2xN 的维度
            num_nodes = neg_x.size(0)
            
            if neg_edge_index.dim() == 1:
                # 如果是 1D 张量，需要重塑
                if neg_edge_index.size(0) % 2 == 0:
                    neg_edge_index = neg_edge_index.view(2, -1)
                else:
                    # 如果长度不是偶数，创建一个空的 edge_index
                    neg_edge_index = torch.tensor([[], []], dtype=torch.long, device=neg_edge_index.device)
            elif neg_edge_index.dim() == 2:
                # 如果是 2D 张量，确保第一个维度是 2
                if neg_edge_index.size(0) != 2:
                    # 检查第二个维度是否是 2
                    if neg_edge_index.size(1) == 2:
                        neg_edge_index = neg_edge_index.t()
                    else:
                        # 如果两个维度都不是 2，创建一个空的 edge_index
                        neg_edge_index = torch.tensor([[], []], dtype=torch.long, device=neg_edge_index.device)
            
            # 确保 edge_index 中的索引值在有效范围内
            if neg_edge_index.size(1) > 0:
                # 检查所有索引值是否都在 [0, num_nodes) 范围内
                max_index = neg_edge_index.max().item()
                if max_index >= num_nodes:
                    # 如果有索引值超出范围，创建一个空的 edge_index
                    neg_edge_index = torch.tensor([[], []], dtype=torch.long, device=neg_edge_index.device)
            
            # 处理 edge_attr 维度
            if neg_edge_attr.dim() == 1:
                neg_edge_attr = neg_edge_attr.unsqueeze(0)
            # 确保 edge_attr 的长度与 edge_index 的边数一致
            if neg_edge_index.size(1) > 0 and neg_edge_attr.size(0) != neg_edge_index.size(1):
                # 如果边数不匹配，创建空的 edge_attr
                neg_edge_attr = torch.zeros(neg_edge_index.size(1), 4, dtype=torch.float, device=neg_edge_attr.device)
            
            # 确保 z_graph 是二维张量
            if neg_z_graph.dim() == 0:
                # 如果是标量，转换为 1x23 张量（与模型初始化时的维度一致）
                neg_z_graph = torch.zeros(1, 23, dtype=torch.float, device=neg_z_graph.device)
            elif neg_z_graph.dim() == 1:
                # 如果是 1D 张量，确保它的长度是 23
                if neg_z_graph.size(0) != 23:
                    # 如果长度不是 23，创建一个 1x23 的零张量
                    neg_z_graph = torch.zeros(1, 23, dtype=torch.float, device=neg_z_graph.device)
                else:
                    # 如果长度是 23，转换为 1x23 张量
                    neg_z_graph = neg_z_graph.unsqueeze(0)
            elif neg_z_graph.dim() == 2:
                # 如果是 2D 张量，确保它的形状是 1x23
                if neg_z_graph.size(1) != 23:
                    # 如果形状不是 1x23，创建一个 1x23 的零张量
                    neg_z_graph = torch.zeros(1, 23, dtype=torch.float, device=neg_z_graph.device)
            
            # 确保 y_base 是二维张量，形状为 (1, 3)
            if neg_y_base.dim() == 0:
                # 如果是标量，转换为 1x3 张量
                neg_y_base = torch.zeros(1, 3, dtype=torch.float, device=neg_y_base.device)
            elif neg_y_base.dim() == 1:
                # 如果是 1D 张量，确保它的长度是 3
                if neg_y_base.size(0) != 3:
                    # 如果长度不是 3，创建一个 1x3 的零张量
                    neg_y_base = torch.zeros(1, 3, dtype=torch.float, device=neg_y_base.device)
                else:
                    # 如果长度是 3，转换为 1x3 张量
                    neg_y_base = neg_y_base.unsqueeze(0)
            elif neg_y_base.dim() == 2:
                # 如果是 2D 张量，确保它的形状是 1x3
                if neg_y_base.size(1) != 3:
                    # 如果形状不是 1x3，创建一个 1x3 的零张量
                    neg_y_base = torch.zeros(1, 3, dtype=torch.float, device=neg_y_base.device)
            
            # 创建负样本 Data 对象
            neg_data = Data(
                x=neg_x,
                edge_index=neg_edge_index,
                edge_attr=neg_edge_attr,
                z_graph=neg_z_graph,
                y_base=neg_y_base
            )
            
            # 移动到设备
            pos_data = pos_data.to(Config.DEVICE)
            neg_data = neg_data.to(Config.DEVICE)
            
            # 前向传播
            pos_output = model(pos_data)
            neg_output = model(neg_data)
            
            # 计算损失
            loss = total_loss(pos_output, neg_output, lambda_res=Config.LAMBDA_RES)
            
            # 计算指标
            accuracy = (pos_output['sqe_c'] > neg_output['sqe_c']).float().item()
            margin = (pos_output['sqe_c'] - neg_output['sqe_c']).item()
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            
            # 计算梯度范数
            grad_norm = 0.0
            for param in model.parameters():
                if param.grad is not None:
                    grad_norm += param.grad.norm().item() ** 2
            grad_norm = grad_norm ** 0.5
            
            optimizer.step()
            
            # 累计统计
            total_loss_epoch += loss.item()
            total_accuracy += accuracy
            total_margin += margin
            
            # 更新进度条
            pbar.set_postfix({
                'loss': loss.item(),
                'accuracy': accuracy,
                'margin': margin
            })
    
    # 计算平均值
    avg_loss = total_loss_epoch / len(dataloader)
    avg_accuracy = total_accuracy / len(dataloader)
    avg_margin = total_margin / len(dataloader)
    
    return avg_loss, avg_accuracy, avg_margin

def validate(model, dataloader, epoch):
    """验证模型"""
    model.eval()
    total_loss_epoch = 0.0
    total_accuracy = 0.0
    total_margin = 0.0
    
    pos_outputs = []
    neg_outputs = []
    perturb_types = []
    
    with torch.no_grad():
        for batch_idx, batch in enumerate(dataloader):
            from torch_geometric.data import Data
            
            # 处理正样本数据
            pos_x = batch.pos_x
            pos_edge_index = batch.pos_edge_index
            pos_edge_attr = batch.pos_edge_attr
            pos_z_graph = batch.pos_z_graph
            pos_y_base = batch.pos_y_base
            
            # 确保维度正确
            if pos_x.dim() == 1:
                pos_x = pos_x.unsqueeze(0)
            
            # 处理 edge_index 维度
            # 正确的 edge_index 应该是 2xN 的维度
            num_nodes = pos_x.size(0)
            
            if pos_edge_index.dim() == 1:
                # 如果是 1D 张量，需要重塑
                if pos_edge_index.size(0) % 2 == 0:
                    pos_edge_index = pos_edge_index.view(2, -1)
                else:
                    # 如果长度不是偶数，创建一个空的 edge_index
                    pos_edge_index = torch.tensor([[], []], dtype=torch.long, device=pos_edge_index.device)
            elif pos_edge_index.dim() == 2:
                # 如果是 2D 张量，确保第一个维度是 2
                if pos_edge_index.size(0) != 2:
                    # 检查第二个维度是否是 2
                    if pos_edge_index.size(1) == 2:
                        pos_edge_index = pos_edge_index.t()
                    else:
                        # 如果两个维度都不是 2，创建一个空的 edge_index
                        pos_edge_index = torch.tensor([[], []], dtype=torch.long, device=pos_edge_index.device)
            
            # 确保 edge_index 中的索引值在有效范围内
            if pos_edge_index.size(1) > 0:
                # 检查所有索引值是否都在 [0, num_nodes) 范围内
                max_index = pos_edge_index.max().item()
                if max_index >= num_nodes:
                    # 如果有索引值超出范围，创建一个空的 edge_index
                    pos_edge_index = torch.tensor([[], []], dtype=torch.long, device=pos_edge_index.device)
            
            # 处理 edge_attr 维度
            if pos_edge_attr.dim() == 1:
                pos_edge_attr = pos_edge_attr.unsqueeze(0)
            # 确保 edge_attr 的长度与 edge_index 的边数一致
            if pos_edge_index.size(1) > 0 and pos_edge_attr.size(0) != pos_edge_index.size(1):
                # 如果边数不匹配，创建空的 edge_attr
                pos_edge_attr = torch.zeros(pos_edge_index.size(1), 4, dtype=torch.float, device=pos_edge_attr.device)
            
            # 确保 z_graph 是二维张量
            if pos_z_graph.dim() == 0:
                # 如果是标量，转换为 1x23 张量（与模型初始化时的维度一致）
                pos_z_graph = torch.zeros(1, 23, dtype=torch.float, device=pos_z_graph.device)
            elif pos_z_graph.dim() == 1:
                # 如果是 1D 张量，确保它的长度是 23
                if pos_z_graph.size(0) != 23:
                    # 如果长度不是 23，创建一个 1x23 的零张量
                    pos_z_graph = torch.zeros(1, 23, dtype=torch.float, device=pos_z_graph.device)
                else:
                    # 如果长度是 23，转换为 1x23 张量
                    pos_z_graph = pos_z_graph.unsqueeze(0)
            elif pos_z_graph.dim() == 2:
                # 如果是 2D 张量，确保它的形状是 1x23
                if pos_z_graph.size(1) != 23:
                    # 如果形状不是 1x23，创建一个 1x23 的零张量
                    pos_z_graph = torch.zeros(1, 23, dtype=torch.float, device=pos_z_graph.device)
            
            # 确保 y_base 是二维张量，形状为 (1, 3)
            if pos_y_base.dim() == 0:
                # 如果是标量，转换为 1x3 张量
                pos_y_base = torch.zeros(1, 3, dtype=torch.float, device=pos_y_base.device)
            elif pos_y_base.dim() == 1:
                # 如果是 1D 张量，确保它的长度是 3
                if pos_y_base.size(0) != 3:
                    # 如果长度不是 3，创建一个 1x3 的零张量
                    pos_y_base = torch.zeros(1, 3, dtype=torch.float, device=pos_y_base.device)
                else:
                    # 如果长度是 3，转换为 1x3 张量
                    pos_y_base = pos_y_base.unsqueeze(0)
            elif pos_y_base.dim() == 2:
                # 如果是 2D 张量，确保它的形状是 1x3
                if pos_y_base.size(1) != 3:
                    # 如果形状不是 1x3，创建一个 1x3 的零张量
                    pos_y_base = torch.zeros(1, 3, dtype=torch.float, device=pos_y_base.device)
            
            # 创建正样本 Data 对象
            pos_data = Data(
                x=pos_x,
                edge_index=pos_edge_index,
                edge_attr=pos_edge_attr,
                z_graph=pos_z_graph,
                y_base=pos_y_base
            )
            
            # 处理负样本数据
            neg_x = batch.neg_x
            neg_edge_index = batch.neg_edge_index
            neg_edge_attr = batch.neg_edge_attr
            neg_z_graph = batch.neg_z_graph
            neg_y_base = batch.neg_y_base
            
            # 确保维度正确
            if neg_x.dim() == 1:
                neg_x = neg_x.unsqueeze(0)
            
            # 处理 edge_index 维度
            # 正确的 edge_index 应该是 2xN 的维度
            num_nodes = neg_x.size(0)
            
            if neg_edge_index.dim() == 1:
                # 如果是 1D 张量，需要重塑
                if neg_edge_index.size(0) % 2 == 0:
                    neg_edge_index = neg_edge_index.view(2, -1)
                else:
                    # 如果长度不是偶数，创建一个空的 edge_index
                    neg_edge_index = torch.tensor([[], []], dtype=torch.long, device=neg_edge_index.device)
            elif neg_edge_index.dim() == 2:
                # 如果是 2D 张量，确保第一个维度是 2
                if neg_edge_index.size(0) != 2:
                    # 检查第二个维度是否是 2
                    if neg_edge_index.size(1) == 2:
                        neg_edge_index = neg_edge_index.t()
                    else:
                        # 如果两个维度都不是 2，创建一个空的 edge_index
                        neg_edge_index = torch.tensor([[], []], dtype=torch.long, device=neg_edge_index.device)
            
            # 确保 edge_index 中的索引值在有效范围内
            if neg_edge_index.size(1) > 0:
                # 检查所有索引值是否都在 [0, num_nodes) 范围内
                max_index = neg_edge_index.max().item()
                if max_index >= num_nodes:
                    # 如果有索引值超出范围，创建一个空的 edge_index
                    neg_edge_index = torch.tensor([[], []], dtype=torch.long, device=neg_edge_index.device)
            
            # 处理 edge_attr 维度
            if neg_edge_attr.dim() == 1:
                neg_edge_attr = neg_edge_attr.unsqueeze(0)
            # 确保 edge_attr 的长度与 edge_index 的边数一致
            if neg_edge_index.size(1) > 0 and neg_edge_attr.size(0) != neg_edge_index.size(1):
                # 如果边数不匹配，创建空的 edge_attr
                neg_edge_attr = torch.zeros(neg_edge_index.size(1), 4, dtype=torch.float, device=neg_edge_attr.device)
            
            # 确保 z_graph 是二维张量
            if neg_z_graph.dim() == 0:
                # 如果是标量，转换为 1x23 张量（与模型初始化时的维度一致）
                neg_z_graph = torch.zeros(1, 23, dtype=torch.float, device=neg_z_graph.device)
            elif neg_z_graph.dim() == 1:
                # 如果是 1D 张量，确保它的长度是 23
                if neg_z_graph.size(0) != 23:
                    # 如果长度不是 23，创建一个 1x23 的零张量
                    neg_z_graph = torch.zeros(1, 23, dtype=torch.float, device=neg_z_graph.device)
                else:
                    # 如果长度是 23，转换为 1x23 张量
                    neg_z_graph = neg_z_graph.unsqueeze(0)
            elif neg_z_graph.dim() == 2:
                # 如果是 2D 张量，确保它的形状是 1x23
                if neg_z_graph.size(1) != 23:
                    # 如果形状不是 1x23，创建一个 1x23 的零张量
                    neg_z_graph = torch.zeros(1, 23, dtype=torch.float, device=neg_z_graph.device)
            
            # 确保 y_base 是二维张量，形状为 (1, 3)
            if neg_y_base.dim() == 0:
                # 如果是标量，转换为 1x3 张量
                neg_y_base = torch.zeros(1, 3, dtype=torch.float, device=neg_y_base.device)
            elif neg_y_base.dim() == 1:
                # 如果是 1D 张量，确保它的长度是 3
                if neg_y_base.size(0) != 3:
                    # 如果长度不是 3，创建一个 1x3 的零张量
                    neg_y_base = torch.zeros(1, 3, dtype=torch.float, device=neg_y_base.device)
                else:
                    # 如果长度是 3，转换为 1x3 张量
                    neg_y_base = neg_y_base.unsqueeze(0)
            elif neg_y_base.dim() == 2:
                # 如果是 2D 张量，确保它的形状是 1x3
                if neg_y_base.size(1) != 3:
                    # 如果形状不是 1x3，创建一个 1x3 的零张量
                    neg_y_base = torch.zeros(1, 3, dtype=torch.float, device=neg_y_base.device)
            
            # 创建负样本 Data 对象
            neg_data = Data(
                x=neg_x,
                edge_index=neg_edge_index,
                edge_attr=neg_edge_attr,
                z_graph=neg_z_graph,
                y_base=neg_y_base
            )
            
            # 移动到设备
            pos_data = pos_data.to(Config.DEVICE)
            neg_data = neg_data.to(Config.DEVICE)
            
            # 前向传播
            pos_output = model(pos_data)
            neg_output = model(neg_data)
            
            # 计算损失
            loss = total_loss(pos_output, neg_output, lambda_res=Config.LAMBDA_RES)
            
            # 计算指标
            accuracy = (pos_output['sqe_c'] > neg_output['sqe_c']).float().item()
            margin = (pos_output['sqe_c'] - neg_output['sqe_c']).item()
            
            # 累计统计
            total_loss_epoch += loss.item()
            total_accuracy += accuracy
            total_margin += margin
            
            # 收集输出和扰动类型
            pos_outputs.append(pos_output)
            neg_outputs.append(neg_output)
            # 确保 perturb_type 是一个字符串
            perturb_type = batch.perturb_type
            if isinstance(perturb_type, list):
                if len(perturb_type) > 0:
                    perturb_type = perturb_type[0]
                else:
                    perturb_type = "unknown"
            perturb_types.append(perturb_type)
    
    # 计算平均值
    avg_loss = total_loss_epoch / len(dataloader)
    avg_accuracy = total_accuracy / len(dataloader)
    avg_margin = total_margin / len(dataloader)
    
    # 计算按扰动类型的准确率
    if perturb_types:
        metrics = compute_metrics(pos_outputs, neg_outputs, perturb_types)
        margin_by_type = metrics.get('margin_by_perturb_type', {})
    else:
        margin_by_type = {}
    
    return avg_loss, avg_accuracy, avg_margin, margin_by_type

# =========================================================
# 扰动类型 holdout 验证函数
# =========================================================

def perturbation_holdout_split(dataset, holdout_perturb_type, random_seed=42):
    """
    按扰动类型进行 holdout 验证
    
    参数:
        dataset: PhaseCPairDataset 数据集
        holdout_perturb_type: 保留为验证集的扰动类型
        random_seed: 随机种子
    
    返回:
        train_indices, valid_indices
    """
    import numpy as np
    np.random.seed(random_seed)
    
    train_indices = []
    valid_indices = []
    
    for idx in range(len(dataset)):
        perturb_type = dataset.pairs.iloc[idx]['perturb_type']
        if perturb_type == holdout_perturb_type:
            valid_indices.append(idx)
        else:
            train_indices.append(idx)
    
    print(f"[INFO] 扰动类型 Holdout 验证: 保留 {holdout_perturb_type} 作为验证集")
    print(f"[INFO] 训练样本数: {len(train_indices)}")
    print(f"[INFO] 验证样本数: {len(valid_indices)}")
    
    return train_indices, valid_indices

# =========================================================
# 主函数
# =========================================================
def main():
    """主函数"""
    print("开始 Phase C 训练 v2 (Group-based Split)...")
    
    # 打印配置
    Config.print_config()
    
    # 创建输出目录
    create_output_dirs()
    
    # 加载数据
    print("[INFO] 加载数据...")
    graphs_file = os.path.join(_project_root, Config.GRAPHS_FILE)
    pairs_file = os.path.join(_project_root, Config.PAIRS_FILE)
    graph_store = PhaseCGraphStore(graphs_file)
    dataset = PhaseCPairDataset(pairs_file, graph_store)
    
    # 按 group_id 分组切分数据集
    print("[INFO] 按 group_id 分组切分数据集...")
    train_idx, valid_idx, test_idx = group_based_split(
        dataset, 
        test_size=0.2, 
        valid_size=0.1, 
        random_seed=Config.SEED
    )
    
    # 分析扰动类型分布
    analyze_perturbation_distribution(dataset, train_idx, "训练")
    analyze_perturbation_distribution(dataset, valid_idx, "验证")
    analyze_perturbation_distribution(dataset, test_idx, "测试")
    
    train_dataset = Subset(dataset, train_idx)
    valid_dataset = Subset(dataset, valid_idx)
    test_dataset = Subset(dataset, test_idx)
    
    # 创建数据加载器 - 使用 batch_size=1，因为每个批次只处理一个样本对
    print("[INFO] 使用 batch_size=1")
    train_loader = DataLoader(train_dataset, batch_size=1, shuffle=True, num_workers=0)
    valid_loader = DataLoader(valid_dataset, batch_size=1, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=0)
    
    # 初始化模型
    print("[INFO] 初始化模型...")
    sample = dataset[0]
    node_in_dim = sample.pos_x.size(1)
    
    # 处理 z_graph 维度
    if sample.pos_z_graph.dim() == 1:
        graph_in_dim = sample.pos_z_graph.size(0)
    else:
        graph_in_dim = sample.pos_z_graph.size(1)
    
    # 打印维度信息
    print(f"[INFO] 节点特征维度: {node_in_dim}")
    print(f"[INFO] 图级特征维度: {graph_in_dim}")
    print(f"[INFO] 池化维度: {Config.HIDDEN_DIM * 2}")
    print(f"[INFO] MLP 输入维度: {Config.HIDDEN_DIM * 2 + graph_in_dim}")
    
    model = ResidualGNNv1(
        node_in_dim=node_in_dim,
        graph_in_dim=graph_in_dim
    ).to(Config.DEVICE)
    
    # 初始化优化器 - 增加权重衰减
    optimizer = optim.Adam(
        model.parameters(), 
        lr=Config.LEARNING_RATE, 
        weight_decay=0.005  # 增加权重衰减
    )
    
    # 训练日志
    logs = []
    curves = {
        'train_loss': [],
        'train_accuracy': [],
        'train_margin': [],
        'valid_loss': [],
        'valid_accuracy': [],
        'valid_margin': []
    }
    
    # 最佳指标
    best_accuracy = 0.0
    best_margin = 0.0
    no_improvement = 0
    
    # 训练循环
    for epoch in tqdm(range(Config.EPOCHS), desc="训练进度", unit="epoch"):
        # 训练一个轮次
        train_loss, train_accuracy, train_margin = train_one_epoch(model, train_loader, optimizer, epoch)
        
        # 验证
        valid_loss, valid_accuracy, valid_margin, margin_by_type = validate(model, valid_loader, epoch)
        
        # 记录日志
        log = {
            'epoch': epoch + 1,
            'train_loss': train_loss,
            'train_accuracy': train_accuracy,
            'train_margin': train_margin,
            'valid_loss': valid_loss,
            'valid_accuracy': valid_accuracy,
            'valid_margin': valid_margin
        }
        logs.append(log)
        
        # 记录训练曲线
        curves['train_loss'].append(train_loss)
        curves['train_accuracy'].append(train_accuracy)
        curves['train_margin'].append(train_margin)
        curves['valid_loss'].append(valid_loss)
        curves['valid_accuracy'].append(valid_accuracy)
        curves['valid_margin'].append(valid_margin)
        
        # 打印验证结果
        print(f"\n[INFO] Epoch {epoch+1}/{Config.EPOCHS}")
        print(f"[INFO] 训练: Loss={train_loss:.4f}, Accuracy={train_accuracy:.4f}, Margin={train_margin:.4f}")
        print(f"[INFO] 验证: Loss={valid_loss:.4f}, Accuracy={valid_accuracy:.4f}, Margin={valid_margin:.4f}")
        
        # 保存最佳模型
        if valid_accuracy > best_accuracy:
            best_accuracy = valid_accuracy
            save_checkpoint(model, optimizer, epoch, best_accuracy, 'best_by_acc.pt')
            no_improvement = 0
        else:
            no_improvement += 1
        
        if valid_margin > best_margin:
            best_margin = valid_margin
            save_checkpoint(model, optimizer, epoch, best_margin, 'best_by_margin.pt')
        
        # 早停
        if no_improvement >= Config.EARLY_STOP:
            print(f"[INFO] 早停: {no_improvement} 轮无改进")
            break
    
    # 最终测试
    print("\n[INFO] 在测试集上评估...")
    test_loss, test_accuracy, test_margin, test_margin_by_type = validate(model, test_loader, Config.EPOCHS)
    print(f"[INFO] 测试集结果: Loss={test_loss:.4f}, Accuracy={test_accuracy:.4f}, Margin={test_margin:.4f}")
    print(f"[INFO] 测试集按扰动类型的 Margin:")
    for ptype, margin in sorted(test_margin_by_type.items()):
        print(f"  {ptype}: {margin:.4f}")
    
    # 扰动类型 Holdout 验证
    print("\n[INFO] 进行扰动类型 Holdout 验证...")
    perturb_types = dataset.pairs['perturb_type'].unique()
    holdout_results = {}
    
    for perturb_type in perturb_types:
        print(f"\n[INFO] Holdout 验证: {perturb_type}")
        holdout_train_idx, holdout_valid_idx = perturbation_holdout_split(dataset, perturb_type)
        
        holdout_train_dataset = Subset(dataset, holdout_train_idx)
        holdout_valid_dataset = Subset(dataset, holdout_valid_idx)
        
        holdout_train_loader = DataLoader(holdout_train_dataset, batch_size=1, shuffle=True, num_workers=0)
        holdout_valid_loader = DataLoader(holdout_valid_dataset, batch_size=1, shuffle=False, num_workers=0)
        
        # 重新初始化模型
        holdout_model = ResidualGNNv1(
            node_in_dim=node_in_dim,
            graph_in_dim=graph_in_dim
        ).to(Config.DEVICE)
        
        holdout_optimizer = optim.Adam(
            holdout_model.parameters(), 
            lr=Config.LEARNING_RATE, 
            weight_decay=Config.LAMBDA_REG
        )
        
        # 训练 5 个 epoch
        for epoch in range(5):
            train_one_epoch(holdout_model, holdout_train_loader, holdout_optimizer, epoch)
        
        # 验证
        holdout_loss, holdout_accuracy, holdout_margin, _ = validate(holdout_model, holdout_valid_loader, 5)
        print(f"[INFO] Holdout 验证结果: Loss={holdout_loss:.4f}, Accuracy={holdout_accuracy:.4f}, Margin={holdout_margin:.4f}")
        holdout_results[perturb_type] = {
            'loss': holdout_loss,
            'accuracy': holdout_accuracy,
            'margin': holdout_margin
        }
    
    # 保存最后模型
    save_checkpoint(model, optimizer, Config.EPOCHS, best_accuracy, 'last.pt')
    
    # 保存日志和训练曲线
    save_logs(logs, 'train_log_v2.csv')
    save_curves(curves, 'train_curves_v2.json')
    
    # 保存测试集结果
    test_results = {
        'test_loss': test_loss,
        'test_accuracy': test_accuracy,
        'test_margin': test_margin,
        'margin_by_type': test_margin_by_type,
        'holdout_results': holdout_results
    }
    with open(os.path.join(Config.LOG_DIR, 'test_results_v2.json'), 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print("\n[INFO] Phase C 训练 v2 完成！")

if __name__ == "__main__":
    main()
