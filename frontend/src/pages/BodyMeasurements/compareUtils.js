import { parseISO, getISOWeek, getISOWeekYear, isWithinInterval, startOfDay, endOfDay } from 'date-fns';

export const MEASUREMENT_FIELDS = [
  'neck', 'chest', 'belly', 'butt',
  'left_biceps', 'right_biceps', 'left_triceps', 'right_triceps',
  'left_forearm', 'right_forearm',
  'left_thigh', 'right_thigh', 'left_lower_leg', 'right_lower_leg',
];

export function getISOWeekKey(dateStr) {
  const d = parseISO(dateStr);
  const week = String(getISOWeek(d)).padStart(2, '0');
  return `${getISOWeekYear(d)}-W${week}`;
}

export function groupByWeek(measurements) {
  const groups = {};
  for (const m of measurements) {
    if (!m.date) continue;
    const key = getISOWeekKey(m.date);
    if (!groups[key]) groups[key] = [];
    groups[key].push(m);
  }
  return groups;
}

function pickLatest(entries) {
  return entries.reduce((best, e) => !best || e.date > best.date ? e : best, null);
}

function pickFirst(entries) {
  return entries.reduce((best, e) => !best || e.date < best.date ? e : best, null);
}

function computeAverage(entries) {
  if (!entries.length) return null;
  const averaged = { date: pickLatest(entries).date };
  for (const field of MEASUREMENT_FIELDS) {
    const vals = entries.map(e => e[field]).filter(v => v != null);
    averaged[field] = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
  }
  return averaged;
}

export function resolveSnapshot(measurements, mode, selector, strategy) {
  if (mode === 'date') {
    return measurements.find(m => m.id === selector) || null;
  }

  let entries = [];

  if (mode === 'week') {
    entries = measurements.filter(m => m.date && getISOWeekKey(m.date) === selector);
  }

  if (mode === 'period') {
    const { start, end } = selector;
    entries = measurements.filter(m => {
      if (!m.date) return false;
      return isWithinInterval(parseISO(m.date), {
        start: startOfDay(parseISO(start)),
        end: endOfDay(parseISO(end)),
      });
    });
  }

  if (!entries.length) return null;
  if (strategy === 'latest') return pickLatest(entries);
  if (strategy === 'average') return computeAverage(entries);
  if (strategy === 'firstlast') return { first: pickFirst(entries), last: pickLatest(entries) };
  return pickLatest(entries);
}

export function computeDeltas(sideA, sideB, fields) {
  const deltas = {};
  for (const field of fields) {
    const a = sideA?.[field] ?? null;
    const b = sideB?.[field] ?? null;
    deltas[field] = a != null && b != null ? parseFloat((b - a).toFixed(2)) : null;
  }
  return deltas;
}

export function computeSummary(deltas, weightA, weightB) {
  const values = Object.values(deltas).filter(v => v != null);
  const improved = values.filter(v => v < 0).length;
  const worsened = values.filter(v => v > 0).length;
  const totalCmLost = parseFloat(
    Math.abs(values.filter(v => v < 0).reduce((s, v) => s + v, 0)).toFixed(2)
  );
  const totalCmGained = parseFloat(
    values.filter(v => v > 0).reduce((s, v) => s + v, 0).toFixed(2)
  );
  const weightChange = weightA != null && weightB != null
    ? parseFloat((weightB - weightA).toFixed(2)) : null;
  return { weightChange, totalCmLost, totalCmGained, improved, worsened };
}
