// Nutrition values are stored and transported exactly (24.6 kcal, 0.54g) so
// that quick-add can round-trip them without drift. These helpers do the
// rounding that used to happen in the API payload -- at render time only.
import { describe, it, expect } from 'vitest';
import { displayKcal, displayMacro } from '../format';

describe('displayKcal', () => {
  it('rounds to a whole number', () => {
    expect(displayKcal(291.85)).toBe('292');
    expect(displayKcal(24.6)).toBe('25');
    expect(displayKcal(105)).toBe('105');
  });
  it('handles missing values', () => {
    expect(displayKcal(null)).toBe('0');
    expect(displayKcal(undefined)).toBe('0');
    expect(displayKcal('')).toBe('0');
  });
  it('accepts numeric strings', () => {
    expect(displayKcal('268.64')).toBe('269');
  });
});

describe('displayMacro', () => {
  it('rounds to one decimal', () => {
    expect(displayMacro(0.54)).toBe('0.5');
    expect(displayMacro(11.28)).toBe('11.3');
  });
  it('drops a trailing .0 so whole grams read cleanly', () => {
    expect(displayMacro(27)).toBe('27');
    expect(displayMacro(5.0)).toBe('5');
    expect(displayMacro(1.3)).toBe('1.3');
  });
  it('handles missing values', () => {
    expect(displayMacro(null)).toBe('0');
    expect(displayMacro(undefined)).toBe('0');
  });
});
