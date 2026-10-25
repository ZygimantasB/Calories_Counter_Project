// End-to-end offline-stack test: runs the real repositories + logic against the
// real seeded user data, using better-sqlite3 as a synchronous stand-in for the
// Capacitor SQLite layer (same SQL, same schema, same seed.json).
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
    db.prepare(`INSERT INTO user_settings (${cols.join(',')}) VALUES (${cols.map(() => '?').join(',')})`)
      .run(cols.map((c) => seed.user_settings[c]));
  }

  return {
    initDb: async () => db,
    getDb: () => db,
    persist: async () => {},
    dbAll: async (sql, params = []) => db.prepare(sql).all(...params),
    dbGet: async (sql, params = []) => db.prepare(sql).get(...params) ?? null,
    dbRun: async (sql, params = []) => {
      const r = db.prepare(sql).run(...params);
      return { changes: r.changes, lastId: Number(r.lastInsertRowid) };
    },
  };
});

// Row counts come from the seed itself: the point is that the offline stack
// sees every seeded row, not that the seed has one particular size.
const seedData = (await import('../../assets/seed/seed.json')).default;
const SEEDED_FOODS = seedData.food_item.length;
const SEEDED_WEIGHTS = seedData.weight.length;

const foods = await import('../foods');
const weightLogic = await import('../weight');
const { buildDashboard } = await import('../dashboard');

describe('offline stack against real seeded data', () => {
  it('food list totals cover every seeded item', async () => {
    const res = await foods.listWithTotals({ days: 'all', per_page: 50 });
    expect(res.pagination.total_items).toBe(SEEDED_FOODS);
    expect(res.items.length).toBe(50);
    expect(res.totals.calories).toBeGreaterThan(0);
  });

  it('quick-add returns up to 15 grouped foods', async () => {
    const { foods: qa } = await foods.quickAdd();
    expect(qa.length).toBeGreaterThan(0);
    expect(qa.length).toBeLessThanOrEqual(15);
    expect(qa[0]).toHaveProperty('name');
    expect(qa[0]).toHaveProperty('calories');
  });

  it('search filters by name', async () => {
    const res = await foods.search('', 20);
    expect(res.results.length).toBeGreaterThan(0);
    expect(res.total).toBe(res.results.length);
  });

  it('weight list covers every seeded entry with stats', async () => {
    const res = await weightLogic.listWithStats({ days: 'all' });
    expect(res.items.length).toBe(SEEDED_WEIGHTS);
    expect(res.stats.current).toBeGreaterThan(0);
    expect(res.stats.bmi).toBeGreaterThan(0);
    expect(typeof res.stats.change_rate).toBe('number');
  });

  it('weight-calories correlation paginates by 10', async () => {
    const res = await weightLogic.correlation(1);
    expect(res.correlation_data.length).toBe(10);
    expect(res.pagination.current_page).toBe(1);
    expect(res.correlation_data[0]).toHaveProperty('daily_avg_calories');
  });

  it('dashboard builds with auto (ripped) goals', async () => {
    const d = await buildDashboard();
    expect(d.goals.is_auto).toBe(true);
    expect(d.goals.fitness_goal).toBe('ripped');
    expect(d.goals.daily_calories).toBeGreaterThan(1500);
    expect(d.recent_foods.length).toBeGreaterThan(0);
    expect(d.recent_foods[0]).toHaveProperty('product_name');
    expect(typeof d.streak).toBe('number');
  });

  it('top foods returns ranked lists', async () => {
    const res = await foods.topFoods({ days: 'all' });
    expect(res.by_frequency[0].count).toBeGreaterThanOrEqual(res.by_frequency[1].count);
    expect(res.by_calories[0].total_calories).toBeGreaterThanOrEqual(res.by_calories[1].total_calories);
  });
});
