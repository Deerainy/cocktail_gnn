import axios from 'axios';

const BASE_URL = process.env.VUE_APP_API_BASE_URL || '/api';

const traceApi = {
  getTrace(traceId) {
    return axios.get(`${BASE_URL}/trace/${traceId}`);
  },

  getTraceList(params) {
    return axios.get(`${BASE_URL}/trace/list`, { params });
  }
};

export default traceApi;
