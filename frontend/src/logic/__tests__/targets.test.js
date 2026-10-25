import { describe, it, expect } from 'vitest';
import { calculateTdee, recommendedMacros, effectiveTargets } from '../targets';

// Real user profile from the seeded Django data.
const user = {
  age: 33, height: 190, gender: 'male', activity_level: 'moderate',
  fitness_goal: 'ripped', use_auto_macros: 1,
  daily_calorie_target: 2000, protein_target: 150, carbs_target: 200, fat_target: 65,
  current_weight: 105.1,
};
const latest = 105.1;

describe('calculateTdee (Mifflin-St Jeor + activity)', () => {
  it('matches Django for the seeded profile', () => {
    // 10*105.1 + 6.25*190 - 5*33 + 5 = 2078.5 ; *1.55 = 3221.675 -> 3222
    expect(calculateTdee(user, latest)).toBe(3222);
  });
  it('female offset (-161)', () => {
    // male bmr 2078.5 -> female 1912.5 ; *1.55 = 2964.375 -> 2964
    expect(calculateTdee({ ...user, gender: 'female' }, latest)).toBe(2964);
  });
  it('returns null when inputs missing', () => {
    expect(calculateTdee({ ...user, age: null }, latest)).toBeNull();
    expect(calculateTdee(user, null)).toBe(3222); // falls back to current_weight
    expect(calculateTdee({ ...user, current_weight: null }, null)).toBeNull();
  });
});

describe('recommendedMacros (ripped goal)', () => {
  it('matches Django Atwater math exactly', () => {
    const m = recommendedMacros(user, latest);
    // total = 3222 - 750 = 2472 ; protein=round(105.1*2.2)=231 ; fat=round(105.1*0.9)=95
    // carbs = round((2472 - 924 - 855)/4) = round(173.25) = 173
    expect(m).toMatchObject({ protein: 231, fat: 95, carbs: 173, calories: 2472, goal: 'ripped' });
  });
  it('maintain goal has zero offset', () => {
    const m = recommendedMacros({ ...user, fitness_goal: 'maintain' }, latest);
    expect(m.calories).toBe(3222);
  });
});

describe('effectiveTargets', () => {
  it('uses auto macros when enabled and weight present', () => {
    const t = effectiveTargets(user, latest);
    expect(t).toMatchObject({ calories: 2472, protein: 231, carbs: 173, fat: 95, is_auto: true });
  });
  it('falls back to manual when auto disabled', () => {
    const t = effectiveTargets({ ...user, use_auto_macros: 0 }, latest);
    expect(t).toMatchObject({ calories: 2000, protein: 150, carbs: 200, fat: 65, is_auto: false });
  });
});

function round(v, n = 0) { const f = 10 ** n; return Math.round(v * f) / f; }
