import apiClient from './client';

export const runningApi = {
  getRunningItems: async (params = {}) => {
    const response = await apiClient.get('/api/react/running-items/', { params });
    return response.data;
  },

  addSession: async (sessionData) => {
    const response = await apiClient.post('/api/react/running-items/add/', sessionData);
    return response.data;
  },

  update: async (id, data) => {
    const response = await apiClient.put(`/api/react/running-items/${id}/update/`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await apiClient.delete(`/api/react/running-items/${id}/delete/`);
    return response.data;
  },

  getRunningData: async (days = 365) => {
    const response = await apiClient.get('/api/running-data/', {
      params: { days },
    });
    return response.data;
  },
};

export default runningApi;
