from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import make_password
from .models import User, Entity, Alias, ReviewTask, ReviewEntity, Candidate, ReviewResult
from .serializers import UserSerializer, UserLoginSerializer, UserRegisterSerializer, EntitySerializer, AliasSerializer, ReviewTaskSerializer, ReviewSubmitSerializer, ProcessTextSerializer, BatchProcessSerializer, AddAliasSerializer
import uuid

class AuthViewSet(viewsets.ViewSet):
    permission_classes = []
    def register(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            if User.objects.filter(username=username).exists():
                return Response({'status': 'error', 'message': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = User(username=username, role='user')
            user.set_password(password)
            user.save()
            
            return Response({
                'status': 'success',
                'message': '注册成功',
                'data': {
                    'user_id': user.user_id,
                    'username': user.username,
                    'role': user.role
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            try:
                user = User.objects.get(username=username)
                if user.check_password(password):
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'status': 'success',
                        'message': '登录成功',
                        'data': {
                            'user_id': user.user_id,
                            'username': user.username,
                            'role': user.role,
                            'token': str(refresh.access_token)
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({'status': 'error', 'message': '密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({'status': 'error', 'message': '用户不存在'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def me(self, request):
        if not request.user.is_authenticated:
            return Response({'status': 'error', 'message': '未认证'}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = request.user
        return Response({
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role
        }, status=status.HTTP_200_OK)

class EntityViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        label = request.query_params.get('label')
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 10))
        
        queryset = Entity.objects.all()
        if label:
            queryset = queryset.filter(label=label)
        
        total = queryset.count()
        start = (page - 1) * size
        end = start + size
        entities = queryset[start:end]
        
        serializer = EntitySerializer(entities, many=True)
        return Response({
            'total': total,
            'entities': serializer.data
        }, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk):
        try:
            entity = Entity.objects.get(entity_id=pk)
            aliases = Alias.objects.filter(entity_id=entity)
            serializer = EntitySerializer(entity)
            alias_list = [alias.alias_name for alias in aliases]
            return Response({
                **serializer.data,
                'aliases': alias_list
            }, status=status.HTTP_200_OK)
        except Entity.DoesNotExist:
            return Response({'status': 'error', 'message': '实体不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    def create(self, request):
        serializer = EntitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk):
        try:
            entity = Entity.objects.get(entity_id=pk)
            serializer = EntitySerializer(entity, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Entity.DoesNotExist:
            return Response({'status': 'error', 'message': '实体不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk):
        try:
            entity = Entity.objects.get(entity_id=pk)
            entity.delete()
            return Response({'status': 'success', 'message': '实体删除成功'}, status=status.HTTP_200_OK)
        except Entity.DoesNotExist:
            return Response({'status': 'error', 'message': '实体不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    def get_aliases(self, request, pk):
        try:
            entity = Entity.objects.get(entity_id=pk)
            aliases = Alias.objects.filter(entity_id=entity)
            alias_data = [{'alias_id': alias.alias_id, 'alias_name': alias.alias_name} for alias in aliases]
            return Response({
                'entity_id': entity.entity_id,
                'name': entity.name,
                'aliases': alias_data
            }, status=status.HTTP_200_OK)
        except Entity.DoesNotExist:
            return Response({'status': 'error', 'message': '实体不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    def add_alias(self, request, pk):
        try:
            entity = Entity.objects.get(entity_id=pk)
            serializer = AddAliasSerializer(data=request.data)
            if serializer.is_valid():
                alias_name = serializer.validated_data['alias_name']
                
                if Alias.objects.filter(alias_name=alias_name).exists():
                    return Response({'status': 'error', 'message': '别名已存在'}, status=status.HTTP_400_BAD_REQUEST)
                
                alias = Alias(entity_id=entity, alias_name=alias_name)
                alias.save()
                return Response({
                    'alias_id': alias.alias_id,
                    'entity_id': alias.entity_id.entity_id,
                    'alias_name': alias.alias_name
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Entity.DoesNotExist:
            return Response({'status': 'error', 'message': '实体不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete_alias(self, request, pk):
        try:
            alias = Alias.objects.get(alias_id=pk)
            alias.delete()
            return Response({'status': 'success', 'message': '别名删除成功'}, status=status.HTTP_200_OK)
        except Alias.DoesNotExist:
            return Response({'status': 'error', 'message': '别名不存在'}, status=status.HTTP_404_NOT_FOUND)

class ReviewViewSet(viewsets.ViewSet):
    permission_classes = []
    
    def submit_review(self, request):
        # 覆盖默认权限，允许匿名提交审核
        self.permission_classes = []
        super().check_permissions(request)
        
        serializer = ReviewSubmitSerializer(data=request.data)
        if serializer.is_valid():
            review_id = serializer.validated_data['review_id']
            entity_id = serializer.validated_data['entity_id']
            original_text = serializer.validated_data['original_text']
            approved_candidate = serializer.validated_data['approved_candidate']
            add_as_alias = serializer.validated_data['add_as_alias']
            
            try:
                task = ReviewTask.objects.get(review_id=review_id)
                
                # 创建审核结果
                result = ReviewResult(
                    review_id_id=task.review_id,
                    entity_id=entity_id,
                    original_text=original_text,
                    approved_candidate_text=approved_candidate['text'],
                    approved_candidate_label=approved_candidate['label'],
                    add_as_alias=add_as_alias
                )
                
                # 处理实体和别名
                if 'entity_id' in approved_candidate:
                    try:
                        # 尝试获取现有实体
                        entity = Entity.objects.get(entity_id=approved_candidate['entity_id'])
                        
                        # 如果需要添加为别名
                        if add_as_alias:
                            alias = Alias(entity_id=entity, alias_name=original_text)
                            alias.save()
                            result.action = 'add_alias'
                    except Entity.DoesNotExist:
                        # 如果实体不存在，创建新实体
                        if approved_candidate.get('text'):
                            import uuid
                            new_entity = Entity(
                                entity_id=str(uuid.uuid4()),
                                name=approved_candidate['text'],
                                label=approved_candidate.get('label', 'UNKNOWN'),
                                normalized_name=approved_candidate.get('normalized_name', approved_candidate['text'])
                            )
                            new_entity.save()
                            
                            # 如果需要添加为别名
                            if add_as_alias:
                                alias = Alias(entity_id=new_entity, alias_name=original_text)
                                alias.save()
                                result.action = 'create_entity_and_add_alias'
                            else:
                                result.action = 'create_entity'
                
                result.save()
                task.status = 'processed'
                task.save()
                
                return Response({
                    'status': 'success',
                    'message': '审核结果已处理',
                    'data': {
                        'review_id': review_id,
                        'entity_id': entity_id,
                        'action': result.action,
                        'alias': original_text if add_as_alias else None,
                        'canonical_id': approved_candidate.get('entity_id'),
                        'canonical_name': approved_candidate.get('normalized_name')
                    }
                }, status=status.HTTP_200_OK)
            except ReviewTask.DoesNotExist:
                return Response({'status': 'error', 'message': '审核任务不存在'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_tasks(self, request):
        status_param = request.query_params.get('status')
        page = int(request.query_params.get('page', 1))
        size = int(request.query_params.get('size', 10))
        
        queryset = ReviewTask.objects.all()
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        total = queryset.count()
        start = (page - 1) * size
        end = start + size
        tasks = list(queryset[start:end])
        
        # 为每个任务的每个实体生成候选实体
        for task in tasks:
            for entity in task.entities.all():
                # 检查是否已有候选实体，如果有超过2个，就删除多余的
                if entity.candidates.count() > 2:
                    # 保留前2个候选实体，删除其余的
                    candidates_to_delete = entity.candidates.all()[2:]
                    for candidate in candidates_to_delete:
                        candidate.delete()
                    print(f"Deleted {len(candidates_to_delete)} excess candidates for entity {entity.review_entity_id}")
                # 检查是否已有候选实体
                elif entity.candidates.count() == 0:
                    # 从Entity和Alias中查找相似的实体
                    similar_entities = self.find_similar_entities(entity.text)
                    
                    # 去重，确保相同名字的实体只算一个
                    seen_text = set()
                    unique_similar_entities = []
                    for similar_entity in similar_entities:
                        if similar_entity['text'] not in seen_text:
                            seen_text.add(similar_entity['text'])
                            unique_similar_entities.append(similar_entity)
                    similar_entities = unique_similar_entities
                    
                    # 检查当前实体是否已经在相似实体列表中
                    current_entity_in_list = any(
                        similar_entity['text'] == entity.text and similar_entity['label'] == entity.label
                        for similar_entity in similar_entities
                    )
                    
                    # 限制候选实体的总数为2个
                    candidate_count = 0
                    
                    # 创建候选实体
                    for i, similar_entity in enumerate(similar_entities):
                        if candidate_count >= 2:
                            break
                        Candidate.objects.create(
                            review_entity_id=entity,
                            text=similar_entity['text'],
                            label=similar_entity['label'],
                            confidence=similar_entity['confidence'],
                            source=similar_entity['source']
                        )
                        candidate_count += 1
                    
                    # 只有当当前实体不在相似实体列表中且候选实体数量不足2个时，才添加当前实体作为新的候选
                    if not current_entity_in_list and candidate_count < 2:
                        try:
                            candidate = Candidate.objects.create(
                                review_entity_id=entity,
                                text=entity.text,
                                label=entity.label,
                                confidence=0.8,
                                source='current'
                            )
                            print(f"Created candidate for entity {entity.review_entity_id}: {candidate.text}")
                        except Exception as e:
                            print(f"Failed to create candidate: {e}")
        
        # 重新获取任务列表，确保包含我们生成的候选实体
        tasks = list(ReviewTask.objects.filter(review_id__in=[task.review_id for task in tasks]).prefetch_related('entities', 'entities__candidates'))
        
        serializer = ReviewTaskSerializer(tasks, many=True)
        return Response({
            'total': total,
            'tasks': serializer.data
        }, status=status.HTTP_200_OK)
    
    def get_task(self, request, pk):
        try:
            task = ReviewTask.objects.get(review_id=pk)
            
            # 为每个实体生成候选实体
            for entity in task.entities.all():
                # 检查是否已有候选实体
                if entity.candidates.count() == 0:
                    # 从Entity和Alias中查找相似的实体
                    similar_entities = self.find_similar_entities(entity.text)
                    
                    # 去重，确保相同名字的实体只算一个
                    seen_text = set()
                    unique_similar_entities = []
                    for similar_entity in similar_entities:
                        if similar_entity['text'] not in seen_text:
                            seen_text.add(similar_entity['text'])
                            unique_similar_entities.append(similar_entity)
                    similar_entities = unique_similar_entities
                    
                    # 检查当前实体是否已经在相似实体列表中
                    current_entity_in_list = any(
                        similar_entity['text'] == entity.text and similar_entity['label'] == entity.label
                        for similar_entity in similar_entities
                    )
                    
                    # 限制候选实体的总数为2个
                    candidate_count = 0
                    
                    # 创建候选实体
                    for i, similar_entity in enumerate(similar_entities):
                        if candidate_count >= 2:
                            break
                        Candidate.objects.create(
                            review_entity_id=entity,
                            text=similar_entity['text'],
                            label=similar_entity['label'],
                            confidence=similar_entity['confidence'],
                            source=similar_entity['source']
                        )
                        candidate_count += 1
                    
                    # 只有当当前实体不在相似实体列表中且候选实体数量不足2个时，才添加当前实体作为新的候选
                    if not current_entity_in_list and candidate_count < 2:
                        try:
                            candidate = Candidate.objects.create(
                                review_entity_id=entity,
                                text=entity.text,
                                label=entity.label,
                                confidence=0.8,
                                source='current'
                            )
                            print(f"Created candidate for entity {entity.review_entity_id}: {candidate.text}")
                        except Exception as e:
                            print(f"Failed to create candidate: {e}")
            
            serializer = ReviewTaskSerializer(task)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ReviewTask.DoesNotExist:
            return Response({'status': 'error', 'message': '审核任务不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    def find_similar_entities(self, text):
        """查找相似的实体"""
        similar_entities = []
        
        # 从Entity中查找相似实体
        from django.db.models import Q
        entities = Entity.objects.filter(
            Q(name__icontains=text) | Q(normalized_name__icontains=text)
        )[:2]
        
        for entity in entities:
            similar_entities.append({
                'text': entity.name,
                'label': entity.label,
                'confidence': 0.9,
                'source': 'entity'
            })
        
        # 从Alias中查找相似实体
        aliases = Alias.objects.filter(alias_name__icontains=text)[:2]
        for alias in aliases:
            try:
                entity = alias.entity_id
                similar_entities.append({
                    'text': alias.alias_name,
                    'label': entity.label,
                    'confidence': 0.85,
                    'source': 'alias'
                })
            except:
                pass
        
        # 去重
        seen = set()
        unique_entities = []
        for entity in similar_entities:
            key = f"{entity['text']}_{entity['label']}"
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        # 如果没有找到相似实体，返回空列表
        return unique_entities

class ProcessViewSet(viewsets.ViewSet):
    permission_classes = []
    def process_text(self, request):
        serializer = ProcessTextSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data['text']
            
            # 这里实现实体处理逻辑
            # 由于agent文件夹下的项目已经实现了具体的实体识别逻辑
            # 这里暂时返回模拟数据
            
            # 模拟实体识别结果
            entities = [
                {
                    "text": "smoky",
                    "label": "FLAVOR",
                    "start": 9,
                    "end": 14,
                    "processing_level": "lexicon_rule",
                    "confidence": 1.0,
                    "normalized_flavor": "aroma"
                },
                {
                    "text": "Margarita",
                    "label": "RECIPE",
                    "start": 15,
                    "end": 24,
                    "processing_level": "lexicon_rule",
                    "confidence": 1.0,
                    "entity_id": 723,
                    "normalized_name": "Margarita"
                }
            ]
            
            return Response({
                "text": text,
                "entities": entities,
                "processing_level": "lexicon_rule"
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def batch_process(self, request):
        serializer = BatchProcessSerializer(data=request.data)
        if serializer.is_valid():
            texts = serializer.validated_data['texts']
            results = []
            
            for text in texts:
                # 模拟批量处理结果
                entities = [
                    {
                        "text": "test",
                        "label": "TEST",
                        "start": 0,
                        "end": 4,
                        "processing_level": "lexicon_rule",
                        "confidence": 1.0
                    }
                ]
                results.append({
                    "text": text,
                    "entities": entities,
                    "processing_level": "lexicon_rule"
                })
            
            return Response(results, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
