# -*- coding: utf-8 -*-
"""
Phase C 训练结果可视化脚本

功能：
1. 绘制训练曲线（loss, accuracy, margin）
2. 对比训练集和验证集指标
3. 生成分析报告
"""

import os
import sys
import json
import csv
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_curves(log_dir):
    """加载训练曲线数据"""
    curves_file = os.path.join(log_dir, 'train_curves.json')
    with open(curves_file, 'r', encoding='utf-8') as f:
        curves = json.load(f)
    return curves

def load_logs(log_dir):
    """加载训练日志数据"""
    log_file = os.path.join(log_dir, 'train_log.csv')
    logs = []
    with open(log_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            logs.append(row)
    return logs

def plot_training_curves(curves, output_dir):
    """绘制训练曲线"""
    epochs = range(1, len(curves['train_loss']) + 1)
    
    # 创建子图
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Phase C 训练曲线', fontsize=16, fontweight='bold')
    
    # 1. Loss 曲线
    ax1 = axes[0, 0]
    ax1.plot(epochs, curves['train_loss'], 'b-', label='训练 Loss', linewidth=2)
    ax1.plot(epochs, curves['valid_loss'], 'r-', label='验证 Loss', linewidth=2)
    ax1.axhline(y=0.693, color='g', linestyle='--', label='随机猜测 (0.693)', alpha=0.7)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Loss 曲线')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Accuracy 曲线
    ax2 = axes[0, 1]
    ax2.plot(epochs, curves['train_accuracy'], 'b-', label='训练 Accuracy', linewidth=2)
    ax2.plot(epochs, curves['valid_accuracy'], 'r-', label='验证 Accuracy', linewidth=2)
    ax2.axhline(y=0.5, color='g', linestyle='--', label='随机猜测 (0.5)', alpha=0.7)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy')
    ax2.set_title('Accuracy 曲线')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. Margin 曲线
    ax3 = axes[1, 0]
    ax3.plot(epochs, curves['train_margin'], 'b-', label='训练 Margin', linewidth=2)
    ax3.plot(epochs, curves['valid_margin'], 'r-', label='验证 Margin', linewidth=2)
    ax3.axhline(y=0, color='g', linestyle='--', label='零边界', alpha=0.7)
    ax3.set_xlabel('Epoch')
    ax3.set_ylabel('Margin')
    ax3.set_title('Margin 曲线')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 综合对比（最后一轮）
    ax4 = axes[1, 1]
    metrics = ['Loss', 'Accuracy', 'Margin']
    train_values = [
        curves['train_loss'][-1],
        curves['train_accuracy'][-1],
        curves['train_margin'][-1]
    ]
    valid_values = [
        curves['valid_loss'][-1],
        curves['valid_accuracy'][-1],
        curves['valid_margin'][-1]
    ]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = ax4.bar(x - width/2, train_values, width, label='训练集', color='blue', alpha=0.7)
    bars2 = ax4.bar(x + width/2, valid_values, width, label='验证集', color='red', alpha=0.7)
    
    ax4.set_ylabel('数值')
    ax4.set_title('最终轮次指标对比')
    ax4.set_xticks(x)
    ax4.set_xticklabels(metrics)
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 在柱状图上添加数值标签
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax4.annotate(f'{height:.4f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    # 保存图片
    output_path = os.path.join(output_dir, 'training_curves.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[INFO] 训练曲线已保存到: {output_path}")
    
    plt.show()

def analyze_training_status(curves):
    """分析训练状态"""
    print("\n" + "="*60)
    print("训练状态分析报告")
    print("="*60)
    
    # 检查 Loss
    final_train_loss = curves['train_loss'][-1]
    final_valid_loss = curves['valid_loss'][-1]
    
    print(f"\n1. Loss 分析:")
    print(f"   最终训练 Loss: {final_train_loss:.6f}")
    print(f"   最终验证 Loss: {final_valid_loss:.6f}")
    
    if abs(final_train_loss - 0.693147) < 0.0001:
        print("   [WARNING] Loss 卡在 0.693 附近，模型可能没有正常学习")
        print("   可能原因:")
        print("   - 正负样本 y_base 相同（已修复）")
        print("   - 梯度消失或梯度爆炸")
        print("   - 学习率过小或过大")
        print("   - 数据对构造有问题")
    elif final_train_loss > 0.5:
        print("   [WARNING] Loss 较高，模型学习不充分")
    else:
        print("   [OK] Loss 正常下降")
    
    # 检查 Accuracy
    final_train_acc = curves['train_accuracy'][-1]
    final_valid_acc = curves['valid_accuracy'][-1]
    
    print(f"\n2. Accuracy 分析:")
    print(f"   最终训练 Accuracy: {final_train_acc:.4f}")
    print(f"   最终验证 Accuracy: {final_valid_acc:.4f}")
    
    if final_train_acc < 0.1:
        print("   [WARNING] 训练 Accuracy 极低，模型完全没有学到东西")
    elif final_train_acc < 0.5:
        print("   [WARNING] 训练 Accuracy 低于随机猜测，可能存在严重问题")
    elif final_train_acc > 0.9 and final_valid_acc < 0.6:
        print("   [WARNING] 训练 Accuracy 很高但验证 Accuracy 很低，可能过拟合")
    elif final_valid_acc > 0.8:
        print("   [OK] 验证 Accuracy 良好")
    
    # 检查 Margin
    final_train_margin = curves['train_margin'][-1]
    final_valid_margin = curves['valid_margin'][-1]
    
    print(f"\n3. Margin 分析:")
    print(f"   最终训练 Margin: {final_train_margin:.6f}")
    print(f"   最终验证 Margin: {final_valid_margin:.6f}")
    
    if final_train_margin <= 0:
        print("   [WARNING] Margin 非正，模型无法区分正负样本")
    elif final_train_margin < 0.5:
        print("   [WARNING] Margin 较小，区分度不够")
    else:
        print("   [OK] Margin 良好")
    
    # 检查是否早停
    n_epochs = len(curves['train_loss'])
    print(f"\n4. 训练轮次: {n_epochs}")
    
    if n_epochs < 100:
        print("   [WARNING] 训练提前结束（早停）")
    
    print("\n" + "="*60)

def main():
    """主函数"""
    print("Phase C 训练结果可视化")
    
    # 设置路径
    log_dir = os.path.join('outputs', 'phaseC', 'logs')
    
    if not os.path.exists(log_dir):
        print(f"[ERROR] 日志目录不存在: {log_dir}")
        return
    
    # 加载数据
    print("[INFO] 加载训练曲线数据...")
    try:
        curves = load_curves(log_dir)
    except FileNotFoundError:
        print(f"[ERROR] 找不到训练曲线文件: {os.path.join(log_dir, 'train_curves.json')}")
        return
    
    # 分析训练状态
    analyze_training_status(curves)
    
    # 绘制训练曲线
    print("[INFO] 绘制训练曲线...")
    plot_training_curves(curves, log_dir)
    
    print("\n[INFO] 可视化完成！")

if __name__ == "__main__":
    main()
