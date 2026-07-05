import apiClient from './client';

export const workoutApi = {
  getWorkouts: async (params = {}) => {
    const response = await apiClient.get('/api/react/workouts/', { params });
    return response.data;
  },

  getExercises: async () => {
    const response = await apiClient.get('/api/react/exercises/');
    return response.data;
  },

  getWorkoutFrequency: async (days = 90) => {
    const response = await apiClient.get('/api/workout-frequency/', {
      params: { days },
    });
    return response.data;
  },

  getExerciseProgress: async (exerciseId = null) => {
    const url = exerciseId
      ? `/api/exercise-progress/${exerciseId}/`
      : '/api/exercise-progress/';
    const response = await apiClient.get(url);
    return response.data;
  },

  getWorkoutTables: async () => {
    const response = await apiClient.get('/api/react/workout-tables/');
    return response.data;
  },

  saveWorkoutTable: async (tableData) => {
    const response = await apiClient.post('/api/react/workout-tables/add/', tableData);
    return response.data;
  },

  deleteWorkoutTable: async (tableId) => {
    const response = await apiClient.delete(`/api/react/workout-tables/${tableId}/delete/`);
    return response.data;
  },

  add: async (data) => {
    const response = await apiClient.post('/api/react/workouts/add/', data);
    return response.data;
  },

  update: async (id, data) => {
    const response = await apiClient.put(`/api/react/workouts/${id}/update/`, data);
    return response.data;
  },

  delete: async (id) => {
    const response = await apiClient.delete(`/api/react/workouts/${id}/delete/`);
    return response.data;
  },

  addExercise: async (workoutId, data) => {
    const response = await apiClient.post(`/api/react/workouts/${workoutId}/exercises/add/`, data);
    return response.data;
  },

  updateExercise: async (workoutId, exerciseId, data) => {
    const response = await apiClient.put(`/api/react/workouts/${workoutId}/exercises/${exerciseId}/update/`, data);
    return response.data;
  },

  deleteExercise: async (workoutId, exerciseId) => {
    const response = await apiClient.delete(`/api/react/workouts/${workoutId}/exercises/${exerciseId}/delete/`);
    return response.data;
  },

  addExerciseToLibrary: async (data) => {
    const response = await apiClient.post('/api/react/exercises/add/', data);
    return response.data;
  },

  deleteExerciseFromLibrary: async (id) => {
    const response = await apiClient.delete(`/api/react/exercises/${id}/delete/`);
    return response.data;
  },
};

export default workoutApi;
