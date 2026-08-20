// Regression test: quick-add and search must report the most recently logged
// nutrition for a product name, never an average across differing history.
//
// Bug: groupByName() summed every row sharing a product_name and quickAdd()/
// search() divided by count. When the same name had been logged with different
// nutrition (an AI lookup returning different numbers later on), the tile showed
// a blend that was never true for any entry -- and because tapping the tile
// saves what it displays, that fabricated value fed the next average.
//
// Real case: 'Bananas (1)' had 152 rows at 15g protein and 68 rows at 0.3g,
// so the tile advertised 10.5g protein for a banana.
import { describe, it, expect, vi, beforeEach } from 'vitest';

const rows = [];
vi.mock('../../db/repositories/foodRepo', () => ({
  foodRepo: { all: async () => rows },
}));

const foods = await import('../foods');

const OLD_WRONG = { calories: 168.5, protein: 15, fat: 0.5, carbohydrates: 26 };
const NEW_TRUTH = { calories: 105, protein: 1.3, fat: 0.4, carbohydrates: 27 };

beforeEach(() => {
  rows.length = 0;
  // Five old entries with the wrong profile...
  for (let i = 0; i < 5; i += 1) {
    rows.push({
      id: i + 1, product_name: 'Bananas (1)', ...OLD_WRONG,
      consumed_at: `2026-01-0${i + 1}T12:00:00.000Z`, hide_from_quick_list: 0,
    });
  }
  // ...and one newer, corrected entry.
  rows.push({
    id: 6, product_name: 'Bananas (1)', ...NEW_TRUTH,
    consumed_at: '2026-08-19T12:00:00.000Z', hide_from_quick_list: 0,
  });
});

describe('offline quick-add / search nutrition', () => {
  it('quickAdd reports the latest entry, not the average', async () => {
    const { foods: qa } = await foods.quickAdd();
    const banana = qa.find((f) => f.name === 'Bananas (1)');
    // Average protein would be (5*15 + 1.3)/6 = 12.7 -- never logged.
    expect(banana.protein).toBe(1.3);
    expect(banana.calories).toBe(105);
    expect(banana.fat).toBe(0.4);
    expect(banana.carbs).toBe(27);
  });

  it('search reports the latest entry, not the average', async () => {
    const { results } = await foods.search('banana', 20);
    const banana = results.find((r) => r.name === 'Bananas (1)');
    expect(banana.protein).toBe(1.3);
    expect(banana.calories).toBe(105);
    expect(banana.count).toBe(6);
  });

  it('re-adding what quick-add displayed does not drift the value', async () => {
    const before = (await foods.quickAdd()).foods.find((f) => f.name === 'Bananas (1)');
    rows.push({
      id: 7, product_name: 'Bananas (1)',
      calories: before.calories, protein: before.protein,
      fat: before.fat, carbohydrates: before.carbs,
      consumed_at: '2026-08-20T12:00:00.000Z', hide_from_quick_list: 0,
    });
    const after = (await foods.quickAdd()).foods.find((f) => f.name === 'Bananas (1)');
    expect(after).toEqual(before);
  });

  it('ties on consumed_at resolve deterministically to the highest id', async () => {
    rows.push({
      id: 99, product_name: 'Bananas (1)', calories: 98.7, protein: 1, fat: 0.3, carbohydrates: 23,
      consumed_at: '2026-08-19T12:00:00.000Z', hide_from_quick_list: 0,
    });
    const banana = (await foods.quickAdd()).foods.find((f) => f.name === 'Bananas (1)');
    expect(banana.protein).toBe(1);
    expect(banana.calories).toBe(98.7);
  });

  it('preserves exact values so a quick-add round-trip creates no new variant', async () => {
    rows.length = 0;
    rows.push({
      id: 1, product_name: 'morkos 60 g.',
      calories: 24.6, protein: 0.54, fat: 0.12, carbohydrates: 5.76,
      consumed_at: '2026-08-01T12:00:00.000Z', hide_from_quick_list: 0,
    });
    const tile = (await foods.quickAdd()).foods.find((f) => f.name === 'morkos 60 g.');
    // Rounding here would write 25 kcal / 0.5g over the real 24.6 / 0.54.
    expect(tile.calories).toBe(24.6);
    expect(tile.protein).toBe(0.54);
    expect(tile.fat).toBe(0.12);
    expect(tile.carbs).toBe(5.76);
  });
});
