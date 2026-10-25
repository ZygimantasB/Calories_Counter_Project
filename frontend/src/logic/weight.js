// Port of api_weight_items, get_weight_data, get_weight_calories_correlation.
import { format } from 'date-fns';
import { round, subDays, daysBetween } from './dates';
import { weightRepo } from '../db/repositories/weightRepo';
import { foodRepo } from '../db/repositories/foodRepo';
import { settingsRepo } from '../db/repositories/settingsRepo';

function localDayBoundsIso(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  return {
    startIso: new Date(y, m - 1, d, 0, 0, 0, 0).toISOString(),
    endIso: new Date(y, m - 1, d, 23, 59, 59, 999).toISOString(),
  };
}

/** Population standard deviation (numpy np.std default, ddof=0). */
function popStd(values) {
  if (values.length < 1) return 0;
  const mean = values.reduce((s, v) => s + v, 0) / values.length;
  const variance = values.reduce((s, v) => s + (v - mean) ** 2, 0) / values.length;
  return Math.sqrt(variance);
}

export function serializeWeight(row) {
  return { id: row.id, weight: Number(row.weight), recorded_at: row.recorded_at, notes: row.notes ?? null };
}

async function fetchFiltered({ days = '365', start_date, end_date } = {}) {
  const now = new Date();
  if (start_date && end_date) {
    const s = localDayBoundsIso(start_date).startIso;
    const e = localDayBoundsIso(end_date).endIso;
    return weightRepo.listBetween(s, e);
  }
  if (days === 'all') return weightRepo.all();
  const n = parseInt(days, 10);
  const start = Number.isNaN(n) ? subDays(now, 365) : subDays(now, n);
  return weightRepo.listBetween(start.toISOString(), null);
}

// ---- api_weight_items ----
export async function listWithStats(params = {}) {
  const weights = await fetchFiltered(params); // desc
  const items = weights.map(serializeWeight);

  let stats = {};
  const values = weights.map((w) => Number(w.weight)); // desc: [0]=newest
  if (values.length) {
    const current = values[0];
    const change = values.length > 1 ? round(values[0] - values[values.length - 1], 1) : 0;

    let changeRate = 0;
    if (weights.length >= 2) {
      const daysSpan = daysBetween(weights[weights.length - 1].recorded_at, weights[0].recorded_at);
      if (daysSpan > 0) changeRate = round(change / (daysSpan / 7), 2);
    }

    const consistency = values.length >= 3 ? round(popStd(values), 2) : 0;

    const settings = await settingsRepo.get();
    const heightM = settings.height ? Number(settings.height) / 100 : 1.75;
    const bmi = current > 0 && heightM > 0 ? round(current / (heightM * heightM), 1) : 0;

    const projected = changeRate !== 0 ? round(current + changeRate * 4, 1) : current;
    const targetWeight = settings.target_weight != null ? Number(settings.target_weight) : null;
    let weeksToGoal = 0;
    let goalDate = 'N/A';
    if (targetWeight && current > targetWeight && changeRate < 0) {
      weeksToGoal = round((current - targetWeight) / Math.abs(changeRate), 1);
      goalDate = format(new Date(new Date(weights[0].recorded_at).getTime() + weeksToGoal * 7 * 86400000), 'yyyy-MM-dd');
    }

    stats = {
      current,
      avg: round(values.reduce((s, v) => s + v, 0) / values.length, 1),
      min: Math.min(...values),
      max: Math.max(...values),
      change,
      change_rate: changeRate,
      consistency,
      bmi,
      projected_weight: projected,
      weeks_to_goal: weeksToGoal,
      goal_date: goalDate,
      weight_goal: targetWeight,
    };
  }
  return { items, stats };
}

// ---- get_weight_data (legacy chart shape) ----
export async function weightData(params = {}) {
  const rows = (await fetchFiltered(params)).slice().reverse(); // asc for chart
  const data = { labels: rows.map((w) => format(new Date(w.recorded_at), 'yyyy-MM-dd')), data: rows.map((w) => Number(w.weight)) };
  if (!rows.length) {
    data.stats = { avg: 0, max: 0, min: 0, latest: 0, change_rate: 0, bmi: 0, consistency: 0, projected_weight: 0, weeks_to_goal: 0, goal_date: 'N/A' };
    return data;
  }
  const values = rows.map((w) => Number(w.weight));
  const latest = values[values.length - 1];
  const settings = await settingsRepo.get();
  const heightM = settings.height ? Number(settings.height) / 100 : 1.75;

  let changeRate = 0;
  if (rows.length >= 2) {
    const weeks = (new Date(rows[rows.length - 1].recorded_at) - new Date(rows[0].recorded_at)) / (86400000 * 7);
    if (weeks > 0) changeRate = (values[values.length - 1] - values[0]) / weeks;
  }
  const stats = {
    avg: values.reduce((s, v) => s + v, 0) / values.length,
    max: Math.max(...values),
    min: Math.min(...values),
    latest,
    change_rate: changeRate,
    bmi: latest > 0 ? round(latest / (heightM * heightM), 1) : 0,
    consistency: values.length >= 3 ? round(popStd(values), 2) : 0,
    projected_weight: changeRate !== 0 ? round(latest + changeRate * 4, 1) : latest,
  };
  const goal = settings.target_weight != null ? Number(settings.target_weight) : null;
  if (goal && latest > goal && changeRate < 0) {
    const w = (latest - goal) / Math.abs(changeRate);
    stats.weeks_to_goal = round(w, 1);
    stats.weight_goal = goal;
    stats.goal_date = format(new Date(new Date(rows[rows.length - 1].recorded_at).getTime() + w * 7 * 86400000), 'yyyy-MM-dd');
  } else {
    stats.weeks_to_goal = 0;
    stats.goal_date = 'N/A';
    stats.weight_goal = goal;
  }
  data.stats = stats;
  return data;
}

// ---- get_weight_calories_correlation ----
export async function correlation(page = 1) {
  const weights = await weightRepo.allAsc();
  const food = await foodRepo.all();
  const rows = [];
  for (let i = 1; i < weights.length; i++) {
    const prev = weights[i - 1];
    const curr = weights[i];
    const weightChange = Number(curr.weight) - Number(prev.weight);
    const prevDate = format(new Date(prev.recorded_at), 'yyyy-MM-dd');
    const currDate = format(new Date(curr.recorded_at), 'yyyy-MM-dd');
    const startIso = localDayBoundsIso(prevDate).startIso;
    const endIso = localDayBoundsIso(currDate).endIso;
    let totalCalories = 0;
    for (const f of food) {
      if (f.consumed_at >= startIso && f.consumed_at <= endIso) totalCalories += Number(f.calories) || 0;
    }
    let daysBtw = daysBetween(prev.recorded_at, curr.recorded_at);
    if (daysBtw === 0) daysBtw = 1;
    rows.push({
      start_date: prevDate,
      end_date: currDate,
      start_weight: Number(prev.weight),
      end_weight: Number(curr.weight),
      weight_change: round(weightChange, 2),
      days_between: daysBtw,
      total_calories: totalCalories,
      daily_avg_calories: round(totalCalories / daysBtw, 1),
    });
  }
  rows.reverse();

  const p = parseInt(page, 10) || 1;
  const perPage = 10;
  const startIdx = (p - 1) * perPage;
  const pageData = rows.slice(startIdx, startIdx + perPage);
  const totalPages = Math.ceil(rows.length / perPage);
  return {
    correlation_data: pageData,
    pagination: { current_page: p, total_pages: totalPages, has_next: p < totalPages, has_prev: p > 1 },
  };
}
