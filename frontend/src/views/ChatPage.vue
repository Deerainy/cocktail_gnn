<template>
  <div class="chat-page">
    <div class="chat-container">
      <div class="chat-main">
        <div class="chat-content-container">
          <div class="chat-tabs-sidebar">
            <div class="chat-tab-buttons">
              <div 
                class="chat-tab-button" 
                :class="{ active: activeTab === 'chat' }"
                @click="activeTab = 'chat'"
              >
                智能对话
              </div>
              <div 
                class="chat-tab-button" 
                :class="{ active: activeTab === 'history' }"
                @click="activeTab = 'history'"
              >
                历史记录
              </div>
            </div>
          </div>
          <div class="chat-content-main">
            <div v-if="activeTab === 'chat'" class="chat-content">
                <ChatHistory :messages="messages" ref="chatHistoryRef" />
                <div class="chat-input-section">
                  <ChatInput
                    :loading="loading"
                    @send="handleSend"
                  />
                </div>
            </div>
            
            <div v-else-if="activeTab === 'history'" class="history-content">
              <a-card class="history-list-card">
                <template #title>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>历史对话</span>
                    <a-button type="primary" size="small" @click="loadSessions">
                      刷新
                    </a-button>
                  </div>
                </template>
                <div v-if="historyLoading" style="text-align: center; padding: 40px;">
                  <a-spin size="large" />
                </div>
                <div v-else-if="sessions.length === 0" style="text-align: center; padding: 40px;">
                  <a-empty description="暂无历史对话" />
                </div>
                <div v-else class="sessions-list">
                  <a-list :dataSource="sessions" item-layout="vertical" size="large">
                    <template #renderItem="{ item }">
                      <a-list-item :style="{ cursor: 'pointer', position: 'relative' }" @click="loadSession(item.session_id)">
                        <a-list-item-meta>
                          <template #title>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                              <span style="font-weight: 600; color: #ffffff;">
                                {{ item.last_user_input || '新对话' }}
                              </span>

                            </div>
                          </template>
                          <template #description>
                            <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                              <span style="color: #cccccc; font-size: 13px;">
                                {{ item.last_system_response ? item.last_system_response.substring(0, 50) + '...' : '无回复' }}
                              </span>
                              <span style="color: #999999; font-size: 13px;">
                                {{ formatTime(item.last_message_time) }}
                              </span>
                            </div>
                          </template>
                        </a-list-item-meta>
                        <div style="position: absolute; right: 16px; top: 30%; transform: translateY(-50%); display: flex; gap: 8px;" @click.stop>
                          <a-button type="link" size="small" @click.stop="viewSessionDetail(item)" style="color: #d4af37;">
                            详情
                          </a-button>
                          <a-popconfirm
                            title="确定要删除这条对话吗？"
                            @confirm="deleteSession(item.session_id)"
                          >
                            <a-button type="link" size="small" danger style="color: #ff4d4f;" @click.stop>
                              删除
                            </a-button>
                          </a-popconfirm>
                        </div>
                      </a-list-item>
                    </template>
                  </a-list>
                </div>
              </a-card>
            </div>
          </div>
        </div>
      </div>
      <div class="chat-sidebar">
        <div class="history-sidebar">
          <h4>对话统计</h4>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-number">{{ totalHistory }}</div>
              <div class="stat-label">总对话</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ successHistory }}</div>
              <div class="stat-label">成功</div>
            </div>
            <div class="stat-item">
              <div class="stat-number">{{ errorHistory }}</div>
              <div class="stat-label">失败</div>
            </div>
          </div>

          <div v-if="currentTrace" class="trace-section">
            <h4>处理流程</h4>
            <ProcessFlow :trace="currentTrace" />
          </div>
          <a-empty v-else description="发送消息后查看处理流程" />
        </div>
      </div>
    </div>

    <a-modal
      v-model:open="detailVisible"
      title="对话详情"
      width="800px"
      :footer="null"
    >
      <div v-if="currentDetail" class="detail-content">
        <a-descriptions bordered :column="2">
          <a-descriptions-item label="会话ID">
            {{ currentDetail.session_id }}
          </a-descriptions-item>
          <a-descriptions-item label="时间">
            {{ formatTime(currentDetail.timestamp) }}
          </a-descriptions-item>
          <a-descriptions-item label="状态" :span="2">
            <a-tag :color="getStatusColor(currentDetail.status)">
              {{ getStatusText(currentDetail.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="用户输入" :span="2">
            {{ currentDetail.user_input }}
          </a-descriptions-item>
          <a-descriptions-item label="系统响应" :span="2">
            {{ currentDetail.system_response }}
          </a-descriptions-item>
        </a-descriptions>

        <div v-if="currentDetail.trace_data" class="trace-section">
          <h4>处理流程</h4>
          <ProcessFlow :trace="currentDetail.trace_data" />
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';
import ChatHistory from '../components/chat/ChatHistory.vue';
import ChatInput from '../components/chat/ChatInput.vue';
import ProcessFlow from '../components/chat/ProcessFlow.vue';
import chatApi from '../api/chatApi';
import traceApi from '../api/traceApi';
import historyApi from '../api/historyApi';

export default {
  name: 'ChatPage',
  components: {
    ChatHistory,
    ChatInput,
    ProcessFlow
  },
  setup() {
    const messages = ref([]);
    const loading = ref(false);
    const currentTrace = ref(null);
    const chatHistoryRef = ref(null);
    const sessionId = ref(null);
    const activeTab = ref('chat');
    const pollingInterval = ref(null);
    const progress = ref(0);
    const progressStatus = ref('active');
    const progressText = ref('正在分析...');
    
    // 历史会话相关状态
    const sessions = ref([]);
    const historyLoading = ref(false);
    const detailVisible = ref(null);
    const currentDetail = ref(null);
    
    // 对话统计信息
    const chatStats = ref({
      total: 0,
      success: 0,
      error: 0
    });

    const totalHistory = computed(() => chatStats.value.total);
    const successHistory = computed(() => chatStats.value.success);
    const errorHistory = computed(() => chatStats.value.error);

    const scrollToBottom = () => {
      if (chatHistoryRef.value) {
        const container = chatHistoryRef.value.$el.querySelector('.chat-history-container');
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      }
    };

    const loadChatStats = async () => {
      try {
        const response = await chatApi.getChatStats();
        if (response.data.success) {
          chatStats.value = response.data.data;
        }
      } catch (error) {
        console.error('加载对话统计信息失败:', error);
      }
    };

    const handleSend = async (input) => {
      const userMessage = {
        type: 'user',
        content: input,
        timestamp: new Date().toISOString()
      };

      messages.value.push(userMessage);
      loading.value = true;
      progress.value = 0;
      progressStatus.value = 'active';
      progressText.value = '正在分析...';

      try {
        // 发送消息并直接获取结果，硬编码用户ID为1（演示用）
        const response = await chatApi.sendMessage(input, sessionId.value, 1);
        
        // 保存后端返回的 session_id
        if (response.data.session_id) {
          sessionId.value = response.data.session_id;
        }
        
        // 显示处理流程
        if (response.data.analysis_result) {
          // 使用 analysis_result.trace 作为 currentTrace，因为 ProcessFlow 组件期望 trace 对象有 visualization_steps 字段
          currentTrace.value = response.data.analysis_result.trace || response.data.analysis_result;
          
          // 从backend_response中提取recommendations
          let recommendations = [];
          const backendResponse = response.data.analysis_result.backend_response;
          if (backendResponse && backendResponse.success && backendResponse.data && backendResponse.data.recommendations) {
            recommendations = backendResponse.data.recommendations;
          }
          
          // 调用 showFinalResult 方法处理响应数据
          showFinalResult(currentTrace.value, recommendations);
        } else {
          // 显示系统消息
          const systemMessage = {
            type: 'system',
            content: response.data.success ? response.data.message : '处理失败: ' + response.data.message,
            timestamp: new Date().toISOString()
          };
          messages.value.push(systemMessage);
        }
        
        // 加载对话统计信息
        loadChatStats();
      } catch (error) {
        message.error('发送失败：' + (error.response?.data?.message || error.message));
      } finally {
        loading.value = false;
        progress.value = 100;
        progressStatus.value = 'success';
        progressText.value = '分析完成';
        setTimeout(() => {
          progress.value = 0;
          progressStatus.value = 'active';
        }, 1000);
        scrollToBottom();
      }
    };

    const startPolling = (traceId) => {
      // 清除之前的轮询
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value);
      }
      
      // 开始新的轮询
      pollingInterval.value = setInterval(async () => {
        try {
          const response = await chatApi.getTraceStatus(traceId);
          
          if (response.data.success) {
            const traceData = response.data.data;
            const isCompleted = response.data.is_completed;
            const currentProgress = response.data.progress || 0;
            
            // 更新进度
            progress.value = currentProgress;
            
            // 更新进度文本
            if (traceData.steps && traceData.steps.length > 0) {
              const lastStep = traceData.steps[traceData.steps.length - 1];
              if (lastStep.title) {
                progressText.value = `正在${lastStep.title}...`;
              }
            }
            
            // 更新 trace 数据
            currentTrace.value = traceData;
            
            // 如果分析完成，停止轮询并显示最终结果
            if (isCompleted) {
              clearInterval(pollingInterval.value);
              progress.value = 100;
              progressStatus.value = 'success';
              progressText.value = '分析完成';
              
              // 延迟显示最终结果，让用户看到100%的进度
              setTimeout(() => {
                showFinalResult(traceData);
                loading.value = false;
                // 延迟清空进度，让用户看到成功状态
                setTimeout(() => {
                  progress.value = 0;
                }, 1000);
              }, 500);
            }
          }
        } catch (error) {
          console.error('获取 trace 状态失败:', error);
          clearInterval(pollingInterval.value);
          message.error('获取处理状态失败：' + (error.response?.data?.message || error.message));
          loading.value = false;
          progress.value = 0;
        }
      }, 1000); // 1秒轮询一次
    };

    const showFinalResult = (traceData, recommendations = []) => {
      // 提取最终回答
      let finalAnswer = '';
      
      // 1. 优先使用 traceData 中的 final_answer
      if (traceData.final_answer) {
        finalAnswer = traceData.final_answer;
      }
      // 2. 其次从 visualization_steps 中提取 final_answer
      else if (traceData.visualization_steps) {
        const lastStep = traceData.visualization_steps[traceData.visualization_steps.length - 1];
        if (lastStep.data && lastStep.data.final_answer) {
          finalAnswer = lastStep.data.final_answer;
        }
      }
      // 3. 从 steps 中提取 summary
      else if (traceData.steps) {
        const lastStep = traceData.steps[traceData.steps.length - 1];
        if (lastStep.data && lastStep.data.summary) {
          finalAnswer = lastStep.data.summary;
        }
      }
      // 4. 如果仍然没有，使用默认值
      if (!finalAnswer) {
        finalAnswer = '为你找到以下替代原料';
      }
      
      // 检查是否有替代原料信息
      let hasSubstitutes = false;
      if (traceData.steps) {
        for (const step of traceData.steps) {
          if (step.data) {
            // 检查是否有使用默认替代建议
            if (step.data['使用默认替代建议']) {
              const substitutes = step.data['使用默认替代建议'];
              if (substitutes.length > 0) {
                finalAnswer += '\n\n具体替代原料：\n';
                substitutes.forEach((substitute, index) => {
                  finalAnswer += `${index + 1}. ${substitute.substitute_name} (相似度: ${substitute.similarity_score})\n`;
                });
                hasSubstitutes = true;
                break;
              }
            }
            // 检查是否有 substitutes 字段
            else if (step.data.substitutes) {
              const substitutes = step.data.substitutes;
              if (substitutes.length > 0) {
                finalAnswer += '\n\n具体替代原料：\n';
                substitutes.forEach((substitute, index) => {
                  // 检查 substitute 是否是对象，如果是则访问 substitute_name 属性
                  if (typeof substitute === 'object' && substitute.substitute_name) {
                    finalAnswer += `${index + 1}. ${substitute.substitute_name}${substitute.similarity_score ? ` (相似度: ${substitute.similarity_score})` : ''}\n`;
                  } else {
                    // 如果不是对象，则直接使用
                    finalAnswer += `${index + 1}. ${substitute}\n`;
                  }
                });
                hasSubstitutes = true;
                break;
              }
            }
          }
        }
      }
      
      // 提取数据库类型和结果数量，添加到最后一步的处理流程中
      let dbType = 'neo4j';
      let resultCount = 0;
      
      // 从 steps 中提取结果数量
      if (traceData.steps) {
        for (const step of traceData.steps) {
          if (step.data) {
            // 检查是否有使用默认替代建议，计算结果数量
            if (step.data['使用默认替代建议']) {
              resultCount = step.data['使用默认替代建议'].length;
              break;
            }
            // 检查是否有 result_count 字段
            else if (step.data.result_count !== undefined) {
              resultCount = step.data.result_count;
              break;
            }
          }
        }
      }
      
      // 将数据库类型和结果数量添加到最后一步的处理流程中
      if (traceData.visualization_steps && traceData.visualization_steps.length > 0) {
        const lastStep = traceData.visualization_steps[traceData.visualization_steps.length - 1];
        if (lastStep.data) {
          lastStep.data.database_type = dbType;
          lastStep.data.result_count = resultCount;
        }
      }
      
      // 保存 session_id
      if (traceData.session_id) {
        sessionId.value = traceData.session_id;
      }
      
      // 添加系统消息
      const systemMessage = {
        type: 'system',
        content: finalAnswer,
        timestamp: new Date().toISOString(),
        recommendations: recommendations
      };

      messages.value.push(systemMessage);
      scrollToBottom();
    };

    const loadSessions = async () => {
      historyLoading.value = true;
      try {
        const response = await historyApi.getSessions({});

        if (response.success) {
          sessions.value = response.data?.sessions || [];
        } else {
          message.error('加载会话列表失败：' + (response.message || '未知错误'));
        }
      } catch (error) {
        message.error('加载会话列表失败：' + (error.response?.data?.message || error.message));
      } finally {
        historyLoading.value = false;
      }
    };

    const loadSession = async (selectedSessionId) => {
      try {
        const response = await historyApi.getSessionDetail(selectedSessionId);

        if (response.success) {
          const sessionData = response.data;
          
          // 切换到智能对话标签页
          activeTab.value = 'chat';
          
          // 清空当前对话
          messages.value = [];
          
          // 设置当前 sessionId
          sessionId.value = selectedSessionId;
          
          // 把该会话的所有消息转换为前端显示格式
          const sessionMessages = sessionData.messages || [];
          for (const trace of sessionMessages) {
            // 添加用户消息
            if (trace.user_input) {
              messages.value.push({
                type: 'user',
                content: trace.user_input,
                timestamp: trace.created_at
              });
            }
            
            // 添加系统消息
            if (trace.final_answer) {
              messages.value.push({
                type: 'system',
                content: trace.final_answer,
                timestamp: trace.created_at
              });
            }
          }
          
          // 滚动到底部
          setTimeout(scrollToBottom, 100);
          
          message.success('加载会话成功');
        } else {
          message.error('加载会话失败：' + response.data.message);
        }
      } catch (error) {
        message.error('加载会话失败：' + (error.response?.data?.message || error.message));
      }
    };

    const viewSessionDetail = (sessionItem) => {
      try {
        currentDetail.value = {
          session_id: sessionItem.session_id,
          user_input: sessionItem.last_user_input,
          system_response: sessionItem.last_system_response,
          timestamp: sessionItem.last_message_time,
          status: sessionItem.status,
          trace_data: null
        };
        detailVisible.value = true;
      } catch (error) {
        message.error('加载详情失败：' + (error.response?.data?.message || error.message));
      }
    };

    const deleteSession = async (sessionId) => {
      try {
        // 从数据库中删除该会话的所有消息
        const response = await historyApi.deleteSession(sessionId);

        if (response.success) {
          message.success('删除会话成功');
          // 重新加载会话列表
          loadSessions();
        } else {
          message.error('删除会话失败：' + (response.message || '未知错误'));
        }
      } catch (error) {
        message.error('删除会话失败：' + (error.response?.data?.message || error.message));
      }
    };

    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    };

    const getStatusColor = (status) => {
      switch (status) {
        case 'success': return 'success';
        case 'error': return 'error';
        case 'running': return 'processing';
        default: return 'default';
      }
    };

    const getStatusText = (status) => {
      switch (status) {
        case 'success': return '成功';
        case 'error': return '失败';
        case 'running': return '处理中';
        default: return '未知';
      }
    };

    onMounted(() => {
      loadSessions();
      loadChatStats();
    });

    onUnmounted(() => {
      // 清理轮询
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value);
      }
    });

    return {
      messages,
      loading,
      currentTrace,
      chatHistoryRef,
      handleSend,
      activeTab,
      sessions,
      historyLoading,
      detailVisible,
      currentDetail,
      totalHistory,
      successHistory,
      errorHistory,
      loadSessions,
      loadSession,
      viewSessionDetail,
      deleteSession,
      formatTime,
      getStatusColor,
      getStatusText,
      progress,
      progressStatus,
      progressText
    };
  }
};
</script>

<style scoped>
/* 全局动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.chat-page {
  padding: var(--spacing-xl) var(--spacing-2xl);
  min-height: calc(100vh - 200px);
  background: linear-gradient(135deg, #1a1410 0%, #2c241a 50%, #1a1410 100%);
}

.chat-container {
  display: grid;
  grid-template-columns: 1fr 450px;
  gap: var(--spacing-xl);
  max-width: 1600px;
  margin: 0 auto;
  animation: fadeIn 0.8s ease-out;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.chat-main {
  margin-top:80px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.chat-content-container {
  display: flex;
  gap: 0;
  flex: 1;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  overflow: hidden;
  background: rgba(26, 20, 16, 0.8);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  min-height: 600px;
  max-height: 80vh;
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
  position: relative;
}

.chat-tabs-sidebar {
  flex-shrink: 0;
  width: 120px;
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.95) 0%, rgba(26, 20, 16, 0.98) 100%);
  border-right: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: flex-start;
  padding-top: var(--spacing-md);
}

.chat-tab-buttons {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.chat-tab-button {
  width: 100%;
  text-align: center;
  padding: var(--spacing-md) var(--spacing-sm);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
  background: rgba(26, 20, 16, 0.8);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-normal);
  font-family: var(--font-display);
  letter-spacing: 0.05em;
  position: relative;
  overflow: hidden;
}

.chat-tab-button:hover {
  border-color: var(--color-gold-400);
  background: rgba(212, 175, 55, 0.1);
  color: var(--color-gold-300);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
}

.chat-tab-button.active {
  border-color: var(--color-gold-300);
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%);
  color: var(--color-gold-100);
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.25);
}

.chat-tab-button.active::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 3px;
  height: 100%;
  background: linear-gradient(180deg, var(--color-gold-300), var(--color-gold-400));
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
}

.chat-content-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  max-width: 100%;
  box-sizing: border-box;
  position: relative;
}

.chat-content-main > div {
  flex: 1;
  overflow: hidden;
}

.chat-header {
  text-align: center;
  padding: var(--spacing-xl);
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.9) 0%, rgba(26, 20, 16, 0.95) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

/* 添加装饰元素 */
.chat-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
  animation: pulse 3s infinite;
}

.chat-header:hover {
  border-color: var(--color-gold-400);
  box-shadow: 0 12px 40px rgba(212, 175, 55, 0.2);
  transform: translateY(-4px);
}

.chat-header h2 {
  margin: 0 0 var(--spacing-xs) 0;
  font-size: 32px;
  font-weight: 700;
  font-family: var(--font-display);
  color: var(--color-gold-100);
  text-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);
  letter-spacing: -0.02em;
  position: relative;
  z-index: 1;
}

.chat-header p {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 16px;
  color: var(--color-text-primary);
  font-weight: 500;
  position: relative;
  z-index: 1;
}

.chat-tabs {
  margin-top: var(--spacing-md);
  position: relative;
  z-index: 1;
}

.chat-content {
  display: flex;
  flex-direction: column;
  gap: 0;
  flex: 1;
  overflow: hidden;
  background: transparent;
  min-height: 400px;
  max-height: 80vh;
  max-width: 100%;
  width: 100%;
  box-sizing: border-box;
  position: relative;
}

.chat-content > :first-child {
  flex: 1;
  overflow-y: auto;
}

.chat-content > :last-child {
  flex-shrink: 0;
}

.history-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  flex: 1;
  padding: var(--spacing-lg);
  overflow-y: auto;
  background: transparent;
}

.progress-section {
  background: linear-gradient(135deg, rgba(26, 20, 16, 0.9) 0%, rgba(26, 20, 16, 0.95) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  transition: all var(--transition-normal);
  animation: slideInRight 0.5s ease-out;
}

.progress-section:hover {
  border-color: var(--color-gold-400);
  box-shadow: 0 4px 16px rgba(212, 175, 55, 0.15);
}

.chat-progress {
  margin-bottom: var(--spacing-sm);
}

.progress-text {
  font-size: 14px;
  color: #ffffff;
  text-align: center;
  font-weight: 500;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
}

.chat-input-section {
  position: sticky;
  bottom: 0;
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.95) 0%, rgba(26, 20, 16, 0.98) 100%);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-border-subtle);
  box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  transition: all var(--transition-normal);
}

.chat-input-section:hover {
  border-top-color: var(--color-gold-400);
}

.chat-sidebar {
  margin-top: 80px;
  position: sticky;
  top: var(--spacing-xl);
  height: fit-content;
  max-height: 80vh;
  min-height: 600px;
  overflow-y: auto;
  animation: slideInLeft 0.8s ease-out;
}

.history-sidebar {
  padding: var(--spacing-xl);
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.9) 0%, rgba(26, 20, 16, 0.95) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

/* 添加装饰元素 */
.history-sidebar::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
  animation: pulse 3s infinite reverse;
}

.history-sidebar:hover {
  border-color: var(--color-gold-400);
  box-shadow: 0 12px 40px rgba(212, 175, 55, 0.2);
  transform: translateY(-4px);
}

.history-sidebar h4 {
  margin: 0 0 var(--spacing-lg) 0;
  font-size: 18px;
  font-weight: 700;
  font-family: var(--font-display);
  color: var(--color-gold-200);
  text-align: center;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-xl);
}

.stat-item {
  text-align: center;
  padding: var(--spacing-lg);
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-subtle);
  transition: all var(--transition-normal);
  position: relative;
  overflow: hidden;
}

/* 添加装饰元素 */
.stat-item::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
}

.stat-item:hover {
  border-color: var(--color-gold-400);
  box-shadow: 0 6px 20px rgba(212, 175, 55, 0.15);
  transform: translateY(-4px);
}

.stat-number {
  font-size: 36px;
  font-weight: 700;
  font-family: var(--font-display);
  color: var(--color-gold-100);
  margin-bottom: var(--spacing-xs);
  text-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);
  transition: all var(--transition-normal);
}

.stat-item:hover .stat-number {
  transform: scale(1.05);
}

.stat-label {
  font-size: 14px;
  color: var(--color-text-primary);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  transition: all var(--transition-normal);
}

.stat-item:hover .stat-label {
  color: var(--color-gold-300);
}

.filter-card,
.history-list-card {
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.9) 0%, rgba(26, 20, 16, 0.95) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-xl);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  transition: all var(--transition-normal);
  overflow: hidden;
  position: relative;
}

/* 添加装饰元素 */
.filter-card::before,
.history-list-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
}

.filter-card:hover,
.history-list-card:hover {
  border-color: var(--color-gold-400);
  box-shadow: 0 12px 40px rgba(212, 175, 55, 0.2);
  transform: translateY(-4px);
}

.filter-card {
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
}

.history-list-card {
  padding: 0;
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.trace-section {
  margin-top: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: linear-gradient(135deg, rgba(26, 20, 16, 0.8) 0%, rgba(26, 20, 16, 0.9) 100%);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-lg);
  animation: fadeIn 0.5s ease-out;
}

.trace-section h4 {
  margin: 0 0 var(--spacing-md) 0;
  font-size: 18px;
  font-weight: 700;
  font-family: var(--font-display);
  color: var(--color-gold-200);
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

/* 自定义滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(26, 20, 16, 0.5);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, var(--color-gold-400), var(--color-gold-500));
  border-radius: 4px;
  transition: all var(--transition-normal);
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, var(--color-gold-300), var(--color-gold-400));
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
}

:deep(.ant-table) {
  font-size: 14px;
  background: transparent !important;
}

:deep(.ant-table-container) {
  background: transparent !important;
}

:deep(.ant-table-thead > tr > th) {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.08) 100%) !important;
  font-weight: 700;
  color: var(--color-gold-200) !important;
  border-bottom: 1px solid var(--color-border-strong) !important;
  transition: all var(--transition-normal);
}

:deep(.ant-table-thead > tr > th:hover) {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%) !important;
}

:deep(.ant-table-tbody > tr > td) {
  color: var(--color-text-primary) !important;
  border-bottom: 1px solid var(--color-border-subtle) !important;
  transition: all var(--transition-normal);
}

:deep(.ant-table-tbody > tr:hover > td) {
  background: rgba(212, 175, 55, 0.08) !important;
}

:deep(.ant-descriptions-item-label) {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.08) 100%) !important;
  font-weight: 600;
  color: var(--color-gold-200) !important;
  border-right: 1px solid var(--color-border-strong) !important;
}

:deep(.ant-descriptions-item-content) {
  color: var(--color-text-primary) !important;
  border-right: 1px solid var(--color-border-subtle) !important;
}

:deep(.ant-tabs) {
  background: transparent;
}

:deep(.ant-tabs-nav) {
  margin-bottom: var(--spacing-lg) !important;
  justify-content: center;
}

:deep(.ant-tabs-tab) {
  padding: var(--spacing-md) var(--spacing-lg) !important;
  margin: 0 var(--spacing-sm) !important;
  border-radius: var(--radius-lg) !important;
  transition: all var(--transition-normal) !important;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
}

:deep(.ant-tabs-tab:hover) {
  background: rgba(212, 175, 55, 0.1) !important;
  transform: translateY(-2px) !important;
}

:deep(.ant-tabs-tab.ant-tabs-tab-active) {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%) !important;
  transform: translateY(-2px) !important;
}

:deep(.ant-tabs-tab.ant-tabs-tab-active .ant-tabs-tab-btn) {
  color: var(--color-gold-100) !important;
  font-weight: 600 !important;
}

:deep(.ant-tabs-ink-bar) {
  background: linear-gradient(90deg, var(--color-gold-300), var(--color-gold-400)) !important;
  height: 3px !important;
  border-radius: 1.5px !important;
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
}

/* 垂直标签页样式 */
:deep(.chat-tabs-vertical) {
  width: 100%;
  background: transparent;
}

:deep(.chat-tabs-vertical .ant-tabs-tabpane) {
  display: none;
}

:deep(.chat-tabs-vertical .ant-tabs-nav) {
  width: 100%;
  margin: 0 !important;
  border-right: none !important;
}

:deep(.chat-tabs-vertical .ant-tabs-tab) {
  width: 100%;
  text-align: center;
  padding: var(--spacing-md) var(--spacing-sm) !important;
  margin: 0 !important;
  border-radius: 0 !important;
  border-bottom: 1px solid var(--color-border-subtle) !important;
  border-right: 3px solid transparent !important;
  transition: all var(--transition-normal) !important;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
}

:deep(.chat-tabs-vertical .ant-tabs-tab:hover) {
  background: rgba(212, 175, 55, 0.1) !important;
  border-right-color: var(--color-gold-400) !important;
}

:deep(.chat-tabs-vertical .ant-tabs-tab.ant-tabs-tab-active) {
  background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%) !important;
  border-right-color: var(--color-gold-300) !important;
  font-weight: 600 !important;
}

:deep(.chat-tabs-vertical .ant-tabs-tab.ant-tabs-tab-active .ant-tabs-tab-btn) {
  color: var(--color-gold-100) !important;
  font-weight: 600 !important;
}

:deep(.chat-tabs-vertical .ant-tabs-ink-bar) {
  background: linear-gradient(180deg, var(--color-gold-300), var(--color-gold-400)) !important;
  width: 3px !important;
  height: auto !important;
  border-radius: 1.5px !important;
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
}

:deep(.ant-picker) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid var(--color-border-subtle) !important;
  color: var(--color-text-primary) !important;
  transition: all var(--transition-normal) !important;
}

:deep(.ant-picker:hover) {
  border-color: var(--color-gold-400) !important;
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.2) !important;
}

:deep(.ant-picker-input input) {
  color: var(--color-text-primary) !important;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, var(--color-gold-500) 0%, var(--color-gold-400) 50%, var(--color-gold-300) 100%) !important;
  border: none !important;
  box-shadow: 0 4px 20px rgba(212, 175, 55, 0.25) !important;
  color: var(--color-bg-0) !important;
  font-weight: 600 !important;
  transition: all var(--transition-normal) !important;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
  position: relative;
  overflow: hidden;
}

:deep(.ant-btn-primary::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

:deep(.ant-btn-primary:hover::before) {
  left: 100%;
}

:deep(.ant-btn-primary:hover) {
  transform: translateY(-3px) !important;
  box-shadow: 0 8px 30px rgba(212, 175, 55, 0.35) !important;
}

:deep(.ant-btn) {
  background: transparent !important;
  border: 1px solid var(--color-border-strong) !important;
  color: var(--color-gold-300) !important;
  transition: all var(--transition-normal) !important;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
}

:deep(.ant-btn:hover) {
  background: rgba(212, 175, 55, 0.1) !important;
  border-color: var(--color-gold-400) !important;
  color: var(--color-gold-200) !important;
  box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2) !important;
  transform: translateY(-2px) !important;
}

:deep(.ant-popconfirm .ant-popconfirm-inner) {
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.95) 0%, rgba(26, 20, 16, 0.98) 100%) !important;
  border: 1px solid var(--color-border-strong) !important;
  border-radius: var(--radius-lg) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
}

:deep(.ant-popconfirm .ant-popconfirm-title) {
  color: var(--color-text-primary) !important;
  font-weight: 600 !important;
  font-family: var(--font-display);
}

:deep(.ant-modal-content) {
  background: linear-gradient(180deg, rgba(26, 20, 16, 0.95) 0%, rgba(26, 20, 16, 0.98) 100%) !important;
  border: 1px solid var(--color-border-strong) !important;
  border-radius: var(--radius-xl) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  box-shadow: 0 16px 64px rgba(0, 0, 0, 0.4) !important;
  position: relative;
  overflow: hidden;
}

:deep(.ant-modal-content::before) {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--color-gold-400), transparent);
}

:deep(.ant-modal-header) {
  background: transparent !important;
  border-bottom: 1px solid var(--color-border-subtle) !important;
  padding: var(--spacing-xl) var(--spacing-xl) var(--spacing-lg) !important;
}

:deep(.ant-modal-title) {
  color: var(--color-gold-100) !important;
  font-weight: 700 !important;
  font-family: var(--font-display) !important;
  font-size: 20px !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

:deep(.ant-modal-body) {
  padding: var(--spacing-xl) !important;
  color: var(--color-text-primary) !important;
}

:deep(.ant-empty) {
  color: var(--color-text-secondary) !important;
}

:deep(.ant-empty-description) {
  color: var(--color-text-secondary) !important;
  font-size: 14px !important;
  font-family: var(--font-display);
  letter-spacing: 0.05em;
}

:deep(.ant-progress-bg) {
  background: linear-gradient(90deg, #d4af37 0%, #b8941f 100%) !important;
  box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
}

:deep(.ant-progress-success-bg) {
  background: linear-gradient(90deg, #52c41a 0%, #389e0d 100%) !important;
  box-shadow: 0 0 10px rgba(82, 196, 26, 0.5);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .chat-container {
    grid-template-columns: 1fr;
  }
  
  .chat-sidebar {
    position: static;
    max-height: none;
  }
  
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .chat-page {
    padding: var(--spacing-lg) var(--spacing-md);
  }
  
  .chat-header {
    padding: var(--spacing-lg);
  }
  
  .chat-header h2 {
    font-size: 24px;
  }
  
  .chat-tabs-sidebar {
    width: 100px;
  }
  
  .chat-tab-button {
    font-size: 12px;
    padding: var(--spacing-sm) var(--spacing-xs);
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-number {
    font-size: 28px;
  }
}

@media (max-width: 480px) {
  .chat-tabs-sidebar {
    width: 80px;
  }
  
  .chat-tabs-sidebar .ant-tabs-tab {
    font-size: 11px;
    padding: var(--spacing-sm) var(--spacing-xs) !important;
  }
}
</style>