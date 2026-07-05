// Port of api_settings, api_update_settings, api_update_fitness_goal.
import { calculateTdee, recommendedMacros, effectiveTargets } from './targets';
import { settingsRepo } from '../db/repositories/settingsRepo';

const CHOICES = {
  activity_levels: [
    { value: 'sedentary', label: 'Sedentary (little or no exercise)' },
    { value: 'light', label: 'Light (exercise 1-3 days/week)' },
    { value: 'moderate', label: 'Moderate (exercise 3-5 days/week)' },
    { value: 'active', label: 'Active (exercise 6-7 days/week)' },
    { value: 'very_active', label: 'Very Active (hard exercise daily)' },
  ],
  genders: [{ value: 'male', label: 'Male' }, { value: 'female', label: 'Female' }],
  fitness_goals: [
    { value: 'maintain', label: 'Maintain Weight' },
    { value: 'bulk', label: 'Bulk (Gain Muscle)' },
    { value: 'cut', label: 'Cut (Lose Fat)' },
    { value: 'ripped', label: 'Get Ripped' },
  ],
  themes: [{ value: 'light', label: 'Light' }, { value: 'dark', label: 'Dark' }, { value: 'auto', label: 'System Default' }],
  chart_colors: [
    { value: 'blue', label: 'Blue' }, { value: 'green', label: 'Green' }, { value: 'purple', label: 'Purple' },
    { value: 'orange', label: 'Orange' }, { value: 'pink', label: 'Pink' },
  ],
  date_ranges: [
    { value: 7, label: 'Last 7 days' }, { value: 14, label: 'Last 14 days' },
    { value: 30, label: 'Last 30 days' }, { value: 90, label: 'Last 90 days' },
  ],
};

const VALID_GOALS = CHOICES.fitness_goals.map((g) => g.value);

function num(v) { return v == null || v === '' ? null : Number(v); }
function jsonField(v) {
  if (v == null) return v;
  if (typeof v === 'string') { try { return JSON.parse(v); } catch { return v; } }
  return v;
}

export async function buildSettings() {
  const s = await settingsRepo.get();
  const latest = await settingsRepo.latestWeight();
  const bmr = calculateTdee(s, latest);
  return {
    profile: {
      name: s.name, age: s.age,
      height: num(s.height), current_weight: num(s.current_weight),
      gender: s.gender, activity_level: s.activity_level, fitness_goal: s.fitness_goal,
      use_auto_macros: !!s.use_auto_macros,
      daily_calorie_target: s.daily_calorie_target,
      target_weight: num(s.target_weight),
      weekly_workout_goal: s.weekly_workout_goal,
      protein_target: s.protein_target, carbs_target: s.carbs_target, fat_target: s.fat_target,
      bmr, tdee: bmr,
    },
    recommended_macros: recommendedMacros(s, latest),
    effective_targets: effectiveTargets(s, latest),
    appearance: { theme: s.theme, chart_color: s.chart_color, default_date_range: s.default_date_range },
    notifications: {
      meal_reminder_enabled: !!s.meal_reminder_enabled,
      meal_reminder_times: jsonField(s.meal_reminder_times),
      workout_reminder_enabled: !!s.workout_reminder_enabled,
      workout_reminder_time: s.workout_reminder_time || null,
      workout_reminder_days: jsonField(s.workout_reminder_days),
      weight_reminder_enabled: !!s.weight_reminder_enabled,
      weight_reminder_time: s.weight_reminder_time || null,
    },
    choices: CHOICES,
  };
}

export async function updateSettings(data) {
  const patch = {};
  const collect = (obj, fields) => { for (const f of fields) if (obj && f in obj) patch[f] = obj[f]; };
  collect(data.profile, ['name', 'age', 'height', 'current_weight', 'gender', 'activity_level', 'fitness_goal',
    'use_auto_macros', 'daily_calorie_target', 'target_weight', 'weekly_workout_goal', 'protein_target', 'carbs_target', 'fat_target']);
  collect(data.appearance, ['theme', 'chart_color', 'default_date_range']);
  collect(data.notifications, ['meal_reminder_enabled', 'meal_reminder_times', 'workout_reminder_enabled',
    'workout_reminder_time', 'workout_reminder_days', 'weight_reminder_enabled', 'weight_reminder_time']);

  const s = await settingsRepo.update(patch);
  const latest = await settingsRepo.latestWeight();
  const bmr = calculateTdee(s, latest);
  return {
    success: true,
    message: 'Settings updated successfully',
    bmr, tdee: bmr,
    recommended_macros: recommendedMacros(s, latest),
    effective_targets: effectiveTargets(s, latest),
  };
}

export async function updateFitnessGoal(goal) {
  if (!VALID_GOALS.includes(goal)) {
    return { success: false, error: `Invalid fitness goal. Must be one of: ${VALID_GOALS.join(', ')}` };
  }
  const patch = { fitness_goal: goal };
  const latest = await settingsRepo.latestWeight();
  if (latest != null) patch.current_weight = latest;
  const s = await settingsRepo.update(patch);
  return { success: true, fitness_goal: goal, effective_targets: effectiveTargets(s, latest) };
}
