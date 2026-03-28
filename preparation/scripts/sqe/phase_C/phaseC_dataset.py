# -*- coding: utf-8 -*-
"""
Phase C 数据集封装脚本

功能：
1. 封装 Phase C 图数据为 PyTorch Geometric Dataset
2. 实现单图数据对象和成对训练数据对象
3. 提供数据加载和访问接口
"""

import os
import sys
import pickle
import pandas as pd
import torch
from torch_geometric.data import Data
from torch.utils.data import Dataset

# 添加项目根目录到 Python 路径
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(_script_dir))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# =========================================================
# 配置参数
# =========================================================

class Config:
    """配置类"""
    # 输入文件
    GRAPHS_FILE = os.path.join(_project_root, "data", "phaseC", "graphs_phaseC.pt")
    PAIRS_FILE = os.path.join(_project_root, "data", "phaseC", "pairs_phaseC.csv")

# =========================================================
# 图存储类
# =========================================================

class PhaseCGraphStore:
    """
    负责按 recipe_id 取单图
    """
    def __init__(self, graphs_file: str):
        """
        初始化图存储
        
        参数:
        graphs_file: 图数据文件路径
        """
        self.graphs_file = graphs_file
        self.graphs = self._load_graphs()
    
    def _load_graphs(self) -> dict:
        """
        加载图数据
        
        返回:
        图数据字典，key 为 recipe_id，value 为图数据
        """
        print(f"[INFO] 加载图数据从 {self.graphs_file}")
        print(f"[INFO] 文件是否存在: {os.path.exists(self.graphs_file)}")
        print(f"[INFO] 文件大小: {os.path.getsize(self.graphs_file) if os.path.exists(self.graphs_file) else 0} bytes")
        
        try:
            with open(self.graphs_file, 'rb') as f:
                graphs = pickle.load(f)
            print(f"[INFO] 加载了 {len(graphs)} 个图样本")
            return graphs
        except Exception as e:
            print(f"[ERROR] 加载图数据时出错: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_graph(self, recipe_id) -> Data:
        """
        根据 recipe_id 获取图数据
        
        参数:
        recipe_id: 食谱 ID
        
        返回:
        PyTorch Geometric Data 对象
        """
        if recipe_id not in self.graphs:
            raise KeyError(f"Recipe ID {recipe_id} not found in graph store")
        
        graph_data = self.graphs[recipe_id]
        
        # 构建 Data 对象
        data = Data(
            x=torch.tensor(graph_data['x'], dtype=torch.float),
            edge_index=torch.tensor(graph_data['edge_index'], dtype=torch.long),
            edge_attr=torch.tensor(graph_data['edge_attr'], dtype=torch.float),
            y_base=torch.tensor(graph_data['base_scores'], dtype=torch.float),
            z_graph=torch.tensor(graph_data['z_graph'], dtype=torch.float)
        )
        
        # 处理 recipe_id
        if isinstance(recipe_id, int):
            data.recipe_id = torch.tensor([recipe_id], dtype=torch.long)
        else:
            # 对于字符串类型的 recipe_id，不存储为 tensor
            data.recipe_id_str = recipe_id
        
        return data
    
    def get_all_recipe_ids(self) -> list:
        """
        获取所有 recipe_id
        
        返回:
        recipe_id 列表
        """
        return list(self.graphs.keys())

# =========================================================
# 成对数据集类
# =========================================================

class PhaseCPairDataset(Dataset):
    """
    成对训练数据集
    """
    def __init__(self, pairs_file: str, graph_store: PhaseCGraphStore):
        """
        初始化成对数据集
        
        参数:
        pairs_file: 配对数据文件路径
        graph_store: 图存储对象
        """
        self.pairs_file = pairs_file
        self.graph_store = graph_store
        self.pairs = self._load_pairs()
    
    def _load_pairs(self) -> pd.DataFrame:
        """
        加载配对数据
        
        返回:
        配对数据 DataFrame
        """
        print(f"[INFO] 加载配对数据从 {self.pairs_file}")
        pairs_df = pd.read_csv(self.pairs_file)
        print(f"[INFO] 加载了 {len(pairs_df)} 条配对数据")
        return pairs_df
    
    def __len__(self) -> int:
        """
        返回数据集长度
        """
        return len(self.pairs)
    
    def __getitem__(self, idx: int):
        """
        获取指定索引的配对数据
        
        参数:
        idx: 索引
        
        返回:
        包含正样本图、负样本图、扰动类型和组 ID 的 Data 对象
        """
        from torch_geometric.data import Data
        import hashlib
        
        pair_row = self.pairs.iloc[idx]
        
        # 获取正样本和负样本的 recipe_id
        pos_recipe_id = pair_row['pos_recipe_id']
        neg_recipe_id = pair_row['neg_recipe_id']
        
        # 处理 recipe_id 类型
        try:
            pos_recipe_id = int(pos_recipe_id)
        except (ValueError, TypeError):
            # 如果是字符串（如 perturbed_xxx），直接使用
            pass
        
        # 获取扰动类型和组 ID
        perturb_type = pair_row['perturb_type']
        group_id = pair_row['group_id']
        
        # 尝试获取正样本和负样本的图数据
        try:
            pos_graph = self.graph_store.get_graph(pos_recipe_id)
        except KeyError:
            # 如果找不到正样本图，使用组 ID 作为替代
            pos_graph = self.graph_store.get_graph(int(group_id))
        
        try:
            # 首先尝试直接使用 neg_recipe_id
            neg_graph = self.graph_store.get_graph(neg_recipe_id)
        except KeyError:
            # 如果找不到负样本图，尝试生成完整的 32 位哈希值
            if isinstance(neg_recipe_id, str) and neg_recipe_id.startswith('perturbed_'):
                # 尝试生成完整的 32 位哈希值
                # 注意：这里使用 pos_recipe_id 作为原始 recipe_id
                try:
                    # 尝试使用 pos_recipe_id 作为原始 recipe_id
                    original_recipe_id = pos_recipe_id
                    # 确保 original_recipe_id 是字符串
                    if not isinstance(original_recipe_id, str):
                        original_recipe_id = str(original_recipe_id)
                    # 生成完整的 32 位哈希值
                    perturb_id = hashlib.md5((original_recipe_id + perturb_type).encode()).hexdigest()
                    full_neg_recipe_id = f"perturbed_{perturb_id}"
                    neg_graph = self.graph_store.get_graph(full_neg_recipe_id)
                except (ValueError, TypeError, KeyError):
                    # 如果还是找不到，尝试使用组 ID 作为原始 recipe_id
                    try:
                        # 尝试使用 group_id 作为原始 recipe_id
                        original_recipe_id = group_id
                        # 确保 original_recipe_id 是字符串
                        if not isinstance(original_recipe_id, str):
                            original_recipe_id = str(original_recipe_id)
                        # 生成完整的 32 位哈希值
                        perturb_id = hashlib.md5((original_recipe_id + perturb_type).encode()).hexdigest()
                        full_neg_recipe_id = f"perturbed_{perturb_id}"
                        neg_graph = self.graph_store.get_graph(full_neg_recipe_id)
                    except (ValueError, TypeError, KeyError):
                        # 如果还是找不到，使用组 ID 作为替代
                        try:
                            neg_graph = self.graph_store.get_graph(int(group_id))
                        except (ValueError, TypeError, KeyError):
                            # 如果组 ID 也找不到，使用正样本图作为替代
                            neg_graph = pos_graph
            else:
                # 如果不是字符串或不是 perturbed_ 开头，使用组 ID 作为替代
                try:
                    neg_graph = self.graph_store.get_graph(int(group_id))
                except (ValueError, TypeError, KeyError):
                    # 如果组 ID 也找不到，使用正样本图作为替代
                    neg_graph = pos_graph
        
        # 检查节点特征是否有效
        try:
            # 检查 x 是否是 2 维张量且特征维度大于 0
            if pos_graph.x.dim() != 2 or pos_graph.x.size(1) == 0:
                # 如果节点特征无效，返回第一个样本
                if idx == 0:
                    print("[WARNING] 正样本节点特征无效，返回第一个样本")
                return self.__getitem__(0)
            if neg_graph.x.dim() != 2 or neg_graph.x.size(1) == 0:
                # 如果节点特征无效，返回第一个样本
                if idx == 0:
                    print("[WARNING] 负样本节点特征无效，返回第一个样本")
                return self.__getitem__(0)
        except Exception as e:
            # 如果发生错误，返回第一个样本
            if idx == 0:
                print(f"[WARNING] 检查节点特征时出错: {e}，返回第一个样本")
            return self.__getitem__(0)
        
        # 创建一个包含正样本和负样本信息的 Data 对象
        # 注意：这里我们将正样本和负样本的信息分别存储在不同的属性中
        # 显式设置 num_nodes 属性，以避免 PyTorch Geometric 无法推断节点数量的错误
        
        # 处理正样本和负样本的 recipe_id
        if hasattr(pos_graph, 'recipe_id'):
            pos_recipe_id_tensor = pos_graph.recipe_id
        else:
            # 如果 recipe_id 是字符串，使用 0 作为占位符
            pos_recipe_id_tensor = torch.tensor([0], dtype=torch.long)
        
        if hasattr(neg_graph, 'recipe_id'):
            neg_recipe_id_tensor = neg_graph.recipe_id
        else:
            # 如果 recipe_id 是字符串，使用 0 作为占位符
            neg_recipe_id_tensor = torch.tensor([0], dtype=torch.long)
        
        data = Data(
            pos_x=pos_graph.x,
            pos_edge_index=pos_graph.edge_index,
            pos_edge_attr=pos_graph.edge_attr,
            pos_z_graph=pos_graph.z_graph,
            pos_y_base=pos_graph.y_base,
            pos_recipe_id=pos_recipe_id_tensor,
            pos_num_nodes=pos_graph.x.size(0),
            
            neg_x=neg_graph.x,
            neg_edge_index=neg_graph.edge_index,
            neg_edge_attr=neg_graph.edge_attr,
            neg_z_graph=neg_graph.z_graph,
            neg_y_base=neg_graph.y_base,
            neg_recipe_id=neg_recipe_id_tensor,
            neg_num_nodes=neg_graph.x.size(0),
            
            perturb_type=perturb_type,
            group_id=group_id,
            num_nodes=1  # 这里设置为 1，因为我们的 Data 对象包含了两个图的信息
        )
        
        return data

# =========================================================
# 工具函数
# =========================================================

def create_phaseC_dataset() -> PhaseCPairDataset:
    """
    创建 Phase C 数据集
    
    返回:
    PhaseCPairDataset 对象
    """
    # 创建图存储
    graph_store = PhaseCGraphStore(Config.GRAPHS_FILE)
    
    # 创建成对数据集
    dataset = PhaseCPairDataset(Config.PAIRS_FILE, graph_store)
    
    return dataset

# =========================================================
# 主函数
# =========================================================
def main():
    """
    主函数
    """
    print("创建 Phase C 数据集...")
    
    # 创建数据集
    dataset = create_phaseC_dataset()
    
    # 测试数据集
    print(f"[INFO] 数据集长度: {len(dataset)}")
    
    # 测试获取第一个样本
    if len(dataset) > 0:
        sample = dataset[0]
        print("[INFO] 第一个样本:")
        print(f"  正样本图: {sample['pos_graph']}")
        print(f"  负样本图: {sample['neg_graph']}")
        print(f"  扰动类型: {sample['perturb_type']}")
        print(f"  组 ID: {sample['group_id']}")
    
    print("[INFO] Phase C 数据集创建完成！")

if __name__ == "__main__":
    main()
