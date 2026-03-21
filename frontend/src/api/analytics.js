import apiClient from './client';

export const analyticsApi = {
  // Get analytics data for React frontend
  getAnalytics: async (params = {}) => {
    const response = await apiClient.get('/api/react/analytics/', { params });
    return response.data;
  },

  getMonthCompare: async (monthA, monthB) => {
    const response = await apiClient.get('/api/react/analytics/month-compare/', {
      params: { month_a: monthA, month_b: monthB }
    });
    return response.data;
  },

  getYearlyTrends: async (year = 'last12') => {
    const response = await apiClient.get('/api/react/analytics/yearly-trends/', { params: { year } });
    return response.data;
  },
};

export default analyticsApi;
