import apiClient from './client';

export const runningApi = {
  // Get running sessions for React frontend
  getRunningItems: async (params = {}) => {
    const response = await apiClient.get('/api/react/running-items/', { params });
    return response.data;
  },

  // Add a running session
  addSession: async (sessionData) => {
    const response = await apiClient.post('/api/react/running-items/add/', sessionData);
    return response.data;
  },

  // Get running data for charts (legacy endpoint)
  getRunningData: async (days = 365) => {
    const response = await apiClient.get('/api/running-data/', {
      params: { days },
    });
    return response.data;
  },
};

export default runningApi;
