// Date helpers reproducing the Django backend's date semantics on-device.
// Stored datetimes are UTC ISO strings; "today"/"this week" are computed in the
// device's LOCAL timezone (matching how the single-user app is experienced).

/** Local 'YYYY-MM-DD' key for a date/ISO string. */
export function localDateKey(input) {
  const d = input instanceof Date ? input : new Date(input);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** Start of the local day (00:00:00.000) as a Date. */
export function startOfLocalDay(input = new Date()) {
  const d = input instanceof Date ? new Date(input) : new Date(input);
  d.setHours(0, 0, 0, 0);
  return d;
}

/** End of the local day (23:59:59.999) as a Date. */
export function endOfLocalDay(input = new Date()) {
  const d = input instanceof Date ? new Date(input) : new Date(input);
  d.setHours(23, 59, 59, 999);
  return d;
}

/** Monday 00:00 of the week containing `now` (Django: now - now.weekday()). */
export function weekStartMonday(now = new Date()) {
  const d = startOfLocalDay(now);
  const weekday = (d.getDay() + 6) % 7; // JS Sunday=0 -> Monday=0 index
  d.setDate(d.getDate() - weekday);
  return d;
}

/** Days between two dates (floor, matching Python timedelta.days). */
export function daysBetween(a, b) {
  const ms = new Date(b).getTime() - new Date(a).getTime();
  return Math.floor(ms / 86400000);
}

/** Subtract `n` days from a date, returning a new Date. */
export function subDays(input, n) {
  const d = input instanceof Date ? new Date(input) : new Date(input);
  d.setDate(d.getDate() - n);
  return d;
}

/** Convert total seconds to an "H:MM:SS" / "MM:SS" display string. */
export function secondsToDuration(totalSeconds) {
  const s = Math.max(0, Math.round(Number(totalSeconds) || 0));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const pad = (n) => String(n).padStart(2, '0');
  return h > 0 ? `${h}:${pad(m)}:${pad(sec)}` : `${m}:${pad(sec)}`;
}

/** Parse an "HH:MM:SS" or "MM:SS" string to total seconds. */
export function durationToSeconds(str) {
  if (str == null) return 0;
  if (typeof str === 'number') return Math.round(str);
  const parts = String(str).split(':').map((p) => parseInt(p, 10) || 0);
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  return parts[0] || 0;
}

/** Round to `n` decimal places (default 0), returning a Number (like Python round). */
export function round(value, n = 0) {
  const f = 10 ** n;
  return Math.round((Number(value) || 0) * f) / f;
}
