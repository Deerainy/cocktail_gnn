<template>
  <div class="admin-view">
    <div class="admin-header">
      <h1 class="admin-title">后台管理系统</h1>
      <div class="admin-user-info">
        <span>欢迎，{{ user?.username }}</span>
        <button class="btn-logout" @click="logout">退出登录</button>
      </div>
    </div>
    
    <div class="admin-content">
      <div class="admin-sidebar">
        <div class="sidebar-menu">
          <div class="menu-item active" @click="activeTab = 'review'">
            <span class="menu-icon">📋</span>
            <span>实体审核</span>
          </div>
          <div class="menu-item" @click="activeTab = 'dashboard'">
            <span class="menu-icon">📊</span>
            <span>系统概览</span>
          </div>
          <div class="menu-item" @click="activeTab = 'analysis'">
            <span class="menu-icon">📈</span>
            <span>数据分析</span>
          </div>
        </div>
      </div>
      
      <div class="admin-main">
        <div v-if="activeTab === 'review'" class="review-section">
          <h2 class="section-title">实体审核</h2>
          <div class="review-filters">
            <input 
              type="text" 
              v-model="searchQuery" 
              placeholder="搜索审核任务"
              class="search-input"
            >
            <select v-model="filterStatus" class="filter-select">
              <option value="all">全部状态</option>
              <option value="pending">待审核</option>
              <option value="processed">已处理</option>
            </select>
          </div>
          
          <div class="review-tasks">
            <div 
              v-for="task in filteredTasks" 
              :key="task.review_id"
              class="review-task-card"
              @click="selectTask(task)"
            >
              <div class="task-header">
                <span class="task-id">任务 ID: {{ task.review_id }}</span>
                <span class="task-status" :class="task.status">
                  {{ task.status === 'pending' ? '待审核' : '已处理' }}
                </span>
              </div>
              <div class="task-content">
                <p class="original-text">{{ task.original_text }}</p>
                <div class="entities-count">
                  需要审核: {{ (task.entities || []).length }} 个实体
                </div>
              </div>
              <div class="task-footer">
                <span class="task-time">{{ formatTime(task.timestamp) }}</span>
              </div>
            </div>
            
            <div v-if="filteredTasks.length === 0" class="empty-state">
              <span>暂无审核任务</span>
            </div>
          </div>
        </div>
        
        <div v-if="activeTab === 'dashboard'" class="dashboard-section">
          <h2 class="section-title">系统概览</h2>
          <div class="dashboard-cards">
            <div class="dashboard-card">
              <div class="card-title">总审核任务</div>
              <div class="card-value">{{ totalTasks }}</div>
            </div>
            <div class="dashboard-card">
              <div class="card-title">待审核任务</div>
              <div class="card-value">{{ pendingTasks }}</div>
            </div>
            <div class="dashboard-card">
              <div class="card-title">已处理任务</div>
              <div class="card-value">{{ processedTasks }}</div>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'analysis'" class="analysis-section">
          <h2 class="section-title">数据分析</h2>
          
          <!-- 加载状态 -->
          <div v-if="analysisLoading" class="analysis-loading">
            <div class="loading-spinner"></div>
            <p class="loading-text">加载数据分析数据中...</p>
          </div>
          
          <div v-else>
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-icon message-icon">
                  <MessageOutlined />
                </div>
                <div class="stat-content">
                  <div class="stat-title">总对话数</div>
                  <div class="stat-value">{{ stats.totalConversations }}</div>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon check-icon">
                  <CheckCircleOutlined />
                </div>
                <div class="stat-content">
                  <div class="stat-title">成功率</div>
                  <div class="stat-value">{{ stats.successRate.toFixed(2) }}%</div>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon clock-icon">
                  <ClockCircleOutlined />
                </div>
                <div class="stat-content">
                  <div class="stat-title">平均响应时间</div>
                  <div class="stat-value">{{ stats.avgResponseTime }}ms</div>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon user-icon">
                  <UserOutlined />
                </div>
                <div class="stat-content">
                  <div class="stat-title">活跃用户数</div>
                  <div class="stat-value">{{ stats.activeUsers }}</div>
                </div>
              </div>
            </div>

            <div class="charts-grid">
              <div class="chart-card">
                <div class="chart-header">
                  <h3 class="chart-title">对话趋势</h3>
                </div>
                <div ref="trendChartRef" class="chart-container" style="height: 300px; width: 100%"></div>
              </div>
              <div class="chart-card">
                <div class="chart-header">
                  <h3 class="chart-title">意图分布</h3>
                </div>
                <div ref="intentChartRef" class="chart-container" style="height: 300px; width: 100%"></div>
              </div>
              <div class="chart-card">
                <div class="chart-header">
                  <h3 class="chart-title">响应时间分布</h3>
                </div>
                <div ref="responseTimeChartRef" class="chart-container" style="height: 300px; width: 100%"></div>
              </div>
              <div class="chart-card">
                <div class="chart-header">
                  <h3 class="chart-title">实体识别统计</h3>
                </div>
                <div ref="entityChartRef" class="chart-container" style="height: 300px; width: 100%"></div>
              </div>
            </div>
          </div>

          <a-card title="详细数据" class="detail-card">
            <a-tabs v-model:activeKey="analysisActiveTab">
              <a-tab-pane key="conversations" tab="对话记录">
                <a-table
                  :dataSource="conversationsData"
                  :columns="conversationColumns"
                  :pagination="conversationPagination"
                  :loading="loading"
                  @change="handleConversationTableChange"
                  rowKey="id"
                >
                  <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'status'">
                      <a-tag :color="getStatusColor(record.status)">
                        {{ getStatusText(record.status) }}
                      </a-tag>
                    </template>
                    <template v-else-if="column.key === 'responseTime'">
                      {{ record.response_time }}ms
                    </template>
                  </template>
                </a-table>
              </a-tab-pane>
              <a-tab-pane key="errors" tab="错误记录">
                <a-table
                  :dataSource="errorsData"
                  :columns="errorColumns"
                  :pagination="errorPagination"
                  :loading="loading"
                  @change="handleErrorTableChange"
                  rowKey="id"
                >
                  <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'action'">
                      <a-button type="link" size="small" @click="viewErrorDetail(record)">
                        查看详情
                      </a-button>
                    </template>
                  </template>
                </a-table>
              </a-tab-pane>
            </a-tabs>
          </a-card>

          <a-modal
            v-model:open="errorDetailVisible"
            title="错误详情"
            width="600px"
            :footer="null"
          >
            <div v-if="currentErrorDetail" class="error-detail-content">
              <a-descriptions bordered :column="1">
                <a-descriptions-item label="错误ID">
                  {{ currentErrorDetail.id }}
                </a-descriptions-item>
                <a-descriptions-item label="错误类型">
                  <a-tag color="error">{{ currentErrorDetail.error_type }}</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="错误信息">
                  {{ currentErrorDetail.error_message }}
                </a-descriptions-item>
                <a-descriptions-item label="发生时间">
                  {{ formatTime(currentErrorDetail.timestamp) }}
                </a-descriptions-item>
                <a-descriptions-item label="用户输入">
                  {{ currentErrorDetail.user_input }}
                </a-descriptions-item>
                <a-descriptions-item label="堆栈信息">
                  <pre class="stack-trace">{{ currentErrorDetail.stack_trace }}</pre>
                </a-descriptions-item>
              </a-descriptions>
            </div>
          </a-modal>
        </div>
      </div>
    </div>
    
    <!-- 审核详情模态框 -->
    <div v-if="selectedTask" class="review-modal" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>审核任务详情</h3>
          <button class="close-btn" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="task-info">
            <p><strong>任务 ID:</strong> {{ selectedTask.review_id }}</p>
            <p><strong>原始文本:</strong> {{ selectedTask.original_text }}</p>
            <p><strong>时间:</strong> {{ formatTime(selectedTask.timestamp) }}</p>
          </div>
          
          <div class="entities-list">
            <h4>需要审核的实体</h4>
            <div 
              v-for="entity in (selectedTask.entities || [])" 
              :key="entity.entity_id || Math.random()"
              class="entity-item"
            >
              <div class="entity-header">
                <span class="entity-text">{{ entity.text }}</span>
                <span class="entity-label" :class="entity.label.toLowerCase()">
                  {{ entity.label }}
                </span>
              </div>
              <div class="entity-candidates">
                <h5>候选实体</h5>
                <div class="candidates-list">
                  <div 
                    v-for="(candidate, index) in (entity.candidates || [])" 
                    :key="index"
                    class="candidate-item"
                    :class="{ selected: entity.selectedCandidate === index }"
                    @click="selectCandidate(entity, index)"
                  >
                    <span class="candidate-text">{{ candidate.text }}</span>
                    <span class="candidate-confidence">{{ (candidate.confidence * 100).toFixed(1) }}%</span>
                  </div>
                </div>
              </div>
              <div class="entity-actions">
                <label class="checkbox-label">
                  <input 
                    type="checkbox" 
                    v-model="entity.addAsAlias"
                  >
                  添加为别名
                </label>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeModal">取消</button>
          <button class="btn-primary" @click="submitReview">提交审核</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getReviewTasks, submitReview } from '@/api/entityApi';
import { getHistoryList, getSessions, getAnalysisStats } from '@/api/historyApi';
import * as echarts from 'echarts';
import {
  MessageOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  UserOutlined
} from '@ant-design/icons-vue';

export default {
  name: 'AdminView',
  components: {
    MessageOutlined,
    CheckCircleOutlined,
    ClockCircleOutlined,
    UserOutlined
  },
  data() {
    return {
      user: null,
      activeTab: 'review',
      analysisActiveTab: 'conversations',
      searchQuery: '',
      filterStatus: 'all',
      selectedTask: null,
      errorDetailVisible: false,
      currentErrorDetail: null,
      reviewTasks: [],
      loading: false,
      error: null,
      
      // 数据分析相关
      stats: {
        totalConversations: 0,
        successRate: 0,
        avgResponseTime: 0,
        activeUsers: 0
      },
      analysisLoading: false,
      chartData: {
        trendData: {
          labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
          conversations: [120, 132, 101, 134, 90, 230, 210],
          success: [110, 120, 91, 124, 85, 220, 200]
        },
        intentData: [
          {"value": 1048, "name": "查询配方"},
          {"value": 735, "name": "推荐组合"},
          {"value": 580, "name": "调整风味"},
          {"value": 484, "name": "生成创新"},
          {"value": 300, "name": "其他"}
        ],
        responseTimeData: {
          labels: ['<500ms', '500-1000ms', '1000-2000ms', '2000-3000ms', '>3000ms'],
          data: [320, 200, 150, 80, 70]
        },
        entityData: [
          {"value": 256, "name": "酒类"},
          {"value": 189, "name": "水果"},
          {"value": 156, "name": "调味品"},
          {"value": 123, "name": "饮料"},
          {"value": 98, "name": "其他"}
        ]
      },
      // 图表实例
      chartInstances: {
        trend: null,
        intent: null,
        responseTime: null,
        entity: null
      },
      conversationsData: [],
      conversationPagination: {
        current: 1,
        pageSize: 10,
        total: 820,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total) => `共 ${total} 条记录`
      },
      errorsData: [],
      errorPagination: {
        current: 1,
        pageSize: 10,
        total: 35,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total) => `共 ${total} 条记录`
      }
    };
  },
  watch: {
    activeTab(newTab) {
      if (newTab === 'analysis') {
        // 切换到数据分析标签时，确保图表初始化
        this.$nextTick(() => {
          this.initTrendChart();
          this.initIntentChart();
          this.initResponseTimeChart();
          this.initEntityChart();
        });
      }
    }
  },
  computed: {
    filteredTasks() {
      return this.reviewTasks.filter(task => {
        const matchesSearch = task.original_text.toLowerCase().includes(this.searchQuery.toLowerCase());
        const matchesStatus = this.filterStatus === 'all' || task.status === this.filterStatus;
        return matchesSearch && matchesStatus;
      });
    },
    totalTasks() {
      return this.reviewTasks.length;
    },
    pendingTasks() {
      return this.reviewTasks.filter(task => task.status === 'pending').length;
    },
    processedTasks() {
      return this.reviewTasks.filter(task => task.status === 'processed').length;
    },
    conversationColumns() {
      return [
        {
          title: '会话ID',
          dataIndex: 'session_id',
          key: 'session_id',
          width: '25%'
        },
        {
          title: '用户输入',
          dataIndex: 'user_input',
          key: 'user_input',
          width: '35%',
          ellipsis: true
        },
        {
          title: '响应时间',
          dataIndex: 'response_time',
          key: 'responseTime',
          width: '15%'
        },
        {
          title: '状态',
          dataIndex: 'status',
          key: 'status',
          width: '10%'
        },
        {
          title: '时间',
          dataIndex: 'timestamp',
          key: 'timestamp',
          width: '15%'
        }
      ];
    },
    errorColumns() {
      return [
        {
          title: '错误ID',
          dataIndex: 'id',
          key: 'id',
          width: '20%'
        },
        {
          title: '错误类型',
          dataIndex: 'error_type',
          key: 'error_type',
          width: '25%'
        },
        {
          title: '错误信息',
          dataIndex: 'error_message',
          key: 'error_message',
          width: '30%',
          ellipsis: true
        },
        {
          title: '时间',
          dataIndex: 'timestamp',
          key: 'timestamp',
          width: '15%'
        },
        {
          title: '操作',
          key: 'action',
          width: '10%',
          align: 'center'
        }
      ];
    }
  },
  mounted() {
    this.loadUser();
    this.loadReviewTasks();
    this.loadConversations();
    this.loadErrors();
    this.loadAnalysisStats();
    
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize);
    
    // 销毁图表实例，避免内存泄漏
    if (this.chartInstances.trend) this.chartInstances.trend.dispose();
    if (this.chartInstances.intent) this.chartInstances.intent.dispose();
    if (this.chartInstances.responseTime) this.chartInstances.responseTime.dispose();
    if (this.chartInstances.entity) this.chartInstances.entity.dispose();
  },
  methods: {
    async loadReviewTasks() {
      this.loading = true;
      this.error = null;
      try {
        const response = await getReviewTasks();
        // 确保reviewTasks始终是一个数组
        this.reviewTasks = response && Array.isArray(response.tasks) ? response.tasks : [];
        
        // 为每个实体初始化selectedCandidate和addAsAlias字段，并将created_at重命名为timestamp
        this.reviewTasks.forEach(task => {
          // 将created_at重命名为timestamp
          if (task.created_at) {
            task.timestamp = task.created_at;
          }
          
          if (task.entities && Array.isArray(task.entities)) {
            task.entities.forEach(entity => {
              if (entity.candidates && entity.candidates.length > 0 && entity.selectedCandidate === undefined) {
                entity.selectedCandidate = 0;
              }
              if (entity.addAsAlias === undefined) {
                entity.addAsAlias = false;
              }
            });
          }
        });
      } catch (err) {
        this.error = '获取审核任务失败';
        console.error('加载审核任务失败:', err);
        // 使用模拟数据作为备用
        this.reviewTasks = [
          {
            review_id: 'uuid-123',
            timestamp: '2026-04-01T10:00:00Z',
            original_text: 'I want a Margareta with lime juice',
            status: 'pending',
            entities: [
              {
                entity_id: 'entity-456',
                text: 'Margareta',
                label: 'RECIPE',
                start: 9,
                end: 17,
                processing_level: 'fuzzy_match',
                confidence: 0.8,
                candidates: [
                  {
                    text: 'Margarita',
                    label: 'RECIPE',
                    confidence: 0.95,
                    source: 'fuzzy'
                  },
                  {
                    text: 'Margherita',
                    label: 'RECIPE',
                    confidence: 0.7,
                    source: 'fuzzy'
                  }
                ],
                context: 'I want a Margareta with lime juice',
                selectedCandidate: 0,
                addAsAlias: true
              }
            ]
          },
          {
            review_id: 'uuid-124',
            timestamp: '2026-04-01T09:30:00Z',
            original_text: '给我一杯龙舌兰酒加青柠',
            status: 'processed',
            entities: [
              {
                entity_id: 'entity-457',
                text: '龙舌兰酒',
                label: 'INGREDIENT',
                start: 3,
                end: 7,
                processing_level: 'lexicon_rule',
                confidence: 1.0,
                candidates: [],
                context: '给我一杯龙舌兰酒加青柠'
              }
            ]
          }
        ];
      } finally {
        this.loading = false;
      }
    },
    loadUser() {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        this.user = JSON.parse(userStr);
      } else {
        // 未登录，跳转到首页
        this.$router.push('/');
      }
    },
    logout() {
      localStorage.removeItem('user');
      this.$router.push('/');
    },
    selectTask(task) {
      // 深拷贝任务对象，避免直接修改原数据
      this.selectedTask = JSON.parse(JSON.stringify(task));
      // 初始化选中状态
      console.log('selectTask called with task:', task);
      console.log('selectedTask.entities:', this.selectedTask.entities);
      if (this.selectedTask.entities) {
        console.log('selectedTask.entities.length:', this.selectedTask.entities.length);
        this.selectedTask.entities.forEach((entity, index) => {
          console.log('Entity', index, ':', entity);
          if (!entity.selectedCandidate) {
            entity.selectedCandidate = 0;
          }
          if (entity.addAsAlias === undefined) {
            entity.addAsAlias = false;
          }
          // 模拟候选实体数据
          console.log('Entity', index, 'candidates:', entity.candidates);
          console.log('Entity', index, 'candidates length:', entity.candidates ? entity.candidates.length : 'undefined');
          console.log('Entity', index, 'candidates type:', typeof entity.candidates);
          console.log('Entity', index, 'candidates is array:', Array.isArray(entity.candidates));
          if (entity.candidates && Array.isArray(entity.candidates)) {
            console.log('Entity', index, 'first candidate:', entity.candidates[0]);
            console.log('Entity', index, 'candidate 0 text:', entity.candidates[0] ? entity.candidates[0].text : 'undefined');
            console.log('Entity', index, 'candidate 0 confidence:', entity.candidates[0] ? entity.candidates[0].confidence : 'undefined');
          }
          if (!entity.candidates || !Array.isArray(entity.candidates) || entity.candidates.length === 0) {
            console.log('Adding mock candidates for entity', index);
            entity.candidates = [
              {
                text: entity.text,
                label: entity.label,
                confidence: 0.8,
                source: 'current'
              },
              {
                text: '模拟候选实体 1',
                label: entity.label,
                confidence: 0.7,
                source: 'entity'
              },
              {
                text: '模拟候选实体 2',
                label: entity.label,
                confidence: 0.6,
                source: 'alias'
              }
            ];
            console.log('Entity', index, 'candidates after adding:', entity.candidates);
          } else {
            console.log('Entity', index, 'already has candidates, length:', entity.candidates.length);
            // 确保每个候选实体都有text和confidence字段
            entity.candidates = entity.candidates.map(candidate => {
              return {
                text: candidate.text || '未知候选实体',
                label: candidate.label || entity.label,
                confidence: candidate.confidence || 0.5,
                source: candidate.source || 'unknown'
              };
            });
            console.log('Entity', index, 'candidates after processing:', entity.candidates);
          }
        });
      } else {
        // 如果没有entities，初始化一个空数组
        console.log('No entities found, initializing empty array');
        this.selectedTask.entities = [];
      }
      // 打印selectedTask对象
      console.log('Final selectedTask:', this.selectedTask);
    },
    closeModal() {
      this.selectedTask = null;
    },
    selectCandidate(entity, index) {
      entity.selectedCandidate = index;
    },
    async submitReview() {
      if (!this.selectedTask) return;
      
      // 检查是否有实体可以审核
      if (!this.selectedTask.entities || this.selectedTask.entities.length === 0) {
        alert('没有可审核的实体');
        return;
      }
      
      try {
        // 遍历所有实体，提交审核
        for (const entity of this.selectedTask.entities) {
          // 检查候选实体
          if (!entity.candidates || entity.candidates.length === 0) {
            alert('没有候选实体可供选择');
            return;
          }
          
          const reviewData = {
            review_id: this.selectedTask.review_id,
            entity_id: entity.entity_id || 'unknown',
            original_text: entity.text || '',
            approved_candidate: entity.candidates[entity.selectedCandidate || 0],
            add_as_alias: entity.addAsAlias || false
          };
          
          // 调用API提交审核
          await submitReview(reviewData);
        }
        
        // 更新任务状态
        const taskIndex = this.reviewTasks.findIndex(t => t.review_id === this.selectedTask.review_id);
        if (taskIndex !== -1) {
          this.reviewTasks[taskIndex].status = 'processed';
        }
        
        // 关闭模态框
        this.closeModal();
        
        // 显示成功消息
        alert('审核提交成功');
      } catch (error) {
        console.error('提交审核失败:', error);
        alert('提交审核失败，请重试');
      }
    },
    formatTime(timestamp) {
      const date = new Date(timestamp);
      return date.toLocaleString();
    },
    
    // 数据分析相关方法
    async loadConversations() {
      try {
        const params = {
          page: this.conversationPagination.current,
          page_size: this.conversationPagination.pageSize
        };
        const response = await getHistoryList(params);
        if (response.success && response.data) {
          this.conversationsData = response.data.list.map((item, index) => ({
            id: index + 1,
            session_id: item.session_id || `session_${index + 1}`,
            user_input: item.user_input || '无用户输入',
            response_time: item.response_time || Math.floor(Math.random() * 2000) + 500,
            status: item.status || 'success',
            timestamp: item.created_at || new Date().toISOString()
          }));
          this.conversationPagination.total = response.data.total || 0;
        }
      } catch (error) {
        console.error('加载对话记录失败:', error);
        // 使用模拟数据作为备用
        this.conversationsData = Array.from({ length: 10 }, (_, i) => ({
          id: i + 1,
          session_id: `session_${i + 1}`,
          user_input: `用户输入示例 ${i + 1}`,
          response_time: Math.floor(Math.random() * 2000) + 500,
          status: Math.random() > 0.1 ? 'success' : 'error',
          timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString()
        }));
      }
    },
    async loadErrors() {
      try {
        const response = await getHistoryList({ page: 1, page_size: 100 });
        if (response.success && response.data) {
          // 过滤出状态为 error 的记录
          const errorRecords = response.data.list.filter(item => item.status === 'error');
          this.errorsData = errorRecords.map((item, index) => ({
            id: `error_${index + 1}`,
            error_type: 'API错误', // 简化处理，实际项目中可以根据错误信息解析
            error_message: item.error_message || '未知错误',
            timestamp: item.created_at || new Date().toISOString(),
            user_input: item.user_input || '无用户输入',
            stack_trace: item.error_stack || '堆栈信息...'
          }));
          this.errorPagination.total = errorRecords.length || 0;
        }
      } catch (error) {
        console.error('加载错误记录失败:', error);
        // 使用模拟数据作为备用
        this.errorsData = Array.from({ length: 10 }, (_, i) => ({
          id: `error_${i + 1}`,
          error_type: ['API错误', '数据库错误', '超时错误', '参数错误'][i % 4],
          error_message: `错误信息示例 ${i + 1}`,
          timestamp: new Date(Date.now() - Math.random() * 86400000).toISOString(),
          user_input: `用户输入示例 ${i + 1}`,
          stack_trace: '堆栈信息...'
        }));
      }
    },
    async loadAnalysisStats() {
      this.analysisLoading = true;
      try {
        const response = await getAnalysisStats();
        if (response.success && response.data) {
          this.stats = {
            totalConversations: response.data.totalConversations || 820,
            successRate: response.data.successRate || 95.67,
            avgResponseTime: response.data.avgResponseTime || 856,
            activeUsers: response.data.activeUsers || Math.floor(Math.random() * 50) + 100 // 模拟活跃用户数
          };
          
          // 更新图表数据，确保只在数据存在且有效时才更新
          if (response.data.trendData && typeof response.data.trendData === 'object') {
            this.chartData.trendData = {
              labels: response.data.trendData.labels || ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
              conversations: response.data.trendData.conversations || [120, 132, 101, 134, 90, 230, 210],
              success: response.data.trendData.success || [110, 120, 91, 124, 85, 220, 200]
            };
          }
          if (response.data.intentData && Array.isArray(response.data.intentData)) {
            this.chartData.intentData = response.data.intentData;
          }
          if (response.data.responseTimeData && typeof response.data.responseTimeData === 'object') {
            this.chartData.responseTimeData = {
              labels: response.data.responseTimeData.labels || ['<500ms', '500-1000ms', '1000-2000ms', '2000-3000ms', '>3000ms'],
              data: response.data.responseTimeData.data || [320, 200, 150, 80, 70]
            };
          }
          if (response.data.entityData && Array.isArray(response.data.entityData)) {
            this.chartData.entityData = response.data.entityData;
          }
        }
      } catch (error) {
        console.error('加载数据分析统计数据失败:', error);
        // 使用模拟数据作为备用
        this.stats = {
          totalConversations: 820,
          successRate: 95.67,
          avgResponseTime: 856,
          activeUsers: Math.floor(Math.random() * 50) + 100 // 模拟活跃用户数
        };
        // 确保图表数据有默认值
        this.chartData = {
          trendData: {
            labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
            conversations: [120, 132, 101, 134, 90, 230, 210],
            success: [110, 120, 91, 124, 85, 220, 200]
          },
          intentData: [
            {"value": 1048, "name": "查询配方"},
            {"value": 735, "name": "推荐组合"},
            {"value": 580, "name": "调整风味"},
            {"value": 484, "name": "生成创新"},
            {"value": 300, "name": "其他"}
          ],
          responseTimeData: {
            labels: ['<500ms', '500-1000ms', '1000-2000ms', '2000-3000ms', '>3000ms'],
            data: [320, 200, 150, 80, 70]
          },
          entityData: [
            {"value": 256, "name": "酒类"},
            {"value": 189, "name": "水果"},
            {"value": 156, "name": "调味品"},
            {"value": 123, "name": "饮料"},
            {"value": 98, "name": "其他"}
          ]
        };
      } finally {
        this.analysisLoading = false;
        // 数据加载完成后初始化图表
        this.$nextTick(() => {
          this.initTrendChart();
          this.initIntentChart();
          this.initResponseTimeChart();
          this.initEntityChart();
        });
      }
    },
    handleConversationTableChange(pag) {
      this.conversationPagination.current = pag.current;
      this.conversationPagination.pageSize = pag.pageSize;
      this.loadConversations();
    },
    handleErrorTableChange(pag) {
      this.errorPagination.current = pag.current;
      this.errorPagination.pageSize = pag.pageSize;
      this.loadErrors();
    },
    viewErrorDetail(record) {
      this.currentErrorDetail = record;
      this.errorDetailVisible = true;
    },
    getStatusColor(status) {
      switch (status) {
        case 'success': return 'success';
        case 'error': return 'error';
        case 'running': return 'processing';
        default: return 'default';
      }
    },
    getStatusText(status) {
      switch (status) {
        case 'success': return '成功';
        case 'error': return '失败';
        case 'running': return '处理中';
        default: return '未知';
      }
    },
    
    // 图表初始化方法
    initTrendChart() {
      const trendChartRef = this.$refs.trendChartRef;
      if (!trendChartRef) return;
      
      // 销毁旧的图表实例
      if (this.chartInstances.trend) {
        this.chartInstances.trend.dispose();
      }
      
      // 创建新的图表实例
      const chart = echarts.init(trendChartRef);
      this.chartInstances.trend = chart;
      
      const option = {
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          data: ['对话数', '成功数']
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: this.chartData.trendData.labels
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            name: '对话数',
            type: 'line',
            smooth: true,
            data: this.chartData.trendData.conversations,
            itemStyle: {
              color: '#1890ff'
            }
          },
          {
            name: '成功数',
            type: 'line',
            smooth: true,
            data: this.chartData.trendData.success,
            itemStyle: {
              color: '#52c41a'
            }
          }
        ]
      };

      chart.setOption(option);
    },
    initIntentChart() {
      const intentChartRef = this.$refs.intentChartRef;
      if (!intentChartRef) return;
      
      // 销毁旧的图表实例
      if (this.chartInstances.intent) {
        this.chartInstances.intent.dispose();
      }
      
      // 创建新的图表实例
      const chart = echarts.init(intentChartRef);
      this.chartInstances.intent = chart;
      
      const option = {
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            name: '意图分布',
            type: 'pie',
            radius: '50%',
            data: this.chartData.intentData,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      };

      chart.setOption(option);
    },
    initResponseTimeChart() {
      const responseTimeChartRef = this.$refs.responseTimeChartRef;
      if (!responseTimeChartRef) return;
      
      // 销毁旧的图表实例
      if (this.chartInstances.responseTime) {
        this.chartInstances.responseTime.dispose();
      }
      
      // 创建新的图表实例
      const chart = echarts.init(responseTimeChartRef);
      this.chartInstances.responseTime = chart;
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: this.chartData.responseTimeData.labels
        },
        yAxis: {
          type: 'value',
          name: '数量'
        },
        series: [
          {
            name: '响应时间',
            type: 'bar',
            data: this.chartData.responseTimeData.data,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#83bff6' },
                { offset: 0.5, color: '#188df0' },
                { offset: 1, color: '#188df0' }
              ])
            }
          }
        ]
      };

      chart.setOption(option);
    },
    initEntityChart() {
      const entityChartRef = this.$refs.entityChartRef;
      if (!entityChartRef) return;
      
      // 销毁旧的图表实例
      if (this.chartInstances.entity) {
        this.chartInstances.entity.dispose();
      }
      
      // 创建新的图表实例
      const chart = echarts.init(entityChartRef);
      this.chartInstances.entity = chart;
      
      // 从 chartData.entityData 中提取数据并转换为柱状图格式
      const entityLabels = this.chartData.entityData.map(item => item.name);
      const entityValues = this.chartData.entityData.map(item => item.value);
      
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'value',
          name: '识别次数'
        },
        yAxis: {
          type: 'category',
          data: entityLabels
        },
        series: [
          {
            name: '实体识别',
            type: 'bar',
            data: entityValues,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
                { offset: 0, color: '#83bff6' },
                { offset: 0.5, color: '#188df0' },
                { offset: 1, color: '#188df0' }
              ])
            }
          }
        ]
      };

      chart.setOption(option);
    },
    handleResize() {
      // 图表大小调整
      if (this.chartInstances.trend) this.chartInstances.trend.resize();
      if (this.chartInstances.intent) this.chartInstances.intent.resize();
      if (this.chartInstances.responseTime) this.chartInstances.responseTime.resize();
      if (this.chartInstances.entity) this.chartInstances.entity.resize();
    }
  }
};
</script>

<style scoped>
.admin-view {
  min-height: 100vh;
  background: var(--color-bg-primary);
  padding-top: 80px;
}

.admin-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: rgba(20, 15, 10, 0.95);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 100;
  backdrop-filter: blur(10px);
}

.admin-title {
  color: var(--color-gold-200);
  font-family: var(--font-display);
  font-size: 1.5rem;
  margin: 0;
}

.admin-user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.admin-user-info span {
  color: var(--color-text-secondary);
}

.btn-logout {
  padding: 0.5rem 1rem;
  background: transparent;
  color: var(--color-gold-300);
  border: 1px solid var(--color-gold-500);
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-logout:hover {
  background: rgba(212, 175, 55, 0.1);
}

.admin-content {
  display: flex;
  min-height: calc(100vh - 80px);
}

.admin-sidebar {
  width: 250px;
  background: rgba(30, 25, 20, 0.9);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  padding: 2rem 0;
}

.sidebar-menu {
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 2rem;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.menu-item:hover {
  background: rgba(212, 175, 55, 0.1);
  color: var(--color-gold-200);
}

.menu-item.active {
  background: rgba(212, 175, 55, 0.15);
  color: var(--color-gold-200);
  border-left-color: var(--color-gold-400);
}

.menu-icon {
  font-size: 1.25rem;
}

.admin-main {
  flex: 1;
  padding: 2rem;
}

.section-title {
  color: var(--color-gold-200);
  font-family: var(--font-display);
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
}

.review-filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.search-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-primary);
  font-size: 1rem;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-gold-400);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
}

.filter-select {
  padding: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-primary);
  font-size: 1rem;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-gold-400);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.1);
}

.review-tasks {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1rem;
}

.review-task-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.review-task-card:hover {
  border-color: var(--color-gold-400);
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.1);
  transform: translateY(-2px);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.task-id {
  font-size: 0.9rem;
  color: var(--color-text-tertiary);
}

.task-status {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.task-status.pending {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

.task-status.processed {
  background: rgba(40, 167, 69, 0.2);
  color: #28a745;
}

.original-text {
  color: var(--color-text-primary);
  margin: 0 0 1rem 0;
  line-height: 1.5;
}

.entities-count {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin-bottom: 1rem;
}

.task-footer {
  font-size: 0.8rem;
  color: var(--color-text-tertiary);
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 4rem 2rem;
  color: var(--color-text-tertiary);
  background: rgba(255, 255, 255, 0.05);
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: 8px;
}

.dashboard-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.dashboard-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 2rem;
  text-align: center;
  transition: all 0.3s ease;
}

.dashboard-card:hover {
  border-color: var(--color-gold-400);
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.1);
  transform: translateY(-2px);
}

.card-title {
  color: var(--color-text-secondary);
  font-size: 1rem;
  margin-bottom: 1rem;
}

.card-value {
  color: var(--color-gold-200);
  font-size: 2rem;
  font-weight: 600;
  font-family: var(--font-display);
}

/* 数据分析部分样式 */
.analysis-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-3xl);
  margin-bottom: var(--spacing-2xl);
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.85) 0%, rgba(26, 20, 16, 0.92) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: var(--color-shadow-soft);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border-subtle);
  border-top: 3px solid var(--color-gold-400);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--spacing-md);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: var(--color-text-secondary);
  font-family: var(--font-body);
  font-size: 14px;
  letter-spacing: 0.05em;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-2xl);
}

.stat-card {
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.85) 0%, rgba(26, 20, 16, 0.92) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: var(--color-shadow-soft);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: var(--spacing-xl);
  transition: all var(--transition-normal);
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent, 
    var(--color-gold-400), 
    transparent
  );
}

.stat-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--color-shadow-soft), var(--color-shadow-gold);
  transform: translateY(-2px);
}

.stat-icon {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  flex-shrink: 0;
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.05) 100%);
  color: var(--color-gold-300);
  border: 1px solid var(--color-border-subtle);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.1);
}

.stat-content {
  flex: 1;
}

.stat-title {
  color: var(--color-text-secondary);
  font-size: 14px;
  margin-bottom: var(--spacing-sm);
  font-family: var(--font-body);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.stat-value {
  font-family: var(--font-display);
  font-size: 2.5rem;
  font-weight: 600;
  background: linear-gradient(135deg, var(--color-gold-200) 0%, var(--color-gold-400) 50%, var(--color-gold-500) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.02em;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(550px, 1fr));
  gap: var(--spacing-xl);
  margin-bottom: var(--spacing-2xl);
}

.chart-card {
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.85) 0%, rgba(26, 20, 16, 0.92) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: var(--color-shadow-soft);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: var(--spacing-xl);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.chart-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent, 
    var(--color-gold-400), 
    transparent
  );
}

.chart-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--color-shadow-soft), var(--color-shadow-gold);
  transform: translateY(-2px);
}

.chart-header {
  margin-bottom: var(--spacing-lg);
  border-bottom: 1px solid var(--color-border-subtle);
  padding-bottom: var(--spacing-md);
}

.chart-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-gold-300);
  letter-spacing: 0.05em;
  margin: 0;
}

.chart-container {
  height: 320px;
  width: 100%;
}

.detail-card {
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.85) 0%, rgba(26, 20, 16, 0.92) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: var(--color-shadow-soft);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: var(--spacing-xl);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

.detail-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent, 
    var(--color-gold-400), 
    transparent
  );
}

.detail-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--color-shadow-soft), var(--color-shadow-gold);
}

.review-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: rgba(20, 15, 10, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  max-width: 800px;
  width: 100%;
  max-height: 80vh;
  overflow-y: auto;
  margin: 2rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 2rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  color: var(--color-gold-200);
  font-family: var(--font-display);
  font-size: 1.25rem;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: 1.5rem;
  cursor: pointer;
  transition: color 0.3s ease;
}

.close-btn:hover {
  color: var(--color-gold-200);
}

.modal-body {
  padding: 2rem;
}

.task-info {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.task-info p {
  margin: 0.5rem 0;
  color: var(--color-text-secondary);
}

.task-info strong {
  color: var(--color-gold-200);
}

.entities-list h4 {
  color: var(--color-gold-200);
  font-family: var(--font-display);
  margin-bottom: 1rem;
}

.entity-item {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

.entity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.entity-text {
  color: var(--color-text-primary);
  font-weight: 600;
}

.entity-label {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.entity-label.recipe {
  background: rgba(40, 167, 69, 0.2);
  color: #28a745;
}

.entity-label.ingredient {
  background: rgba(0, 123, 255, 0.2);
  color: #007bff;
}

.entity-label.canonical {
  background: rgba(123, 31, 162, 0.2);
  color: #7b1fa2;
}

.entity-label.flavor {
  background: rgba(255, 159, 64, 0.2);
  color: #ff9f43;
}

.entity-label.role {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
}

.entity-label.noun {
  background: rgba(108, 117, 125, 0.2);
  color: #6c757d;
}

.entity-candidates h5 {
  color: var(--color-text-secondary);
  margin-bottom: 1rem;
}

.candidates-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.candidate-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.candidate-item:hover {
  border-color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.1);
}

.candidate-item.selected {
  border-color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.15);
}

.candidate-text {
  color: var(--color-text-primary);
}

.candidate-confidence {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
}

.entity-actions {
  margin-top: 1rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  accent-color: var(--color-gold-400);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: var(--color-gold-500);
  color: var(--color-bg-primary);
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary:hover {
  background: var(--color-gold-400);
  transform: translateY(-1px);
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: transparent;
  color: var(--color-gold-300);
  border: 1px solid var(--color-gold-500);
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(212, 175, 55, 0.1);
}
</style>