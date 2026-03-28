# -*- coding: utf-8 -*-
"""
测试模型是否能够正确计算 sqe_c (使用随机数据)
"""

import torch
from model_phaseC_residual import ResidualGNNv1
from torch_geometric.data import Data

# 主函数
def main():
    """主函数"""
    print("测试模型是否能够正确计算 sqe_c...")
    
    # 创建随机数据
    print("[INFO] 创建随机数据...")
    node_in_dim = 22  # 节点特征维度
    graph_in_dim = 23  # 图级特征维度
    
    # 创建一个简单的图数据
    x = torch.randn(5, node_in_dim)  # 5 个节点，每个节点有 node_in_dim 个特征
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 4]], dtype=torch.long)  # 4 条边
    edge_attr = torch.randn(4, 4)  # 每条边有 4 个特征
    z_graph = torch.randn(1, graph_in_dim)  # 图级特征
    y_base = torch.randn(1, 3)  # 基础分数 [syn_B, conf_B, bal_B]
    
    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        z_graph=z_graph,
        y_base=y_base
    )
    
    # 初始化模型
    print("[INFO] 初始化模型...")
    model = ResidualGNNv1(
        node_in_dim=node_in_dim,
        graph_in_dim=graph_in_dim
    )
    
    # 前向传播
    print("[INFO] 前向传播...")
    with torch.no_grad():
        output = model(data)
    
    # 提取结果
    syn_B = y_base[:, 0].item()
    conf_B = y_base[:, 1].item()
    bal_B = y_base[:, 2].item()
    delta_syn = output['delta_syn'].item()
    delta_conf = output['delta_conf'].item()
    delta_bal = output['delta_bal'].item()
    hat_syn = output['hat_syn'].item()
    hat_conf = output['hat_conf'].item()
    hat_bal = output['hat_bal'].item()
    sqe_c = output['sqe_c'].item()
    
    # 计算 sqe_b
    alpha = 0.3521
    beta = 0.3067
    gamma = 0.3412
    sqe_b = alpha * syn_B - beta * conf_B + gamma * bal_B
    
    # 计算修正值的加权和
    delta_sqe = alpha * delta_syn - beta * delta_conf + gamma * delta_bal
    
    # 计算期望的 sqe_c
    expected_sqe_c = sqe_b + delta_sqe
    
    # 打印结果
    print("[INFO] 计算结果:")
    print(f"  syn_B: {syn_B:.4f}")
    print(f"  conf_B: {conf_B:.4f}")
    print(f"  bal_B: {bal_B:.4f}")
    print(f"  delta_syn: {delta_syn:.4f}")
    print(f"  delta_conf: {delta_conf:.4f}")
    print(f"  delta_bal: {delta_bal:.4f}")
    print(f"  hat_syn: {hat_syn:.4f}")
    print(f"  hat_conf: {hat_conf:.4f}")
    print(f"  hat_bal: {hat_bal:.4f}")
    print(f"  sqe_b: {sqe_b:.4f}")
    print(f"  delta_sqe: {delta_sqe:.4f}")
    print(f"  expected_sqe_c: {expected_sqe_c:.4f}")
    print(f"  actual_sqe_c: {sqe_c:.4f}")
    
    # 检查是否一致
    if abs(expected_sqe_c - sqe_c) < 1e-6:
        print("[INFO] 计算结果一致，模型正确计算 sqe_c！")
    else:
        print("[ERROR] 计算结果不一致，模型计算 sqe_c 有误！")

if __name__ == "__main__":
    main()
