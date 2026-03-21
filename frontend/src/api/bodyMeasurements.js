import apiClient from './client';

export const bodyMeasurementsApi = {
  // Get body measurements for React frontend
  getMeasurements: async (params = {}) => {
    const response = await apiClient.get('/api/react/body-measurements/', { params });
    return response.data;
  },

  // Get body measurements data (legacy endpoint)
  getData: async (days = 365) => {
    const response = await apiClient.get('/api/body-measurements-data/', {
      params: { days },
    });
    return response.data;
  },

  // Add a measurement
  addMeasurement: async (measurementData) => {
    const response = await apiClient.post('/api/react/body-measurements/add/', measurementData);
    return response.data;
  },

  // Edit a measurement
  editMeasurement: async (measurementId, measurementData) => {
    const response = await apiClient.put(
      `/api/react/body-measurements/${measurementId}/update/`,
      measurementData
    );
    return response.data;
  },

  // Delete a measurement
  deleteMeasurement: async (measurementId) => {
    const response = await apiClient.delete(`/api/react/body-measurements/${measurementId}/delete/`);
    return response.data;
  },

  // Export to CSV
  exportCsv: async () => {
    const response = await apiClient.get('/body-measurements/export/csv/', {
      responseType: 'blob',
    });
    return response.data;
  },
};

export default bodyMeasurementsApi;
