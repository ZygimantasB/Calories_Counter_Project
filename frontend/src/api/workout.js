import apiClient from './client';

export const workoutApi = {
  // Get workout sessions for React frontend
  getWorkouts: async (params = {}) => {
    const response = await apiClient.get('/api/react/workouts/', { params });
    return response.data;
  },

  // Get exercises for React frontend
  getExercises: async () => {
    const response = await apiClient.get('/api/react/exercises/');
    return response.data;
  },

  // Get workout frequency data
  getWorkoutFrequency: async (days = 90) => {
    const response = await apiClient.get('/api/workout-frequency/', {
      params: { days },
    });
    return response.data;
  },

  // Get exercise progress data
  getExerciseProgress: async (exerciseId = null) => {
    const url = exerciseId
      ? `/api/exercise-progress/${exerciseId}/`
      : '/api/exercise-progress/';
    const response = await apiClient.get(url);
    return response.data;
  },

  // Get workout tables
  getWorkoutTables: async () => {
    const response = await apiClient.get('/api/workout-tables/');
    return response.data;
  },

  // Save workout table
  saveWorkoutTable: async (tableData) => {
    const response = await apiClient.post('/api/workout-tables/save/', tableData);
    return response.data;
  },

  // Delete workout table
  deleteWorkoutTable: async (tableId) => {
    const response = await apiClient.delete(`/api/workout-tables/${tableId}/delete/`);
    return response.data;
  },
};

export default workoutApi;
