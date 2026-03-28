# -*- coding: utf-8 -*-
"""
测试模型是否能够正确计算 sqe_c
"""

import os
import sys
import torch
from phaseC_dataset import PhaseCGraphStore
from model_phaseC_residual import ResidualGNNv1

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(_script_dir)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 配置参数
class Config:
    """配置类"""
    # 数据路径
    GRAPHS_FILE = os.path.join(_project_root, 'data', 'phaseC', 'graphs_phaseC.pt')
    
    # 设备配置
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 主函数
def main():
    """主函数"""
    print("测试模型是否能够正确计算 sqe_c...")
    
    # 加载图数据
    print("[INFO] 加载图数据...")
    graph_store = PhaseCGraphStore(Config.GRAPHS_FILE)
    
    # 获取所有 recipe_id
    recipe_ids = graph_store.get_all_recipe_ids()
    print(f"[INFO] 共有 {len(recipe_ids)} 个 recipe")
    
    # 选择一个 recipe_id 进行测试
    test_recipe_id = recipe_ids[0]
    print(f"[INFO] 测试 recipe_id: {test_recipe_id}")
    
    # 获取图数据
    graph_data = graph_store.get_graph(test_recipe_id)
    
    # 移动到设备
    graph_data = graph_data.to(Config.DEVICE)
    
    # 初始化模型
    print("[INFO] 初始化模型...")
    node_in_dim = graph_data.x.size(1)
    graph_in_dim = graph_data.z_graph.size(1)
    
    model = ResidualGNNv1(
        node_in_dim=node_in_dim,
        graph_in_dim=graph_in_dim
    ).to(Config.DEVICE)
    
    # 前向传播
    print("[INFO] 前向传播...")
    with torch.no_grad():
        output = model(graph_data)
    
    # 提取结果
    syn_B = graph_data.y_base[:, 0].item()
    conf_B = graph_data.y_base[:, 1].item()
    bal_B = graph_data.y_base[:, 2].item()
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
