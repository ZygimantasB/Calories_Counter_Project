// Port of UserSettings.calculate_bmr / get_recommended_macros / get_effective_targets
// (count_calories_app/models.py). Pure functions — unit-testable without a DB.
import { round } from './dates';

const ACTIVITY_MULTIPLIERS = {
  sedentary: 1.2,
  light: 1.375,
  moderate: 1.55,
  active: 1.725,
  very_active: 1.9,
};

const GOAL_CONFIGS = {
  maintain: { calorie_offset: 0, protein_per_kg: 1.8, fat_per_kg: 0.9, description: 'Balanced macros for weight maintenance' },
  bulk: { calorie_offset: 300, protein_per_kg: 1.8, fat_per_kg: 0.9, description: 'Conservative surplus for lean muscle growth' },
  cut: { calorie_offset: -500, protein_per_kg: 2.2, fat_per_kg: 0.9, description: 'High protein to preserve muscle while losing fat' },
  ripped: { calorie_offset: -750, protein_per_kg: 2.2, fat_per_kg: 0.9, description: 'Aggressive deficit with high protein for muscle preservation' },
};

/**
 * Latest weight from the Weight table (kg), falling back to settings.current_weight.
 * @param {object} settings row
 * @param {number|null} latestWeight most recent Weight.weight (kg), or null
 */
export function effectiveWeight(settings, latestWeight) {
  if (latestWeight != null) return Number(latestWeight);
  return settings?.current_weight != null ? Number(settings.current_weight) : null;
}

/** Mifflin-St Jeor BMR × activity multiplier = TDEE (rounded). Null if inputs missing. */
export function calculateTdee(settings, latestWeight) {
  const weight = effectiveWeight(settings, latestWeight);
  const age = settings?.age;
  const height = settings?.height != null ? Number(settings.height) : null;
  if (!age || !height || !weight) return null;

  const w = Number(weight);
  const bmr = settings.gender === 'male'
    ? 10 * w + 6.25 * height - 5 * age + 5
    : 10 * w + 6.25 * height - 5 * age - 161;
  const mult = ACTIVITY_MULTIPLIERS[settings.activity_level] ?? 1.55;
  return Math.round(bmr * mult);
}

/** Recommended macros from TDEE + goal offsets (Atwater 4/4/9). Null if inputs missing. */
export function recommendedMacros(settings, latestWeight) {
  const weightKg = effectiveWeight(settings, latestWeight);
  if (!weightKg) return null;
  const tdee = calculateTdee(settings, latestWeight);
  if (!tdee) return null;

  const config = GOAL_CONFIGS[settings.fitness_goal] || GOAL_CONFIGS.maintain;
  const totalCalories = Math.round(tdee + config.calorie_offset);
  const proteinG = Math.round(weightKg * config.protein_per_kg);
  const fatG = Math.round(weightKg * config.fat_per_kg);
  const proteinCal = proteinG * 4;
  const fatCal = fatG * 9;
  const carbsG = Math.max(Math.round((totalCalories - proteinCal - fatCal) / 4), 0);

  return {
    protein: proteinG,
    carbs: carbsG,
    fat: fatG,
    calories: totalCalories,
    description: config.description,
    goal: settings.fitness_goal,
  };
}

/** Effective targets: auto (if use_auto_macros + a weight) else manual stored targets. */
export function effectiveTargets(settings, latestWeight) {
  const useAuto = settings?.use_auto_macros === 1 || settings?.use_auto_macros === true;
  if (useAuto && effectiveWeight(settings, latestWeight)) {
    const rec = recommendedMacros(settings, latestWeight);
    if (rec) {
      return { calories: rec.calories, protein: rec.protein, carbs: rec.carbs, fat: rec.fat, is_auto: true };
    }
  }
  return {
    calories: settings?.daily_calorie_target ?? 2000,
    protein: settings?.protein_target ?? 150,
    carbs: settings?.carbs_target ?? 200,
    fat: settings?.fat_target ?? 65,
    is_auto: false,
  };
}

export { round };
