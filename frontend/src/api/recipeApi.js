// 配方相关 API 调用封装

const API_BASE_URL = 'http://127.0.0.1:8000/api';

/**
 * 获取配方基础信息
 * @param {string} recipeId - 配方 ID
 * @returns {Promise<Object>} 配方基础信息
 */
export async function fetchRecipe(recipeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/recipes/${recipeId}`);
    const data = await response.json();
    if (data.code === 0) {
      return data.data;
    } else {
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Error fetching recipe:', error);
    throw error;
  }
}

/**
 * 获取配方原料列表
 * @param {string} recipeId - 配方 ID
 * @returns {Promise<Array>} 原料列表
 */
export async function fetchIngredients(recipeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/recipes/${recipeId}/ingredients`);
    const data = await response.json();
    if (data.code === 0) {
      return data.data;
    } else {
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Error fetching ingredients:', error);
    throw error;
  }
}

/**
 * 获取 SQE 评分分析
 * @param {string} recipeId - 配方 ID
 * @returns {Promise<Object>} SQE 评分分析
 */
export async function fetchSQE(recipeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/recipes/${recipeId}/sqe`);
    const data = await response.json();
    if (data.code === 0) {
      return data.data;
    } else {
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Error fetching SQE:', error);
    throw error;
  }
}

/**
 * 获取风味分布与平衡特征
 * @param {string} recipeId - 配方 ID
 * @returns {Promise<Object>} 风味分布与平衡特征
 */
export async function fetchBalance(recipeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/recipes/${recipeId}/balance`);
    const data = await response.json();
    if (data.code === 0) {
      return data.data;
    } else {
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Error fetching balance:', error);
    throw error;
  }
}

/**
 * 获取关键风味节点
 * @param {string} recipeId - 配方 ID
 * @returns {Promise<Array>} 关键风味节点列表
 */
export async function fetchKeyNodes(recipeId) {
  try {
    const response = await fetch(`${API_BASE_URL}/recipes/${recipeId}/key-nodes`);
    const data = await response.json();
    if (data.code === 0) {
      return data.data;
    } else {
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Error fetching key nodes:', error);
    throw error;
  }
}

/**
 * 获取原料替代建议
 * @param {string} recipeId - 配方 ID
 * @param {string} targetCanonicalId - 目标原料的 canonical ID
 * @returns {Promise<Array>} 替代建议列表
 */
export async function fetchSubstitutes(recipeId, targetCanonicalId) {
  try {
    const response = await fetch(`${API_BASE_URL}/recipes/${recipeId}/substitutes?target_canonical_id=${targetCanonicalId}`);
    const data = await response.json();
    if (data.code === 0) {
      return data.data;
    } else {
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Error fetching substitutes:', error);
    return [];
  }
}

/**
 * 获取所有配方的详细信息
 * @returns {Promise<Array>} 配方列表
 */
export async function fetchAllRecipes() {
  try {
    const response = await fetch(`${API_BASE_URL}/recipes`);
    const data = await response.json();
    if (data.code === 0) {
      return data.data;
    } else {
      throw new Error(data.message);
    }
  } catch (error) {
    console.error('Error fetching all recipes:', error);
    throw error;
  }
}
