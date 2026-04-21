// 实体识别和审核相关的API服务

const API_BASE_URL = 'http://127.0.0.1:8000/api/entity';

/**
 * 获取认证令牌
 * @returns {string|null} 认证令牌
 */
function getAuthToken() {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    const user = JSON.parse(userStr);
    return user.token || null;
  }
  return null;
}

/**
 * 构建请求头
 * @returns {Object} 请求头
 */
function buildHeaders() {
  const headers = {
    'Content-Type': 'application/json'
  };
  
  return headers;
}

/**
 * 处理单个文本的实体识别
 * @param {string} text - 要处理的文本
 * @returns {Promise<Object>} 处理结果
 */
export async function processText(text) {
  try {
    const response = await fetch(`${API_BASE_URL}/process`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({ text })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '处理失败');
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('处理文本失败:', error);
    throw error;
  }
}

/**
 * 批量处理文本的实体识别
 * @param {string[]} texts - 要处理的文本数组
 * @returns {Promise<Array>} 处理结果数组
 */
export async function batchProcess(texts) {
  try {
    const response = await fetch(`${API_BASE_URL}/batch_process`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({ texts })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '批量处理失败');
    }
    
    const results = await response.json();
    return results;
  } catch (error) {
    console.error('批量处理失败:', error);
    throw error;
  }
}

/**
 * 提交审核结果
 * @param {Object} reviewData - 审核数据
 * @returns {Promise<Object>} 审核结果
 */
export async function submitReview(reviewData) {
  try {
    const response = await fetch(`${API_BASE_URL}/review`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify(reviewData)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '提交审核失败');
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('提交审核失败:', error);
    throw error;
  }
}

/**
 * 获取审核任务列表
 * @returns {Promise<Array>} 审核任务列表
 */
export async function getReviewTasks() {
  try {
    const response = await fetch(`${API_BASE_URL}/review_tasks`, {
      headers: buildHeaders()
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '获取审核任务失败');
    }
    
    const tasks = await response.json();
    return tasks;
  } catch (error) {
    console.error('获取审核任务失败:', error);
    throw error;
  }
}

/**
 * 获取审核任务详情
 * @param {string} reviewId - 审核任务ID
 * @returns {Promise<Object>} 审核任务详情
 */
export async function getReviewTaskDetail(reviewId) {
  try {
    const response = await fetch(`${API_BASE_URL}/review_tasks/${reviewId}`, {
      headers: buildHeaders()
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '获取审核任务详情失败');
    }
    
    const task = await response.json();
    return task;
  } catch (error) {
    console.error('获取审核任务详情失败:', error);
    throw error;
  }
}
