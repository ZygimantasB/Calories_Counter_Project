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
    const response = await apiClient.get('/api/react/workout-tables/');
    return response.data;
  },

  // Save workout table
  saveWorkoutTable: async (tableData) => {
    const response = await apiClient.post('/api/react/workout-tables/add/', tableData);
    return response.data;
  },

  // Delete workout table
  deleteWorkoutTable: async (tableId) => {
    const response = await apiClient.delete(`/api/react/workout-tables/${tableId}/delete/`);
    return response.data;
  },

  // Add a new workout session
  add: async (data) => {
    const response = await apiClient.post('/api/react/workouts/add/', data);
    return response.data;
  },

  // Update an existing workout session
  update: async (id, data) => {
    const response = await apiClient.put(`/api/react/workouts/${id}/update/`, data);
    return response.data;
  },

  // Delete a workout session
  delete: async (id) => {
    const response = await apiClient.delete(`/api/react/workouts/${id}/delete/`);
    return response.data;
  },

  // Add an exercise to a workout session
  addExercise: async (workoutId, data) => {
    const response = await apiClient.post(`/api/react/workouts/${workoutId}/exercises/add/`, data);
    return response.data;
  },

  // Update an exercise within a workout session
  updateExercise: async (workoutId, exerciseId, data) => {
    const response = await apiClient.put(`/api/react/workouts/${workoutId}/exercises/${exerciseId}/update/`, data);
    return response.data;
  },

  // Delete an exercise from a workout session
  deleteExercise: async (workoutId, exerciseId) => {
    const response = await apiClient.delete(`/api/react/workouts/${workoutId}/exercises/${exerciseId}/delete/`);
    return response.data;
  },

  // Add a new exercise to the library
  addExerciseToLibrary: async (data) => {
    const response = await apiClient.post('/api/react/exercises/add/', data);
    return response.data;
  },

  // Delete an exercise from the library
  deleteExerciseFromLibrary: async (id) => {
    const response = await apiClient.delete(`/api/react/exercises/${id}/delete/`);
    return response.data;
  },
};

export default workoutApi;
