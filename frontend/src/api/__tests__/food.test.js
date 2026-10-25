// foodApi is now offline (local SQLite). These tests exercise the real adapter
// against an in-memory better-sqlite3 DB standing in for the Capacitor layer.
import { describe, it, expect, vi } from 'vitest';

vi.mock('../../db/sqlite', async () => {
  const { default: Database } = await import('better-sqlite3');
  const { SCHEMA_STATEMENTS } = await import('../../db/schema.js');
  const db = new Database(':memory:');
  db.pragma('foreign_keys = ON');
  for (const stmt of SCHEMA_STATEMENTS) db.exec(stmt);
  db.prepare('INSERT INTO user_settings (id) VALUES (1)').run();
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

const { foodApi } = await import('../food');

describe('foodApi (offline)', () => {
  it('adds a food item and returns success + id', async () => {
    const res = await foodApi.addFood({ name: 'Banana', calories: 105, protein: 1.3, carbs: 27, fat: 0.4 });
    expect(res.success).toBe(true);
    expect(res.id).toBeGreaterThan(0);
  });

  it('rejects an empty product name', async () => {
    const res = await foodApi.addFood({ name: '', calories: 10 });
    expect(res.success).toBe(false);
  });

  it('lists added items with correct contract (name/carbs/hidden keys)', async () => {
    await foodApi.addFood({ name: 'Rice', calories: 130, protein: 2.7, carbs: 28, fat: 0.3 });
    const res = await foodApi.getFoodItems({ days: 'all' });
    expect(res.pagination).toHaveProperty('total_items');
    const item = res.items[0];
    expect(item).toHaveProperty('name');
    expect(item).toHaveProperty('carbs');
    expect(item).toHaveProperty('hidden');
    expect(res.totals.count).toBe(res.pagination.total_items);
  });

  it('updates and deletes a food item', async () => {
    const { id } = await foodApi.addFood({ name: 'Temp', calories: 50 });
    const upd = await foodApi.updateFood(id, { name: 'Renamed', calories: 60 });
    expect(upd.success).toBe(true);
    const del = await foodApi.deleteFood(id);
    expect(del.success).toBe(true);
  });

  it('clamps out-of-range numeric values (parity with server validation)', async () => {
    const { id } = await foodApi.addFood({ name: 'Clamp', calories: -10, fat: 999999 });
    const res = await foodApi.getFoodItems({ days: 'all' });
    const row = res.items.find((i) => i.id === id);
    expect(row.calories).toBe(0);
    expect(row.fat).toBe(50000);
  });

  it('getGeminiNutrition reports not-configured when no endpoint set', async () => {
    await expect(foodApi.getGeminiNutrition('chicken')).rejects.toThrow();
  });
});
