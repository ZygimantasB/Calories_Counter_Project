import apiClient from './client';

export const mealTemplatesApi = {
  list: async () => {
    const response = await apiClient.get('/api/react/meal-templates/');
    return response.data;
  },
  save: async (name, date = null) => {
    const response = await apiClient.post('/api/react/meal-templates/add/', { name, ...(date && { date }) });
    return response.data;
  },
  apply: async (templateId) => {
    const response = await apiClient.post(`/api/react/meal-templates/${templateId}/log/`);
    return response.data;
  },
  delete: async (templateId) => {
    const response = await apiClient.delete(`/api/react/meal-templates/${templateId}/delete/`);
    return response.data;
  },
};

export default mealTemplatesApi;
