// End-to-end test of the Phase 2/3 domains (running, body, workout, meal
// templates, analytics) through their API adapters, against a better-sqlite3
// stand-in seeded with the real user data.
import { describe, it, expect, vi } from 'vitest';

vi.mock('../../db/sqlite', async () => {
  const { default: Database } = await import('better-sqlite3');
  const { SCHEMA_STATEMENTS, SEED_COLUMNS } = await import('../../db/schema.js');
  const seed = (await import('../../assets/seed/seed.json')).default;

  const db = new Database(':memory:');
  db.pragma('foreign_keys = ON');
  for (const stmt of SCHEMA_STATEMENTS) db.exec(stmt);
  for (const [table, cols] of Object.entries(SEED_COLUMNS)) {
    const rows = seed[table] || [];
    if (!rows.length) continue;
    const insert = db.prepare(`INSERT INTO ${table} (${cols.join(',')}) VALUES (${cols.map(() => '?').join(',')})`);
    const tx = db.transaction((rs) => { for (const r of rs) insert.run(cols.map((c) => (r[c] === undefined ? null : r[c]))); });
    tx(rows);
  }
  if (seed.user_settings) {
    const cols = Object.keys(seed.user_settings);
    db.prepare(`INSERT INTO user_settings (${cols.join(',')}) VALUES (${cols.map(() => '?').join(',')})`).run(cols.map((c) => seed.user_settings[c]));
  }
  return {
    initDb: async () => db, getDb: () => db, persist: async () => {},
    dbAll: async (sql, params = []) => db.prepare(sql).all(...params),
    dbGet: async (sql, params = []) => db.prepare(sql).get(...params) ?? null,
    dbRun: async (sql, params = []) => { const r = db.prepare(sql).run(...params); return { changes: r.changes, lastId: Number(r.lastInsertRowid) }; },
  };
});

const { runningApi } = await import('../../api/running');
const { bodyMeasurementsApi } = await import('../../api/bodyMeasurements');
const { workoutApi } = await import('../../api/workout');
const { mealTemplatesApi } = await import('../../api/mealTemplates');
const { analyticsApi } = await import('../../api/analytics');
const { foodApi } = await import('../../api/food');

describe('running (offline)', () => {
  it('lists seeded runs with computed pace/speed and stats', async () => {
    const res = await runningApi.getRunningItems({ days: 'all' });
    expect(res.items.length).toBe(7);
    expect(res.stats.total_runs).toBe(7);
    const r = res.items[0];
    expect(r).toHaveProperty('duration');
    expect(r).toHaveProperty('pace');
    expect(r.speed).toBeGreaterThan(0);
  });
  it('adds and deletes a run', async () => {
    const add = await runningApi.addSession({ date: '2026-07-01', distance: 5, duration: '00:30:00', notes: 't' });
    expect(add.success).toBe(true);
    const del = await runningApi.delete(add.id);
    expect(del.success).toBe(true);
  });
});

describe('body measurements (offline)', () => {
  it('lists latest (<=50) with change-from-previous', async () => {
    const res = await bodyMeasurementsApi.getMeasurements();
    expect(res.items.length).toBeGreaterThan(0);
    expect(res.items.length).toBeLessThanOrEqual(50);
    expect(res.items[0]).toHaveProperty('changes');
  });
  it('exports a CSV blob', async () => {
    const blob = await bodyMeasurementsApi.exportCsv();
    expect(blob).toBeInstanceOf(Blob);
    expect(blob.size).toBeGreaterThan(0);
  });
});

describe('workout (offline)', () => {
  it('creates a workout with an exercise and reports volume', async () => {
    const lib = await workoutApi.addExerciseToLibrary({ name: 'Bench Press', muscle_group: 'chest' });
    const w = await workoutApi.add({ name: 'Push Day', date: '2026-07-02' });
    const ex = await workoutApi.addExercise(w.id, { exercise_id: lib.id, sets: 3, reps: 10, weight: 60 });
    expect(ex.success).toBe(true);
    const res = await workoutApi.getWorkouts({ days: 'all' });
    const item = res.items.find((x) => x.id === w.id);
    expect(item.exercises.length).toBe(1);
    expect(item.total_volume).toBe(1800); // 3*10*60
  });
  it('lists the exercise library', async () => {
    const res = await workoutApi.getExercises();
    expect(res.exercises.length).toBeGreaterThan(0);
  });
});

describe('meal templates (offline)', () => {
  it('saves a template from today and applies it', async () => {
    await foodApi.addFood({ name: 'Oatmeal', calories: 300, protein: 10, carbs: 50, fat: 5 });
    const saved = await mealTemplatesApi.save('Breakfast');
    expect(saved.success).toBe(true);
    expect(saved.items_count).toBeGreaterThan(0);
    const list = await mealTemplatesApi.list();
    expect(list.templates.length).toBeGreaterThan(0);
    const applied = await mealTemplatesApi.apply(saved.id);
    expect(applied.items_logged).toBe(saved.items_count);
  });
});

describe('analytics (offline)', () => {
  it('getAnalytics returns all sections with sane values', async () => {
    const a = await analyticsApi.getAnalytics({ period: 'all' });
    for (const k of ['daily_data', 'weekly_summary', 'overall_stats', 'streaks', 'weight_analysis',
      'weight_pace', 'macro_analysis', 'nutrition_score', 'weekly_reports', 'monthly_reports',
      'top_foods', 'meal_timing', 'calorie_distribution']) {
      expect(a).toHaveProperty(k);
    }
    expect(Array.isArray(a.weekly_reports)).toBe(true);
    if (a.nutrition_score.total != null) {
      expect(a.nutrition_score.total).toBeGreaterThanOrEqual(0);
      expect(a.nutrition_score.total).toBeLessThanOrEqual(100);
    }
    expect(a.weight_analysis.days_tracked).toBeGreaterThan(0);
  });
  it('yearlyTrends returns 12 months for last12', async () => {
    const t = await analyticsApi.getYearlyTrends('last12');
    expect(t.months.length).toBe(12);
    expect(t.months[0]).toHaveProperty('consistency');
  });
  it('monthCompare returns both months', async () => {
    const c = await analyticsApi.getMonthCompare('2026-06', '2026-07');
    expect(c.month_a.month).toBe('2026-06');
    expect(c.month_b.month).toBe('2026-07');
  });
});
