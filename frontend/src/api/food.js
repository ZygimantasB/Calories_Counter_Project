import apiClient from './client';

export const foodApi = {
  // Get dashboard data
  getDashboard: async () => {
    const response = await apiClient.get('/api/react/dashboard/');
    return response.data;
  },

  // Get food items with filtering
  getFoodItems: async (params = {}) => {
    const response = await apiClient.get('/api/react/food-items/', { params });
    return response.data;
  },

  // Add a food item
  addFood: async (foodData) => {
    const response = await apiClient.post('/api/react/food-items/add/', foodData);
    return response.data;
  },

  // Update a food item
  updateFood: async (foodId, foodData) => {
    const response = await apiClient.put(`/api/react/food-items/${foodId}/update/`, foodData);
    return response.data;
  },

  // Delete a food item
  deleteFood: async (foodId) => {
    const response = await apiClient.delete(`/api/react/food-items/${foodId}/delete/`);
    return response.data;
  },

  // Get quick-add foods
  getQuickAddFoods: async () => {
    const response = await apiClient.get('/api/react/quick-add-foods/');
    return response.data;
  },

  // Search all foods in database
  searchAllFoods: async (query = '', limit = 20) => {
    const response = await apiClient.get('/api/react/search-foods/', {
      params: { q: query, limit },
    });
    return response.data;
  },

  // Get top foods
  getTopFoods: async (params = {}) => {
    const response = await apiClient.get('/api/react/top-foods/', { params });
    return response.data;
  },

  // Autocomplete food search
  autocomplete: async (query) => {
    const response = await apiClient.get('/api/food-autocomplete/', {
      params: { q: query },
    });
    return response.data;
  },

  // Get nutrition data for a food item
  getNutritionData: async (foodName, weight = 100) => {
    const response = await apiClient.get('/api/nutrition-data/', {
      params: { food: foodName, weight },
    });
    return response.data;
  },

  // Get AI-powered nutrition data
  getGeminiNutrition: async (query) => {
    const response = await apiClient.get('/api/gemini-nutrition/', {
      params: { q: query },
    });
    return response.data;
  },

  // Get calories trend data
  getCaloriesTrend: async (days = 30) => {
    const response = await apiClient.get('/api/calories-trend/', {
      params: { days },
    });
    return response.data;
  },

  // Get macros trend data
  getMacrosTrend: async (days = 30) => {
    const response = await apiClient.get('/api/macros-trend/', {
      params: { days },
    });
    return response.data;
  },

  // Hide from quick list
  hideFromQuickList: async (foodItemId) => {
    const response = await apiClient.post(`/food/${foodItemId}/hide-from-quick-list/`);
    return response.data;
  },
};

export default foodApi;
