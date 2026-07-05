// Port of api_running_items, api_add_running, api_update_running, get_running_data.
import { round, subDays, durationToSeconds } from './dates';
import { runningRepo } from '../db/repositories/runningRepo';

/** Python str(timedelta) style H:MM:SS. */
function durationStr(seconds) {
  const s = Math.max(0, Math.round(Number(seconds) || 0));
  const p = (n) => String(n).padStart(2, '0');
  return `${Math.floor(s / 3600)}:${p(Math.floor((s % 3600) / 60))}:${p(s % 60)}`;
}

export function serializeRun(row) {
  const seconds = Number(row.duration_seconds) || 0;
  const distance = row.distance ? Number(row.distance) : 0;
  const speed = seconds > 0 ? distance / (seconds / 3600) : 0;
  const paceSeconds = distance > 0 ? seconds / distance : 0;
  return {
    id: row.id,
    date: row.date || null,
    distance,
    duration: seconds ? durationStr(seconds) : null,
    duration_minutes: round(seconds / 60, 1),
    speed: round(speed, 2),
    pace: paceSeconds ? `${Math.floor(paceSeconds / 60)}:${String(Math.floor(paceSeconds % 60)).padStart(2, '0')}` : null,
    notes: row.notes,
  };
}

// ---- api_running_items ----
export async function listWithStats({ days = '365' } = {}) {
  let rows;
  if (days === 'all') rows = await runningRepo.all();
  else {
    const n = parseInt(days, 10);
    rows = await runningRepo.listFrom(subDays(new Date(), Number.isNaN(n) ? 365 : n).toISOString());
  }
  const items = rows.map(serializeRun);
  const totalDistance = items.reduce((s, i) => s + i.distance, 0);
  const totalDuration = items.reduce((s, i) => s + i.duration_minutes, 0);
  const stats = {
    total_runs: items.length,
    total_distance: round(totalDistance, 1),
    total_duration: round(totalDuration, 1),
    avg_distance: items.length ? round(totalDistance / items.length, 1) : 0,
    avg_duration: items.length ? round(totalDuration / items.length, 1) : 0,
    avg_speed: items.length ? round(items.reduce((s, i) => s + i.speed, 0) / items.length, 2) : 0,
  };
  return { items, stats };
}

/** Resolve add/update payload duration (string HH:MM:SS / MM:SS) to seconds. */
export function parseDurationField(value, fallback = 1800) {
  if (value == null) return fallback;
  return durationToSeconds(value);
}

/** Normalise an incoming date (ISO or YYYY-MM-DD) to an ISO string. */
export function normalizeDate(value) {
  if (!value) return new Date().toISOString();
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split('-').map(Number);
    return new Date(y, m - 1, d, 12, 0, 0).toISOString();
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? new Date().toISOString() : parsed.toISOString();
}

// ---- get_running_data (legacy chart; unused by pages, kept for signature parity) ----
export async function runningData({ days = '90', min_distance = 3 } = {}) {
  const now = new Date();
  const min = Number(min_distance) || 3;
  let rows = days === 'all' ? await runningRepo.all() : await runningRepo.listFrom(subDays(now, parseInt(days, 10) || 90).toISOString());
  rows = rows.filter((r) => Number(r.distance) >= min).sort((a, b) => new Date(a.date) - new Date(b.date));
  const p = (n) => String(n).padStart(2, '0');
  const labels = rows.map((r) => { const d = new Date(r.date); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; });
  const distances = rows.map((r) => Number(r.distance));
  const durations = rows.map((r) => (Number(r.duration_seconds) || 0) / 60);
  const total = distances.reduce((s, v) => s + v, 0);
  return {
    labels, distances, durations,
    stats: {
      total_distance: round(total, 1),
      total_sessions: rows.length,
      avg_distance: rows.length ? round(total / rows.length, 1) : 0,
      longest_run: rows.length ? round(Math.max(...distances), 1) : 0,
    },
  };
}
