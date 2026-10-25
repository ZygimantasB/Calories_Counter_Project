import { describe, it, expect } from 'vitest';
import { ingredientTotals, perServing, scaled } from '../productMath.js';

const rows = [
  { name: 'Wrap', calories: 200, protein: 6, fat: 5, carbohydrates: 33, quantity: 1 },
  { name: 'Chicken', calories: '330', protein: '62', fat: '7', carbohydrates: '0', quantity: '0.5' },
];

describe('productMath', () => {
  it('sums macros times quantity', () => {
    expect(ingredientTotals(rows)).toEqual({ calories: 365, protein: 37, fat: 8.5, carbohydrates: 33 });
  });

  it('treats blank or invalid values as zero', () => {
    expect(ingredientTotals([{ calories: '', protein: 'x', fat: null, carbohydrates: undefined, quantity: 2 }]))
      .toEqual({ calories: 0, protein: 0, fat: 0, carbohydrates: 0 });
  });

  it('divides by yield and rounds to 2 dp', () => {
    expect(perServing({ calories: 1000, protein: 10, fat: 1, carbohydrates: 0 }, 3))
      .toEqual({ calories: 333.33, protein: 3.33, fat: 0.33, carbohydrates: 0 });
  });

  it('returns zeros for a non-positive yield', () => {
    expect(perServing({ calories: 100, protein: 1, fat: 1, carbohydrates: 1 }, 0))
      .toEqual({ calories: 0, protein: 0, fat: 0, carbohydrates: 0 });
  });

  it('scales by servings', () => {
    expect(scaled({ calories: 250, protein: 20.5, fat: 3, carbohydrates: 10 }, 1.5).protein).toBe(30.75);
  });
});
