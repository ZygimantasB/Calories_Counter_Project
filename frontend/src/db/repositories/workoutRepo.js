// Raw DB access for workouts: sessions, per-workout exercises, exercise library,
// and workout tables.
import { dbAll, dbGet, dbRun } from '../sqlite';

export const workoutRepo = {
  // ---- sessions ----
  async listFrom(startIso) {
    if (!startIso) return dbAll(`SELECT * FROM workout_session ORDER BY date DESC;`);
    return dbAll(`SELECT * FROM workout_session WHERE date >= ? ORDER BY date DESC;`, [startIso]);
  },
  async allSessions() { return dbAll(`SELECT * FROM workout_session ORDER BY date DESC;`); },
  async getSession(id) { return dbGet(`SELECT * FROM workout_session WHERE id = ?;`, [id]); },
  async insertSession({ name, date, notes = '' }) {
    const { lastId } = await dbRun(`INSERT INTO workout_session (name, date, notes) VALUES (?, ?, ?);`, [name, date, notes]);
    return lastId;
  },
  async updateSession(id, fields) {
    const cols = []; const vals = [];
    for (const key of ['name', 'date', 'notes']) if (key in fields) { cols.push(`${key} = ?`); vals.push(fields[key]); }
    if (!cols.length) return;
    vals.push(id);
    await dbRun(`UPDATE workout_session SET ${cols.join(', ')} WHERE id = ?;`, vals);
  },
  async removeSession(id) { await dbRun(`DELETE FROM workout_session WHERE id = ?;`, [id]); },

  // ---- per-workout exercises (joined to the library for the name) ----
  async exercisesForWorkout(workoutId) {
    return dbAll(
      `SELECT we.*, e.name AS exercise_name, e.muscle_group AS exercise_muscle
       FROM workout_exercise we LEFT JOIN exercise e ON e.id = we.exercise_id
       WHERE we.workout_id = ? ORDER BY we.id;`, [workoutId],
    );
  },
  async allWorkoutExercises() {
    return dbAll(`SELECT we.*, e.name AS exercise_name FROM workout_exercise we LEFT JOIN exercise e ON e.id = we.exercise_id ORDER BY we.id;`);
  },
  async insertWorkoutExercise({ workout_id, exercise_id, sets = 1, reps = 1, weight = null, notes = '' }) {
    const { lastId } = await dbRun(
      `INSERT INTO workout_exercise (workout_id, exercise_id, sets, reps, weight, notes) VALUES (?, ?, ?, ?, ?, ?);`,
      [workout_id, exercise_id, sets, reps, weight, notes],
    );
    return lastId;
  },
  async updateWorkoutExercise(id, workoutId, fields) {
    const cols = []; const vals = [];
    for (const key of ['sets', 'reps', 'weight', 'notes']) if (key in fields) { cols.push(`${key} = ?`); vals.push(fields[key]); }
    if (!cols.length) return;
    vals.push(id, workoutId);
    await dbRun(`UPDATE workout_exercise SET ${cols.join(', ')} WHERE id = ? AND workout_id = ?;`, vals);
  },
  async removeWorkoutExercise(id, workoutId) {
    await dbRun(`DELETE FROM workout_exercise WHERE id = ? AND workout_id = ?;`, [id, workoutId]);
  },

  // ---- exercise library ----
  async libraryAll() { return dbAll(`SELECT * FROM exercise ORDER BY name;`); },
  async libraryGet(id) { return dbGet(`SELECT * FROM exercise WHERE id = ?;`, [id]); },
  async libraryInsert({ name, muscle_group = '', description = '' }) {
    const { lastId } = await dbRun(`INSERT INTO exercise (name, muscle_group, description) VALUES (?, ?, ?);`, [name, muscle_group, description]);
    return lastId;
  },
  async libraryRemove(id) { await dbRun(`DELETE FROM exercise WHERE id = ?;`, [id]); },

  // ---- workout tables ----
  async tablesAll() { return dbAll(`SELECT * FROM workout_table ORDER BY created_at DESC;`); },
  async tableGet(id) { return dbGet(`SELECT * FROM workout_table WHERE id = ?;`, [id]); },
  async tableInsert({ name, table_data, created_at }) {
    const { lastId } = await dbRun(`INSERT INTO workout_table (name, table_data, created_at) VALUES (?, ?, ?);`, [name, table_data, created_at]);
    return lastId;
  },
  async tableUpdate(id, { name, table_data }) {
    await dbRun(`UPDATE workout_table SET name = ?, table_data = ? WHERE id = ?;`, [name, table_data, id]);
  },
  async tableRemove(id) { await dbRun(`DELETE FROM workout_table WHERE id = ?;`, [id]); },
};

export default workoutRepo;
