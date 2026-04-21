import axios from 'axios';

const BASE_URL = process.env.VUE_APP_API_BASE_URL || '/api';

const chatApi = {
  sendMessage(message, sessionId = null, userId = null) {
    return axios.post(`${BASE_URL}/chat/send`, {
      message,
      session_id: sessionId,
      user_id: userId
    });
  },

  getTraceStatus(traceId) {
    return axios.get(`${BASE_URL}/trace/${traceId}/status`);
  },

  getSystemStatus() {
    return axios.get(`${BASE_URL}/system/status`);
  },

  getChatStats() {
    return axios.get(`${BASE_URL}/chat/stats`);
  }
};

export default chatApi;