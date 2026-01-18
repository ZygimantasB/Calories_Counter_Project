import apiClient from './client';

export const analyticsApi = {
  // Get analytics data for React frontend
  getAnalytics: async (params = {}) => {
    const response = await apiClient.get('/api/react/analytics/', { params });
    return response.data;
  },
};

export default analyticsApi;
