import { describe, it, expect } from 'vitest';
import {
  getISOWeekKey,
  groupByWeek,
  resolveSnapshot,
  computeDeltas,
  computeSummary,
  MEASUREMENT_FIELDS,
} from '../compareUtils.js';

const m1 = { id: 1, date: '2025-04-07T10:00:00', belly: 98, chest: 114, neck: null, butt: 110,
  left_biceps: 43, right_biceps: 43, left_triceps: 35, right_triceps: 35,
  left_forearm: 30, right_forearm: 30, left_thigh: 60, right_thigh: 60,
  left_lower_leg: 40, right_lower_leg: 40 };
const m2 = { id: 2, date: '2025-04-20T10:00:00', belly: 95, chest: 115.7, neck: null, butt: 108,
  left_biceps: 44.5, right_biceps: 44.5, left_triceps: 36, right_triceps: 36,
  left_forearm: 31, right_forearm: 31, left_thigh: 61, right_thigh: 61,
  left_lower_leg: 41, right_lower_leg: 41 };
const m3 = { id: 3, date: '2025-04-27T10:00:00', belly: 93, chest: 116, neck: 38, butt: 107,
  left_biceps: 45, right_biceps: 45, left_triceps: 37, right_triceps: 37,
  left_forearm: 32, right_forearm: 32, left_thigh: 62, right_thigh: 62,
  left_lower_leg: 42, right_lower_leg: 42 };

const measurements = [m3, m2, m1]; // newest first

describe('getISOWeekKey', () => {
  it('returns ISO week key for a date string', () => {
    expect(getISOWeekKey('2025-04-27T10:00:00')).toMatch(/^\d{4}-W\d{2}$/);
  });
  it('two dates in same week return the same key', () => {
    expect(getISOWeekKey('2025-04-21T00:00:00')).toBe(getISOWeekKey('2025-04-27T00:00:00'));
  });
  it('dates in different weeks return different keys', () => {
    expect(getISOWeekKey('2025-04-20T00:00:00')).not.toBe(getISOWeekKey('2025-04-27T00:00:00'));
  });
});

describe('groupByWeek', () => {
  it('groups measurements by ISO week', () => {
    const groups = groupByWeek(measurements);
    expect(Object.keys(groups).length).toBeGreaterThanOrEqual(2);
  });
});

describe('resolveSnapshot - date mode', () => {
  it('returns the entry matching the given id', () => {
    expect(resolveSnapshot(measurements, 'date', 2, 'latest')).toEqual(m2);
  });
  it('returns null for unknown id', () => {
    expect(resolveSnapshot(measurements, 'date', 999, 'latest')).toBeNull();
  });
});

describe('resolveSnapshot - week mode', () => {
  it('latest strategy returns the most recent entry in the week', () => {
    const weekKey = getISOWeekKey(m3.date);
    const result = resolveSnapshot(measurements, 'week', weekKey, 'latest');
    expect(result.id).toBe(m3.id);
  });
  it('average strategy returns averaged values', () => {
    const sameDayM = { ...m2, id: 99, date: m3.date };
    const weekKey = getISOWeekKey(m3.date);
    const result = resolveSnapshot([m3, sameDayM], 'week', weekKey, 'average');
    expect(result.belly).toBeCloseTo(94, 1);
  });
  it('firstlast strategy returns object with first and last keys', () => {
    const weekKey = getISOWeekKey(m3.date);
    const result = resolveSnapshot(measurements, 'week', weekKey, 'firstlast');
    expect(result).toHaveProperty('first');
    expect(result).toHaveProperty('last');
  });
  it('returns null for a week with no entries', () => {
    expect(resolveSnapshot(measurements, 'week', '2020-W01', 'latest')).toBeNull();
  });
});

describe('resolveSnapshot - period mode', () => {
  it('latest strategy returns last entry in range', () => {
    const result = resolveSnapshot(measurements, 'period', { start: '2025-04-01', end: '2025-04-30' }, 'latest');
    expect(result.id).toBe(m3.id);
  });
  it('returns null for an empty range', () => {
    expect(resolveSnapshot(measurements, 'period', { start: '2020-01-01', end: '2020-01-31' }, 'latest')).toBeNull();
  });
});

describe('computeDeltas', () => {
  it('computes correct deltas between two snapshots', () => {
    const deltas = computeDeltas(m1, m2, MEASUREMENT_FIELDS);
    expect(deltas.belly).toBeCloseTo(-3, 1);
    expect(deltas.chest).toBeCloseTo(1.7, 1);
  });
  it('returns null delta when either side is null', () => {
    expect(computeDeltas(m1, m2, ['neck']).neck).toBeNull();
  });
});

describe('computeSummary', () => {
  it('computes weight change and cm totals', () => {
    const deltas = computeDeltas(m1, m3, MEASUREMENT_FIELDS);
    const summary = computeSummary(deltas, 113.6, 101.82);
    expect(summary.weightChange).toBeCloseTo(-11.78, 1);
    expect(summary.totalCmLost).toBeGreaterThan(0);
    expect(summary.improved).toBeGreaterThan(0);
  });
  it('handles null weight gracefully', () => {
    const deltas = computeDeltas(m1, m2, MEASUREMENT_FIELDS);
    expect(computeSummary(deltas, null, null).weightChange).toBeNull();
  });
});
