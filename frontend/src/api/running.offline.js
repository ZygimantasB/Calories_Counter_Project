// Offline running API: same exports/signatures, backed by local SQLite.
import * as runningLogic from '../logic/running';
import { runningRepo } from '../db/repositories/runningRepo';

export const runningApi = {
  getRunningItems: (params = {}) => runningLogic.listWithStats(params),

  addSession: async (sessionData) => {
    const id = await runningRepo.insert({
      date: runningLogic.normalizeDate(sessionData.date),
      distance: sessionData.distance,
      duration_seconds: runningLogic.parseDurationField(sessionData.duration),
      notes: sessionData.notes ?? '',
    });
    return { success: true, id };
  },

  update: async (id, data) => {
    const fields = {};
    if ('date' in data) fields.date = runningLogic.normalizeDate(data.date);
    if ('distance' in data) fields.distance = data.distance;
    if ('duration' in data) fields.duration_seconds = runningLogic.parseDurationField(data.duration);
    if ('notes' in data) fields.notes = data.notes ?? '';
    await runningRepo.update(id, fields);
    return { success: true };
  },

  delete: async (id) => {
    await runningRepo.remove(id);
    return { success: true };
  },

  getRunningData: (days = 365) => runningLogic.runningData({ days }),
};

export default runningApi;
