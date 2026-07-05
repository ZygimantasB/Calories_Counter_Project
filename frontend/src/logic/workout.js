// Port of api_workouts, api_exercises, api_workout_tables, get_workout_frequency_data,
// get_exercise_progress_data.
import { format } from 'date-fns';
import { round, subDays } from './dates';
import { workoutRepo } from '../db/repositories/workoutRepo';

// ---- api_workouts ----
export async function listWorkoutsWithStats({ days = '90' } = {}) {
  let sessions;
  if (days === 'all') sessions = await workoutRepo.allSessions();
  else {
    const n = parseInt(days, 10);
    sessions = await workoutRepo.listFrom(subDays(new Date(), Number.isNaN(n) ? 90 : n).toISOString());
  }

  const items = [];
  for (const w of sessions) {
    const exs = await workoutRepo.exercisesForWorkout(w.id);
    let totalVolume = 0;
    const exerciseList = exs.map((ex) => {
      const volume = (ex.sets || 0) * (ex.reps || 0) * (ex.weight ? Number(ex.weight) : 0);
      totalVolume += volume;
      return {
        id: ex.id,
        exercise: ex.exercise_name || 'Unknown',
        sets: ex.sets,
        reps: ex.reps,
        weight: ex.weight == null ? null : Number(ex.weight),
        volume: round(volume, 1),
      };
    });
    items.push({
      id: w.id,
      name: w.name,
      date: w.date || null,
      notes: w.notes,
      exercises: exerciseList,
      exercise_count: exerciseList.length,
      total_volume: round(totalVolume, 1),
    });
  }

  const stats = {
    total_workouts: items.length,
    total_exercises: items.reduce((s, i) => s + i.exercise_count, 0),
    total_volume: round(items.reduce((s, i) => s + i.total_volume, 0), 1),
  };
  return { items, stats };
}

// ---- api_exercises ----
export async function exerciseLibrary() {
  const rows = await workoutRepo.libraryAll();
  return { exercises: rows.map((ex) => ({ id: ex.id, name: ex.name, muscle_group: ex.muscle_group, description: ex.description })) };
}

// ---- api_workout_tables ----
function parseTableData(raw) {
  if (raw == null) return { workouts: [], exercises: [] };
  if (typeof raw === 'object') return raw;
  try { return JSON.parse(raw); } catch { return { workouts: [], exercises: [] }; }
}
export async function workoutTables() {
  const rows = await workoutRepo.tablesAll();
  return { tables: rows.map((t) => ({ id: t.id, name: t.name, created_at: t.created_at, data: parseTableData(t.table_data) })) };
}

// ---- get_workout_frequency_data (legacy; unused by pages) ----
export async function workoutFrequency() {
  const rows = await workoutRepo.listFrom(subDays(new Date(), 90).toISOString());
  const byDay = new Map();
  for (const w of rows) {
    const key = format(new Date(w.date), 'yyyy-MM-dd');
    byDay.set(key, (byDay.get(key) || 0) + 1);
  }
  const keys = [...byDay.keys()].sort();
  return { labels: keys, data: keys.map((k) => byDay.get(k)) };
}

// ---- get_exercise_progress_data (legacy; unused by pages) ----
export async function exerciseProgress(exerciseId) {
  if (!exerciseId) return { error: 'No exercise ID provided' };
  const exercise = await workoutRepo.libraryGet(exerciseId);
  if (!exercise) return { error: 'Exercise not found' };
  const all = await workoutRepo.allWorkoutExercises();
  const mine = [];
  for (const we of all.filter((x) => x.exercise_id === Number(exerciseId))) {
    const session = await workoutRepo.getSession(we.workout_id);
    mine.push({ ...we, _date: session?.date });
  }
  mine.sort((a, b) => new Date(a._date) - new Date(b._date));
  return {
    exercise_name: exercise.name,
    labels: mine.map((we) => format(new Date(we._date), 'yyyy-MM-dd')),
    weight: mine.map((we) => (we.weight ? Number(we.weight) : 0)),
    sets: mine.map((we) => we.sets),
    reps: mine.map((we) => we.reps),
    volume: mine.map((we) => (we.weight ? Number(we.weight) * we.sets * we.reps : 0)),
  };
}
