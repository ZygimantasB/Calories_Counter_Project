// Offline workout API: same exports/signatures, backed by local SQLite.
import * as workoutLogic from '../logic/workout';
import { workoutRepo } from '../db/repositories/workoutRepo';

function normalizeDate(value) {
  if (!value) return new Date().toISOString();
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split('-').map(Number);
    return new Date(y, m - 1, d, 12, 0, 0).toISOString();
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? new Date().toISOString() : parsed.toISOString();
}
function numOrNull(v) { return v === '' || v == null ? null : Number(v); }

export const workoutApi = {
  getWorkouts: (params = {}) => workoutLogic.listWorkoutsWithStats(params),
  getExercises: () => workoutLogic.exerciseLibrary(),
  getWorkoutFrequency: (/* days */) => workoutLogic.workoutFrequency(),
  getExerciseProgress: (exerciseId = null) => workoutLogic.exerciseProgress(exerciseId),
  getWorkoutTables: () => workoutLogic.workoutTables(),

  saveWorkoutTable: async (tableData) => {
    const name = tableData.name || 'Workout Table';
    const data = JSON.stringify(tableData.data ?? {});
    if (tableData.id) {
      await workoutRepo.tableUpdate(tableData.id, { name, table_data: data });
      return { success: true, id: tableData.id };
    }
    const id = await workoutRepo.tableInsert({ name, table_data: data, created_at: new Date().toISOString() });
    return { success: true, id };
  },
  deleteWorkoutTable: async (tableId) => { await workoutRepo.tableRemove(tableId); return { success: true }; },

  add: async (data) => {
    const id = await workoutRepo.insertSession({ name: data.name ?? 'Workout', date: normalizeDate(data.date), notes: data.notes ?? '' });
    return { success: true, id };
  },
  update: async (id, data) => {
    const fields = {};
    if ('name' in data) fields.name = data.name;
    if ('notes' in data) fields.notes = data.notes;
    if ('date' in data) fields.date = normalizeDate(data.date);
    await workoutRepo.updateSession(id, fields);
    return { success: true };
  },
  delete: async (id) => { await workoutRepo.removeSession(id); return { success: true }; },

  addExercise: async (workoutId, data) => {
    const id = await workoutRepo.insertWorkoutExercise({
      workout_id: workoutId, exercise_id: data.exercise_id,
      sets: data.sets ?? 1, reps: data.reps ?? 1,
      weight: data.weight ? numOrNull(data.weight) : null, notes: data.notes ?? '',
    });
    return { success: true, id };
  },
  updateExercise: async (workoutId, exerciseId, data) => {
    const fields = {};
    for (const f of ['sets', 'reps', 'notes']) if (f in data) fields[f] = data[f];
    if ('weight' in data) fields.weight = data.weight ? numOrNull(data.weight) : null;
    await workoutRepo.updateWorkoutExercise(exerciseId, workoutId, fields);
    return { success: true };
  },
  deleteExercise: async (workoutId, exerciseId) => {
    await workoutRepo.removeWorkoutExercise(exerciseId, workoutId);
    return { success: true };
  },

  addExerciseToLibrary: async (data) => {
    const name = String(data.name ?? '').trim();
    if (!name) return { success: false, message: 'Exercise name is required' };
    const id = await workoutRepo.libraryInsert({ name, muscle_group: data.muscle_group ?? '', description: data.description ?? '' });
    return { success: true, id };
  },
  deleteExerciseFromLibrary: async (id) => { await workoutRepo.libraryRemove(id); return { success: true }; },
};

export default workoutApi;
