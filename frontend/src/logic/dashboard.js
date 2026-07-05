// Port of api_dashboard (count_calories_app/views.py).
import { round, weekStartMonday, subDays, localDateKey, startOfLocalDay, endOfLocalDay } from './dates';
import { effectiveTargets } from './targets';
import { dbAll } from '../db/sqlite';
import { foodRepo } from '../db/repositories/foodRepo';
import { weightRepo } from '../db/repositories/weightRepo';
import { settingsRepo } from '../db/repositories/settingsRepo';

function sums(rows) {
  let calories = 0, protein = 0, carbs = 0, fat = 0;
  for (const r of rows) {
    calories += Number(r.calories) || 0;
    protein += Number(r.protein) || 0;
    carbs += Number(r.carbohydrates) || 0;
    fat += Number(r.fat) || 0;
  }
  return { calories, protein, carbs, fat, count: rows.length };
}

/** Distinct local-day count + per-day averages for calories/protein. */
function dailyAverages(rows) {
  const byDay = new Map();
  for (const r of rows) {
    const key = localDateKey(r.consumed_at);
    let g = byDay.get(key);
    if (!g) { g = { cal: 0, prot: 0 }; byDay.set(key, g); }
    g.cal += Number(r.calories) || 0;
    g.prot += Number(r.protein) || 0;
  }
  const days = byDay.size;
  let totalCal = 0, totalProt = 0;
  for (const g of byDay.values()) { totalCal += g.cal; totalProt += g.prot; }
  return {
    days,
    avgCal: days ? round(totalCal / days, 0) : 0,
    avgProt: days ? round(totalProt / days, 1) : 0,
  };
}

export async function buildDashboard() {
  const now = new Date();
  const todayKey = localDateKey(now);
  const weekStart = weekStartMonday(now);
  const lastWeekStart = subDays(weekStart, 7);

  const allFood = await foodRepo.all();

  const todayRows = allFood.filter((r) => localDateKey(r.consumed_at) === todayKey);
  const weekRows = allFood.filter((r) => new Date(r.consumed_at) >= weekStart && new Date(r.consumed_at) <= endOfLocalDay(now));
  const lastWeekRows = allFood.filter((r) => {
    const d = new Date(r.consumed_at);
    return d >= lastWeekStart && d < weekStart;
  });

  const today = sums(todayRows);
  const week = sums(weekRows);
  const thisWeekAvg = dailyAverages(weekRows);
  const lastWeekAvg = dailyAverages(lastWeekRows);

  // Weight
  const weights = await weightRepo.all(); // desc
  const latestWeight = weights[0] || null;
  const weekAgo = subDays(now, 7);
  const weightWeekAgo = weights.find((w) => new Date(w.recorded_at) <= weekAgo) || null;
  let weightChange = null;
  if (latestWeight && weightWeekAgo) {
    weightChange = Number(latestWeight.weight) - Number(weightWeekAgo.weight);
  }

  // Workouts & runs this / last week
  const weekStartIso = weekStart.toISOString();
  const lastWeekStartIso = lastWeekStart.toISOString();
  const [[wThis], [wLast], runRows] = await Promise.all([
    dbAll(`SELECT COUNT(*) AS c FROM workout_session WHERE date >= ?;`, [weekStartIso]),
    dbAll(`SELECT COUNT(*) AS c FROM workout_session WHERE date >= ? AND date < ?;`, [lastWeekStartIso, weekStartIso]),
    dbAll(`SELECT distance FROM running_session WHERE date >= ?;`, [weekStartIso]),
  ]);
  const weekWorkouts = wThis?.c || 0;
  const lastWeekWorkouts = wLast?.c || 0;
  const weekRuns = runRows.length;
  const weekRunDistance = runRows.reduce((s, r) => s + (Number(r.distance) || 0), 0);

  // Recent foods (keep Django .values() key names: product_name / carbohydrates)
  const recentFoods = allFood.slice(0, 5).map((r) => ({
    id: r.id,
    product_name: r.product_name,
    calories: Number(r.calories) || 0,
    protein: Number(r.protein) || 0,
    carbohydrates: Number(r.carbohydrates) || 0,
    fat: Number(r.fat) || 0,
    consumed_at: r.consumed_at || null,
  }));

  // Streak: walk back local days while a food entry exists.
  const dayKeys = new Set(allFood.map((r) => localDateKey(r.consumed_at)));
  let streak = 0;
  let check = startOfLocalDay(now);
  while (dayKeys.has(localDateKey(check))) {
    streak += 1;
    check = subDays(check, 1);
  }

  // Targets (sync current_weight to latest, like the endpoint)
  const settings = await settingsRepo.get();
  if (latestWeight) await settingsRepo.syncCurrentWeight();
  const targets = effectiveTargets(settings, latestWeight ? Number(latestWeight.weight) : null);

  // Warnings
  const todayCal = today.calories, todayProt = today.protein, todayCarb = today.carbs, todayFat = today.fat;
  const warnings = [];
  if (todayCal > targets.calories * 1.1) {
    warnings.push({ type: 'calories', message: `You have exceeded your daily calorie target by ${Math.trunc(todayCal - targets.calories)} kcal`,
      severity: todayCal <= targets.calories * 1.25 ? 'warning' : 'error', current: todayCal, target: targets.calories });
  }
  if (todayProt > targets.protein * 1.1) {
    warnings.push({ type: 'protein', message: `You have exceeded your daily protein target by ${Math.trunc(todayProt - targets.protein)}g`,
      severity: 'info', current: round(todayProt, 1), target: targets.protein });
  }
  if (todayCarb > targets.carbs * 1.1) {
    warnings.push({ type: 'carbs', message: `You have exceeded your daily carbs target by ${Math.trunc(todayCarb - targets.carbs)}g`,
      severity: 'warning', current: round(todayCarb, 1), target: targets.carbs });
  }
  if (todayFat > targets.fat * 1.1) {
    warnings.push({ type: 'fat', message: `You have exceeded your daily fat target by ${Math.trunc(todayFat - targets.fat)}g`,
      severity: todayFat <= targets.fat * 1.25 ? 'warning' : 'error', current: round(todayFat, 1), target: targets.fat });
  }

  return {
    today: { calories: todayCal, protein: round(todayProt, 1), carbs: round(todayCarb, 1), fat: round(todayFat, 1), count: today.count },
    week: {
      calories: week.calories, protein: round(week.protein, 1), carbs: round(week.carbs, 1), fat: round(week.fat, 1),
      count: week.count, workouts: weekWorkouts, runs: weekRuns, run_distance: weekRunDistance,
      avg_calories: thisWeekAvg.avgCal, avg_protein: thisWeekAvg.avgProt, days_logged: thisWeekAvg.days,
    },
    last_week: { avg_calories: lastWeekAvg.avgCal, avg_protein: lastWeekAvg.avgProt, workouts: lastWeekWorkouts, days_logged: lastWeekAvg.days },
    comparison: {
      calories_diff: lastWeekAvg.avgCal ? round(thisWeekAvg.avgCal - lastWeekAvg.avgCal, 0) : null,
      calories_percent: lastWeekAvg.avgCal ? round(((thisWeekAvg.avgCal - lastWeekAvg.avgCal) / lastWeekAvg.avgCal) * 100, 1) : null,
      protein_diff: lastWeekAvg.avgProt ? round(thisWeekAvg.avgProt - lastWeekAvg.avgProt, 1) : null,
      protein_percent: lastWeekAvg.avgProt ? round(((thisWeekAvg.avgProt - lastWeekAvg.avgProt) / lastWeekAvg.avgProt) * 100, 1) : null,
      workouts_diff: weekWorkouts - lastWeekWorkouts,
    },
    weight: {
      current: latestWeight ? Number(latestWeight.weight) : null,
      change: weightChange ? round(weightChange, 2) : null,
    },
    recent_foods: recentFoods,
    streak,
    goals: {
      daily_calories: targets.calories, daily_protein: targets.protein, daily_carbs: targets.carbs, daily_fat: targets.fat,
      weekly_workouts: settings.weekly_workout_goal, weekly_runs: 2,
      is_auto: targets.is_auto, fitness_goal: settings.fitness_goal,
    },
    warnings,
  };
}
