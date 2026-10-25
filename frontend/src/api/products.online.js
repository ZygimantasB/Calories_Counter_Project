// Online (browser) composite-products API — talks to the Django backend via axios.
import apiClient from './client';

export const productsApi = {
  list: async () => {
    const response = await apiClient.get('/api/react/products/');
    return response.data;
  },
  create: async (payload) => {
    const response = await apiClient.post('/api/react/products/add/', payload);
    return response.data;
  },
  update: async (productId, payload) => {
    const response = await apiClient.put(`/api/react/products/${productId}/update/`, payload);
    return response.data;
  },
  delete: async (productId) => {
    const response = await apiClient.delete(`/api/react/products/${productId}/delete/`);
    return response.data;
  },
  log: async (productId, servings = 1, date = null) => {
    const response = await apiClient.post(`/api/react/products/${productId}/log/`, { servings, ...(date && { date }) });
    return response.data;
  },
};

export default productsApi;
