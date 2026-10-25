// Port of api_body_measurements, get_body_measurements_data, export_body_measurements_csv.
import { round } from './dates';
import { bodyRepo, METRIC_FIELDS } from '../db/repositories/bodyRepo';
import { weightRepo } from '../db/repositories/weightRepo';

const CHANGE_FIELDS = ['neck', 'chest', 'belly', 'left_biceps', 'right_biceps', 'butt'];

function num(v) { return v == null ? null : Number(v); }
function localDateKey(iso) {
  const d = new Date(iso);
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function serialize(row) {
  const item = { id: row.id, date: row.date || null };
  for (const f of METRIC_FIELDS) item[f] = row[f] ? Number(row[f]) : null;
  item.notes = row.notes;
  item.changes = {};
  return item;
}

// ---- api_body_measurements (latest 50, with change-from-previous) ----
export async function listMeasurements() {
  const rows = await bodyRepo.all(50); // desc
  const asc = [...rows].reverse();
  const items = [];
  let prev = null;
  for (const m of asc) {
    const item = serialize(m);
    if (prev) {
      for (const f of CHANGE_FIELDS) {
        const cur = m[f]; const pv = prev[f];
        if (cur && pv) item.changes[f] = round(Number(cur) - Number(pv), 1);
      }
    }
    items.push(item);
    prev = m;
  }
  items.reverse(); // most recent first
  return { items };
}

// ---- get_body_measurements_data (legacy chart; unused by pages) ----
export async function measurementsData() {
  const rows = await bodyRepo.allAsc();
  const empty = { dates: [], weight: [] };
  for (const f of METRIC_FIELDS) empty[f] = [];
  if (!rows.length) return empty;

  const weights = await weightRepo.all();
  const weightByDate = new Map();
  for (const w of weights) {
    const key = localDateKey(w.recorded_at);
    if (!weightByDate.has(key)) weightByDate.set(key, Number(w.weight));
  }

  const out = { dates: rows.map((m) => localDateKey(m.date)), weight: [] };
  for (const f of METRIC_FIELDS) out[f] = rows.map((m) => num(m[f]));
  out.weight = rows.map((m) => {
    const v = weightByDate.get(localDateKey(m.date));
    return v == null ? null : v;
  });
  return out;
}

// ---- export_body_measurements_csv (returns CSV string; adapter wraps in Blob) ----
export async function exportCsvContent() {
  const rows = await bodyRepo.all(); // desc
  const weights = await weightRepo.all();
  const weightByDate = new Map();
  for (const w of weights) {
    const key = localDateKey(w.recorded_at);
    if (!weightByDate.has(key)) weightByDate.set(key, Number(w.weight));
  }

  const header = ['Date', 'Weight (kg)', 'Neck (cm)', 'Chest (cm)', 'Belly/Waist (cm)',
    'Left Biceps (cm)', 'Right Biceps (cm)', 'Left Triceps (cm)', 'Right Triceps (cm)',
    'Left Forearm (cm)', 'Right Forearm (cm)', 'Left Thigh (cm)', 'Right Thigh (cm)',
    'Left Lower Leg (cm)', 'Right Lower Leg (cm)', 'Butt/Glutes (cm)', 'Notes'];

  const field = (v) => {
    if (v == null || v === '') return '';
    const s = String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const numOrBlank = (v) => (v == null ? '' : Number(v));

  const lines = [header.map(field).join(',')];
  for (const m of rows) {
    const w = weightByDate.get(localDateKey(m.date));
    const row = [
      localDateKey(m.date), w == null ? '' : w,
      numOrBlank(m.neck), numOrBlank(m.chest), numOrBlank(m.belly),
      numOrBlank(m.left_biceps), numOrBlank(m.right_biceps), numOrBlank(m.left_triceps), numOrBlank(m.right_triceps),
      numOrBlank(m.left_forearm), numOrBlank(m.right_forearm), numOrBlank(m.left_thigh), numOrBlank(m.right_thigh),
      numOrBlank(m.left_lower_leg), numOrBlank(m.right_lower_leg), numOrBlank(m.butt),
      (m.notes || '').replace(/[\r\n]/g, ' ').trim(),
    ];
    lines.push(row.map(field).join(','));
  }
  return lines.join('\n');
}
