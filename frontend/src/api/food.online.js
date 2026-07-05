// Online (browser) food API — talks to the Django REST backend via axios.
import apiClient from './client';

export const foodApi = {
  getDashboard: async () => {
    const response = await apiClient.get('/api/react/dashboard/');
    return response.data;
  },
  getFoodItems: async (params = {}) => {
    const response = await apiClient.get('/api/react/food-items/', { params });
    return response.data;
  },
  addFood: async (foodData) => {
    const response = await apiClient.post('/api/react/food-items/add/', foodData);
    return response.data;
  },
  updateFood: async (foodId, foodData) => {
    const response = await apiClient.put(`/api/react/food-items/${foodId}/update/`, foodData);
    return response.data;
  },
  deleteFood: async (foodId) => {
    const response = await apiClient.delete(`/api/react/food-items/${foodId}/delete/`);
    return response.data;
  },
  getQuickAddFoods: async () => {
    const response = await apiClient.get('/api/react/quick-add-foods/');
    return response.data;
  },
  searchAllFoods: async (query = '', limit = 20) => {
    const response = await apiClient.get('/api/react/search-foods/', { params: { q: query, limit } });
    return response.data;
  },
  getTopFoods: async (params = {}) => {
    const response = await apiClient.get('/api/react/top-foods/', { params });
    return response.data;
  },
  autocomplete: async (query) => {
    const response = await apiClient.get('/api/food-autocomplete/', { params: { q: query } });
    return response.data;
  },
  getNutritionData: async (foodName, weight = 100) => {
    const response = await apiClient.get('/api/nutrition-data/', { params: { food: foodName, weight } });
    return response.data;
  },
  // AI nutrition lookup — shared with the offline app via api/gemini.js.
  getGeminiNutrition: async (query) => {
    const { getGeminiNutrition } = await import('./gemini');
    return getGeminiNutrition(query);
  },
  getCaloriesTrend: async (days = 30) => {
    const response = await apiClient.get('/api/calories-trend/', { params: { days } });
    return response.data;
  },
  getMacrosTrend: async (days = 30) => {
    const response = await apiClient.get('/api/macros-trend/', { params: { days } });
    return response.data;
  },
  getHourlyPattern: async (params) => {
    const response = await apiClient.get('/api/react/food-items/hourly/', { params });
    return response.data;
  },
  hideFromQuickList: async (foodItemId) => {
    const response = await apiClient.post(`/food/${foodItemId}/hide-from-quick-list/`);
    return response.data;
  },
  copyDayFoods: async (sourceDate, targetDate = null) => {
    const response = await apiClient.post('/api/react/food-items/copy-day/', {
      source_date: sourceDate,
      ...(targetDate && { target_date: targetDate }),
    });
    return response.data;
  },
};

export default foodApi;
