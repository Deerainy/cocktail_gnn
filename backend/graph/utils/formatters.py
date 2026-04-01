"""
结果格式化工具

用于将 Neo4j 查询结果格式化为标准化的输出结构
"""

from typing import Dict, Any, List


def format_node(node: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化节点数据
    Args:
        node: Neo4j 节点数据
    Returns: 格式化后的节点数据
    """
    # 提取节点属性，排除内部 ID
    properties = {k: v for k, v in node.items() if k != 'id'}
    # 尝试获取业务 ID，如果不存在则使用内部 ID
    node_id = node.get('id') or node.get('recipe_id') or node.get('ingredient_id') or node.get('canonical_id')
    return {
        "id": node_id,
        "name": node.get('name'),
        "raw": properties
    }


def format_relationship(rel: Dict[str, Any], source_id: str, target_id: str) -> Dict[str, Any]:
    """
    格式化关系数据
    Args:
        rel: Neo4j 关系数据
        source_id: 源节点 ID
        target_id: 目标节点 ID
    Returns: 格式化后的关系数据
    """
    # 提取关系属性，排除类型和内部 ID
    properties = {k: v for k, v in rel.items() if k not in ['type', 'id']}
    return {
        "source": source_id,
        "target": target_id,
        "type": rel.get('type'),
        "properties": properties
    }


def format_recipe_subgraph(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    格式化食谱子图结果
    Args:
        results: Neo4j 查询结果
    Returns: 格式化后的子图数据
    """
    recipe = None
    ingredients = []
    canonicals = []
    edges = []
    ingredient_ids = set()
    canonical_ids = set()
    edge_keys = set()

    for record in results:
        # 处理食谱节点
        if 'r' in record and not recipe:
            recipe = format_node(record['r'])

        # 处理食材节点
        if 'i' in record and record['i']:
            ingredient = format_node(record['i'])
            if ingredient['id'] not in ingredient_ids:
                ingredients.append(ingredient)
                ingredient_ids.add(ingredient['id'])

        # 处理规范食材节点 (ci)
        if 'ci' in record and record['ci']:
            canonical = format_node(record['ci'])
            if canonical['id'] not in canonical_ids:
                canonicals.append(canonical)
                canonical_ids.add(canonical['id'])

        # 处理规范食材节点 (ci2)
        if 'ci2' in record and record['ci2']:
            canonical = format_node(record['ci2'])
            if canonical['id'] not in canonical_ids:
                canonicals.append(canonical)
                canonical_ids.add(canonical['id'])

        # 处理规范食材之间的关系
        if 'rel' in record and record['rel'] and 'ci3' in record and 'ci4' in record:
            # 尝试获取业务 ID，如果不存在则使用内部 ID
            ci3_id = record['ci3'].get('id') or record['ci3'].get('canonical_id')
            ci4_id = record['ci4'].get('id') or record['ci4'].get('canonical_id')
            if ci3_id and ci4_id:
                edge = format_relationship(record['rel'], ci3_id, ci4_id)
                edge_key = f"{edge['source']}-{edge['target']}-{edge['type']}"
                if edge_key not in edge_keys:
                    edges.append(edge)
                    edge_keys.add(edge_key)

    return {
        "recipe": recipe,
        "ingredients": ingredients,
        "canonicals": canonicals,
        "edges": edges
    }



def format_global_substitutes(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    格式化全局替代结果
    Args:
        results: Neo4j 查询结果
    Returns: 格式化后的替代数据
    """
    target = None
    candidates = []

    for record in results:
        # 处理目标规范食材
        if 'c' in record and not target:
            target = format_node(record['c'])

        # 处理候选替代规范食材
        if 'cs' in record and 'gs' in record:
            canonical = format_node(record['cs'])
            relation = {
                "type": record['gs'].get('type'),
                "properties": {k: v for k, v in record['gs'].items() if k not in ['type', 'id']}
            }
            candidates.append({
                "canonical": canonical,
                "relation": relation
            })

    return {
        "target": target,
        "candidates": candidates
    }


def format_recipe_substitute_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    格式化食谱替代结果
    Args:
        results: Neo4j 查询结果
    Returns: 格式化后的替代结果数据
    """
    recipe = None
    substitute_results = {}

    for record in results:
        # 处理食谱节点
        if 'r' in record and not recipe:
            recipe = format_node(record['r'])

        # 处理替代结果节点
        if 'sr' in record and record['sr']:
            sr_id = record['sr'].get('id')
            if sr_id not in substitute_results:
                substitute_results[sr_id] = {
                    "substitute_result": format_node(record['sr']),
                    "target": None,
                    "candidates": []
                }

            # 处理目标节点
            if 't' in record and record['t']:
                substitute_results[sr_id]['target'] = format_node(record['t'])

            # 处理候选节点
            if 'c' in record and record['c']:
                candidate = format_node(record['c'])
                # 处理关系属性
                relation = {}
                if 'cr' in record and record['cr']:
                    relation = {
                        "type": record['cr'].get('type'),
                        "properties": {k: v for k, v in record['cr'].items() if k not in ['type', 'id']}
                    }
                candidate['relation'] = relation
                substitute_results[sr_id]['candidates'].append(candidate)

    return {
        "recipe": recipe,
        "results": list(substitute_results.values())
    }


def format_canonical_neighbors(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    格式化规范食材邻域结果
    Args:
        results: Neo4j 查询结果
    Returns: 格式化后的邻域数据
    """
    center = None
    neighbors = []

    for record in results:
        # 处理中心节点
        if 'c' in record and not center:
            center = format_node(record['c'])

        # 处理邻居节点
        if 'n' in record and 'rel' in record:
            neighbor = {
                "node": format_node(record['n']),
                "edge": {
                    "type": record['rel'].get('type'),
                    "properties": {k: v for k, v in record['rel'].items() if k not in ['type', 'id']}
                }
            }
            neighbors.append(neighbor)

    return {
        "center": center,
        "neighbors": neighbors
    }
