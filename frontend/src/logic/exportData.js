// Port of export_data (count_calories_app/views.py) — builds CSV/JSON export
// content client-side from the local DB. Matches the Django column order/format.
import { dbAll } from '../db/sqlite';

function csvField(v) {
  if (v == null) return '';
  const s = String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}
function csvRow(cols) { return cols.map(csvField).join(','); }

/** 'YYYY-MM-DD HH:MM' in local time (Django strftime output). */
function dtMinute(iso) {
  const d = new Date(iso);
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}
function dateOnly(iso) {
  const d = new Date(iso);
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}
/** Python str(timedelta) style: H:MM:SS. */
function durationStr(seconds) {
  const s = Math.max(0, Math.round(Number(seconds) || 0));
  const p = (n) => String(n).padStart(2, '0');
  return `${Math.floor(s / 3600)}:${p(Math.floor((s % 3600) / 60))}:${p(s % 60)}`;
}
const numOrBlank = (v) => (v == null ? '' : Number(v));

export async function buildExport(type = 'all', format = 'csv') {
  if (type === 'all' || format === 'json') {
    const [food, weight, running, body, workouts, wexs] = await Promise.all([
      dbAll('SELECT * FROM food_item'),
      dbAll('SELECT * FROM weight'),
      dbAll('SELECT * FROM running_session'),
      dbAll('SELECT * FROM body_measurement'),
      dbAll('SELECT * FROM workout_session'),
      dbAll('SELECT we.*, e.name AS exercise_name FROM workout_exercise we JOIN exercise e ON e.id = we.exercise_id'),
    ]);
    const data = {
      food_items: food.map((i) => ({ consumed_at: i.consumed_at, product_name: i.product_name, calories: Number(i.calories), protein: Number(i.protein), carbohydrates: Number(i.carbohydrates), fat: Number(i.fat) })),
      weight: weight.map((i) => ({ recorded_at: i.recorded_at, weight: Number(i.weight), notes: i.notes })),
      workouts: workouts.map((w) => ({ date: w.date, name: w.name, notes: w.notes,
        exercises: wexs.filter((e) => e.workout_id === w.id).map((e) => ({ exercise_name: e.exercise_name, sets: e.sets, reps: e.reps, weight: e.weight == null ? null : Number(e.weight), notes: e.notes })) })),
      running: running.map((i) => ({ date: i.date, distance: Number(i.distance), duration: durationStr(i.duration_seconds), notes: i.notes })),
      body_measurements: body.map((i) => ({ date: i.date, neck: numOrNull(i.neck), chest: numOrNull(i.chest), belly: numOrNull(i.belly), notes: i.notes })),
    };
    return { filename: 'all_data.json', mime: 'application/json', content: JSON.stringify(data, null, 2) };
  }

  const lines = [];
  if (type === 'food') {
    lines.push(csvRow(['Date', 'Product Name', 'Calories', 'Protein (g)', 'Carbs (g)', 'Fat (g)']));
    for (const i of await dbAll('SELECT * FROM food_item ORDER BY consumed_at DESC')) {
      lines.push(csvRow([dtMinute(i.consumed_at), i.product_name, Number(i.calories), Number(i.protein), Number(i.carbohydrates), Number(i.fat)]));
    }
    return { filename: 'food_data.csv', mime: 'text/csv', content: lines.join('\n') };
  }
  if (type === 'weight') {
    lines.push(csvRow(['Date', 'Weight (kg)', 'Notes']));
    for (const i of await dbAll('SELECT * FROM weight ORDER BY recorded_at DESC')) {
      lines.push(csvRow([dtMinute(i.recorded_at), Number(i.weight), i.notes || '']));
    }
    return { filename: 'weight_data.csv', mime: 'text/csv', content: lines.join('\n') };
  }
  if (type === 'workout') {
    lines.push(csvRow(['Date', 'Workout Name', 'Exercise', 'Sets', 'Reps', 'Weight (kg)', 'Notes']));
    const workouts = await dbAll('SELECT * FROM workout_session ORDER BY date DESC');
    const wexs = await dbAll('SELECT we.*, e.name AS exercise_name FROM workout_exercise we JOIN exercise e ON e.id = we.exercise_id');
    for (const w of workouts) {
      for (const e of wexs.filter((x) => x.workout_id === w.id)) {
        lines.push(csvRow([dateOnly(w.date), w.name || 'Unnamed', e.exercise_name, e.sets, e.reps, e.weight == null ? '' : Number(e.weight), e.notes || '']));
      }
    }
    return { filename: 'workout_data.csv', mime: 'text/csv', content: lines.join('\n') };
  }
  if (type === 'running') {
    lines.push(csvRow(['Date', 'Distance (km)', 'Duration', 'Notes']));
    for (const i of await dbAll('SELECT * FROM running_session ORDER BY date DESC')) {
      lines.push(csvRow([dateOnly(i.date), Number(i.distance), durationStr(i.duration_seconds), i.notes || '']));
    }
    return { filename: 'running_data.csv', mime: 'text/csv', content: lines.join('\n') };
  }
  if (type === 'body') {
    lines.push(csvRow(['Date', 'Neck', 'Chest', 'Belly', 'Left Biceps', 'Right Biceps', 'Left Triceps', 'Right Triceps',
      'Left Forearm', 'Right Forearm', 'Left Thigh', 'Right Thigh', 'Left Lower Leg', 'Right Lower Leg', 'Butt', 'Notes']));
    for (const i of await dbAll('SELECT * FROM body_measurement ORDER BY date DESC')) {
      lines.push(csvRow([dateOnly(i.date), numOrBlank(i.neck), numOrBlank(i.chest), numOrBlank(i.belly),
        numOrBlank(i.left_biceps), numOrBlank(i.right_biceps), numOrBlank(i.left_triceps), numOrBlank(i.right_triceps),
        numOrBlank(i.left_forearm), numOrBlank(i.right_forearm), numOrBlank(i.left_thigh), numOrBlank(i.right_thigh),
        numOrBlank(i.left_lower_leg), numOrBlank(i.right_lower_leg), numOrBlank(i.butt), i.notes || '']));
    }
    return { filename: 'body_measurements.csv', mime: 'text/csv', content: lines.join('\n') };
  }
  return { filename: 'export.csv', mime: 'text/csv', content: '' };
}

function numOrNull(v) { return v == null ? null : Number(v); }
