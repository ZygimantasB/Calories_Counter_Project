// Dev-time script: reads the Django SQLite DB (../db.sqlite3) and emits
// src/assets/seed/seed.json, already shaped to the app's local SQLite schema.
// Not shipped in the APK as a script — only its JSON output is bundled by Vite.
//
// Usage:  node scripts/build-seed.mjs [path-to-db.sqlite3]
import Database from 'better-sqlite3';
import { writeFileSync, mkdirSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SRC_DB = resolve(__dirname, '..', process.argv[2] || '../db.sqlite3');
const OUT = resolve(__dirname, '..', 'src/assets/seed/seed.json');

// Django (USE_TZ=True) stores naive UTC datetimes as "YYYY-MM-DD HH:MM:SS[.ffffff]".
// Normalize to ISO-8601 with an explicit UTC offset so `new Date()` parses it correctly.
function toIso(v) {
  if (v == null || v === '') return null;
  if (typeof v !== 'string') return v;
  // Already ISO?
  if (v.includes('T')) return v;
  const m = v.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})(\.\d+)?/);
  if (!m) return v;
  const frac = m[7] || '';
  return `${m[1]}-${m[2]}-${m[3]}T${m[4]}:${m[5]}:${m[6]}${frac}Z`;
}

const db = new Database(SRC_DB, { readonly: true });
const P = 'count_calories_app_';
const all = (sql) => db.prepare(sql).all();
const one = (sql) => db.prepare(sql).get();

// Map Django rows -> app-schema rows (column names mostly identical).
const seed = {
  version: 1,
  generated_at: new Date().toISOString(),
  food_item: all(`SELECT id,product_name,calories,fat,carbohydrates,protein,consumed_at,hide_from_quick_list FROM ${P}fooditem`).map((r) => ({
    ...r, consumed_at: toIso(r.consumed_at), hide_from_quick_list: r.hide_from_quick_list ? 1 : 0,
  })),
  weight: all(`SELECT id,weight,recorded_at,notes FROM ${P}weight`).map((r) => ({
    ...r, recorded_at: toIso(r.recorded_at),
  })),
  running_session: all(`SELECT id,date,distance,duration,notes FROM ${P}runningsession`).map((r) => ({
    id: r.id, date: toIso(r.date), distance: r.distance,
    duration_seconds: Math.round((Number(r.duration) || 0) / 1_000_000), // Django DurationField = microseconds
    notes: r.notes,
  })),
  exercise: all(`SELECT id,name,description,muscle_group FROM ${P}exercise`),
  workout_session: all(`SELECT id,date,name,notes FROM ${P}workoutsession`).map((r) => ({
    ...r, date: toIso(r.date),
  })),
  workout_exercise: all(`SELECT id,workout_id,exercise_id,sets,reps,weight,notes FROM ${P}workoutexercise`),
  workout_table: all(`SELECT id,name,created_at,table_data FROM ${P}workouttable`).map((r) => ({
    ...r, created_at: toIso(r.created_at),
    // table_data is already a JSON string in SQLite; keep it as a string for the TEXT column.
    table_data: typeof r.table_data === 'string' ? r.table_data : JSON.stringify(r.table_data),
  })),
  body_measurement: all(`SELECT * FROM ${P}bodymeasurement`).map((r) => ({
    ...r, date: toIso(r.date),
  })),
  meal_template: all(`SELECT id,name,created_at FROM ${P}mealtemplate`).map((r) => ({
    ...r, created_at: toIso(r.created_at),
  })),
  meal_template_item: all(`SELECT id,template_id,product_name,calories,protein,fat,carbohydrates FROM ${P}mealtemplateitem`),
  user_settings: (() => {
    const s = one(`SELECT * FROM ${P}usersettings WHERE id=1`);
    if (!s) return null;
    return {
      ...s,
      use_auto_macros: s.use_auto_macros ? 1 : 0,
      meal_reminder_enabled: s.meal_reminder_enabled ? 1 : 0,
      workout_reminder_enabled: s.workout_reminder_enabled ? 1 : 0,
      weight_reminder_enabled: s.weight_reminder_enabled ? 1 : 0,
      created_at: toIso(s.created_at),
      updated_at: toIso(s.updated_at),
    };
  })(),
};

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(seed));

const counts = Object.fromEntries(
  Object.entries(seed).filter(([, v]) => Array.isArray(v)).map(([k, v]) => [k, v.length])
);
console.log('Seed written:', OUT);
console.log('Row counts:', JSON.stringify(counts));
console.log('Settings:', seed.user_settings ? 'present' : 'MISSING');
db.close();
