import apiClient from './client';

const settingsApi = {
  getSettings: async () => {
    const response = await apiClient.get('/api/react/settings/');
    return response.data;
  },

  updateSettings: async (data) => {
    const response = await apiClient.put('/api/react/settings/update/', data);
    return response.data;
  },

  exportData: (type = 'all', format = 'csv') => {
    window.location.href = `/settings/export/?type=${type}&format=${format}`;
  },
};

export default settingsApi;
