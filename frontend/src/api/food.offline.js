// Offline food API: same exports/signatures as before, backed by local SQLite.
import * as foods from '../logic/foods';
import { buildDashboard } from '../logic/dashboard';
import { foodRepo } from '../db/repositories/foodRepo';
import { getGeminiNutrition } from './gemini';

function todayLocalDate() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

/** Resolve the consumed_at timestamp from add-food payload (date string or now). */
function resolveConsumedAt(data) {
  if (data.date) {
    const [y, m, d] = data.date.split('-').map(Number);
    const now = new Date();
    return new Date(y, m - 1, d, now.getHours(), now.getMinutes(), now.getSeconds()).toISOString();
  }
  if (data.consumed_at) return data.consumed_at;
  return new Date().toISOString();
}

function sanitize(data) {
  const name = String(data.name ?? '').trim().slice(0, 200);
  const clampNum = (v) => {
    let n = Number(v ?? 0) || 0;
    if (n < 0) n = 0;
    if (n > 50000) n = 50000;
    return n;
  };
  return {
    name,
    calories: clampNum(data.calories),
    protein: clampNum(data.protein),
    carbs: clampNum(data.carbs),
    fat: clampNum(data.fat),
  };
}

export const foodApi = {
  getDashboard: () => buildDashboard(),
  getFoodItems: (params = {}) => foods.listWithTotals(params),

  addFood: async (foodData) => {
    const s = sanitize(foodData);
    if (!s.name) return { success: false, error: 'Product name is required' };
    const id = await foodRepo.insert({
      product_name: s.name, calories: s.calories, protein: s.protein,
      carbohydrates: s.carbs, fat: s.fat, consumed_at: resolveConsumedAt(foodData),
    });
    return { success: true, id, message: 'Food item added successfully' };
  },

  updateFood: async (foodId, foodData) => {
    await foodRepo.update(foodId, foodData);
    return { success: true, message: 'Food item updated' };
  },

  deleteFood: async (foodId) => {
    await foodRepo.remove(foodId);
    return { success: true, message: 'Food item deleted' };
  },

  getQuickAddFoods: () => foods.quickAdd(),
  searchAllFoods: (query = '', limit = 20) => foods.search(query, limit),
  getTopFoods: (params = {}) => foods.topFoods(params),
  autocomplete: (query) => foods.autocomplete(query),
  getNutritionData: (foodName, weight = 100) => foods.nutritionData(foodName, weight),
  getGeminiNutrition: (query) => getGeminiNutrition(query),
  getCaloriesTrend: (days = 30) => foods.caloriesTrend({ days }),
  getMacrosTrend: (days = 30) => foods.macrosTrend({ days }),
  getHourlyPattern: (params) => foods.hourlyPattern(params || {}),

  hideFromQuickList: async (foodItemId) => {
    await foodRepo.setHidden(foodItemId, true);
    return { success: true };
  },

  copyDayFoods: (sourceDate, targetDate = null) => foods.copyDay(sourceDate || todayLocalDate(), targetDate),
};

export default foodApi;
