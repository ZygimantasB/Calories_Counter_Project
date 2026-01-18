import apiClient from './client';

export const weightApi = {
  // Get weight items for React frontend
  getWeightItems: async (params = {}) => {
    const response = await apiClient.get('/api/react/weight-items/', { params });
    return response.data;
  },

  // Add a weight entry
  addWeight: async (weightData) => {
    const response = await apiClient.post('/api/react/weight-items/add/', weightData);
    return response.data;
  },

  // Delete a weight entry
  deleteWeight: async (weightId) => {
    const response = await apiClient.delete(`/api/react/weight-items/${weightId}/delete/`);
    return response.data;
  },

  // Get weight data for charts (legacy endpoint)
  getWeightData: async (days = 365) => {
    const response = await apiClient.get('/api/weight-data/', {
      params: { days },
    });
    return response.data;
  },

  // Get weight-calories correlation
  getWeightCaloriesCorrelation: async () => {
    const response = await apiClient.get('/api/weight-calories-correlation/');
    return response.data;
  },
};

export default weightApi;
