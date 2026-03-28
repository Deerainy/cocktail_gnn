from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q, Count, Avg, Max
from .models_recipe import (
    CanonicalFreqV2, IngredientFlavorAnchor, IngredientFlavorFeature,
    SqeNodeImportance, GraphEdgeStatsV2, GraphFlavorEdgeStats,
    GraphFlavorCompatEdgeStats, LlmCanonicalMap
)
from .serializers_flavor_graph import (
    FlavorGraphNodeSerializer, FlavorGraphEdgeSerializer,
    FlavorNodeDetailSerializer, FlavorEdgeDetailSerializer,
    FlavorGraphStatsSerializer
)


class FlavorGraphView(APIView):
    """
    获取全局风味图谱主图数据
    """
    
    def get(self, request):
        try:
            # 获取查询参数
            layer = request.GET.get('layer', 'compat')
            ingredient_type = request.GET.get('ingredient_type')
            min_weight = float(request.GET.get('min_weight', 0.0))
            topk = int(request.GET.get('topk', 8))
            keyword = request.GET.get('keyword')
            limit_nodes = int(request.GET.get('limit_nodes', 100))
            only_key_nodes = request.GET.get('only_key_nodes', 'false').lower() == 'true'
            
            # 构建过滤条件
            filters = {'layer': layer, 'min_weight': min_weight, 'topk': topk, 
                      'keyword': keyword, 'limit_nodes': limit_nodes, 'only_key_nodes': only_key_nodes}
            
            # 根据图层选择边表
            if layer == 'compat':
                edge_model = GraphFlavorCompatEdgeStats
                edge_field = 'weight'
            elif layer == 'cooccur':
                edge_model = GraphEdgeStatsV2
                edge_field = 'weight'
            elif layer == 'flavor':
                edge_model = GraphFlavorEdgeStats
                edge_field = 'weight'
            else:
                return Response({
                    'code': 400,
                    'message': f'Invalid layer: {layer}',
                    'data': None
                })
            
            # 1. 按min_weight过滤边
            edges = edge_model.objects.filter(**{edge_field + '__gte': min_weight})
            
            # 2. 按ingredient_type过滤节点
            if ingredient_type:
                types = [t.strip() for t in ingredient_type.split(',')]
                # 获取符合类型的canonical_id
                anchors = IngredientFlavorAnchor.objects.filter(
                    anchor_source__in=types
                ).values_list('canonical_id', flat=True)
                # 过滤边，只保留两端都在类型列表中的边
                edges = edges.filter(
                    Q(i_canonical_id__in=anchors) | Q(j_canonical_id__in=anchors)
                )
            
            # 3. 如果有keyword，返回匹配节点及其邻域子图
            if keyword:
                # 查找匹配的节点
                matching_nodes = LlmCanonicalMap.objects.filter(
                    canonical_name__icontains=keyword,
                    status='ok'
                ).values_list('canonical_id', flat=True)
                
                if not matching_nodes:
                    return Response({
                        'code': 0,
                        'message': 'ok',
                        'data': {
                            'meta': filters,
                            'nodes': [],
                            'edges': []
                        }
                    })
                
                # 过滤边，只保留与匹配节点相关的边
                edges = edges.filter(
                    Q(i_canonical_id__in=matching_nodes) | 
                    Q(j_canonical_id__in=matching_nodes)
                )
            
            # 4. 如果only_key_nodes=true，只保留关键节点
            if only_key_nodes:
                key_nodes = SqeNodeImportance.objects.filter(
                    is_key_node=True
                ).values_list('canonical_id', flat=True)
                
                # 过滤边，只保留关键节点之间的边
                edges = edges.filter(
                    Q(i_canonical_id__in=key_nodes) | 
                    Q(j_canonical_id__in=key_nodes)
                )
            
            # 5. 获取所有节点ID
            node_ids = set()
            for edge in edges:
                node_ids.add(str(edge.i_canonical_id))
                node_ids.add(str(edge.j_canonical_id))
            
            # 6. 按limit_nodes限制节点总数
            if len(node_ids) > limit_nodes:
                # 按频次排序，保留高频节点
                freq_map = {}
                for nid in node_ids:
                    freq = CanonicalFreqV2.objects.filter(canonical_id=nid).aggregate(
                        total=Count('id')
                    )['total'] or 0
                    freq_map[nid] = freq
                
                # 按频次排序，取前limit_nodes个
                sorted_nodes = sorted(freq_map.items(), key=lambda x: x[1], reverse=True)[:limit_nodes]
                node_ids = set([nid for nid, _ in sorted_nodes])
                
                # 过滤边，只保留这些节点之间的边
                edges = edges.filter(
                    Q(i_canonical_id__in=node_ids) | 
                    Q(j_canonical_id__in=node_ids)
                )
            
            # 7. topk邻边裁剪
            if topk > 0:
                # 统计每个节点的边数
                edge_count = {}
                for edge in edges:
                    i_id = str(edge.i_canonical_id)
                    j_id = str(edge.j_canonical_id)
                    edge_count[i_id] = edge_count.get(i_id, 0) + 1
                    edge_count[j_id] = edge_count.get(j_id, 0) + 1
                
                # 对每个节点，只保留权重最高的topk条边
                node_edges = {}
                for edge in edges:
                    i_id = str(edge.i_canonical_id)
                    j_id = str(edge.j_canonical_id)
                    
                    # 为i节点添加边
                    if i_id not in node_edges:
                        node_edges[i_id] = []
                    if len(node_edges[i_id]) < topk:
                        node_edges[i_id].append(edge)
                    else:
                        # 如果已有topk条边，比较权重
                        min_weight = min(e.weight for e in node_edges[i_id])
                        if edge.weight > min_weight:
                            # 替换权重最小的边
                            for idx, e in enumerate(node_edges[i_id]):
                                if e.weight == min_weight:
                                    node_edges[i_id][idx] = edge
                                    break
                    
                    # 为j节点添加边
                    if j_id not in node_edges:
                        node_edges[j_id] = []
                    if len(node_edges[j_id]) < topk:
                        node_edges[j_id].append(edge)
                    else:
                        min_weight = min(e.weight for e in node_edges[j_id])
                        if edge.weight > min_weight:
                            for idx, e in enumerate(node_edges[j_id]):
                                if e.weight == min_weight:
                                    node_edges[j_id][idx] = edge
                                    break
                
                # 合并所有边
                edges = []
                for node_id, edge_list in node_edges.items():
                    edges.extend(edge_list)
            
            # 构建节点数据
            nodes_data = []
            for node_id in node_ids:
                # 获取节点基本信息
                freq = CanonicalFreqV2.objects.filter(canonical_id=node_id).aggregate(
                    total=Count('id')
                )['total'] or 0
                
                # 获取重要性分数
                importance = SqeNodeImportance.objects.filter(
                    canonical_id=node_id
                ).order_by('-normalized_contribution').first()
                
                # 获取anchor信息
                anchor = IngredientFlavorAnchor.objects.filter(canonical_id=node_id).first()
                
                # 获取中文名
                mapping = LlmCanonicalMap.objects.filter(
                    canonical_id=node_id,
                    status='ok'
                ).first()
                
                node_data = {
                    'id': f'c_{node_id}',
                    'label': mapping.canonical_name if mapping else str(node_id),
                    'label_zh': mapping.canonical_name_zh if mapping else None,
                    'ingredient_type': anchor.anchor_source if anchor else None,
                    'role': anchor.anchor_form if anchor else None,
                    'freq': freq,
                    'importance_score': importance.normalized_contribution if importance else None,
                    'anchor_name': anchor.anchor_name if anchor else None,
                    'is_key_node': importance.is_key_node if importance else False
                }
                nodes_data.append(node_data)
            
            # 构建边数据
            edges_data = []
            for edge in edges:
                edges_data.append({
                    'source': f'c_{edge.i_canonical_id}',
                    'target': f'c_{edge.j_canonical_id}',
                    'type': layer,
                    'weight': float(getattr(edge, edge_field))
                })
            
            return Response({
                'code': 0,
                'message': 'ok',
                'data': {
                    'meta': {
                        'layer': layer,
                        'node_count': len(nodes_data),
                        'edge_count': len(edges_data),
                        'filters': {
                            'ingredient_type': types if ingredient_type else [],
                            'min_weight': min_weight,
                            'topk': topk,
                            'keyword': keyword,
                            'limit_nodes': limit_nodes,
                            'only_key_nodes': only_key_nodes
                        }
                    },
                    'nodes': nodes_data,
                    'edges': edges_data
                }
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': str(e),
                'data': None
            })


class FlavorNodeDetailView(APIView):
    """
    获取节点详情
    """
    
    def get(self, request, node_id):
        try:
            # 去掉c_前缀
            canonical_id = node_id.replace('c_', '')
            
            # 获取节点基本信息
            freq = CanonicalFreqV2.objects.filter(canonical_id=canonical_id).aggregate(
                total=Count('id')
            )['total'] or 0
            
            # 获取重要性分数
            importance = SqeNodeImportance.objects.filter(
                canonical_id=canonical_id
            ).order_by('-normalized_contribution').first()
            
            # 获取anchor信息
            anchor = IngredientFlavorAnchor.objects.filter(canonical_id=canonical_id).first()
            
            # 获取中文名
            mapping = LlmCanonicalMap.objects.filter(
                canonical_id=canonical_id,
                status='ok'
            ).first()
            
            # 获取风味特征
            features = None
            if anchor:
                feature = IngredientFlavorFeature.objects.filter(
                    anchor_name=anchor.anchor_name
                ).first()
                if feature:
                    features = {
                        'sour': feature.sour,
                        'sweet': feature.sweet,
                        'bitter': feature.bitter,
                        'aroma': feature.aroma,
                        'fruity': feature.fruity,
                        'body': feature.body
                    }
            
            # 获取top邻居（基于compat图层）
            neighbors = GraphFlavorCompatEdgeStats.objects.filter(
                Q(i_canonical_id=canonical_id) | Q(j_canonical_id=canonical_id)
            ).order_by('-weight')[:5]
            
            top_neighbors = []
            for neighbor in neighbors:
                other_id = neighbor.j_canonical_id if neighbor.i_canonical_id == canonical_id else neighbor.i_canonical_id
                other_mapping = LlmCanonicalMap.objects.filter(
                    canonical_id=other_id,
                    status='ok'
                ).first()
                
                top_neighbors.append({
                    'id': f'c_{other_id}',
                    'label': other_mapping.canonical_name if other_mapping else str(other_id),
                    'weight': float(neighbor.weight),
                    'type': 'compat'
                })
            
            node_data = {
                'id': f'c_{canonical_id}',
                'label': mapping.canonical_name if mapping else str(canonical_id),
                'label_zh': mapping.canonical_name_zh if mapping else None,
                'ingredient_type': anchor.anchor_source if anchor else None,
                'role': anchor.anchor_form if anchor else None,
                'freq': freq,
                'importance_score': importance.normalized_contribution if importance else None,
                'is_key_node': importance.is_key_node if importance else False,
                'anchor': {
                    'anchor_name': anchor.anchor_name if anchor else None,
                    'anchor_source': anchor.anchor_source if anchor else None,
                    'match_confidence': anchor.match_confidence if anchor else None
                } if anchor else None,
                'features': features,
                'top_neighbors': top_neighbors,
                'summary': f'{mapping.canonical_name if mapping else canonical_id} is a {anchor.anchor_source if anchor else "ingredient"} with {freq} occurrences.'
            }
            
            return Response({
                'code': 0,
                'message': 'ok',
                'data': node_data
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': str(e),
                'data': None
            })


class FlavorEdgeDetailView(APIView):
    """
    获取边详情
    """
    
    def get(self, request):
        try:
            source = request.GET.get('source')
            target = request.GET.get('target')
            layer = request.GET.get('layer', 'compat')
            
            if not source or not target:
                return Response({
                    'code': 400,
                    'message': 'source and target are required',
                    'data': None
                })
            
            # 去掉c_前缀
            source_id = source.replace('c_', '')
            target_id = target.replace('c_', '')
            
            # 根据图层选择边表
            if layer == 'compat':
                edge_model = GraphFlavorCompatEdgeStats
                i_field = 'i_canonical_id'
                j_field = 'j_canonical_id'
            elif layer == 'cooccur':
                edge_model = GraphEdgeStatsV2
                i_field = 'i_id'
                j_field = 'j_id'
            elif layer == 'flavor':
                edge_model = GraphFlavorEdgeStats
                i_field = 'i_id'
                j_field = 'j_id'
            else:
                return Response({
                    'code': 400,
                    'message': f'Invalid layer: {layer}',
                    'data': None
                })
            
            # 查找边
            edge = edge_model.objects.filter(
                **{i_field: source_id, j_field: target_id}
            ).first()
            
            if not edge:
                edge = edge_model.objects.filter(
                    **{i_field: target_id, j_field: source_id}
                ).first()
            
            if not edge:
                return Response({
                    'code': 404,
                    'message': 'edge not found',
                    'data': None
                })
            
            # 获取source和target的中文名
            source_mapping = LlmCanonicalMap.objects.filter(
                canonical_id=source_id,
                status='ok'
            ).first()
            
            target_mapping = LlmCanonicalMap.objects.filter(
                canonical_id=target_id,
                status='ok'
            ).first()
            
            # 构建metrics
            metrics = {}
            if layer == 'compat':
                metrics = {
                    'compat_score': float(edge.compat_score),
                    'role_bonus': float(edge.role_bonus),
                    'taste_complement_score': float(edge.taste_complement_score),
                    'anchor_bonus': float(edge.anchor_bonus),
                    'cooccur_bonus': float(edge.cooccur_bonus),
                    'penalty_score': float(edge.penalty_score)
                }
            elif layer == 'cooccur':
                metrics = {
                    'co_count': edge.co_count,
                    'pmi': float(edge.pmi),
                    'weight': float(edge.weight)
                }
            elif layer == 'flavor':
                metrics = {
                    'cosine_sim': float(edge.sim_cosine),
                    'l2_distance': float(edge.dist_l2),
                    'weight': float(edge.weight)
                }
            
            edge_data = {
                'source': {
                    'id': f'c_{source_id}',
                    'label': source_mapping.canonical_name if source_mapping else str(source_id),
                    'label_zh': source_mapping.canonical_name_zh if source_mapping else None
                },
                'target': {
                    'id': f'c_{target_id}',
                    'label': target_mapping.canonical_name if target_mapping else str(target_id),
                    'label_zh': target_mapping.canonical_name_zh if target_mapping else None
                },
                'type': layer,
                'weight': float(edge.weight),
                'metrics': metrics,
                'summary': f'{source_mapping.canonical_name if source_mapping else source_id} and {target_mapping.canonical_name if target_mapping else target_id} have a {layer} relationship with weight {edge.weight}.'
            }
            
            return Response({
                'code': 0,
                'message': 'ok',
                'data': edge_data
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': str(e),
                'data': None
            })


class FlavorGraphStatsView(APIView):
    """
    获取图谱统计
    """
    
    def get(self, request):
        try:
            layer = request.GET.get('layer', 'compat')
            ingredient_type = request.GET.get('ingredient_type')
            
            # 根据图层选择边表
            if layer == 'compat':
                edge_model = GraphFlavorCompatEdgeStats
                i_field = 'i_canonical_id'
                j_field = 'j_canonical_id'
                weight_field = 'weight'
            elif layer == 'cooccur':
                edge_model = GraphEdgeStatsV2
                i_field = 'i_id'
                j_field = 'j_id'
                weight_field = 'weight'
            elif layer == 'flavor':
                edge_model = GraphFlavorEdgeStats
                i_field = 'i_id'
                j_field = 'j_id'
                weight_field = 'weight'
            else:
                return Response({
                    'code': 400,
                    'message': f'Invalid layer: {layer}',
                    'data': None
                })
            
            # 按ingredient_type过滤
            edges = edge_model.objects.all()
            if ingredient_type:
                types = [t.strip() for t in ingredient_type.split(',')]
                anchors = IngredientFlavorAnchor.objects.filter(
                    anchor_source__in=types
                ).values_list('canonical_id', flat=True)
                edges = edges.filter(
                    Q(**{i_field + '__in': anchors}) | 
                    Q(**{j_field + '__in': anchors})
                )
            
            # 统计信息
            node_count = edges.aggregate(
                count=Count(i_field)
            )['count']
            
            edge_count = edges.count()
            
            avg_degree = edge_count * 2 / node_count if node_count > 0 else 0
            
            max_weight = edges.aggregate(
                max_weight=Max(weight_field)
            )['max_weight'] or 0
            
            # top_nodes（按重要性分数排序）
            top_nodes = SqeNodeImportance.objects.filter(
                is_key_node=True
            ).order_by('-normalized_contribution')[:10]
            
            top_nodes_data = []
            for node in top_nodes:
                mapping = LlmCanonicalMap.objects.filter(
                    canonical_id=node.canonical_id,
                    status='ok'
                ).first()
                top_nodes_data.append({
                    'id': f'c_{node.canonical_id}',
                    'label': mapping.canonical_name if mapping else str(node.canonical_id),
                    'score': float(node.normalized_contribution)
                })
            
            # top_freq（按频次排序）
            top_freq = CanonicalFreqV2.objects.order_by('-freq')[:10]
            
            top_freq_data = []
            for freq in top_freq:
                mapping = LlmCanonicalMap.objects.filter(
                    canonical_id=freq.canonical_id,
                    status='ok'
                ).first()
                top_freq_data.append({
                    'id': f'c_{freq.canonical_id}',
                    'label': mapping.canonical_name if mapping else str(freq.canonical_id),
                    'freq': freq.freq
                })
            
            # top_anchors（按数量排序）
            top_anchors = IngredientFlavorAnchor.objects.values(
                'anchor_name'
            ).annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            top_anchors_data = []
            for anchor in top_anchors:
                top_anchors_data.append({
                    'anchor_name': anchor['anchor_name'],
                    'count': anchor['count']
                })
            
            stats_data = {
                'summary': {
                    'node_count': node_count,
                    'edge_count': edge_count,
                    'avg_degree': round(avg_degree, 2),
                    'max_weight': float(max_weight)
                },
                'top_nodes': top_nodes_data,
                'top_freq': top_freq_data,
                'top_anchors': top_anchors_data
            }
            
            return Response({
                'code': 0,
                'message': 'ok',
                'data': stats_data
            })
        except Exception as e:
            return Response({
                'code': 500,
                'message': str(e),
                'data': None
            })
