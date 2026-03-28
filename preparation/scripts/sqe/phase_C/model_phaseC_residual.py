# -*- coding: utf-8 -*-
"""
Phase C 模型定义脚本

功能：
1. 定义 Residual GNN v1 模型
2. 实现节点编码器、GINEConv、Pooling、图级特征拼接和 residual head
3. 提供模型的前向传播逻辑
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GINEConv, global_mean_pool, global_max_pool

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 模型参数
    HIDDEN_DIM = 64  # 隐藏维度
    NUM_LAYERS = 2  # GINEConv 层数
    DROPOUT = 0.4  # 增加 dropout 率
    
    # 固定的外层权重（来自 Phase B）
    ALPHA = 0.3521  # 协同权重
    BETA = 0.3067   # 冲突权重
    GAMMA = 0.3412  # 平衡权重

# =========================================================
# 节点编码器
# =========================================================

class NodeEncoder(nn.Module):
    """
    节点编码器
    将原始节点特征映射到隐藏维度
    """
    def __init__(self, in_dim: int, hidden_dim: int):
        """
        初始化节点编码器
        
        参数:
        in_dim: 输入特征维度
        hidden_dim: 隐藏维度
        """
        super(NodeEncoder, self).__init__()
        self.mlp = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(Config.DROPOUT),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(Config.DROPOUT)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        参数:
        x: 节点特征
        
        返回:
        编码后的节点特征
        """
        return self.mlp(x)

# =========================================================
# GINE 层
# =========================================================

class GINELayer(nn.Module):
    """
    GINE 层
    """
    def __init__(self, hidden_dim: int):
        """
        初始化 GINE 层
        
        参数:
        hidden_dim: 隐藏维度
        """
        super(GINELayer, self).__init__()
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(Config.DROPOUT),
            nn.Linear(hidden_dim, hidden_dim)
        )
        self.conv = GINEConv(self.mlp, edge_dim=4)  # 边特征维度为 4
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_attr: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        参数:
        x: 节点特征
        edge_index: 边索引
        edge_attr: 边特征
        
        返回:
        传播后的节点特征
        """
        return self.conv(x, edge_index, edge_attr)

# =========================================================
# Residual Head
# =========================================================

class ResidualHead(nn.Module):
    """
    Residual Head
    输出残差修正量
    """
    def __init__(self, in_dim: int):
        """
        初始化 Residual Head
        
        参数:
        in_dim: 输入特征维度
        """
        super(ResidualHead, self).__init__()
        self.mlp = nn.Sequential(
            nn.Linear(in_dim, in_dim // 2),
            nn.ReLU(),
            nn.Dropout(Config.DROPOUT),  # 添加 dropout 层
            nn.Linear(in_dim // 2, 1)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播
        
        参数:
        x: 输入特征
        
        返回:
        残差修正量
        """
        return self.mlp(x).squeeze(-1)

# =========================================================
# 主模型
# =========================================================

class ResidualGNNv1(nn.Module):
    """
    Residual GNN v1 模型
    """
    def __init__(self, node_in_dim: int, graph_in_dim: int):
        """
        初始化模型
        
        参数:
        node_in_dim: 节点输入特征维度
        graph_in_dim: 图级输入特征维度
        """
        super(ResidualGNNv1, self).__init__()
        
        # 节点编码器
        self.node_encoder = NodeEncoder(node_in_dim, Config.HIDDEN_DIM)
        
        # GINE 层
        self.gine_layers = nn.ModuleList()
        for _ in range(Config.NUM_LAYERS):
            self.gine_layers.append(GINELayer(Config.HIDDEN_DIM))
        
        # Pooling 后的特征维度
        pool_dim = 2 * Config.HIDDEN_DIM  # mean + max
        
        # 图级特征拼接后的维度
        graph_emb_dim = pool_dim + graph_in_dim
        
        # Residual Heads
        self.syn_head = ResidualHead(graph_emb_dim)
        self.conf_head = ResidualHead(graph_emb_dim)
        self.bal_head = ResidualHead(graph_emb_dim)
        
        # 固定的外层权重
        self.alpha = Config.ALPHA
        self.beta = Config.BETA
        self.gamma = Config.GAMMA
    
    def forward(self, data) -> dict:
        """
        前向传播
        
        参数:
        data: PyTorch Geometric Data 对象，包含：
            - x: 节点特征
            - edge_index: 边索引
            - edge_attr: 边特征
            - z_graph: 图级特征
            - y_base: 基础分数 [syn_B, conf_B, bal_B]
        
        返回:
        包含各种预测结果的字典
        """
        x, edge_index, edge_attr, z_graph, y_base = data.x, data.edge_index, data.edge_attr, data.z_graph, data.y_base
        
        # 处理 batch 信息
        if hasattr(data, 'batch'):
            batch = data.batch
        else:
            # 单图情况
            batch = torch.zeros(x.size(0), dtype=torch.long, device=x.device)
        
        # 确保 y_base 是二维张量 [batch_size, 3]
        if y_base.dim() == 1:
            y_base = y_base.unsqueeze(0)
        
        # 确保 z_graph 是二维张量 [batch_size, graph_in_dim]
        if z_graph.dim() == 1:
            z_graph = z_graph.unsqueeze(0)
        
        # 节点编码
        h = self.node_encoder(x)
        
        # GINE 层传播
        for gine_layer in self.gine_layers:
            h = gine_layer(h, edge_index, edge_attr)
            h = F.relu(h)
        
        # Pooling
        h_mean = global_mean_pool(h, batch)
        h_max = global_max_pool(h, batch)
        h_pool = torch.cat([h_mean, h_max], dim=1)
        
        # 拼接图级特征
        h_G = torch.cat([h_pool, z_graph], dim=1)
        
        # Residual Heads
        delta_syn = self.syn_head(h_G)
        delta_conf = self.conf_head(h_G)
        delta_bal = self.bal_head(h_G)
        
        # 计算预测分数
        syn_B, conf_B, bal_B = y_base[:, 0], y_base[:, 1], y_base[:, 2]
        hat_syn = syn_B + delta_syn
        hat_conf = conf_B + delta_conf
        hat_bal = bal_B + delta_bal
        
        # 计算 SQE 总分 (按照用户要求：修正值乘以权重，再和 sqe_b 相加)
        # 首先计算 sqe_b
        sqe_b = self.alpha * syn_B - self.beta * conf_B + self.gamma * bal_B
        # 然后计算修正值的加权和
        delta_sqe = self.alpha * delta_syn - self.beta * delta_conf + self.gamma * delta_bal
        # 最后计算 sqe_c
        sqe_c = sqe_b + delta_sqe
        # 使用 sigmoid 激活函数将 sqe_c 映射到 (0, 1) 之间
        sqe_c = torch.sigmoid(sqe_c)
        
        # 返回结果
        return {
            "delta_syn": delta_syn,
            "delta_conf": delta_conf,
            "delta_bal": delta_bal,
            "hat_syn": hat_syn,
            "hat_conf": hat_conf,
            "hat_bal": hat_bal,
            "sqe_c": sqe_c,
            "graph_emb": h_G
        }

# =========================================================
# 工具函数
# =========================================================

def create_residual_gnn_v1(node_in_dim: int, graph_in_dim: int) -> ResidualGNNv1:
    """
    创建 Residual GNN v1 模型
    
    参数:
    node_in_dim: 节点输入特征维度
    graph_in_dim: 图级输入特征维度
    
    返回:
    ResidualGNNv1 模型
    """
    model = ResidualGNNv1(node_in_dim, graph_in_dim)
    return model

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("创建 Residual GNN v1 模型...")
    
    # 示例：创建模型
    node_in_dim = 22  # 节点特征维度
    graph_in_dim = 23  # 图级特征维度
    model = create_residual_gnn_v1(node_in_dim, graph_in_dim)
    
    print(f"[INFO] 模型创建成功！")
    print(f"[INFO] 节点输入维度: {node_in_dim}")
    print(f"[INFO] 图级输入维度: {graph_in_dim}")
    print(f"[INFO] 隐藏维度: {Config.HIDDEN_DIM}")
    print(f"[INFO] GINE 层数: {Config.NUM_LAYERS}")
    print(f"[INFO] 外层权重 - alpha: {Config.ALPHA}, beta: {Config.BETA}, gamma: {Config.GAMMA}")

if __name__ == "__main__":
    main()
