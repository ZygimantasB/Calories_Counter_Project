// Body-composition helpers derived from tape measurements.
// belly = waist, butt = hip. All measurements in centimetres.

// Per-field goal direction: is a smaller number "better" (leaner) or a larger
// number "better" (more muscle)? Used for goal-aware trend coloring.
export const MEASUREMENT_GOALS = {
  neck: 'lower',
  chest: 'higher',
  belly: 'lower',
  butt: 'higher',
  left_biceps: 'higher',
  right_biceps: 'higher',
  left_triceps: 'higher',
  right_triceps: 'higher',
  left_forearm: 'higher',
  right_forearm: 'higher',
  left_thigh: 'higher',
  right_thigh: 'higher',
  left_lower_leg: 'higher',
  right_lower_leg: 'higher',
};

// Left/right pairs for symmetry analysis: [key, label]
export const SYMMETRY_PAIRS = [
  { base: 'biceps', label: 'Biceps', left: 'left_biceps', right: 'right_biceps' },
  { base: 'triceps', label: 'Triceps', left: 'left_triceps', right: 'right_triceps' },
  { base: 'forearm', label: 'Forearm', left: 'left_forearm', right: 'right_forearm' },
  { base: 'thigh', label: 'Thigh', left: 'left_thigh', right: 'right_thigh' },
  { base: 'calf', label: 'Calf', left: 'left_lower_leg', right: 'right_lower_leg' },
];

const log10 = (x) => Math.log(x) / Math.LN10;

/**
 * US Navy body-fat estimate (%). Returns null when required inputs are missing
 * or invalid (e.g. waist <= neck).
 * @param {{gender?: string, height?: number, neck?: number, waist?: number, hip?: number}} p
 */
export function navyBodyFat({ gender, height, neck, waist, hip }) {
  if (!height || !neck || !waist) return null;
  const isFemale = String(gender).toLowerCase() === 'female';

  if (isFemale) {
    if (!hip) return null;
    const inner = waist + hip - neck;
    if (inner <= 0) return null;
    const bf =
      495 / (1.29579 - 0.35004 * log10(inner) + 0.22100 * log10(height)) - 450;
    return clampBodyFat(bf);
  }

  const inner = waist - neck;
  if (inner <= 0) return null;
  const bf =
    495 / (1.0324 - 0.19077 * log10(inner) + 0.15456 * log10(height)) - 450;
  return clampBodyFat(bf);
}

function clampBodyFat(bf) {
  if (!Number.isFinite(bf)) return null;
  // Guard against nonsensical outputs from bad inputs
  if (bf < 2 || bf > 70) return null;
  return Math.round(bf * 10) / 10;
}

/** Waist-to-hip ratio (belly / butt). */
export function waistToHip(waist, hip) {
  if (!waist || !hip) return null;
  return Math.round((waist / hip) * 100) / 100;
}

/** Waist-to-height ratio (belly / height). */
export function waistToHeight(waist, height) {
  if (!waist || !height) return null;
  return Math.round((waist / height) * 100) / 100;
}

/**
 * Left/right imbalance for a pair.
 * @returns {{left:number, right:number, diff:number, pct:number, bigger:'left'|'right'|'even'}|null}
 */
export function limbImbalance(left, right) {
  if (!left || !right) return null;
  const diff = Math.round((right - left) * 10) / 10;
  const avg = (left + right) / 2;
  const pct = avg ? Math.round((Math.abs(diff) / avg) * 1000) / 10 : 0;
  let bigger = 'even';
  if (diff > 0) bigger = 'right';
  else if (diff < 0) bigger = 'left';
  return { left, right, diff, pct, bigger };
}

/**
 * Is a change "good" given the field's goal direction?
 * @returns {'good'|'bad'|'neutral'}
 */
export function changeQuality(field, change) {
  if (change === null || change === 0) return 'neutral';
  const goal = MEASUREMENT_GOALS[field] || 'higher';
  if (goal === 'lower') return change < 0 ? 'good' : 'bad';
  return change > 0 ? 'good' : 'bad';
}
