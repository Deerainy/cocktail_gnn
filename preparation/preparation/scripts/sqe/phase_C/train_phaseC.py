# -*- coding: utf-8 -*-
"""
Phase C 训练主脚本

功能：
1. 读取配置
2. 构造数据集与 dataloader
3. 初始化模型
4. 训练循环
5. 验证循环
6. 保存 checkpoint
7. 输出训练日志
"""

import os
import sys
import json
import csv
import torch
import torch.optim as optim
from torch.utils.data import Subset
from torch_geometric.loader import DataLoader
from sklearn.model_selection import train_test_split
from typing import Dict, List, Tuple

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
    """
    创建输出目录
    """
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(Config.CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(Config.LOG_DIR, exist_ok=True)

def save_checkpoint(model: ResidualGNNv1, optimizer: optim.Optimizer, epoch: int, best_metric: float, filename: str):
    """
    保存模型检查点
    
    参数:
    model: 模型
    optimizer: 优化器
    epoch: 当前轮数
    best_metric: 最佳指标
    filename: 文件名
    """
    checkpoint_path = os.path.join(Config.CHECKPOINT_DIR, filename)
    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'best_metric': best_metric
    }, checkpoint_path)
    print(f"[INFO] 检查点已保存到: {checkpoint_path}")

def save_logs(logs: List[Dict], filename: str):
    """
    保存日志
    
    参数:
    logs: 日志列表
    filename: 文件名
    """
    log_path = os.path.join(Config.LOG_DIR, filename)
    with open(log_path, 'w', encoding='utf-8', newline='') as f:
        if logs:
            fieldnames = logs[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for log in logs:
                writer.writerow(log)
    print(f"[INFO] 日志已保存到: {log_path}")

def save_curves(curves: Dict, filename: str):
    """
    保存训练曲线
    
    参数:
    curves: 训练曲线数据
    filename: 文件名
    """
    curve_path = os.path.join(Config.LOG_DIR, filename)
    with open(curve_path, 'w', encoding='utf-8') as f:
        json.dump(curves, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 训练曲线已保存到: {curve_path}")

# =========================================================
# 训练函数
# =========================================================

def train_one_epoch(model: ResidualGNNv1, dataloader: DataLoader, optimizer: optim.Optimizer, epoch: int) -> Tuple[float, float, float]:
    """
    训练一个轮次
    
    参数:
    model: 模型
    dataloader: 数据加载器
    optimizer: 优化器
    epoch: 当前轮数
    
    返回:
    平均损失、平均准确率、平均 margin
    """
    model.train()
    total_loss_epoch = 0.0
    total_accuracy = 0.0
    total_margin = 0.0
    
    for batch_idx, batch in enumerate(dataloader):
        # 提取正样本数据
        # 注意：由于 batch_size=1，我们需要使用 squeeze() 来移除 batch 维度
        from torch_geometric.data import Data
        
        # 处理正样本数据
        pos_x = batch.pos_x.squeeze(0)
        pos_edge_index = batch.pos_edge_index.squeeze(0)
        pos_edge_attr = batch.pos_edge_attr.squeeze(0)
        pos_z_graph = batch.pos_z_graph.squeeze(0)
        pos_y_base = batch.pos_y_base.squeeze(0)
        
        # 确保 x 是 2 维的
        if pos_x.dim() == 1:
            pos_x = pos_x.unsqueeze(0)
        # 确保 edge_index 是 2xN 的维度
        if pos_edge_index.dim() == 1:
            pos_edge_index = pos_edge_index.unsqueeze(0)
        # 确保 edge_attr 是 Nx4 的维度
        if pos_edge_attr.dim() == 1:
            pos_edge_attr = pos_edge_attr.unsqueeze(0)
        # 确保 edge_index 是 2xN 的维度
        if pos_edge_index.size(0) != 2:
            pos_edge_index = pos_edge_index.t()
        
        # 创建正样本 Data 对象
        pos_data = Data(
            x=pos_x,
            edge_index=pos_edge_index,
            edge_attr=pos_edge_attr,
            z_graph=pos_z_graph,
            y_base=pos_y_base
        )
        
        # 处理负样本数据
        neg_x = batch.neg_x.squeeze(0)
        neg_edge_index = batch.neg_edge_index.squeeze(0)
        neg_edge_attr = batch.neg_edge_attr.squeeze(0)
        neg_z_graph = batch.neg_z_graph.squeeze(0)
        neg_y_base = batch.neg_y_base.squeeze(0)
        
        # 确保 x 是 2 维的
        if neg_x.dim() == 1:
            neg_x = neg_x.unsqueeze(0)
        # 确保 edge_index 是 2xN 的维度
        if neg_edge_index.dim() == 1:
            neg_edge_index = neg_edge_index.unsqueeze(0)
        # 确保 edge_attr 是 Nx4 的维度
        if neg_edge_attr.dim() == 1:
            neg_edge_attr = neg_edge_attr.unsqueeze(0)
        # 确保 edge_index 是 2xN 的维度
        if neg_edge_index.size(0) != 2:
            neg_edge_index = neg_edge_index.t()
        
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
        accuracy = (pos_output['sqe_c'] > neg_output['sqe_c']).float().mean().item()
        margin = (pos_output['sqe_c'] - neg_output['sqe_c']).mean().item()
        
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
        
        # 打印训练进度
        if (batch_idx + 1) % 100 == 0:
            print(f"[INFO] Epoch {epoch+1}, Batch {batch_idx+1}/{len(dataloader)}")
            print(f"[DEBUG] Loss: {loss.item():.4f}, Accuracy: {accuracy:.4f}, Margin: {margin:.4f}")
            print(f"[DEBUG] Pos y_base: {pos_y_base.cpu().numpy()}")
            print(f"[DEBUG] Neg y_base: {neg_y_base.cpu().numpy()}")
            print(f"[DEBUG] Pos delta: syn={pos_output['delta_syn'].item():.4f}, conf={pos_output['delta_conf'].item():.4f}, bal={pos_output['delta_bal'].item():.4f}")
            print(f"[DEBUG] Neg delta: syn={neg_output['delta_syn'].item():.4f}, conf={neg_output['delta_conf'].item():.4f}, bal={neg_output['delta_bal'].item():.4f}")
            print(f"[DEBUG] Pos sqe_c: {pos_output['sqe_c'].item():.4f}, Neg sqe_c: {neg_output['sqe_c'].item():.4f}")
            print(f"[DEBUG] Gradient norm: {grad_norm:.4f}")
    
    # 计算平均值
    avg_loss = total_loss_epoch / len(dataloader)
    avg_accuracy = total_accuracy / len(dataloader)
    avg_margin = total_margin / len(dataloader)
    
    return avg_loss, avg_accuracy, avg_margin

def validate(model: ResidualGNNv1, dataloader: DataLoader, epoch: int) -> Tuple[float, float, float, Dict]:
    """
    验证模型
    
    参数:
    model: 模型
    dataloader: 数据加载器
    epoch: 当前轮数
    
    返回:
    平均损失、平均准确率、平均 margin、按扰动类型的准确率
    """
    model.eval()
    total_loss_epoch = 0.0
    total_accuracy = 0.0
    total_margin = 0.0
    
    pos_outputs = []
    neg_outputs = []
    perturb_types = []
    
    with torch.no_grad():
        for batch_idx, batch in enumerate(dataloader):
            # 提取正样本数据
            # 注意：由于 batch_size=1，我们需要使用 squeeze() 来移除 batch 维度
            from torch_geometric.data import Data
            
            # 处理正样本数据
            pos_x = batch.pos_x.squeeze(0)
            pos_edge_index = batch.pos_edge_index.squeeze(0)
            pos_edge_attr = batch.pos_edge_attr.squeeze(0)
            pos_z_graph = batch.pos_z_graph.squeeze(0)
            pos_y_base = batch.pos_y_base.squeeze(0)
            
            # 确保 x 是 2 维的
            if pos_x.dim() == 1:
                pos_x = pos_x.unsqueeze(0)
            # 确保 edge_index 是 2xN 的维度
            if pos_edge_index.dim() == 1:
                pos_edge_index = pos_edge_index.unsqueeze(0)
            # 确保 edge_attr 是 Nx4 的维度
            if pos_edge_attr.dim() == 1:
                pos_edge_attr = pos_edge_attr.unsqueeze(0)
            # 确保 edge_index 是 2xN 的维度
            if pos_edge_index.size(0) != 2:
                pos_edge_index = pos_edge_index.t()
            
            # 创建正样本 Data 对象
            pos_data = Data(
                x=pos_x,
                edge_index=pos_edge_index,
                edge_attr=pos_edge_attr,
                z_graph=pos_z_graph,
                y_base=pos_y_base
            )
            
            # 处理负样本数据
            neg_x = batch.neg_x.squeeze(0)
            neg_edge_index = batch.neg_edge_index.squeeze(0)
            neg_edge_attr = batch.neg_edge_attr.squeeze(0)
            neg_z_graph = batch.neg_z_graph.squeeze(0)
            neg_y_base = batch.neg_y_base.squeeze(0)
            
            # 确保 x 是 2 维的
            if neg_x.dim() == 1:
                neg_x = neg_x.unsqueeze(0)
            # 确保 edge_index 是 2xN 的维度
            if neg_edge_index.dim() == 1:
                neg_edge_index = neg_edge_index.unsqueeze(0)
            # 确保 edge_attr 是 Nx4 的维度
            if neg_edge_attr.dim() == 1:
                neg_edge_attr = neg_edge_attr.unsqueeze(0)
            # 确保 edge_index 是 2xN 的维度
            if neg_edge_index.size(0) != 2:
                neg_edge_index = neg_edge_index.t()
            
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
            accuracy = (pos_output['sqe_c'] > neg_output['sqe_c']).float().mean().item()
            margin = (pos_output['sqe_c'] - neg_output['sqe_c']).mean().item()
            
            # 累计统计
            total_loss_epoch += loss.item()
            total_accuracy += accuracy
            total_margin += margin
            
            # 收集输出和扰动类型
            pos_outputs.append(pos_output)
            neg_outputs.append(neg_output)
            perturb_types.append(batch.perturb_type[0])  # 移除 batch 维度
    
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
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("开始 Phase C 训练...")
    
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
    
    # 划分训练集和验证集
    print("[INFO] 划分训练集和验证集...")
    train_idx, valid_idx = train_test_split(
        range(len(dataset)), 
        test_size=0.2, 
        random_state=Config.SEED
    )
    
    train_dataset = Subset(dataset, train_idx)
    valid_dataset = Subset(dataset, valid_idx)
    
    # 创建数据加载器，batch_size=1，因为我们的 Data 对象包含了两个图的信息
    train_loader = DataLoader(train_dataset, batch_size=1, shuffle=True, num_workers=0)
    valid_loader = DataLoader(valid_dataset, batch_size=1, shuffle=False, num_workers=0)
    
    # 初始化模型
    print("[INFO] 初始化模型...")
    # 获取节点和图级特征维度
    sample = dataset[0]
    # 从样本中获取正样本的节点和图级特征维度
    node_in_dim = sample.pos_x.size(1)
    # 处理 z_graph 维度
    if sample.pos_z_graph.dim() == 1:
        graph_in_dim = sample.pos_z_graph.size(0)
    else:
        graph_in_dim = sample.pos_z_graph.size(1)
    
    model = ResidualGNNv1(
        node_in_dim=node_in_dim,
        graph_in_dim=graph_in_dim
    ).to(Config.DEVICE)
    
    # 初始化优化器
    optimizer = optim.Adam(
        model.parameters(), 
        lr=Config.LEARNING_RATE, 
        weight_decay=Config.LAMBDA_REG
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
    print("[INFO] 开始训练...")
    for epoch in range(Config.EPOCHS):
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
        print(f"[INFO] Epoch {epoch+1}/{Config.EPOCHS}")
        print(f"[INFO] 训练: Loss={train_loss:.4f}, Accuracy={train_accuracy:.4f}, Margin={train_margin:.4f}")
        print(f"[INFO] 验证: Loss={valid_loss:.4f}, Accuracy={valid_accuracy:.4f}, Margin={valid_margin:.4f}")
        print(f"[INFO] 按扰动类型的 Margin: {margin_by_type}")
        
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
    
    # 保存最后模型
    save_checkpoint(model, optimizer, Config.EPOCHS, best_accuracy, 'last.pt')
    
    # 保存日志和训练曲线
    save_logs(logs, 'train_log.csv')
    save_curves(curves, 'train_curves.json')
    
    print("[INFO] Phase C 训练完成！")

if __name__ == "__main__":
    main()
