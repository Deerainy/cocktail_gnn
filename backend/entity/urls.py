from django.urls import path
from .views import AuthViewSet, EntityViewSet, ReviewViewSet, ProcessViewSet

urlpatterns = [
    # 认证相关
    path('auth/register', AuthViewSet.as_view({'post': 'register'})),
    path('auth/login', AuthViewSet.as_view({'post': 'login'})),
    path('auth/me', AuthViewSet.as_view({'get': 'me'})),
    
    # 实体管理
    path('', EntityViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<int:pk>', EntityViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('<int:pk>/aliases', EntityViewSet.as_view({'get': 'get_aliases', 'post': 'add_alias'})),
    path('aliases/<int:pk>', EntityViewSet.as_view({'delete': 'delete_alias'})),
    
    # 审核管理
    path('review_tasks', ReviewViewSet.as_view({'get': 'get_tasks'})),
    path('review_tasks/<str:pk>', ReviewViewSet.as_view({'get': 'get_task'})),
    path('review', ReviewViewSet.as_view({'post': 'submit_review'})),
    # 保留旧路径以保持向后兼容
    path('review/tasks', ReviewViewSet.as_view({'get': 'get_tasks'})),
    path('review/tasks/<str:pk>', ReviewViewSet.as_view({'get': 'get_task'})),
    
    # 实体处理
    path('process', ProcessViewSet.as_view({'post': 'process_text'})),
    path('batch_process', ProcessViewSet.as_view({'post': 'batch_process'})),
]