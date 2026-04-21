import axios from 'axios';

const BASE_URL =  'http://localhost:8000/api';

const graphApi = {
  /**
   * 获取风味图谱数据
   * @param {Object} params - 查询参数
   * @returns {Promise} - 响应数据
   */
  getFlavorGraph(params) {
    return axios.get(`${BASE_URL}/flavor-graph/graph`, { params });
  },

  /**
   * 获取原料类型列表
   * @returns {Promise} - 响应数据
   */
  getIngredientTypes() {
    return axios.get(`${BASE_URL}/flavor-graph/ingredient-types`);
  },

  /**
   * 获取图层类型列表
   * @returns {Promise} - 响应数据
   */
  getGraphLayers() {
    return axios.get(`${BASE_URL}/flavor-graph/layers`);
  },

  /**
   * 获取节点排名数据
   * @param {Object} params - 查询参数
   * @returns {Promise} - 响应数据
   */
  getRankings(params) {
    return axios.get(`${BASE_URL}/flavor-graph/rankings`, { params });
  },

  /**
   * 获取节点详情
   * @param {string} nodeId - 节点ID
   * @returns {Promise} - 响应数据
   */
  getNodeDetail(nodeId) {
    return axios.get(`${BASE_URL}/flavor-graph/nodes/${nodeId}`);
  },

  /**
   * 获取边详情
   * @param {Object} params - 查询参数
   * @returns {Promise} - 响应数据
   */
  getEdgeDetail(params) {
    return axios.get(`${BASE_URL}/flavor-graph/edges/detail`, { params });
  },

  /**
   * 获取图谱统计数据
   * @param {Object} params - 查询参数
   * @returns {Promise} - 响应数据
   */
  getGraphStats(params) {
    return axios.get(`${BASE_URL}/flavor-graph/stats`, { params });
  }
};

export default graphApi;