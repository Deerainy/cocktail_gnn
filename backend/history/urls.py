from django.urls import path
from .views import HistoryViewSet

# 直接使用 path 定义路由
urlpatterns = [
    # 会话相关路由（必须放在 <str:pk> 前面，避免被错误匹配）
    path('sessions', HistoryViewSet.as_view({'get': 'sessions'}), name='sessions-list'),
    path('<str:pk>/session_detail', HistoryViewSet.as_view({'get': 'session_detail'}), name='session-detail'),

    # 历史记录列表和详情
    path('', HistoryViewSet.as_view({'get': 'list'}), name='history-list'),
    path('<str:pk>', HistoryViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='history-detail'),
]
