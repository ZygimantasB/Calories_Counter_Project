// Offline weight API: same exports/signatures as before, backed by local SQLite.
import * as weightLogic from '../logic/weight';
import { weightRepo } from '../db/repositories/weightRepo';

export const weightApi = {
  getWeightItems: (params = {}) => weightLogic.listWithStats(params),

  addWeight: async (weightData) => {
    const id = await weightRepo.insert({
      weight: weightData.weight,
      notes: weightData.notes ?? '',
      recorded_at: weightData.recorded_at || new Date().toISOString(),
    });
    return { success: true, id };
  },

  deleteWeight: async (weightId) => {
    await weightRepo.remove(weightId);
    return { success: true };
  },

  update: async (id, data) => {
    await weightRepo.update(id, data);
    return { success: true, message: 'Weight entry updated' };
  },

  getWeightData: (days = 365) => weightLogic.weightData({ days }),

  getWeightCaloriesCorrelation: (page = 1) => weightLogic.correlation(page),
};

export default weightApi;
