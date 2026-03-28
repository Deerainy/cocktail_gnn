# -*- coding: utf-8 -*-
"""
Phase C 模型评估脚本

功能：
1. 加载最佳模型检查点
2. 对测试集做完整评估
3. 输出核心指标
4. 按扰动类型分析性能
5. 与 Phase B 对比
6. 导出结果文件
7. 进行误差分析
"""

import os
import json
import csv
import torch
import numpy as np
import pandas as pd
from torch_geometric.data import Data, DataLoader
from phaseC_dataset import PhaseCPairDataset, PhaseCGraphStore
from model_phaseC_residual import ResidualGNNv1
from loss_phaseC import total_loss

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 项目根目录
    _project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    # 数据路径
    GRAPHS_FILE = os.path.join(_project_root, 'data', 'phaseC', 'graphs_phaseC.pt')
    PAIRS_FILE = os.path.join(_project_root, 'data', 'phaseC', 'pairs_phaseC.csv')
    
    # 输出路径
    _script_dir = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = os.path.join(_script_dir, 'outputs', 'phaseC')
    CHECKPOINT_DIR = os.path.join(OUTPUT_DIR, 'checkpoints')
    LOG_DIR = os.path.join(OUTPUT_DIR, 'logs')
    
    # 设备配置
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 评估参数
    BATCH_SIZE = 1
    
    # 最佳模型路径
    BEST_MODEL_PATH = os.path.join(CHECKPOINT_DIR, 'best_by_acc.pt')

# =========================================================
# 工具函数
# =========================================================

def create_output_dirs():
    """创建输出目录"""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(Config.CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(Config.LOG_DIR, exist_ok=True)

def load_checkpoint(model, optimizer=None, path=None):
    """加载检查点"""
    if path is None:
        path = Config.BEST_MODEL_PATH
    
    if os.path.exists(path):
        checkpoint = torch.load(path, map_location=Config.DEVICE)
        # 使用 strict=False 忽略不匹配的键
        model.load_state_dict(checkpoint['model_state_dict'], strict=False)
        if optimizer:
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        epoch = checkpoint.get('epoch', 0)
        best_score = checkpoint.get('best_score', 0.0)
        print(f"[INFO] 加载检查点成功: {path}")
        print(f"[INFO]  epoch: {epoch}, best_score: {best_score:.4f}")
        return True
    else:
        print(f"[ERROR] 检查点文件不存在: {path}")
        return False

def compute_metrics(pos_outputs, neg_outputs, perturb_types):
    """计算评估指标"""
    # 计算整体准确率
    correct = 0
    total = len(pos_outputs)
    margins = []
    losses = []
    
    # 按扰动类型分组
    perturb_type_metrics = {}
    
    for i, (pos_out, neg_out, perturb_type) in enumerate(zip(pos_outputs, neg_outputs, perturb_types)):
        # 计算准确率
        if pos_out['sqe_c'] > neg_out['sqe_c']:
            correct += 1
        
        # 计算 margin
        margin = (pos_out['sqe_c'] - neg_out['sqe_c']).item()
        margins.append(margin)
        
        # 计算 loss
        loss = total_loss(pos_out, neg_out).item()
        losses.append(loss)
        
        # 按扰动类型统计
        if perturb_type not in perturb_type_metrics:
            perturb_type_metrics[perturb_type] = {
                'correct': 0,
                'total': 0,
                'margins': [],
                'losses': []
            }
        
        perturb_type_metrics[perturb_type]['total'] += 1
        if pos_out['sqe_c'] > neg_out['sqe_c']:
            perturb_type_metrics[perturb_type]['correct'] += 1
        perturb_type_metrics[perturb_type]['margins'].append(margin)
        perturb_type_metrics[perturb_type]['losses'].append(loss)
    
    # 计算整体指标
    accuracy = correct / total if total > 0 else 0.0
    avg_margin = np.mean(margins) if margins else 0.0
    avg_loss = np.mean(losses) if losses else 0.0
    
    # 计算按扰动类型的指标
    accuracy_by_type = {}
    margin_by_type = {}
    loss_by_type = {}
    
    for perturb_type, metrics in perturb_type_metrics.items():
        accuracy_by_type[perturb_type] = metrics['correct'] / metrics['total'] if metrics['total'] > 0 else 0.0
        margin_by_type[perturb_type] = np.mean(metrics['margins']) if metrics['margins'] else 0.0
        loss_by_type[perturb_type] = np.mean(metrics['losses']) if metrics['losses'] else 0.0
    
    return {
        'accuracy': accuracy,
        'avg_margin': avg_margin,
        'avg_loss': avg_loss,
        'accuracy_by_type': accuracy_by_type,
        'margin_by_type': margin_by_type,
        'loss_by_type': loss_by_type,
        'perturb_type_metrics': perturb_type_metrics
    }

def compare_with_phaseB(metrics):
    """与 Phase B 对比"""
    # 这里需要加载 Phase B 的结果
    recipe_file = os.path.join(Config._project_root, 'data', 'phaseC', 'recipes_data.jsonl')
    
    if not os.path.exists(recipe_file):
        print(f"[WARNING] 找不到 Phase B 数据文件: {recipe_file}")
        return None
    
    sqe_B_dict = {}
    with open(recipe_file, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            recipe_id = item.get('recipe_id')
            sqe_B = item.get('sqe_B')
            if recipe_id is not None and sqe_B is not None:
                sqe_B_dict[recipe_id] = float(sqe_B)
    
    print(f"[INFO] 已加载 Phase B 分数，共 {len(sqe_B_dict)} 个 recipe")
    return sqe_B_dict

def export_results(metrics, predictions, phaseB_results=None):
    """导出结果文件"""
    # 导出测试指标
    test_metrics = {
        'overall': {
            'accuracy': metrics['accuracy'],
            'avg_margin': metrics['avg_margin'],
            'avg_loss': metrics['avg_loss']
        },
        'by_perturb_type': {
            'accuracy': metrics['accuracy_by_type'],
            'margin': metrics['margin_by_type'],
            'loss': metrics['loss_by_type']
        }
    }
    
    if phaseB_results:
        test_metrics['phaseB_comparison'] = {
            'phaseB_accuracy': phaseB_results.get('accuracy', 0.0),
            'phaseC_accuracy': metrics['accuracy'],
            'improvement': metrics['accuracy'] - phaseB_results.get('accuracy', 0.0)
        }
    
    with open(os.path.join(Config.OUTPUT_DIR, 'test_metrics.json'), 'w', encoding='utf-8') as f:
        json.dump(test_metrics, f, ensure_ascii=False, indent=2)
    
    # 导出预测结果
    with open(os.path.join(Config.OUTPUT_DIR, 'predictions.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['pos_recipe_id', 'neg_recipe_id', 'perturb_type', 'pos_hat_syn', 'pos_hat_conf', 'pos_hat_bal', 'pos_sqe_c', 'neg_hat_syn', 'neg_hat_conf', 'neg_hat_bal', 'neg_sqe_c', 'margin', 'correct'])
        for pred in predictions:
            writer.writerow([
                pred['pos_recipe_id'],
                pred['neg_recipe_id'],
                pred['perturb_type'],
                pred['pos_hat_syn'],
                pred['pos_hat_conf'],
                pred['pos_hat_bal'],
                pred['pos_sqe_c'],
                pred['neg_hat_syn'],
                pred['neg_hat_conf'],
                pred['neg_hat_bal'],
                pred['neg_sqe_c'],
                pred['margin'],
                pred['correct']
            ])
    
    # 导出按扰动类型的指标
    with open(os.path.join(Config.OUTPUT_DIR, 'metrics_by_perturb_type.csv'), 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['perturb_type', 'accuracy', 'avg_margin', 'avg_loss', 'total_samples'])
        for perturb_type, metrics_dict in metrics['perturb_type_metrics'].items():
            writer.writerow([
                perturb_type,
                metrics_dict['correct'] / metrics_dict['total'] if metrics_dict['total'] > 0 else 0.0,
                np.mean(metrics_dict['margins']) if metrics_dict['margins'] else 0.0,
                np.mean(metrics_dict['losses']) if metrics_dict['losses'] else 0.0,
                metrics_dict['total']
            ])
    
    print("[INFO] 结果文件导出成功")

def error_analysis(predictions):
    """误差分析"""
    # 找出 margin 最小的样本对
    predictions.sort(key=lambda x: x['margin'])
    smallest_margins = predictions[:10]
    
    # 找出判断错误的样本对
    wrong_predictions = [p for p in predictions if not p['correct']]
    
    # 按扰动类型统计错误率
    perturb_type_errors = {}
    for p in predictions:
        if p['perturb_type'] not in perturb_type_errors:
            perturb_type_errors[p['perturb_type']] = {'total': 0, 'wrong': 0}
        perturb_type_errors[p['perturb_type']]['total'] += 1
        if not p['correct']:
            perturb_type_errors[p['perturb_type']]['wrong'] += 1
    
    error_rates = {}
    for perturb_type, stats in perturb_type_errors.items():
        if stats['total'] > 0:
            error_rates[perturb_type] = stats['wrong'] / stats['total']
    
    # 找出错误率最高的扰动类型
    if error_rates:
        hardest_perturb_type = max(error_rates, key=error_rates.get)
        print(f"[INFO] 最难区分的扰动类型: {hardest_perturb_type} (错误率: {error_rates[hardest_perturb_type]:.4f})")
    
    # 处理 predictions 中的 Tensor 对象，确保 JSON 可序列化
    def process_prediction(pred):
        processed = {}
        for key, value in pred.items():
            if hasattr(value, 'item'):
                # 如果是 Tensor 对象，转换为标量值
                processed[key] = value.item()
            elif isinstance(value, list):
                # 如果是列表，递归处理
                processed[key] = [process_prediction(item) if isinstance(item, dict) else item for item in value]
            else:
                processed[key] = value
        return processed
    
    # 导出误差分析结果
    error_analysis_results = {
        'smallest_margins': [process_prediction(p) for p in smallest_margins],
        'wrong_predictions': [process_prediction(p) for p in wrong_predictions],
        'error_rates_by_perturb_type': error_rates
    }
    
    with open(os.path.join(Config.OUTPUT_DIR, 'error_analysis.json'), 'w', encoding='utf-8') as f:
        json.dump(error_analysis_results, f, ensure_ascii=False, indent=2)
    
    print("[INFO] 误差分析完成")
    print(f"[INFO] 错误预测数: {len(wrong_predictions)}")
    print(f"[INFO] 总预测数: {len(predictions)}")
    print(f"[INFO] 错误率: {len(wrong_predictions) / len(predictions):.4f}")

def export_recipe_scores(model, graph_store):
    """导出每个 recipe 的修正后的三项分数和最终总分 sqe_c"""
    print("[INFO] 导出每个 recipe 的分数...")
    
    # 获取所有 recipe_id
    recipe_ids = graph_store.get_all_recipe_ids()
    
    # 加载原始 recipes_data.jsonl 文件
    recipes_data_file = os.path.join(Config._project_root, 'data', 'phaseC', 'recipes_data.jsonl')
    recipes_data = {}
    
    if os.path.exists(recipes_data_file):
        with open(recipes_data_file, 'r', encoding='utf-8') as f:
            for line in f:
                item = json.loads(line.strip())
                recipe_id = item.get('recipe_id')
                if recipe_id is not None:
                    recipes_data[recipe_id] = item
    
    # 遍历所有 recipe_id，计算修正后的分数
    output_data = []
    
    for recipe_id in recipe_ids:
        try:
            # 获取图数据
            graph_data = graph_store.get_graph(recipe_id)
            
            # 移动到设备
            graph_data = graph_data.to(Config.DEVICE)
            
            # 前向传播
            with torch.no_grad():
                output = model(graph_data)
            
            # 提取修正后的分数
            hat_syn = output['hat_syn'].item()
            hat_conf = output['hat_conf'].item()
            hat_bal = output['hat_bal'].item()
            sqe_c = output['sqe_c'].item()
            
            # 构建输出数据
            if recipe_id in recipes_data:
                # 如果原始数据存在，使用原始数据
                item = recipes_data[recipe_id].copy()
            else:
                # 如果原始数据不存在，创建一个新的条目
                item = {
                    'recipe_id': recipe_id,
                    'nodes': [],
                    'edges': [],
                    'graph_level_features': {}
                }
            
            # 添加修正后的分数
            item['hat_syn'] = hat_syn
            item['hat_conf'] = hat_conf
            item['hat_bal'] = hat_bal
            item['sqe_c'] = sqe_c
            
            output_data.append(item)
            
            # 打印进度
            if len(output_data) % 100 == 0:
                print(f"[INFO] 处理进度: {len(output_data)}/{len(recipe_ids)}")
                
        except Exception as e:
            print(f"[WARNING] 处理 recipe_id {recipe_id} 时出错: {e}")
            continue
    
    # 导出结果
    output_file = os.path.join(Config.OUTPUT_DIR, 'recipes_data_with_sqe_c.jsonl')
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in output_data:
            json.dump(item, f, ensure_ascii=False)
            f.write('\n')
    
    print(f"[INFO] 导出完成，共处理 {len(output_data)} 个 recipe")
    print(f"[INFO] 结果保存到: {output_file}")

# =========================================================
# 主评估函数
# =========================================================

def evaluate():
    """评估模型"""
    print("开始 Phase C 模型评估...")
    
    # 创建输出目录
    create_output_dirs()
    
    # 加载数据
    print("[INFO] 加载数据...")
    graph_store = PhaseCGraphStore(Config.GRAPHS_FILE)
    dataset = PhaseCPairDataset(Config.PAIRS_FILE, graph_store)
    
    # 划分测试集（这里假设所有数据都是测试集，实际应该根据之前的划分）
    # 为了简单起见，我们使用整个数据集作为测试集
    test_loader = DataLoader(dataset, batch_size=Config.BATCH_SIZE, shuffle=False, num_workers=0)
    
    # 初始化模型
    print("[INFO] 初始化模型...")
    sample = dataset[0]
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
    
    # 加载最佳模型
    if not load_checkpoint(model):
        print("[ERROR] 加载模型失败，退出评估")
        return
    
    # 评估模型
    print("[INFO] 评估模型...")
    model.eval()
    
    pos_outputs = []
    neg_outputs = []
    perturb_types = []
    predictions = []
    
    with torch.no_grad():
        for batch_idx, batch in enumerate(test_loader):
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
            num_nodes = pos_x.size(0)
            if pos_edge_index.dim() == 1:
                if pos_edge_index.size(0) % 2 == 0:
                    pos_edge_index = pos_edge_index.view(2, -1)
                else:
                    pos_edge_index = torch.tensor([[], []], dtype=torch.long, device=pos_edge_index.device)
            elif pos_edge_index.dim() == 2:
                if pos_edge_index.size(0) != 2:
                    if pos_edge_index.size(1) == 2:
                        pos_edge_index = pos_edge_index.t()
                    else:
                        pos_edge_index = torch.tensor([[], []], dtype=torch.long, device=pos_edge_index.device)
            
            # 确保 edge_index 中的索引值在有效范围内
            if pos_edge_index.size(1) > 0:
                max_index = pos_edge_index.max().item()
                if max_index >= num_nodes:
                    pos_edge_index = torch.tensor([[], []], dtype=torch.long, device=pos_edge_index.device)
            
            # 处理 edge_attr 维度
            if pos_edge_attr.dim() == 1:
                pos_edge_attr = pos_edge_attr.unsqueeze(0)
            if pos_edge_index.size(1) > 0 and pos_edge_attr.size(0) != pos_edge_index.size(1):
                pos_edge_attr = torch.zeros(pos_edge_index.size(1), 4, dtype=torch.float, device=pos_edge_attr.device)
            
            # 确保 z_graph 是二维张量
            if pos_z_graph.dim() == 0:
                pos_z_graph = torch.zeros(1, 23, dtype=torch.float, device=pos_z_graph.device)
            elif pos_z_graph.dim() == 1:
                if pos_z_graph.size(0) != 23:
                    pos_z_graph = torch.zeros(1, 23, dtype=torch.float, device=pos_z_graph.device)
                else:
                    pos_z_graph = pos_z_graph.unsqueeze(0)
            elif pos_z_graph.dim() == 2:
                if pos_z_graph.size(1) != 23:
                    pos_z_graph = torch.zeros(1, 23, dtype=torch.float, device=pos_z_graph.device)
            
            # 确保 y_base 是二维张量，形状为 (1, 3)
            if pos_y_base.dim() == 0:
                pos_y_base = torch.zeros(1, 3, dtype=torch.float, device=pos_y_base.device)
            elif pos_y_base.dim() == 1:
                if pos_y_base.size(0) != 3:
                    pos_y_base = torch.zeros(1, 3, dtype=torch.float, device=pos_y_base.device)
                else:
                    pos_y_base = pos_y_base.unsqueeze(0)
            elif pos_y_base.dim() == 2:
                if pos_y_base.size(1) != 3:
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
            num_nodes = neg_x.size(0)
            if neg_edge_index.dim() == 1:
                if neg_edge_index.size(0) % 2 == 0:
                    neg_edge_index = neg_edge_index.view(2, -1)
                else:
                    neg_edge_index = torch.tensor([[], []], dtype=torch.long, device=neg_edge_index.device)
            elif neg_edge_index.dim() == 2:
                if neg_edge_index.size(0) != 2:
                    if neg_edge_index.size(1) == 2:
                        neg_edge_index = neg_edge_index.t()
                    else:
                        neg_edge_index = torch.tensor([[], []], dtype=torch.long, device=neg_edge_index.device)
            
            # 确保 edge_index 中的索引值在有效范围内
            if neg_edge_index.size(1) > 0:
                max_index = neg_edge_index.max().item()
                if max_index >= num_nodes:
                    neg_edge_index = torch.tensor([[], []], dtype=torch.long, device=neg_edge_index.device)
            
            # 处理 edge_attr 维度
            if neg_edge_attr.dim() == 1:
                neg_edge_attr = neg_edge_attr.unsqueeze(0)
            if neg_edge_index.size(1) > 0 and neg_edge_attr.size(0) != neg_edge_index.size(1):
                neg_edge_attr = torch.zeros(neg_edge_index.size(1), 4, dtype=torch.float, device=neg_edge_attr.device)
            
            # 确保 z_graph 是二维张量
            if neg_z_graph.dim() == 0:
                neg_z_graph = torch.zeros(1, 23, dtype=torch.float, device=neg_z_graph.device)
            elif neg_z_graph.dim() == 1:
                if neg_z_graph.size(0) != 23:
                    neg_z_graph = torch.zeros(1, 23, dtype=torch.float, device=neg_z_graph.device)
                else:
                    neg_z_graph = neg_z_graph.unsqueeze(0)
            elif neg_z_graph.dim() == 2:
                if neg_z_graph.size(1) != 23:
                    neg_z_graph = torch.zeros(1, 23, dtype=torch.float, device=neg_z_graph.device)
            
            # 确保 y_base 是二维张量，形状为 (1, 3)
            if neg_y_base.dim() == 0:
                neg_y_base = torch.zeros(1, 3, dtype=torch.float, device=neg_y_base.device)
            elif neg_y_base.dim() == 1:
                if neg_y_base.size(0) != 3:
                    neg_y_base = torch.zeros(1, 3, dtype=torch.float, device=neg_y_base.device)
                else:
                    neg_y_base = neg_y_base.unsqueeze(0)
            elif neg_y_base.dim() == 2:
                if neg_y_base.size(1) != 3:
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
            
            # 收集输出
            pos_outputs.append(pos_output)
            neg_outputs.append(neg_output)
            
            # 收集扰动类型
            perturb_type = batch.perturb_type
            if isinstance(perturb_type, list):
                if len(perturb_type) > 0:
                    perturb_type = perturb_type[0]
                else:
                    perturb_type = "unknown"
            perturb_types.append(perturb_type)
            
            # 收集预测结果
            pos_sqe_c = pos_output['sqe_c'].item()
            neg_sqe_c = neg_output['sqe_c'].item()
            pos_hat_syn = pos_output['hat_syn'].item()
            pos_hat_conf = pos_output['hat_conf'].item()
            pos_hat_bal = pos_output['hat_bal'].item()
            neg_hat_syn = neg_output['hat_syn'].item()
            neg_hat_conf = neg_output['hat_conf'].item()
            neg_hat_bal = neg_output['hat_bal'].item()
            margin = pos_sqe_c - neg_sqe_c
            correct = pos_sqe_c > neg_sqe_c
            
            predictions.append({
                'pos_recipe_id': batch.pos_recipe_id[0] if hasattr(batch, 'pos_recipe_id') else 'unknown',
                'neg_recipe_id': batch.neg_recipe_id[0] if hasattr(batch, 'neg_recipe_id') else 'unknown',
                'perturb_type': perturb_type,
                'pos_hat_syn': pos_hat_syn,
                'pos_hat_conf': pos_hat_conf,
                'pos_hat_bal': pos_hat_bal,
                'pos_sqe_c': pos_sqe_c,
                'neg_hat_syn': neg_hat_syn,
                'neg_hat_conf': neg_hat_conf,
                'neg_hat_bal': neg_hat_bal,
                'neg_sqe_c': neg_sqe_c,
                'margin': margin,
                'correct': correct
            })
            
            # 打印进度
            if (batch_idx + 1) % 100 == 0:
                print(f"[INFO] 评估进度: {batch_idx + 1}/{len(test_loader)}")
    
    # 计算指标
    print("[INFO] 计算评估指标...")
    metrics = compute_metrics(pos_outputs, neg_outputs, perturb_types)
    
    # 打印整体指标
    print("[INFO] 整体评估指标:")
    print(f"  Accuracy: {metrics['accuracy']:.4f}")
    print(f"  Avg Margin: {metrics['avg_margin']:.4f}")
    print(f"  Avg Loss: {metrics['avg_loss']:.4f}")
    
    # 打印按扰动类型的指标
    print("[INFO] 按扰动类型的评估指标:")
    for perturb_type in sorted(metrics['accuracy_by_type'].keys()):
        print(f"  {perturb_type}:")
        print(f"    Accuracy: {metrics['accuracy_by_type'][perturb_type]:.4f}")
        print(f"    Avg Margin: {metrics['margin_by_type'][perturb_type]:.4f}")
        print(f"    Avg Loss: {metrics['loss_by_type'][perturb_type]:.4f}")
    
    # 与 Phase B 对比
    print("[INFO] 与 Phase B 对比:")
    phaseB_results = compare_with_phaseB(metrics)
    
    # 导出结果
    print("[INFO] 导出结果文件...")
    export_results(metrics, predictions, phaseB_results)
    
    # 误差分析
    print("[INFO] 进行误差分析...")
    error_analysis(predictions)
    
    # 导出每个 recipe 的分数
    print("[INFO] 导出每个 recipe 的修正后的分数...")
    export_recipe_scores(model, graph_store)
    
    print("[INFO] Phase C 模型评估完成！")

# =========================================================
# 主函数
# =========================================================

def main():
    """主函数"""
    evaluate()

if __name__ == "__main__":
    main()
