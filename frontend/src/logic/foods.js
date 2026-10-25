// Food aggregation logic — ports of api_food_items, api_quick_add_foods,
// api_search_all_foods, api_copy_day_foods, get_calories_trend_data,
// get_macros_trend_data, api_hourly_eating_pattern, api_top_foods.
// Pure functions take DB rows and produce the exact legacy JSON contracts.
import { format } from 'date-fns';
import { round, subDays } from './dates';
import { foodRepo } from '../db/repositories/foodRepo';

// ---- helpers ----

/** Local day [start,end] ISO bounds for a 'YYYY-MM-DD' string. */
function localDayBoundsIso(dateStr) {
  const [y, m, d] = dateStr.split('-').map(Number);
  const start = new Date(y, m - 1, d, 0, 0, 0, 0);
  const end = new Date(y, m - 1, d, 23, 59, 59, 999);
  return { startIso: start.toISOString(), endIso: end.toISOString() };
}

/** One food row -> legacy food-item contract. */
export function serializeFood(row) {
  return {
    id: row.id,
    name: row.product_name,
    calories: row.calories ? Number(row.calories) : 0,
    protein: row.protein ? Number(row.protein) : 0,
    carbs: row.carbohydrates ? Number(row.carbohydrates) : 0,
    fat: row.fat ? Number(row.fat) : 0,
    consumed_at: row.consumed_at || null,
    hidden: !!row.hide_from_quick_list,
  };
}

function sumTotals(rows) {
  let calories = 0, protein = 0, carbs = 0, fat = 0;
  for (const r of rows) {
    calories += Number(r.calories) || 0;
    protein += Number(r.protein) || 0;
    carbs += Number(r.carbohydrates) || 0;
    fat += Number(r.fat) || 0;
  }
  return { calories, protein: round(protein, 1), carbs: round(carbs, 1), fat: round(fat, 1), count: rows.length };
}

/** Resolve api_food_items-style filters into [startIso,endIso] and fetch rows (desc). */
async function fetchFiltered({ days = '90', date, start_date, end_date } = {}) {
  const now = new Date();
  if (date) {
    const { startIso, endIso } = localDayBoundsIso(date);
    return foodRepo.listBetween(startIso, endIso);
  }
  if (start_date && end_date) {
    const s = localDayBoundsIso(start_date).startIso;
    const e = localDayBoundsIso(end_date).endIso;
    return foodRepo.listBetween(s, e);
  }
  if (days === 'all') return foodRepo.all();
  const n = parseInt(days, 10);
  const start = Number.isNaN(n) ? subDays(now, 90) : subDays(now, n);
  return foodRepo.listBetween(start.toISOString(), null);
}

// ---- api_food_items ----
export async function listWithTotals(params = {}) {
  const rows = await fetchFiltered(params);
  const page = parseInt(params.page ?? 1, 10) || 1;
  const perPage = parseInt(params.per_page ?? 50, 10) || 50;
  const totalItems = rows.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / perPage));
  const startIdx = (page - 1) * perPage;
  const pageRows = rows.slice(startIdx, startIdx + perPage);
  return {
    items: pageRows.map(serializeFood),
    totals: sumTotals(rows),
    pagination: { page, per_page: perPage, total_pages: totalPages, total_items: totalItems },
  };
}

// ---- shared name-grouping ----
/** True if `r` was logged more recently than `cur` (id breaks timestamp ties). */
function isNewer(r, cur) {
  if (!cur) return true;
  if (r.consumed_at !== cur.consumed_at) return (r.consumed_at || '') > (cur.consumed_at || '');
  return (Number(r.id) || 0) > (Number(cur.id) || 0);
}

function groupByName(rows) {
  const map = new Map();
  for (const r of rows) {
    let g = map.get(r.product_name);
    if (!g) {
      g = { name: r.product_name, count: 0, cal: 0, prot: 0, carb: 0, fat: 0, last: null, latest: null };
      map.set(r.product_name, g);
    }
    g.count += 1;
    // Running sums are real totals (api_top_foods); `latest` is the row whose
    // values quick-add/search must report.
    g.cal += Number(r.calories) || 0;
    g.prot += Number(r.protein) || 0;
    g.carb += Number(r.carbohydrates) || 0;
    g.fat += Number(r.fat) || 0;
    if (isNewer(r, g.latest)) g.latest = r;
    if (!g.last || r.consumed_at > g.last) g.last = r.consumed_at;
  }
  return [...map.values()];
}

/**
 * Nutrition for a group: the most recently logged row's actual values.
 *
 * Averaging across every row sharing a name fabricates values that were never
 * logged, and quick-add re-saves what it displays, so the fabricated value
 * feeds the next average. Mirrors _annotate_latest_nutrition in views.py.
 */
function latestNutrition(g) {
  const r = g.latest || {};
  // Deliberately unrounded: the quick-add tile posts back the values it is
  // given, so rounding here would overwrite 24.6 kcal with 25 and leave a
  // permanently degraded second variant. Rounding is the display layer's job.
  return {
    calories: Number(r.calories) || 0,
    protein: Number(r.protein) || 0,
    carbs: Number(r.carbohydrates) || 0,
    fat: Number(r.fat) || 0,
  };
}

// ---- api_quick_add_foods ----
export async function quickAdd() {
  const rows = (await foodRepo.all()).filter((r) => !r.hide_from_quick_list);
  const groups = groupByName(rows).sort((a, b) => b.count - a.count).slice(0, 15);
  const foods = groups.map((g, i) => ({
    id: i + 1,
    name: g.name,
    ...latestNutrition(g),
  }));
  return { foods };
}

// ---- api_search_all_foods ----
export async function search(query = '', limit = 20) {
  const q = String(query).trim();
  const lim = Math.min(Math.max(parseInt(limit, 10) || 20, 1), 100);
  let rows = await foodRepo.all();
  if (q) rows = rows.filter((r) => r.product_name.toLowerCase().includes(q.toLowerCase()));
  const groups = groupByName(rows).sort((a, b) => b.count - a.count).slice(0, lim);
  const results = groups.map((g) => ({
    name: g.name,
    ...latestNutrition(g),
    count: g.count,
    last_used: g.last || null,
  }));
  return { results, query: q, total: results.length };
}

// ---- autocomplete (used by Django template historically; kept for parity) ----
export async function autocomplete(query = '') {
  const q = String(query).trim().toLowerCase();
  if (!q) return [];
  const rows = await foodRepo.all();
  const seen = new Set();
  const out = [];
  for (const r of rows) {
    if (r.product_name.toLowerCase().includes(q) && !seen.has(r.product_name)) {
      seen.add(r.product_name);
      out.push(r.product_name);
      if (out.length >= 10) break;
    }
  }
  return out;
}

// ---- nutrition-data (scale most-recent match to a gram weight); best-effort parity ----
export async function nutritionData(foodName, weight = 100) {
  const rows = await foodRepo.all();
  const match = rows.find((r) => r.product_name.toLowerCase() === String(foodName).toLowerCase());
  if (!match) return null;
  const factor = (Number(weight) || 100) / 100;
  return {
    product_name: match.product_name,
    calories: round((Number(match.calories) || 0) * factor, 1),
    protein: round((Number(match.protein) || 0) * factor, 1),
    carbohydrates: round((Number(match.carbohydrates) || 0) * factor, 1),
    fat: round((Number(match.fat) || 0) * factor, 1),
  };
}

// ---- api_copy_day_foods ----
export async function copyDay(sourceDate, targetDate = null) {
  if (!sourceDate) return { success: false, message: 'source_date is required' };
  const { startIso, endIso } = localDayBoundsIso(sourceDate);
  const source = await foodRepo.listBetween(startIso, endIso);
  if (!source.length) return { success: false, message: `No food items found for ${sourceDate}` };

  const [ty, tm, td] = (targetDate || format(new Date(), 'yyyy-MM-dd')).split('-').map(Number);
  let copied = 0;
  for (const item of source) {
    const src = new Date(item.consumed_at);
    const when = new Date(ty, tm - 1, td, src.getHours(), src.getMinutes(), 0, 0);
    await foodRepo.insert({
      product_name: item.product_name,
      calories: item.calories, fat: item.fat,
      carbohydrates: item.carbohydrates, protein: item.protein,
      consumed_at: when.toISOString(),
    });
    copied += 1;
  }
  const targetLabel = targetDate || format(new Date(), 'yyyy-MM-dd');
  return { success: true, copied_count: copied, message: `Copied ${copied} items to ${targetLabel}` };
}

// ---- daily grouping for trends (local day) ----
function dailyGroups(rows) {
  const map = new Map();
  for (const r of rows) {
    const d = new Date(r.consumed_at);
    const key = format(d, 'yyyy-MM-dd');
    let g = map.get(key);
    if (!g) { g = { key, date: d, cal: 0, prot: 0, carb: 0, fat: 0 }; map.set(key, g); }
    g.cal += Number(r.calories) || 0;
    g.prot += Number(r.protein) || 0;
    g.carb += Number(r.carbohydrates) || 0;
    g.fat += Number(r.fat) || 0;
  }
  return [...map.values()].sort((a, b) => a.date - b.date);
}

async function trendRows({ days = 30, start_date, end_date } = {}) {
  const now = new Date();
  if (start_date && end_date) {
    const s = localDayBoundsIso(start_date).startIso;
    const e = localDayBoundsIso(end_date).endIso;
    return foodRepo.listBetween(s, e);
  }
  if (days === 'all') return foodRepo.all();
  const n = parseInt(days, 10);
  const start = Number.isNaN(n) ? subDays(now, 30) : subDays(now, n);
  return foodRepo.listBetween(start.toISOString(), null);
}

// ---- get_calories_trend_data ----
export async function caloriesTrend(params = {}) {
  const groups = dailyGroups(await trendRows(params));
  return {
    labels: groups.map((g) => g.key),
    data: groups.map((g) => g.cal),
    protein_calories: groups.map((g) => round(g.prot * 4, 1)),
    carbs_calories: groups.map((g) => round(g.carb * 4, 1)),
    fat_calories: groups.map((g) => round(g.fat * 9, 1)),
    protein_grams: groups.map((g) => round(g.prot, 1)),
    carbs_grams: groups.map((g) => round(g.carb, 1)),
    fat_grams: groups.map((g) => round(g.fat, 1)),
    trend: groups.map((g) => ({ date: format(g.date, 'MMM dd'), calories: g.cal })),
  };
}

// ---- get_macros_trend_data ----
export async function macrosTrend(params = {}) {
  const groups = dailyGroups(await trendRows(params));
  return {
    labels: groups.map((g) => g.key),
    protein: groups.map((g) => g.prot),
    carbs: groups.map((g) => g.carb),
    fat: groups.map((g) => g.fat),
  };
}

// ---- api_hourly_eating_pattern ----
export async function hourlyPattern({ days = '30', date } = {}) {
  let rows;
  if (date) {
    const { startIso, endIso } = localDayBoundsIso(date);
    rows = await foodRepo.listBetween(startIso, endIso);
  } else if (days === 'all') {
    rows = await foodRepo.all();
  } else {
    const n = parseInt(days, 10) || 30;
    rows = await foodRepo.listBetween(subDays(new Date(), n).toISOString(), null);
  }
  const hourly = new Array(24).fill(0);
  for (const r of rows) {
    if (r.consumed_at) hourly[new Date(r.consumed_at).getHours()] += Number(r.calories) || 0;
  }
  return { hours: Array.from({ length: 24 }, (_, h) => h), calories: hourly.map((c) => round(c, 1)) };
}

// ---- api_top_foods ----
export async function topFoods({ days = '90', sort = 'count' } = {}) {
  let rows;
  if (days === 'all') rows = await foodRepo.all();
  else {
    const n = parseInt(days, 10);
    rows = await foodRepo.listBetween(subDays(new Date(), Number.isNaN(n) ? 90 : n).toISOString(), null);
  }
  const items = groupByName(rows).map((g) => ({
    name: g.name,
    count: g.count,
    total_calories: g.cal,
    avg_calories: round(g.cal / g.count),
    total_protein: round(g.prot, 1),
    total_carbs: round(g.carb, 1),
    total_fat: round(g.fat, 1),
    latest: g.last || null,
  }));
  const by_calories = [...items].sort((a, b) => b.total_calories - a.total_calories);
  const by_protein = [...items].sort((a, b) => b.total_protein - a.total_protein);
  const by_frequency = [...items].sort((a, b) => b.count - a.count);
  const primary = sort === 'calories' ? by_calories : sort === 'protein' ? by_protein : by_frequency;
  return { items: primary, by_calories, by_protein, by_frequency };
}
