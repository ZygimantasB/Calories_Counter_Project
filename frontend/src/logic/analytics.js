// Port of api_analytics (count_calories_app/views.py). Read-only aggregation over
// food + weight. Reproduces every key the Django endpoint returns.
import { round, subDays, weekStartMonday } from './dates';
import { foodRepo } from '../db/repositories/foodRepo';
import { weightRepo } from '../db/repositories/weightRepo';
import { dbAll } from '../db/sqlite';

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

function mean(arr) { return arr.length ? arr.reduce((s, v) => s + v, 0) / arr.length : 0; }
function stdev(arr) { // sample stdev (statistics.stdev, ddof=1)
  if (arr.length < 2) return 0;
  const m = mean(arr);
  return Math.sqrt(arr.reduce((s, v) => s + (v - m) ** 2, 0) / (arr.length - 1));
}
function p(n) { return String(n).padStart(2, '0'); }
function dateKey(d) { return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; }
function keyToDate(key) { const [y, m, d] = key.split('-').map(Number); return new Date(y, m - 1, d); }
function weekdayOf(key) { return (keyToDate(key).getDay() + 6) % 7; } // Monday=0
function diffDays(aKey, bKey) { return Math.round((keyToDate(bKey) - keyToDate(aKey)) / 86400000); }

/** Long US date "June 05, 2026". */
function longDate(d) {
  const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  return `${months[d.getMonth()]} ${p(d.getDate())}, ${d.getFullYear()}`;
}

export async function getAnalytics({ period = '90' } = {}) {
  const now = new Date();
  const start = period === 'all' ? null : subDays(now, Number.isNaN(parseInt(period, 10)) ? 90 : parseInt(period, 10));

  const allFood = await foodRepo.all();
  const allWeight = await weightRepo.allAsc();
  const foodItems = start ? allFood.filter((f) => new Date(f.consumed_at) >= start && new Date(f.consumed_at) <= now) : allFood.filter((f) => new Date(f.consumed_at) <= now);
  const weights = start ? allWeight.filter((w) => new Date(w.recorded_at) >= start && new Date(w.recorded_at) <= now) : allWeight;

  // === DAILY STATS ===
  const dayMap = new Map();
  for (const f of foodItems) {
    const key = dateKey(new Date(f.consumed_at));
    let g = dayMap.get(key);
    if (!g) { g = { day: key, cal: 0, prot: 0, carb: 0, fat: 0 }; dayMap.set(key, g); }
    g.cal += Number(f.calories) || 0; g.prot += Number(f.protein) || 0;
    g.carb += Number(f.carbohydrates) || 0; g.fat += Number(f.fat) || 0;
  }
  const daily = [...dayMap.values()].sort((a, b) => a.day.localeCompare(b.day));
  const daily_data = daily.map((d) => ({ date: d.day, calories: d.cal, protein: round(d.prot, 1), carbs: round(d.carb, 1), fat: round(d.fat, 1) }));

  // === WEEKLY SUMMARY ===
  const thisWeekStart = weekStartMonday(now);
  const lastWeekStart = subDays(thisWeekStart, 7);
  const inRange = (f, a, b) => { const d = new Date(f.consumed_at); return d >= a && (b ? d < b : d <= now); };
  const dayAgg = (rows) => {
    const m = new Map();
    for (const f of rows) { const k = dateKey(new Date(f.consumed_at)); const g = m.get(k) || { cal: 0, prot: 0 }; g.cal += Number(f.calories) || 0; g.prot += Number(f.protein) || 0; m.set(k, g); }
    const days = m.size; let cal = 0, prot = 0;
    for (const g of m.values()) { cal += g.cal; prot += g.prot; }
    return { days, cal, prot, avgCal: days ? round(cal / days, 0) : 0, avgProt: days ? round(prot / days, 1) : 0 };
  };
  const tw = dayAgg(allFood.filter((f) => inRange(f, thisWeekStart, null)));
  const lw = dayAgg(allFood.filter((f) => inRange(f, lastWeekStart, thisWeekStart)));
  const [[twWk], [lwWk], twRuns] = await Promise.all([
    dbAll(`SELECT COUNT(*) AS c FROM workout_session WHERE date >= ?;`, [thisWeekStart.toISOString()]),
    dbAll(`SELECT COUNT(*) AS c FROM workout_session WHERE date >= ? AND date < ?;`, [lastWeekStart.toISOString(), thisWeekStart.toISOString()]),
    dbAll(`SELECT COUNT(*) AS c FROM running_session WHERE date >= ?;`, [thisWeekStart.toISOString()]),
  ]);
  const weekly_summary = {
    this_week: { days_logged: tw.days, total_calories: tw.cal, avg_calories: tw.avgCal, total_protein: round(tw.prot, 0), avg_protein: tw.avgProt, workouts: twWk?.c || 0, runs: twRuns[0]?.c || 0 },
    last_week: { days_logged: lw.days, avg_calories: lw.avgCal, avg_protein: lw.avgProt, workouts: lwWk?.c || 0 },
    comparison: {
      calories_diff: lw.avgCal ? round(tw.avgCal - lw.avgCal, 0) : null,
      protein_diff: lw.avgProt ? round(tw.avgProt - lw.avgProt, 1) : null,
      workouts_diff: (twWk?.c || 0) - (lwWk?.c || 0),
    },
  };

  // === OVERALL STATS ===
  const overall_stats = {};
  const caloriesList = daily.filter((d) => d.cal).map((d) => d.cal);
  if (caloriesList.length) {
    overall_stats.avg_daily_calories = round(mean(caloriesList), 0);
    overall_stats.total_days_logged = daily.length;
    overall_stats.calorie_min = round(Math.min(...caloriesList), 0);
    overall_stats.calorie_max = round(Math.max(...caloriesList), 0);
    const proteinList = daily.filter((d) => d.prot).map((d) => d.prot);
    const carbsList = daily.filter((d) => d.carb).map((d) => d.carb);
    const fatList = daily.filter((d) => d.fat).map((d) => d.fat);
    if (proteinList.length) { overall_stats.avg_daily_protein = round(mean(proteinList), 1); overall_stats.total_protein = round(proteinList.reduce((s, v) => s + v, 0), 0); }
    if (carbsList.length) { overall_stats.avg_daily_carbs = round(mean(carbsList), 1); overall_stats.total_carbs = round(carbsList.reduce((s, v) => s + v, 0), 0); }
    if (fatList.length) { overall_stats.avg_daily_fat = round(mean(fatList), 1); overall_stats.total_fat = round(fatList.reduce((s, v) => s + v, 0), 0); }
  }

  // === STREAKS ===
  const streaks = {};
  if (daily.length) {
    const sortedDays = daily.map((d) => d.day).sort();
    let current = 1;
    for (let i = sortedDays.length - 1; i > 0; i--) { if (diffDays(sortedDays[i - 1], sortedDays[i]) === 1) current += 1; else break; }
    let longest = 1, temp = 1;
    for (let i = 1; i < sortedDays.length; i++) { if (diffDays(sortedDays[i - 1], sortedDays[i]) === 1) { temp += 1; longest = Math.max(longest, temp); } else temp = 1; }
    streaks.current_streak = current;
    streaks.longest_streak = longest;
    streaks.total_days = sortedDays.length;
    const daysSinceStart = diffDays(sortedDays[0], dateKey(now)) + 1;
    streaks.consistency_rate = daysSinceStart > 0 ? round((sortedDays.length / daysSinceStart) * 100, 1) : 0;
  }

  // === WEIGHT ANALYSIS / PACE / PROJECTIONS ===
  const weight_analysis = {};
  const weight_pace = {};
  const projections = {};
  if (weights.length >= 2) {
    const first = Number(weights[0].weight), last = Number(weights[weights.length - 1].weight);
    const values = weights.map((w) => Number(w.weight));
    Object.assign(weight_analysis, {
      start_weight: first, current_weight: last, total_change: round(last - first, 1),
      min_weight: Math.min(...values), max_weight: Math.max(...values), avg_weight: round(mean(values), 1), days_tracked: weights.length,
    });
    const daysDiff = Math.round((new Date(weights[weights.length - 1].recorded_at) - new Date(weights[0].recorded_at)) / 86400000);
    if (daysDiff > 0) {
      const totalChange = last - first;
      weight_pace.weekly_rate = round((totalChange / daysDiff) * 7, 2);
      weight_pace.monthly_rate = round((totalChange / daysDiff) * 30, 1);
      weight_pace.days = daysDiff;
      if (totalChange < 0) { weight_pace.status = 'losing'; weight_pace.pace_assessment = Math.abs(weight_pace.weekly_rate) >= 0.5 ? 'Healthy weight loss pace (0.5-1 kg/week)' : 'Slow but steady weight loss (<0.5 kg/week)'; }
      else if (totalChange > 0) weight_pace.status = 'gaining';
      else weight_pace.status = 'maintaining';
      if (daysDiff >= 7) weight_pace.estimated_daily_deficit = round((totalChange * 7700) / daysDiff, 0);
    }
    if (weight_pace.weekly_rate) {
      const rate = weight_pace.weekly_rate;
      if (rate !== 0) {
        projections['4_weeks'] = round(last + rate * 4, 1);
        projections['8_weeks'] = round(last + rate * 8, 1);
        projections['12_weeks'] = round(last + rate * 12, 1);
        if (rate < 0) {
          projections.goals = [];
          for (const goal of [70, 75, 80, 85, 90, 95]) {
            if (goal < last) {
              const weeks = (last - goal) / Math.abs(rate);
              if (weeks <= 52) projections.goals.push({ weight: goal, weeks: round(weeks, 0), date: longDate(new Date(now.getTime() + weeks * 7 * 86400000)) });
            }
          }
        }
      }
    }
  }

  // === MACRO ANALYSIS ===
  const macro_analysis = {};
  if (overall_stats.avg_daily_protein && overall_stats.avg_daily_carbs && overall_stats.avg_daily_fat) {
    const pg = overall_stats.avg_daily_protein, cg = overall_stats.avg_daily_carbs, fg = overall_stats.avg_daily_fat;
    const pc = pg * 4, cc = cg * 4, fc = fg * 9, tot = pc + cc + fc;
    if (tot > 0) {
      macro_analysis.protein_percent = round((pc / tot) * 100, 1);
      macro_analysis.carbs_percent = round((cc / tot) * 100, 1);
      macro_analysis.fat_percent = round((fc / tot) * 100, 1);
      if (weights.length) macro_analysis.protein_per_kg = round(pg / Number(weights[weights.length - 1].weight), 2);
    }
  }

  // === DAY OF WEEK ===
  const day_of_week_stats = {};
  if (daily.length) {
    for (let dn = 0; dn < 7; dn++) {
      const dayCals = daily.filter((d) => weekdayOf(d.day) === dn && d.cal).map((d) => d.cal);
      if (dayCals.length) day_of_week_stats[DAY_NAMES[dn]] = { avg_calories: round(mean(dayCals), 0), count: dayCals.length };
    }
  }
  const weekday_insights = {};
  const dowEntries = Object.entries(day_of_week_stats);
  if (dowEntries.length) {
    const sorted = [...dowEntries].sort((a, b) => a[1].avg_calories - b[1].avg_calories);
    weekday_insights.lowest_day = { name: sorted[0][0], calories: sorted[0][1].avg_calories };
    weekday_insights.highest_day = { name: sorted[sorted.length - 1][0], calories: sorted[sorted.length - 1][1].avg_calories };
    const wd = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].filter((k) => day_of_week_stats[k]).map((k) => day_of_week_stats[k].avg_calories);
    const we = ['Saturday', 'Sunday'].filter((k) => day_of_week_stats[k]).map((k) => day_of_week_stats[k].avg_calories);
    if (wd.length && we.length) {
      weekday_insights.weekday_avg = round(mean(wd), 0);
      weekday_insights.weekend_avg = round(mean(we), 0);
      weekday_insights.weekend_difference = round(weekday_insights.weekend_avg - weekday_insights.weekday_avg, 0);
    }
  }

  // === CONSISTENCY SCORE ===
  let consistency_score = {};
  if (caloriesList.length >= 7) {
    const avg = mean(caloriesList);
    const sd = caloriesList.length > 1 ? stdev(caloriesList) : 0;
    const cv = avg > 0 ? (sd / avg) * 100 : 0;
    if (cv < 10) consistency_score = { rating: 'Excellent', score: 95, cv: round(cv, 1) };
    else if (cv < 15) consistency_score = { rating: 'Good', score: 80, cv: round(cv, 1) };
    else if (cv < 25) consistency_score = { rating: 'Moderate', score: 60, cv: round(cv, 1) };
    else consistency_score = { rating: 'Variable', score: 40, cv: round(cv, 1) };
  }

  // === INSIGHTS ===
  const insights = [];
  if (macro_analysis.protein_per_kg >= 1.6) insights.push({ type: 'protein', icon: '💪', title: 'Strong Protein Intake', description: `Excellent! You're getting ${macro_analysis.protein_per_kg.toFixed(2)}g protein per kg body weight.`, recommendation: 'Keep up the good protein intake for muscle health.' });
  if ((streaks.current_streak || 0) >= 7) insights.push({ type: 'streak', icon: '🔥', title: 'Logging Streak', description: `Great job! You've logged ${streaks.current_streak} days in a row. Your longest streak is ${streaks.longest_streak} days.`, recommendation: 'Keep the momentum going!' });

  if (weights.length >= 3) {
    const periods = [];
    for (let i = 0; i < weights.length - 1; i++) {
      const older = weights[i], newer = weights[i + 1];
      const wChange = Number(newer.weight) - Number(older.weight);
      const s = new Date(older.recorded_at), e = new Date(newer.recorded_at);
      const pf = allFood.filter((f) => { const d = new Date(f.consumed_at); return d >= s && d <= e; });
      if (pf.length) {
        const daysCount = new Set(pf.map((f) => dateKey(new Date(f.consumed_at)))).size;
        if (daysCount > 0) {
          const agg = pf.reduce((a, f) => { a.cal += Number(f.calories) || 0; a.carb += Number(f.carbohydrates) || 0; return a; }, { cal: 0, carb: 0 });
          periods.push({ weight_change: wChange, avg_calories: agg.cal / daysCount, avg_carbs: agg.carb / daysCount });
        }
      }
    }
    if (periods.length >= 3) {
      const loss = periods.filter((x) => x.weight_change < -0.1);
      const gain = periods.filter((x) => x.weight_change > 0.1);
      if (loss.length && gain.length) {
        const calLoss = mean(loss.map((x) => x.avg_calories)), calGain = mean(gain.map((x) => x.avg_calories));
        if (calLoss < calGain) insights.push({ type: 'calories', icon: '🔥', title: 'Calorie Impact', description: `You tend to lose weight when averaging ${calLoss.toFixed(0)} kcal/day and gain when averaging ${calGain.toFixed(0)} kcal/day.`, recommendation: `Try to stay around ${calLoss.toFixed(0)} kcal/day for weight loss.` });
        const carbLoss = mean(loss.map((x) => x.avg_carbs)), carbGain = mean(gain.map((x) => x.avg_carbs));
        if (carbLoss < carbGain * 0.9) insights.push({ type: 'carbs', icon: '🍞', title: 'Carbohydrate Pattern', description: `Lower carb intake (~${carbLoss.toFixed(0)}g/day) correlates with weight loss vs (~${carbGain.toFixed(0)}g/day) with weight gain.`, recommendation: `Consider keeping carbs around ${carbLoss.toFixed(0)}g/day.` });
      }
    }
  }
  if (weekday_insights.weekend_difference > 200) insights.push({ type: 'weekend', icon: '📅', title: 'Weekend Pattern', description: `You consume about ${weekday_insights.weekend_difference.toFixed(0)} more calories on weekends compared to weekdays.`, recommendation: 'Try to maintain more consistent eating patterns throughout the week.' });

  // === ACHIEVEMENTS ===
  const achievements = [];
  if ((streaks.current_streak || 0) >= 30) achievements.push({ icon: '🔥', title: 'Monthly Warrior', desc: '30+ day logging streak' });
  if (weight_pace.weekly_rate && (weight_analysis.total_change || 0) <= -2) achievements.push({ icon: '🥈', title: 'Good Start', desc: 'Lost 2+ kg' });
  if ((macro_analysis.protein_per_kg || 0) >= 2.0) achievements.push({ icon: '💪', title: 'Protein Champion', desc: '2+ g protein per kg body weight' });
  if ((streaks.total_days || 0) >= 50) achievements.push({ icon: '📈', title: 'Dedicated Tracker', desc: '50+ days logged' });
  if ((streaks.consistency_rate || 0) >= 90) achievements.push({ icon: '⭐', title: 'Super Consistent', desc: '90%+ logging consistency' });

  // === NUTRITION SCORE ===
  const nutrition_score = {};
  if (Object.keys(macro_analysis).length && overall_stats.avg_daily_calories) {
    let score = 0; const breakdown = [];
    const ppk = macro_analysis.protein_per_kg || 0;
    if (ppk >= 1.6) { score += 25; breakdown.push({ name: 'Protein', score: 25, max: 25 }); }
    else if (ppk >= 1.2) { score += 20; breakdown.push({ name: 'Protein', score: 20, max: 25 }); }
    else { score += 10; breakdown.push({ name: 'Protein', score: 10, max: 25 }); }
    let balance = 25;
    if ((macro_analysis.carbs_percent || 0) < 40 || (macro_analysis.carbs_percent || 0) > 65) balance -= 8;
    breakdown.push({ name: 'Macro Balance', score: Math.max(0, balance), max: 25 }); score += Math.max(0, balance);
    if (consistency_score.score) { const cp = round(consistency_score.score * 0.25); breakdown.push({ name: 'Consistency', score: cp, max: 25 }); score += cp; }
    if (streaks.consistency_rate) { const ls = Math.min(25, round(streaks.consistency_rate * 0.25)); breakdown.push({ name: 'Logging', score: ls, max: 25 }); score += ls; }
    nutrition_score.total = Math.min(100, score);
    nutrition_score.breakdown = breakdown;
    nutrition_score.grade = score >= 85 ? 'A' : score >= 70 ? 'B' : score >= 55 ? 'C' : 'D';
  }

  // === WEEKLY / MONTHLY REPORTS ===
  const weekAgg = new Map(), monthAgg = new Map();
  for (const f of foodItems) {
    const d = new Date(f.consumed_at);
    const wk = dateKey(weekStartMonday(d));
    const mo = `${d.getFullYear()}-${p(d.getMonth() + 1)}-01`;
    for (const [map, key] of [[weekAgg, wk], [monthAgg, mo]]) {
      let g = map.get(key);
      if (!g) { g = { cal: 0, prot: 0, carb: 0, fat: 0, days: new Set() }; map.set(key, g); }
      g.cal += Number(f.calories) || 0; g.prot += Number(f.protein) || 0; g.carb += Number(f.carbohydrates) || 0; g.fat += Number(f.fat) || 0;
      g.days.add(dateKey(d));
    }
  }
  const buildReport = (map, labelKey) => [...map.entries()].sort((a, b) => b[0].localeCompare(a[0])).slice(0, 12).map(([k, g]) => {
    const days = g.days.size || 1;
    return { [labelKey]: k, avg_calories: round(g.cal / days, 0), avg_protein: round(g.prot / days, 0), avg_carbs: round(g.carb / days, 0), avg_fat: round(g.fat / days, 0), days_logged: days };
  });
  const weekly_reports = buildReport(weekAgg, 'week_start');
  const monthly_reports = buildReport(monthAgg, 'month');

  // === TOP FOODS ===
  const nameMap = new Map();
  for (const f of foodItems) { const g = nameMap.get(f.product_name) || { count: 0, cal: 0 }; g.count += 1; g.cal += Number(f.calories) || 0; nameMap.set(f.product_name, g); }
  const top_foods = [...nameMap.entries()].map(([name, g]) => ({ name, count: g.count, total_calories: g.cal })).sort((a, b) => b.count - a.count);

  // === BEST/WORST DAYS ===
  const best_worst_days = {};
  const validDays = daily.filter((d) => d.cal >= 500);
  if (validDays.length) {
    const lowest = validDays.reduce((a, b) => (b.cal < a.cal ? b : a));
    const highest = validDays.reduce((a, b) => (b.cal > a.cal ? b : a));
    const hp = validDays.reduce((a, b) => ((b.prot || 0) > (a.prot || 0) ? b : a));
    best_worst_days.lowest_calorie_day = { date: lowest.day, calories: lowest.cal };
    best_worst_days.highest_calorie_day = { date: highest.day, calories: highest.cal };
    best_worst_days.highest_protein_day = { date: hp.day, protein: round(hp.prot, 1) === hp.prot ? hp.prot : hp.prot };
  }

  // === CALORIE DISTRIBUTION ===
  let calorie_distribution = [];
  if (caloriesList.length >= 10) {
    const total = caloriesList.length;
    const bucket = (pred) => { const c = caloriesList.filter(pred).length; return { count: c, percent: round((c / total) * 100, 1) }; };
    calorie_distribution = [
      { label: '<1500 kcal', ...bucket((c) => c < 1500) },
      { label: '1500-2000 kcal', ...bucket((c) => c >= 1500 && c < 2000) },
      { label: '2000-2500 kcal', ...bucket((c) => c >= 2000 && c < 2500) },
      { label: '2500-3000 kcal', ...bucket((c) => c >= 2500 && c < 3000) },
      { label: '3000+ kcal', ...bucket((c) => c >= 3000) },
    ];
  }

  // === MEAL TIMING ===
  let meal_timing = {};
  if (foodItems.length) {
    const hours = new Array(24).fill(0);
    for (const f of foodItems) hours[new Date(f.consumed_at).getHours()] += Number(f.calories) || 0;
    const sumH = (range) => range.reduce((s, h) => s + hours[h], 0);
    const morning = sumH([5, 6, 7, 8, 9, 10]), midday = sumH([11, 12, 13, 14]), afternoon = sumH([15, 16, 17]), evening = sumH([18, 19, 20, 21]), night = sumH([22, 23, 0, 1, 2, 3, 4]);
    const totalCal = morning + midday + afternoon + evening + night;
    if (totalCal > 0) meal_timing = { morning: round((morning / totalCal) * 100, 1), midday: round((midday / totalCal) * 100, 1), afternoon: round((afternoon / totalCal) * 100, 1), evening: round((evening / totalCal) * 100, 1), night: round((night / totalCal) * 100, 1) };
  }
  if ((meal_timing.night || 0) > 15) insights.push({ type: 'timing', icon: '🌙', title: 'Late Night Eating', description: `${(meal_timing.night).toFixed(0)}% of your calories are consumed late at night (after 10 PM).`, recommendation: 'Try to finish eating earlier for better digestion and sleep quality.' });
  if (calorie_distribution.length) {
    const high = calorie_distribution.find((d) => d.label.includes('3000+'));
    if (high && high.percent > 20) insights.push({ type: 'distribution', icon: '📊', title: 'High Calorie Days', description: `${high.percent.toFixed(0)}% of your days exceed 3000 calories.`, recommendation: 'Identify triggers for high-calorie days and plan alternatives.' });
  }
  if ((nutrition_score.total || 0) >= 80) achievements.push({ icon: '🌟', title: 'Nutrition Master', desc: 'Excellent overall nutrition score' });

  return {
    period, daily_data, weekly_summary, overall_stats, streaks, weight_analysis, weight_pace, projections,
    macro_analysis, day_of_week_stats, weekday_insights, consistency_score, insights, achievements,
    nutrition_score, weekly_reports, monthly_reports, top_foods, best_worst_days, calorie_distribution, meal_timing,
  };
}

const MONTH_ABBR = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function monthBounds(year, month) {
  const start = new Date(year, month - 1, 1, 0, 0, 0, 0);
  const end = new Date(year, month, 0, 23, 59, 59, 999); // day 0 of next month = last day
  return { start, end, lastDay: end.getDate() };
}

async function monthData(monthStr, allFood, allWeight) {
  const [year, month] = monthStr.split('-').map(Number);
  const { start, end } = monthBounds(year, month);
  const food = allFood.filter((f) => { const d = new Date(f.consumed_at); return d >= start && d <= end; });
  const daysLogged = new Set(food.map((f) => dateKey(new Date(f.consumed_at)))).size;
  const totals = food.reduce((a, f) => { a.cal += Number(f.calories) || 0; a.prot += Number(f.protein) || 0; a.carb += Number(f.carbohydrates) || 0; a.fat += Number(f.fat) || 0; return a; }, { cal: 0, prot: 0, carb: 0, fat: 0 });

  const weights = allWeight.filter((w) => { const d = new Date(w.recorded_at); return d >= start && d <= end; });
  let weight = null;
  if (weights.length) {
    const vals = weights.map((w) => Number(w.weight));
    weight = { avg: round(mean(vals), 1), start: vals[0], end: vals[vals.length - 1], change: round(vals[vals.length - 1] - vals[0], 2), min: round(Math.min(...vals), 1), max: round(Math.max(...vals), 1) };
  }

  const nameMap = new Map();
  for (const f of food) { const g = nameMap.get(f.product_name) || { count: 0, total_cal: 0 }; g.count += 1; g.total_cal += Number(f.calories) || 0; nameMap.set(f.product_name, g); }
  const top_foods = [...nameMap.entries()].map(([product_name, g]) => ({ product_name, count: g.count, total_cal: g.total_cal })).sort((a, b) => b.count - a.count).slice(0, 10);

  return {
    month: monthStr, days_logged: daysLogged,
    total_calories: totals.cal, total_protein: totals.prot, total_carbs: totals.carb, total_fat: totals.fat,
    avg_calories: daysLogged ? round(totals.cal / daysLogged, 0) : 0,
    avg_protein: daysLogged ? round(totals.prot / daysLogged, 1) : 0,
    avg_carbs: daysLogged ? round(totals.carb / daysLogged, 1) : 0,
    avg_fat: daysLogged ? round(totals.fat / daysLogged, 1) : 0,
    items_count: food.length,
    weight, top_foods,
  };
}

export async function monthCompare(monthA, monthB) {
  if (!monthA || !monthB) return { error: 'Both month_a and month_b are required' };
  const allFood = await foodRepo.all();
  const allWeight = await weightRepo.allAsc();
  return { month_a: await monthData(monthA, allFood, allWeight), month_b: await monthData(monthB, allFood, allWeight) };
}

export async function yearlyTrends(yearParam = 'last12') {
  const now = new Date();
  const allFood = await foodRepo.all();
  const allWeight = await weightRepo.allAsc();

  let months = [];
  if (yearParam === 'last12') {
    for (let i = 11; i >= 0; i--) { const dt = subDays(now, i * 30); months.push([dt.getFullYear(), dt.getMonth() + 1]); }
  } else if (yearParam === 'all') {
    const first = [...allFood].sort((a, b) => new Date(a.consumed_at) - new Date(b.consumed_at))[0];
    if (first) {
      const d0 = new Date(first.consumed_at);
      let y = d0.getFullYear(), m = d0.getMonth() + 1;
      while (y < now.getFullYear() || (y === now.getFullYear() && m <= now.getMonth() + 1)) {
        months.push([y, m]); m += 1; if (m === 13) { m = 1; y += 1; }
      }
    } else months = [[now.getFullYear(), now.getMonth() + 1]];
  } else {
    const y = parseInt(yearParam, 10);
    months = Array.from({ length: 12 }, (_, i) => [y, i + 1]);
  }

  const monthly_data = [];
  for (const [year, month] of months) {
    const { start, end, lastDay } = monthBounds(year, month);
    const food = allFood.filter((f) => { const d = new Date(f.consumed_at); return d >= start && d <= end; });
    const daysLogged = new Set(food.map((f) => dateKey(new Date(f.consumed_at)))).size;
    const totals = food.reduce((a, f) => { a.cal += Number(f.calories) || 0; a.prot += Number(f.protein) || 0; a.carb += Number(f.carbohydrates) || 0; a.fat += Number(f.fat) || 0; return a; }, { cal: 0, prot: 0, carb: 0, fat: 0 });

    const weights = allWeight.filter((w) => { const d = new Date(w.recorded_at); return d >= start && d <= end; });
    let avgWeight = null, weightDelta = null;
    if (weights.length) { const vals = weights.map((w) => Number(w.weight)); avgWeight = round(mean(vals), 1); weightDelta = vals.length > 1 ? round(vals[vals.length - 1] - vals[0], 2) : 0; }

    const nameMap = new Map();
    for (const f of food) nameMap.set(f.product_name, (nameMap.get(f.product_name) || 0) + 1);
    let topFood = null, topCount = -1;
    for (const [name, c] of nameMap) if (c > topCount) { topCount = c; topFood = name; }

    monthly_data.push({
      month: `${year}-${p(month)}`, month_name: MONTH_ABBR[month], year,
      days_logged: daysLogged, days_in_month: lastDay,
      consistency: lastDay > 0 ? round((daysLogged / lastDay) * 100, 1) : 0,
      total_calories: totals.cal,
      avg_calories: daysLogged ? round(totals.cal / daysLogged, 0) : 0,
      avg_protein: daysLogged ? round(totals.prot / daysLogged, 1) : 0,
      avg_carbs: daysLogged ? round(totals.carb / daysLogged, 1) : 0,
      avg_fat: daysLogged ? round(totals.fat / daysLogged, 1) : 0,
      avg_weight: avgWeight, weight_delta: weightDelta, top_food: topFood,
    });
  }
  return { months: monthly_data };
}
