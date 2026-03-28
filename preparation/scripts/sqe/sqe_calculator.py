# -*- coding: utf-8 -*-
"""
SQE 计算器封装类

功能：
1. 封装 SQE 计算逻辑，支持直接从配方原料计算 SQE 分数
2. 整合 phaseA 和 phaseC 的计算方法
3. 提供简洁的接口，便于后续使用
"""

import os
import sys
import pandas as pd
import numpy as np
import torch
from typing import List, Dict, Optional, Any

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_script_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

class SQECalculator:
    """
    SQE 计算器类
    """
    
    def __init__(self, use_phaseC: bool = False):
        """
        初始化 SQE 计算器
        
        参数:
        use_phaseC: 是否使用 phaseC 的模型进行优化
        """
        self.use_phaseC = use_phaseC
        self.phaseC_model = None
        self.phaseC_config = None
        self.graph_store = None
        
        # 加载 phaseB 最优参数
        self.optimal_params = self._load_optimal_params()
        
        # 加载权重
        self.synergy_weight = self.optimal_params['sqe']['lambda_synergy']  # 协同权重
        self.conflict_weight = self.optimal_params['sqe']['lambda_conflict']  # 冲突权重
        self.balance_weight = self.optimal_params['sqe']['lambda_balance']  # 平衡权重
        
        # 加载 baseline 统计信息
        self.baseline_stats = self._load_baseline_stats()
        
        # 如果使用 phaseC，加载模型和图存储
        if self.use_phaseC:
            self._load_phaseC_model()
            self._load_graph_store()
    
    def _load_optimal_params(self) -> Dict:
        """
        加载 phaseB 的最优参数
        """
        params_file = os.path.join(_project_root, "data", "phaseC", "optimal_params.json")
        if not os.path.exists(params_file):
            # 如果文件不存在，使用默认值
            return {
                "synergy": {
                    "alpha1": 0.45,
                    "alpha2": 0.45,
                    "alpha3": 0.1
                },
                "conflict": {
                    "eta1": 0.3033,
                    "eta2": 0.2315,
                    "eta3": 0.3128,
                    "eta4": 0.1523
                },
                "balance": {
                    "mu1": 0.6521,
                    "mu2": 0.3479
                },
                "sqe": {
                    "lambda_synergy": 0.3521,
                    "lambda_conflict": 0.3067,
                    "lambda_balance": 0.3412
                }
            }
        
        with open(params_file, 'r', encoding='utf-8') as f:
            import json
            params = json.load(f)
        
        return params
    
    def _load_baseline_stats(self) -> Dict:
        """
        加载 baseline 统计信息
        """
        baseline_file = os.path.join(_project_root, "data", "phaseA_baseline_v2.csv")
        if not os.path.exists(baseline_file):
            # 如果文件不存在，使用默认值
            return {
                'synergy_min': 0.0,
                'synergy_max': 1.0,
                'conflict_min': 0.0,
                'conflict_max': 1.0,
                'balance_min': 0.0,
                'balance_max': 1.0
            }
        
        df = pd.read_csv(baseline_file)
        return {
            'synergy_min': df['synergy_score'].min(),
            'synergy_max': df['synergy_score'].max(),
            'conflict_min': df['conflict_score'].min(),
            'conflict_max': df['conflict_score'].max(),
            'balance_min': df['final_balance_score'].min(),
            'balance_max': df['final_balance_score'].max()
        }
    
    def _load_phaseC_model(self):
        """
        加载 phaseC 模型
        """
        try:
            from scripts.sqe.phase_C.model_phaseC_residual import ResidualGNNv1
            from scripts.sqe.phase_C.build_phaseC_graph_data import build_graph_from_recipe
            
            # 创建模型
            node_in_dim = 22  # 节点特征维度
            graph_in_dim = 23  # 图级特征维度
            self.phaseC_model = ResidualGNNv1(node_in_dim, graph_in_dim)
            
            # 尝试不同的模型路径（根据实际找到的模型文件位置）
            model_paths = [
                os.path.join(_project_root, "data", "phaseC", "checkpoints", "best_by_acc.pt"),
                os.path.join(_project_root, "data", "phaseC", "checkpoints", "best_by_margin.pt"),
                os.path.join(_project_root, "data", "phaseC", "checkpoints", "last.pt"),
                os.path.join(_project_root, "scripts", "sqe", "phase_C", "outputs", "phaseC", "checkpoints", "best_by_acc.pt"),
                os.path.join(_project_root, "scripts", "sqe", "phase_C", "out", "phaseC_model.pth")
            ]
            
            model_loaded = False
            for model_path in model_paths:
                if os.path.exists(model_path):
                    # 加载模型，使用 strict=False 忽略不匹配的键
                    checkpoint = torch.load(model_path, map_location=torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
                    self.phaseC_model.load_state_dict(checkpoint['model_state_dict'], strict=False)
                    self.phaseC_model.eval()
                    print(f"[INFO] 成功加载 PhaseC 模型: {model_path}")
                    model_loaded = True
                    break
            
            if not model_loaded:
                print("[WARNING] PhaseC 模型权重文件不存在，将使用 phaseA 计算")
                self.use_phaseC = False
        except Exception as e:
            print(f"[ERROR] 加载 PhaseC 模型失败: {e}")
            self.use_phaseC = False
    
    def _load_graph_store(self):
        """
        加载 PhaseCGraphStore
        """
        try:
            from scripts.sqe.phase_C.phaseC_dataset import PhaseCGraphStore
            
            # 图数据文件路径
            graphs_file = os.path.join(_project_root, "data", "phaseC", "graphs_phaseC.pt")
            
            if os.path.exists(graphs_file):
                self.graph_store = PhaseCGraphStore(graphs_file)
                print(f"[INFO] 成功加载图存储: {graphs_file}")
                print(f"[INFO] 图存储包含 {len(self.graph_store.get_all_recipe_ids())} 个图样本")
            else:
                print(f"[WARNING] 图数据文件不存在: {graphs_file}")
                print("[WARNING] 将使用实时构建的图数据")
        except Exception as e:
            print(f"[ERROR] 加载图存储失败: {e}")
            self.graph_store = None
    
    def set_weights(self, synergy_weight: float, conflict_weight: float, balance_weight: float):
        """
        设置 SQE 权重
        
        参数:
        synergy_weight: 协同权重
        conflict_weight: 冲突权重
        balance_weight: 平衡权重
        """
        # 验证权重和
        assert abs(synergy_weight + conflict_weight + balance_weight - 1.0) < 1e-6, "权重和必须为 1"
        
        self.synergy_weight = synergy_weight
        self.conflict_weight = conflict_weight
        self.balance_weight = balance_weight
    
    def normalize_score(self, score: float, min_val: float, max_val: float) -> float:
        """
        标准化分数
        
        参数:
        score: 原始分数
        min_val: 最小值
        max_val: 最大值
        
        返回:
        标准化后的分数 (0-1)
        """
        if max_val == min_val:
            return 0.5
        return max(0.0, min(1.0, (score - min_val) / (max_val - min_val)))
    
    def calculate_phaseA_score(self, ingredients: List[Dict]) -> Dict:
        """
        计算 phaseA 的 SQE 分数
        
        参数:
        ingredients: 原料列表，每个原料包含以下字段:
            - ingredient_id: 原料 ID
            - amount: 原料用量
            - unit: 单位
            - role: 角色
            - line_no: 行号
            - raw_text: 原始文本
        
        返回:
        包含各维度分数的字典
        """
        try:
            if not ingredients:
                return {
                    "synergy_score": 0.0,
                    "conflict_score": 0.0,
                    "balance_score": 0.0,
                    "synergy_normalized": 0.0,
                    "conflict_normalized": 0.0,
                    "balance_normalized": 0.0,
                    "conflict_good": 1.0,
                    "sqe_total": 0.0
                }
            
            # 导入评分接口函数
            from scripts.sqe.phase_A.sqe_scorer_conflict_v2 import calculate_conflict_score_from_ingredients
            from scripts.sqe.phase_A.sqe_scorer_balance import calculate_balance_score_from_ingredients
            from scripts.sqe.phase_A.sqe_scorer_synergy import score_recipe_from_ingredients, set_synergy_weights
            
            # 设置与 phaseB 最优参数一致的权重
            set_synergy_weights(
                flavor_weight=self.optimal_params['synergy']['alpha1'],
                cooccur_weight=self.optimal_params['synergy']['alpha2'],
                anchor_weight=self.optimal_params['synergy']['alpha3']
            )
            
            # 计算各维度分数
            synergy_result = score_recipe_from_ingredients(ingredients)
            syn_score = synergy_result["synergy_score"]
            
            conflict_result = calculate_conflict_score_from_ingredients(ingredients)
            conf_score = conflict_result["conflict_score"]
            conf_norm = conflict_result["conflict_normalized"]
            
            balance_result = calculate_balance_score_from_ingredients(ingredients)
            bal_score = balance_result["final_balance_score"]
            
            # 标准化分数
            syn_norm = self.normalize_score(
                syn_score, 
                self.baseline_stats['synergy_min'], 
                self.baseline_stats['synergy_max']
            )
            
            bal_norm = self.normalize_score(
                bal_score, 
                self.baseline_stats['balance_min'], 
                self.baseline_stats['balance_max']
            )
            
            # 转换冲突分数为越大越好的形式
            conf_good = 1 - conf_norm
            
            # 计算 SQE 总分
            sqe_total = (
                self.synergy_weight * syn_norm +
                self.conflict_weight * conf_good +
                self.balance_weight * bal_norm
            )
            
            return {
                "synergy_score": syn_score,
                "conflict_score": conf_score,
                "balance_score": bal_score,
                "synergy_normalized": syn_norm,
                "conflict_normalized": conf_norm,
                "balance_normalized": bal_norm,
                "conflict_good": conf_good,
                "sqe_total": sqe_total
            }
        except Exception as e:
            print(f"[ERROR] 计算 phaseA 分数失败: {e}")
            import traceback
            traceback.print_exc()
            # 记录错误但返回默认值
            return {
                "synergy_score": 0.0,
                "conflict_score": 0.0,
                "balance_score": 0.0,
                "synergy_normalized": 0.0,
                "conflict_normalized": 0.0,
                "balance_normalized": 0.0,
                "conflict_good": 1.0,
                "sqe_total": 0.0
            }
    
    def calculate_phaseC_score(self, ingredients: List[Dict], phaseA_score: Dict) -> Dict:
        """
        计算 phaseC 的 SQE 分数（包含结构修正项）
        
        参数:
        ingredients: 原料列表
        phaseA_score: phaseA 的分数结果
        
        返回:
        包含 phaseC 分数的字典
        """
        try:
            if not self.use_phaseC or self.phaseC_model is None:
                return {
                    "sqe_c": phaseA_score["sqe_total"],
                    "hat_syn": phaseA_score["synergy_score"],
                    "hat_conf": phaseA_score["conflict_score"],
                    "hat_bal": phaseA_score["balance_score"],
                    "structure_correction": 0.0
                }
            
            # 尝试从图存储中获取预处理的图数据
            graph_data = None
            if self.graph_store:
                # 尝试从原料列表中提取 recipe_id
                recipe_id = None
                for ing in ingredients:
                    if 'recipe_id' in ing:
                        recipe_id = ing['recipe_id']
                        break
                
                if recipe_id is not None:
                    try:
                        graph_data = self.graph_store.get_graph(recipe_id)
                        print(f"[INFO] 从图存储中获取 recipe {recipe_id} 的图数据")
                    except Exception as e:
                        print(f"[WARNING] 从图存储中获取图数据失败: {e}")
            
            # 如果没有图存储或获取失败，使用实时构建的图数据
            if graph_data is None:
                from scripts.sqe.phase_C.build_phaseC_graph_data import build_graph_from_recipe
                
                # 构建图数据
                graph_data = build_graph_from_recipe(ingredients)
                if graph_data is None:
                    return {
                        "sqe_c": phaseA_score["sqe_total"],
                        "hat_syn": phaseA_score["synergy_score"],
                        "hat_conf": phaseA_score["conflict_score"],
                        "hat_bal": phaseA_score["balance_score"],
                        "structure_correction": 0.0
                    }
                
                # 准备输入数据 - 使用原始分数作为 y_base，与 eval_phaseC.py 一致
                y_base = torch.tensor([
                    phaseA_score["synergy_score"],
                    phaseA_score["conflict_score"],
                    phaseA_score["balance_score"]
                ], dtype=torch.float32)
                
                # 设置图级特征
                if not hasattr(graph_data, 'z_graph'):
                    # 如果没有图级特征，创建默认值
                    graph_data.z_graph = torch.zeros(23, dtype=torch.float32)
                
                # 确保 z_graph 是二维张量，与 eval_phaseC.py 一致
                if graph_data.z_graph.dim() == 1:
                    graph_data.z_graph = graph_data.z_graph.unsqueeze(0)
                
                # 设置基础分数
                graph_data.y_base = y_base
            
            # 模型预测
            with torch.no_grad():
                output = self.phaseC_model(graph_data)
            
            # 提取修正后的分数，与 eval_phaseC.py 一致
            hat_syn = output['hat_syn'].item()
            hat_conf = output['hat_conf'].item()
            hat_bal = output['hat_bal'].item()
            sqe_c = output['sqe_c'].item()
            
            # 计算结构修正项
            structure_correction = sqe_c - phaseA_score["sqe_total"]
            
            return {
                "sqe_c": sqe_c,
                "hat_syn": hat_syn,
                "hat_conf": hat_conf,
                "hat_bal": hat_bal,
                "structure_correction": structure_correction
            }
        except Exception as e:
            print(f"[ERROR] 计算 phaseC 分数失败: {e}")
            import traceback
            traceback.print_exc()
            # 记录错误但返回 phaseA 分数
            return {
                "sqe_c": phaseA_score["sqe_total"],
                "hat_syn": phaseA_score["synergy_score"],
                "hat_conf": phaseA_score["conflict_score"],
                "hat_bal": phaseA_score["balance_score"],
                "structure_correction": 0.0
            }
    
    def calculate_sqe(self, ingredients: List[Dict]) -> Dict:
        """
        计算 SQE 分数
        
        参数:
        ingredients: 原料列表，每个原料包含以下字段:
            - ingredient_id: 原料 ID
            - amount: 原料用量
            - unit: 单位
            - role: 角色
            - line_no: 行号
            - raw_text: 原始文本
        
        返回:
        包含 SQE 分数的字典
        """
        # 计算 phaseA 分数
        phaseA_result = self.calculate_phaseA_score(ingredients)
        
        # 计算 phaseC 分数
        phaseC_result = self.calculate_phaseC_score(ingredients, phaseA_result)
        
        # 合并结果
        result = {
            **phaseA_result,
            **phaseC_result,
            "final_sqe": phaseC_result["sqe_c"] if self.use_phaseC else phaseA_result["sqe_total"],
            "used_model": "phaseC" if self.use_phaseC else "phaseA",
            "optimal_params": self.optimal_params  # 包含最优参数
        }
        
        return result
    
    def calculate_sqe_from_recipe_id(self, recipe_id: int) -> Dict:
        """
        从配方 ID 计算 SQE 分数
        
        参数:
        recipe_id: 配方 ID
        
        返回:
        包含 SQE 分数的字典
        """
        try:
            from src.db import get_engine
            from sqlalchemy import text
            
            engine = get_engine()
            sql = text("""
            SELECT ingredient_id, amount, unit, role, line_no, raw_text
            FROM recipe_ingredient
            WHERE recipe_id = :recipe_id
            ORDER BY line_no
            """)
            
            with engine.begin() as conn:
                result = conn.execute(sql, {"recipe_id": recipe_id})
                ingredients = []
                for row in result:
                    # 处理 decimal 类型和 None 值
                    amount = float(row[1]) if row[1] is not None else 0.0
                    unit = row[2] if row[2] is not None else ""
                    role = row[3] if row[3] is not None else "other"
                    
                    ingredients.append({
                        "ingredient_id": int(row[0]),
                        "amount": amount,
                        "unit": unit,
                        "role": role,
                        "line_no": int(row[4]),
                        "raw_text": row[5] if row[5] is not None else "",
                        "recipe_id": recipe_id  # 添加 recipe_id，用于从图存储中获取数据
                    })
            
            if not ingredients:
                return {
                    "error": f"配方 ID {recipe_id} 不存在或没有原料",
                    "final_sqe": 0.0
                }
            
            return self.calculate_sqe(ingredients)
        except Exception as e:
            print(f"[ERROR] 从配方 ID 计算 SQE 失败: {e}")
            return {
                "error": str(e),
                "final_sqe": 0.0
            }
    
    def recipe_to_graph(self, ingredients: List[Dict]) -> Optional[Any]:
        """
        将新配方转换为图表示
        
        参数:
        ingredients: 原料列表，每个原料包含以下字段:
            - ingredient_id: 原料 ID
            - amount: 原料用量
            - unit: 单位
            - role: 角色
            - line_no: 行号
            - raw_text: 原始文本
        
        返回:
        PyTorch Geometric Data 对象，或 None 如果转换失败
        """
        try:
            from scripts.sqe.phase_C.build_phaseC_graph_data import build_graph_from_recipe
            
            # 构建图数据
            graph_data = build_graph_from_recipe(ingredients)
            
            if graph_data is None:
                print("[ERROR] 构建图数据失败")
                return None
            
            print("[INFO] 成功将配方转换为图表示")
            print(f"[INFO] 节点数: {graph_data.x.size(0)}")
            print(f"[INFO] 边数: {graph_data.edge_index.size(1) // 2}")
            print(f"[INFO] 节点特征维度: {graph_data.x.size(1)}")
            print(f"[INFO] 边特征维度: {graph_data.edge_attr.size(1) if hasattr(graph_data, 'edge_attr') else 0}")
            if hasattr(graph_data, 'z_graph'):
                if graph_data.z_graph.dim() == 1:
                    print(f"[INFO] 图级特征维度: {graph_data.z_graph.size(0)}")
                else:
                    print(f"[INFO] 图级特征维度: {graph_data.z_graph.size(1)}")
            else:
                print("[INFO] 图级特征维度: 0")
            
            return graph_data
        except Exception as e:
            print(f"[ERROR] 配方转换为图表示失败: {e}")
            import traceback
            traceback.print_exc()
            return None

# =========================================================
# 示例用法
# =========================================================
def main():
    """
    示例用法
    """
    print("SQE 计算器示例")
    
    # 示例原料列表 - 手动构建 recipe 1 的原料数据
    # 根据用户提供的数据，recipe 1 的 phaseA_total 为 0.527726，phaseC_pred_score 为 0.768844
    sample_ingredients = [
        {
            "ingredient_id": 1,  # 假设是 Gin
            "amount": 50,
            "unit": "ml",
            "role": "base_spirit",
            "line_no": 1,
            "raw_text": "Gin"
        },
        {
            "ingredient_id": 2,  # 假设是 Dry Vermouth
            "amount": 10,
            "unit": "ml",
            "role": "modifier",
            "line_no": 2,
            "raw_text": "Dry Vermouth"
        },
        {
            "ingredient_id": 3,  # 假设是 Olive
            "amount": 1,
            "unit": "piece",
            "role": "garnish",
            "line_no": 3,
            "raw_text": "Olive"
        }
    ]
    
    # 测试 1: 使用 phaseA 模型
    print("\n=== 测试 1: 使用 phaseA 模型 ===")
    calculator_phaseA = SQECalculator(use_phaseC=False)
    result_phaseA = calculator_phaseA.calculate_sqe(sample_ingredients)
    
    print("计算结果:")
    print(f"协同分数: {result_phaseA['synergy_score']:.4f}")
    print(f"冲突分数: {result_phaseA['conflict_score']:.4f}")
    print(f"平衡分数: {result_phaseA['balance_score']:.4f}")
    print(f"标准化协同: {result_phaseA['synergy_normalized']:.4f}")
    print(f"标准化冲突: {result_phaseA['conflict_normalized']:.4f}")
    print(f"标准化平衡: {result_phaseA['balance_normalized']:.4f}")
    print(f"冲突转换: {result_phaseA['conflict_good']:.4f}")
    print(f"PhaseA SQE: {result_phaseA['sqe_total']:.4f}")
    print(f"最终 SQE: {result_phaseA['final_sqe']:.4f}")
    print(f"使用模型: {result_phaseA['used_model']}")
    

# =========================================================
# 便捷函数
# =========================================================

def calculate_recipe_sqe(ingredients: List[Dict], use_phaseC: bool = False) -> Dict:
    """
    快速计算配方的 SQE 分数
    
    参数:
    ingredients: 原料列表，每个原料包含以下字段:
        - ingredient_id: 原料 ID
        - amount: 原料用量
        - unit: 单位
        - role: 角色
        - line_no: 行号
        - raw_text: 原始文本
    use_phaseC: 是否使用 Phase C 模型
    
    返回:
    包含 SQE 分数的字典，包括:
        - synergy_score: 协同分数
        - conflict_score: 冲突分数
        - balance_score: 平衡分数
        - synergy_normalized: 标准化协同分数
        - conflict_normalized: 标准化冲突分数
        - balance_normalized: 标准化平衡分数
        - conflict_good: 冲突转换分数
        - sqe_total: Phase A SQE 总分
        - final_sqe: 最终 SQE 分数
        - used_model: 使用的模型
        - optimal_params: 最优参数（仅 Phase A）
        - sqe_c: Phase C SQE 分数（仅 Phase C）
        - hat_syn: 修正后协同分数（仅 Phase C）
        - hat_conf: 修正后冲突分数（仅 Phase C）
        - hat_bal: 修正后平衡分数（仅 Phase C）
        - structure_correction: 结构修正项（仅 Phase C）
    """
    calculator = SQECalculator(use_phaseC=use_phaseC)
    return calculator.calculate_sqe(ingredients)


def calculate_recipe_sqe_from_id(recipe_id: int, use_phaseC: bool = False) -> Dict:
    """
    从配方 ID 计算 SQE 分数
    
    参数:
    recipe_id: 配方 ID
    use_phaseC: 是否使用 Phase C 模型
    
    返回:
    包含 SQE 分数的字典，格式同上
    """
    calculator = SQECalculator(use_phaseC=use_phaseC)
    return calculator.calculate_sqe_from_recipe_id(recipe_id)


def recipe_to_graph_representation(ingredients: List[Dict]) -> Optional[Any]:
    """
    将配方转换为图表示
    
    参数:
    ingredients: 原料列表，格式同上
    
    返回:
    PyTorch Geometric Data 对象，或 None 如果转换失败
    """
    calculator = SQECalculator()
    return calculator.recipe_to_graph(ingredients)


if __name__ == "__main__":
    main()
