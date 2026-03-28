# -*- coding: utf-8 -*-
"""
Phase C 训练配置文件
"""

import os
import torch

# =========================================================
# 配置类
# =========================================================

class Config:
    """Phase C 训练配置"""
    # 模型配置
    HIDDEN_DIM = 64  # 隐藏维度
    DROPOUT = 0.2  # Dropout 率
    NUM_LAYERS = 2  # GINE 层数
    
    # 训练配置
    BATCH_SIZE = 32  # 批次大小
    LEARNING_RATE = 0.001  # 学习率
    EPOCHS = 5  # 训练轮数
    LAMBDA_RES = 0.01  # 残差正则化权重
    LAMBDA_REG = 0.001  # 参数正则化权重
    
    # 外层权重（来自 Phase B）
    ALPHA = 0.3521  # 协同权重
    BETA = 0.3067  # 冲突权重
    GAMMA = 0.3412  # 平衡权重
    
    # 数据路径
    GRAPHS_FILE = os.path.join('data', 'phaseC', 'graphs_phaseC.pt')  # 图数据文件
    PAIRS_FILE = os.path.join('data', 'phaseC', 'pairs_phaseC.csv')  # 配对数据文件
    
    # 输出路径
    OUTPUT_DIR = os.path.join('outputs', 'phaseC')  # 输出目录
    CHECKPOINT_DIR = os.path.join(OUTPUT_DIR, 'checkpoints')  # 检查点目录
    LOG_DIR = os.path.join(OUTPUT_DIR, 'logs')  # 日志目录
    
    # 设备配置
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  # 设备
    
    # 其他配置
    SEED = 42  # 随机种子
    EARLY_STOP = 20  # 早停轮数
    
    @classmethod
    def print_config(cls):
        """
        打印配置信息
        """
        print("Phase C 训练配置:")
        print(f"  模型配置:")
        print(f"    隐藏维度: {cls.HIDDEN_DIM}")
        print(f"    Dropout 率: {cls.DROPOUT}")
        print(f"    GINE 层数: {cls.NUM_LAYERS}")
        print(f"  训练配置:")
        print(f"    批次大小: {cls.BATCH_SIZE}")
        print(f"    学习率: {cls.LEARNING_RATE}")
        print(f"    训练轮数: {cls.EPOCHS}")
        print(f"    残差正则化权重: {cls.LAMBDA_RES}")
        print(f"    参数正则化权重: {cls.LAMBDA_REG}")
        print(f"  外层权重:")
        print(f"    Alpha: {cls.ALPHA}")
        print(f"    Beta: {cls.BETA}")
        print(f"    Gamma: {cls.GAMMA}")
        print(f"  数据路径:")
        print(f"    图数据文件: {cls.GRAPHS_FILE}")
        print(f"    配对数据文件: {cls.PAIRS_FILE}")
        print(f"  输出路径:")
        print(f"    输出目录: {cls.OUTPUT_DIR}")
        print(f"    检查点目录: {cls.CHECKPOINT_DIR}")
        print(f"    日志目录: {cls.LOG_DIR}")
        print(f"  设备配置:")
        print(f"    设备: {cls.DEVICE}")
        print(f"  其他配置:")
        print(f"    随机种子: {cls.SEED}")
        print(f"    早停轮数: {cls.EARLY_STOP}")

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    Config.print_config()

if __name__ == "__main__":
    main()
