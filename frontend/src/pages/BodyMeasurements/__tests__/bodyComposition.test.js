import { describe, it, expect } from 'vitest';
import {
  navyBodyFat,
  waistToHip,
  waistToHeight,
  limbImbalance,
  changeQuality,
} from '../bodyComposition.js';

describe('navyBodyFat', () => {
  it('estimates body fat for a male profile', () => {
    // height 180, neck 38, waist 85 -> ~15-16%
    const bf = navyBodyFat({ gender: 'male', height: 180, neck: 38, waist: 85 });
    expect(bf).toBeGreaterThan(10);
    expect(bf).toBeLessThan(25);
  });

  it('estimates body fat for a female profile (needs hip)', () => {
    const bf = navyBodyFat({ gender: 'female', height: 165, neck: 32, waist: 72, hip: 96 });
    expect(bf).toBeGreaterThan(15);
    expect(bf).toBeLessThan(40);
  });

  it('returns null for female without hip', () => {
    expect(navyBodyFat({ gender: 'female', height: 165, neck: 32, waist: 72 })).toBeNull();
  });

  it('returns null when required inputs are missing', () => {
    expect(navyBodyFat({ gender: 'male', height: 180, neck: 38 })).toBeNull();
    expect(navyBodyFat({ gender: 'male', waist: 85, neck: 38 })).toBeNull();
  });

  it('returns null when waist <= neck (invalid log input)', () => {
    expect(navyBodyFat({ gender: 'male', height: 180, neck: 40, waist: 38 })).toBeNull();
  });
});

describe('ratios', () => {
  it('computes waist-to-hip', () => {
    expect(waistToHip(80, 100)).toBe(0.8);
    expect(waistToHip(0, 100)).toBeNull();
  });

  it('computes waist-to-height', () => {
    expect(waistToHeight(90, 180)).toBe(0.5);
    expect(waistToHeight(90, null)).toBeNull();
  });
});

describe('limbImbalance', () => {
  it('flags the bigger side and percentage', () => {
    const r = limbImbalance(40, 42);
    expect(r.bigger).toBe('right');
    expect(r.diff).toBe(2);
    expect(r.pct).toBeCloseTo(4.9, 1);
  });

  it('returns even for equal sides', () => {
    expect(limbImbalance(40, 40).bigger).toBe('even');
  });

  it('returns null when a side is missing', () => {
    expect(limbImbalance(40, null)).toBeNull();
  });
});

describe('changeQuality', () => {
  it('treats shrinking waist as good and growing waist as bad', () => {
    expect(changeQuality('belly', -1)).toBe('good');
    expect(changeQuality('belly', 1)).toBe('bad');
  });

  it('treats growing muscle as good and shrinking muscle as bad', () => {
    expect(changeQuality('left_biceps', 1)).toBe('good');
    expect(changeQuality('left_biceps', -1)).toBe('bad');
  });

  it('treats no change as neutral', () => {
    expect(changeQuality('chest', 0)).toBe('neutral');
    expect(changeQuality('chest', null)).toBe('neutral');
  });
});
