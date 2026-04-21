// 历史记录相关的API服务

const API_BASE_URL = 'http://127.0.0.1:5000/api';

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
 * 获取历史记录列表
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 历史记录列表
 */
export async function getHistoryList(params = {}) {
  try {
    const url = new URL(`${API_BASE_URL}/history`);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, value);
      }
    });
    
    const response = await fetch(url.toString(), {
      headers: buildHeaders()
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '获取历史记录失败');
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('获取历史记录失败:', error);
    throw error;
  }
}

/**
 * 获取会话列表
 * @param {Object} params - 查询参数
 * @returns {Promise<Object>} 会话列表
 */
export async function getSessions(params = {}) {
  try {
    const url = new URL(`${API_BASE_URL}/history/sessions`);
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, value);
      }
    });
    
    const response = await fetch(url.toString(), {
      headers: buildHeaders()
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '获取会话列表失败');
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('获取会话列表失败:', error);
    throw error;
  }
}

/**
 * 获取会话详情
 * @param {string} sessionId - 会话ID
 * @returns {Promise<Object>} 会话详情
 */
export async function getSessionDetail(sessionId) {
  try {
    const response = await fetch(`${API_BASE_URL}/history/${sessionId}/session_detail`, {
      headers: buildHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '获取会话详情失败');
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('获取会话详情失败:', error);
    throw error;
  }
}

/**
 * 删除会话
 * @param {string} sessionId - 会话ID
 * @returns {Promise<Object>} 删除结果
 */
export async function deleteSession(sessionId) {
  try {
    const response = await fetch(`${API_BASE_URL}/history/session/${sessionId}`, {
      method: 'DELETE',
      headers: buildHeaders()
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '删除会话失败');
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('删除会话失败:', error);
    throw error;
  }
}

/**
 * 获取数据分析统计数据
 * @returns {Promise<Object>} 数据分析统计数据
 */
export async function getAnalysisStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/history/analysis`, {
      headers: buildHeaders()
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || '获取数据分析统计数据失败');
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('获取数据分析统计数据失败:', error);
    throw error;
  }
}

// 默认导出
const historyApi = {
  getHistoryList,
  getSessions,
  getSessionDetail,
  deleteSession,
  getAnalysisStats
};

export default historyApi;
