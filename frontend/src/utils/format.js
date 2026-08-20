// Display formatting for nutrition values.
//
// The API returns nutrition exactly as stored (24.6 kcal, 0.54g protein) so a
// quick-add tap can write the value back unchanged. Rounding it before storage
// left a second, degraded variant of the same food on every tap, so rounding
// now happens here -- at render time -- and nowhere else.

/** Calories as a whole number, for display. */
export function displayKcal(value) {
  const n = Number(value);
  return String(Math.round(Number.isFinite(n) ? n : 0));
}

/** Macro grams to one decimal, without a trailing '.0'. */
export function displayMacro(value) {
  const n = Number(value);
  const rounded = Math.round((Number.isFinite(n) ? n : 0) * 10) / 10;
  return String(rounded);
}
