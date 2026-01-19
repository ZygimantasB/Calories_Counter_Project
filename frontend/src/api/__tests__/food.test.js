import { describe, it, expect, beforeEach, vi } from 'vitest';
import { foodApi } from '../food';
import apiClient from '../client';

// Mock the API client
vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('foodApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getDashboard', () => {
    it('should fetch dashboard data', async () => {
      const mockData = {
        today: { calories: 1500, protein: 100, carbs: 150, fat: 50 },
        week: { workouts: 3, runs: 2 },
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await foodApi.getDashboard();

      expect(apiClient.get).toHaveBeenCalledWith('/api/react/dashboard/');
      expect(result).toEqual(mockData);
    });

    it('should handle errors when fetching dashboard data', async () => {
      const mockError = new Error('Network error');
      apiClient.get.mockRejectedValue(mockError);

      await expect(foodApi.getDashboard()).rejects.toThrow('Network error');
    });
  });

  describe('getFoodItems', () => {
    it('should fetch food items without params', async () => {
      const mockData = { items: [], totals: { calories: 0 } };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await foodApi.getFoodItems();

      expect(apiClient.get).toHaveBeenCalledWith('/api/react/food-items/', { params: {} });
      expect(result).toEqual(mockData);
    });

    it('should fetch food items with date filter', async () => {
      const mockData = { items: [{ id: 1, name: 'Apple' }], totals: { calories: 95 } };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await foodApi.getFoodItems({ date: '2026-01-19' });

      expect(apiClient.get).toHaveBeenCalledWith('/api/react/food-items/', {
        params: { date: '2026-01-19' },
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('addFood', () => {
    it('should add a food item', async () => {
      const foodData = {
        name: 'Banana',
        calories: 105,
        protein: 1.3,
        carbs: 27,
        fat: 0.4,
      };
      const mockResponse = { success: true, id: 1 };
      apiClient.post.mockResolvedValue({ data: mockResponse });

      const result = await foodApi.addFood(foodData);

      expect(apiClient.post).toHaveBeenCalledWith('/api/react/food-items/add/', foodData);
      expect(result).toEqual(mockResponse);
    });

    it('should handle validation errors when adding food', async () => {
      const foodData = { name: '', calories: -10 };
      const mockError = {
        response: { data: { error: 'Invalid data' }, status: 400 },
      };
      apiClient.post.mockRejectedValue(mockError);

      await expect(foodApi.addFood(foodData)).rejects.toEqual(mockError);
    });
  });

  describe('updateFood', () => {
    it('should update a food item', async () => {
      const foodId = 1;
      const foodData = { name: 'Updated Apple', calories: 100 };
      const mockResponse = { success: true };
      apiClient.put.mockResolvedValue({ data: mockResponse });

      const result = await foodApi.updateFood(foodId, foodData);

      expect(apiClient.put).toHaveBeenCalledWith(
        `/api/react/food-items/${foodId}/update/`,
        foodData
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle not found error when updating', async () => {
      const foodId = 99999;
      const mockError = {
        response: { data: { error: 'Not found' }, status: 404 },
      };
      apiClient.put.mockRejectedValue(mockError);

      await expect(foodApi.updateFood(foodId, {})).rejects.toEqual(mockError);
    });
  });

  describe('deleteFood', () => {
    it('should delete a food item', async () => {
      const foodId = 1;
      const mockResponse = { success: true };
      apiClient.delete.mockResolvedValue({ data: mockResponse });

      const result = await foodApi.deleteFood(foodId);

      expect(apiClient.delete).toHaveBeenCalledWith(`/api/react/food-items/${foodId}/delete/`);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getQuickAddFoods', () => {
    it('should fetch quick-add foods', async () => {
      const mockData = {
        foods: [
          { id: 1, name: 'Chicken Breast', calories: 165 },
          { id: 2, name: 'Rice', calories: 130 },
        ],
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await foodApi.getQuickAddFoods();

      expect(apiClient.get).toHaveBeenCalledWith('/api/react/quick-add-foods/');
      expect(result).toEqual(mockData);
    });
  });

  describe('searchAllFoods', () => {
    it('should search foods with default params', async () => {
      const mockData = { results: [{ name: 'Apple' }] };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await foodApi.searchAllFoods();

      expect(apiClient.get).toHaveBeenCalledWith('/api/react/search-foods/', {
        params: { q: '', limit: 20 },
      });
      expect(result).toEqual(mockData);
    });

    it('should search foods with custom query and limit', async () => {
      const mockData = { results: [{ name: 'Chicken' }, { name: 'Chicken Breast' }] };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await foodApi.searchAllFoods('chicken', 10);

      expect(apiClient.get).toHaveBeenCalledWith('/api/react/search-foods/', {
        params: { q: 'chicken', limit: 10 },
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('getCaloriesTrend', () => {
    it('should fetch calories trend with default days', async () => {
      const mockData = {
        data: [
          { date: '2026-01-18', calories: 2000 },
          { date: '2026-01-19', calories: 2100 },
        ],
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await foodApi.getCaloriesTrend();

      expect(apiClient.get).toHaveBeenCalledWith('/api/calories-trend/', {
        params: { days: 30 },
      });
      expect(result).toEqual(mockData);
    });

    it('should fetch calories trend with custom days', async () => {
      const mockData = { data: [] };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await foodApi.getCaloriesTrend(7);

      expect(apiClient.get).toHaveBeenCalledWith('/api/calories-trend/', {
        params: { days: 7 },
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('getMacrosTrend', () => {
    it('should fetch macros trend data', async () => {
      const mockData = {
        data: [
          { date: '2026-01-19', protein: 150, carbs: 200, fat: 60 },
        ],
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await foodApi.getMacrosTrend(14);

      expect(apiClient.get).toHaveBeenCalledWith('/api/macros-trend/', {
        params: { days: 14 },
      });
      expect(result).toEqual(mockData);
    });
  });

  describe('getGeminiNutrition', () => {
    it('should fetch AI nutrition data', async () => {
      const query = '200g chicken breast';
      const mockData = {
        success: true,
        name: 'Chicken Breast',
        calories: 330,
        protein: 62,
        carbs: 0,
        fat: 7.2,
      };
      apiClient.get.mockResolvedValue({ data: mockData });

      const result = await foodApi.getGeminiNutrition(query);

      expect(apiClient.get).toHaveBeenCalledWith('/api/gemini-nutrition/', {
        params: { q: query },
      });
      expect(result).toEqual(mockData);
    });

    it('should handle AI service errors', async () => {
      const mockError = {
        response: {
          data: { error: 'Gemini API key not configured' },
          status: 500,
        },
      };
      apiClient.get.mockRejectedValue(mockError);

      await expect(foodApi.getGeminiNutrition('test')).rejects.toEqual(mockError);
    });
  });
});
