import { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Calendar,
  Flame,
  Beef,
  Scale,
  Dumbbell,
  Activity,
  Target,
  Award,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
  AlertCircle,
  Clock,
  Trophy,
  Star,
  ChevronRight,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { Card, Badge, Button, ProgressBar } from '../components/ui';
import { analyticsApi } from '../api';

const COLORS = {
  primary: '#0ea5e9',
  protein: '#ef4444',
  carbs: '#f97316',
  fat: '#eab308',
  success: '#22c55e',
  warning: '#f59e0b',
  grid: '#374151',
  text: '#9ca3af',
};

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('90');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await analyticsApi.getAnalytics({ period: timeRange });
      setData(response);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="text-center py-12">
        <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
        <p className="text-gray-400">{error}</p>
        <Button variant="ghost" onClick={fetchAnalytics} className="mt-4">Try Again</Button>
      </Card>
    );
  }

  const weeklySummary = data?.weekly_summary || {};
  const overallStats = data?.overall_stats || {};
  const streaks = data?.streaks || {};
  const weightAnalysis = data?.weight_analysis || {};
  const weightPace = data?.weight_pace || {};
  const projections = data?.projections || {};
  const macroAnalysis = data?.macro_analysis || {};
  const dayOfWeekStats = data?.day_of_week_stats || {};
  const weekdayInsights = data?.weekday_insights || {};
  const consistencyScore = data?.consistency_score || {};
  const insights = data?.insights || [];
  const achievements = data?.achievements || [];
  const nutritionScore = data?.nutrition_score || {};
  const weeklyReports = data?.weekly_reports || [];
  const monthlyReports = data?.monthly_reports || [];
  const topFoods = data?.top_foods || [];
  const bestWorstDays = data?.best_worst_days || {};
  const calorieDistribution = data?.calorie_distribution || [];
  const mealTiming = data?.meal_timing || {};
  const dailyData = data?.daily_data || [];

  const caloriesDiff = (weeklySummary.comparison?.calories_diff || 0);
  const proteinDiff = (weeklySummary.comparison?.protein_diff || 0);

  // Prepare chart data
  const caloriesChartData = dailyData.slice(-14).map(d => ({
    date: format(parseISO(d.date), 'MMM d'),
    calories: Math.round(d.calories),
  }));

  const macrosChartData = dailyData.slice(-14).map(d => ({
    date: format(parseISO(d.date), 'MMM d'),
    protein: Math.round(d.protein),
    carbs: Math.round(d.carbs),
    fat: Math.round(d.fat),
  }));

  const dayOfWeekChartData = Object.entries(dayOfWeekStats).map(([day, stats]) => ({
    day: day.slice(0, 3),
    calories: stats.avg_calories,
    count: stats.count,
  }));

  const macroPieData = macroAnalysis.protein_percent ? [
    { name: 'Protein', value: macroAnalysis.protein_percent, color: COLORS.protein },
    { name: 'Carbs', value: macroAnalysis.carbs_percent, color: COLORS.carbs },
    { name: 'Fat', value: macroAnalysis.fat_percent, color: COLORS.fat },
  ] : [];

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Analytics</h1>
          <p className="text-gray-400 mt-1">Deep insights into your health journey</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 p-1 bg-gray-700 rounded-lg">
            {[
              { value: '7', label: '1W' },
              { value: '30', label: '1M' },
              { value: '90', label: '3M' },
              { value: '180', label: '6M' },
              { value: '365', label: '1Y' },
              { value: 'all', label: 'All' },
            ].map((range) => (
              <button
                key={range.value}
                onClick={() => setTimeRange(range.value)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  timeRange === range.value
                    ? 'bg-gray-600 text-gray-100 shadow-sm'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
          {streaks.current_streak > 0 && (
            <Badge className="bg-orange-500/20 text-orange-400 border-0 px-3 py-1">
              <Zap className="w-3.5 h-3.5 mr-1" />
              {streaks.current_streak} day streak
            </Badge>
          )}
        </div>
      </div>

      {/* Weekly Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-orange-500/20 to-orange-600/10 border-orange-500/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Avg Calories</p>
              <p className="text-2xl font-bold text-gray-100">{Math.round(weeklySummary.this_week?.avg_calories || 0)}</p>
              <div className={`flex items-center text-sm ${caloriesDiff >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {caloriesDiff >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                {Math.abs(caloriesDiff)} vs last week
              </div>
            </div>
            <Flame className="w-10 h-10 text-orange-500 opacity-50" />
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-red-500/20 to-red-600/10 border-red-500/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Avg Protein</p>
              <p className="text-2xl font-bold text-gray-100">{Math.round(weeklySummary.this_week?.avg_protein || 0)}g</p>
              <div className={`flex items-center text-sm ${proteinDiff >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {proteinDiff >= 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                {Math.abs(proteinDiff)}g vs last week
              </div>
            </div>
            <Beef className="w-10 h-10 text-red-500 opacity-50" />
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border-blue-500/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Workouts</p>
              <p className="text-2xl font-bold text-gray-100">{weeklySummary.this_week?.workouts || 0}</p>
              <p className="text-sm text-gray-500">{weeklySummary.comparison?.workouts_diff || 0} vs last week</p>
            </div>
            <Dumbbell className="w-10 h-10 text-blue-500 opacity-50" />
          </div>
        </Card>

        <Card className="bg-gradient-to-br from-green-500/20 to-green-600/10 border-green-500/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Days Logged</p>
              <p className="text-2xl font-bold text-gray-100">{weeklySummary.this_week?.days_logged || 0}/7</p>
              <p className="text-sm text-gray-500">{Math.round((weeklySummary.this_week?.days_logged || 0) / 7 * 100)}% consistency</p>
            </div>
            <Calendar className="w-10 h-10 text-green-500 opacity-50" />
          </div>
        </Card>
      </div>

      {/* Overall Summary */}
      {overallStats.total_days_logged > 0 && (
        <Card title="Overall Summary" subtitle={`${overallStats.total_days_logged} days logged`}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-orange-400">{Math.round(overallStats.avg_daily_calories || 0)}</p>
              <p className="text-sm text-gray-400">Avg Daily Calories</p>
              <p className="text-xs text-gray-500">Range: {overallStats.calorie_min} - {overallStats.calorie_max}</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-red-400">{overallStats.avg_daily_protein || 0}g</p>
              <p className="text-sm text-gray-400">Avg Daily Protein</p>
              <p className="text-xs text-gray-500">Total: {overallStats.total_protein?.toLocaleString()}g</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-blue-400">{overallStats.avg_daily_carbs || 0}g</p>
              <p className="text-sm text-gray-400">Avg Daily Carbs</p>
              <p className="text-xs text-gray-500">Total: {overallStats.total_carbs?.toLocaleString()}g</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-400">{overallStats.avg_daily_fat || 0}g</p>
              <p className="text-sm text-gray-400">Avg Daily Fat</p>
              <p className="text-xs text-gray-500">Total: {overallStats.total_fat?.toLocaleString()}g</p>
            </div>
          </div>
        </Card>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Calories Trend */}
        <Card title="Calories Trend" subtitle="Last 14 days">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={caloriesChartData}>
                <defs>
                  <linearGradient id="colorCal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.4} />
                    <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
                <XAxis dataKey="date" tick={{ fill: COLORS.text, fontSize: 12 }} />
                <YAxis tick={{ fill: COLORS.text, fontSize: 12 }} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }} />
                <Area type="monotone" dataKey="calories" stroke={COLORS.primary} fill="url(#colorCal)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Macros Distribution */}
        {macroPieData.length > 0 && (
          <Card title="Macro Distribution" subtitle="Average breakdown">
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={macroPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}%`}
                  >
                    {macroPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {macroAnalysis.protein_per_kg && (
              <p className="text-center text-sm text-gray-400 mt-2">
                Protein: {macroAnalysis.protein_per_kg}g per kg body weight
              </p>
            )}
          </Card>
        )}
      </div>

      {/* Weight Progress */}
      {weightAnalysis.current_weight && (
        <Card title="Weight Progress" subtitle={`${weightAnalysis.days_tracked} measurements`}>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-6">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-100">{weightAnalysis.start_weight} kg</p>
              <p className="text-sm text-gray-400">Start Weight</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-primary-400">{weightAnalysis.current_weight} kg</p>
              <p className="text-sm text-gray-400">Current Weight</p>
            </div>
            <div className="text-center">
              <p className={`text-2xl font-bold ${weightAnalysis.total_change < 0 ? 'text-green-400' : 'text-red-400'}`}>
                {weightAnalysis.total_change > 0 ? '+' : ''}{weightAnalysis.total_change} kg
              </p>
              <p className="text-sm text-gray-400">Total Change</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-100">{weightAnalysis.min_weight} kg</p>
              <p className="text-sm text-gray-400">Lowest</p>
            </div>
          </div>

          {weightPace.weekly_rate && (
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-300">Weekly Rate</span>
                <span className={`font-semibold ${weightPace.weekly_rate < 0 ? 'text-green-400' : 'text-orange-400'}`}>
                  {weightPace.weekly_rate > 0 ? '+' : ''}{weightPace.weekly_rate} kg/week
                </span>
              </div>
              {weightPace.pace_assessment && (
                <p className="text-sm text-gray-400">{weightPace.pace_assessment}</p>
              )}
              {weightPace.estimated_daily_deficit && (
                <p className="text-xs text-gray-500 mt-1">
                  Estimated daily deficit: {Math.abs(weightPace.estimated_daily_deficit)} kcal
                </p>
              )}
            </div>
          )}

          {/* Projections */}
          {projections['4_weeks'] && (
            <div className="mt-4 grid grid-cols-3 gap-4">
              <div className="bg-gray-800/50 rounded-lg p-3 text-center">
                <p className="text-sm text-gray-400">In 4 Weeks</p>
                <p className="text-lg font-semibold text-gray-200">{projections['4_weeks']} kg</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3 text-center">
                <p className="text-sm text-gray-400">In 8 Weeks</p>
                <p className="text-lg font-semibold text-gray-200">{projections['8_weeks']} kg</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3 text-center">
                <p className="text-sm text-gray-400">In 12 Weeks</p>
                <p className="text-lg font-semibold text-gray-200">{projections['12_weeks']} kg</p>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Day of Week Analysis */}
      {dayOfWeekChartData.length > 0 && (
        <Card title="Day of Week Analysis" subtitle="Average calories by day">
          <div className="h-64 mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={dayOfWeekChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
                <XAxis dataKey="day" tick={{ fill: COLORS.text, fontSize: 12 }} />
                <YAxis tick={{ fill: COLORS.text, fontSize: 12 }} />
                <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }} />
                <Bar dataKey="calories" fill={COLORS.primary} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {weekdayInsights.lowest_day && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-sm text-gray-400">Lowest Day</p>
                <p className="font-semibold text-green-400">{weekdayInsights.lowest_day.name}</p>
                <p className="text-xs text-gray-500">{weekdayInsights.lowest_day.calories} kcal</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Highest Day</p>
                <p className="font-semibold text-orange-400">{weekdayInsights.highest_day.name}</p>
                <p className="text-xs text-gray-500">{weekdayInsights.highest_day.calories} kcal</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Weekday Avg</p>
                <p className="font-semibold text-gray-200">{weekdayInsights.weekday_avg} kcal</p>
              </div>
              <div>
                <p className="text-sm text-gray-400">Weekend Avg</p>
                <p className="font-semibold text-gray-200">{weekdayInsights.weekend_avg} kcal</p>
                <p className="text-xs text-gray-500">{weekdayInsights.weekend_difference > 0 ? '+' : ''}{weekdayInsights.weekend_difference} vs weekdays</p>
              </div>
            </div>
          )}
        </Card>
      )}

      {/* Streaks & Achievements Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Streaks */}
        <Card title="Logging Streaks" subtitle="Your consistency">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center bg-orange-500/10 rounded-lg p-4">
              <Flame className="w-8 h-8 text-orange-500 mx-auto mb-2" />
              <p className="text-2xl font-bold text-orange-400">{streaks.current_streak || 0}</p>
              <p className="text-sm text-gray-400">Current Streak</p>
            </div>
            <div className="text-center bg-yellow-500/10 rounded-lg p-4">
              <Trophy className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
              <p className="text-2xl font-bold text-yellow-400">{streaks.longest_streak || 0}</p>
              <p className="text-sm text-gray-400">Best Streak</p>
            </div>
            <div className="text-center bg-blue-500/10 rounded-lg p-4">
              <BarChart3 className="w-8 h-8 text-blue-500 mx-auto mb-2" />
              <p className="text-2xl font-bold text-blue-400">{streaks.total_days || 0}</p>
              <p className="text-sm text-gray-400">Total Days</p>
            </div>
            <div className="text-center bg-green-500/10 rounded-lg p-4">
              <Target className="w-8 h-8 text-green-500 mx-auto mb-2" />
              <p className="text-2xl font-bold text-green-400">{streaks.consistency_rate || 0}%</p>
              <p className="text-sm text-gray-400">Consistency</p>
            </div>
          </div>
        </Card>

        {/* Achievements */}
        {achievements.length > 0 && (
          <Card title="Achievements" subtitle={`${achievements.length} unlocked`}>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {achievements.map((achievement, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-3 text-center">
                  <span className="text-2xl">{achievement.icon}</span>
                  <p className="font-semibold text-gray-200 mt-1 text-sm">{achievement.title}</p>
                  <p className="text-xs text-gray-500">{achievement.desc}</p>
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>

      {/* Nutrition Score & Consistency */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Nutrition Score */}
        {nutritionScore.total && (
          <Card title="Nutrition Score" subtitle="Overall health rating">
            <div className="flex items-center gap-6 mb-6">
              <div className={`w-24 h-24 rounded-full flex items-center justify-center text-4xl font-bold ${
                nutritionScore.grade === 'A' ? 'bg-green-500/20 text-green-400' :
                nutritionScore.grade === 'B' ? 'bg-blue-500/20 text-blue-400' :
                nutritionScore.grade === 'C' ? 'bg-yellow-500/20 text-yellow-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {nutritionScore.grade}
              </div>
              <div>
                <p className="text-3xl font-bold text-gray-100">{nutritionScore.total}/100</p>
                <p className="text-gray-400">Overall Score</p>
              </div>
            </div>
            <div className="space-y-3">
              {nutritionScore.breakdown?.map((item, index) => (
                <div key={index}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">{item.name}</span>
                    <span className="text-gray-300">{item.score}/{item.max}</span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{ width: `${(item.score / item.max) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        )}

        {/* Calorie Consistency */}
        {consistencyScore.score && (
          <Card title="Calorie Consistency" subtitle="How stable is your intake">
            <div className="text-center mb-6">
              <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full ${
                consistencyScore.rating === 'Excellent' ? 'bg-green-500/20' :
                consistencyScore.rating === 'Good' ? 'bg-blue-500/20' :
                consistencyScore.rating === 'Moderate' ? 'bg-yellow-500/20' :
                'bg-red-500/20'
              }`}>
                <span className="text-3xl font-bold text-gray-100">{consistencyScore.score}</span>
              </div>
              <p className={`mt-2 font-semibold ${
                consistencyScore.rating === 'Excellent' ? 'text-green-400' :
                consistencyScore.rating === 'Good' ? 'text-blue-400' :
                consistencyScore.rating === 'Moderate' ? 'text-yellow-400' :
                'text-red-400'
              }`}>{consistencyScore.rating}</p>
              <p className="text-sm text-gray-500">Coefficient of Variation: {consistencyScore.cv}%</p>
            </div>
          </Card>
        )}
      </div>

      {/* Insights */}
      {insights.length > 0 && (
        <Card title="Personalized Insights" subtitle={`${insights.length} recommendations`}>
          <div className="space-y-4">
            {insights.map((insight, index) => (
              <div key={index} className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{insight.icon}</span>
                  <div>
                    <p className="font-semibold text-gray-200">{insight.title}</p>
                    <p className="text-sm text-gray-400 mt-1">{insight.description}</p>
                    {insight.recommendation && (
                      <p className="text-sm text-primary-400 mt-2">
                        <span className="font-medium">Tip:</span> {insight.recommendation}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Top Foods */}
      {topFoods.length > 0 && (
        <Card title="Top 10 Most Eaten Foods" subtitle="Your favorites">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                  <th className="pb-2 font-medium">#</th>
                  <th className="pb-2 font-medium">Food</th>
                  <th className="pb-2 font-medium text-right">Times</th>
                  <th className="pb-2 font-medium text-right">Total Cal</th>
                </tr>
              </thead>
              <tbody>
                {topFoods.map((food, index) => (
                  <tr key={index} className="border-b border-gray-800">
                    <td className="py-3 text-gray-500">{index + 1}</td>
                    <td className="py-3 text-gray-200 max-w-xs truncate">{food.name}</td>
                    <td className="py-3 text-right text-gray-400">{food.count}x</td>
                    <td className="py-3 text-right text-orange-400">{Math.round(food.total_calories)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Record Days */}
      {bestWorstDays.lowest_calorie_day && (
        <Card title="Record Days" subtitle="Your extremes">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-500/10 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-400">Lowest Calories</p>
              <p className="text-2xl font-bold text-green-400">{Math.round(bestWorstDays.lowest_calorie_day.calories)}</p>
              <p className="text-xs text-gray-500">{format(parseISO(bestWorstDays.lowest_calorie_day.date), 'MMM d, yyyy')}</p>
            </div>
            <div className="bg-orange-500/10 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-400">Highest Calories</p>
              <p className="text-2xl font-bold text-orange-400">{Math.round(bestWorstDays.highest_calorie_day.calories)}</p>
              <p className="text-xs text-gray-500">{format(parseISO(bestWorstDays.highest_calorie_day.date), 'MMM d, yyyy')}</p>
            </div>
            <div className="bg-red-500/10 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-400">Most Protein</p>
              <p className="text-2xl font-bold text-red-400">{Math.round(bestWorstDays.highest_protein_day.protein)}g</p>
              <p className="text-xs text-gray-500">{format(parseISO(bestWorstDays.highest_protein_day.date), 'MMM d, yyyy')}</p>
            </div>
          </div>
        </Card>
      )}

      {/* Calorie Distribution */}
      {calorieDistribution.length > 0 && (
        <Card title="Calorie Distribution" subtitle="How your days break down">
          <div className="space-y-3">
            {calorieDistribution.map((bucket, index) => (
              <div key={index}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-400">{bucket.label}</span>
                  <span className="text-gray-300">{bucket.count} days ({bucket.percent}%)</span>
                </div>
                <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${bucket.percent}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Meal Timing */}
      {mealTiming.morning !== undefined && (
        <Card title="Meal Timing" subtitle="When you eat">
          <div className="grid grid-cols-5 gap-2">
            {[
              { label: 'Morning', value: mealTiming.morning, time: '5-10' },
              { label: 'Midday', value: mealTiming.midday, time: '11-14' },
              { label: 'Afternoon', value: mealTiming.afternoon, time: '15-17' },
              { label: 'Evening', value: mealTiming.evening, time: '18-21' },
              { label: 'Night', value: mealTiming.night, time: '22-4' },
            ].map((period, index) => (
              <div key={index} className="text-center">
                <div className="h-32 bg-gray-800 rounded-lg relative overflow-hidden">
                  <div
                    className="absolute bottom-0 w-full bg-primary-500/50"
                    style={{ height: `${period.value}%` }}
                  />
                  <span className="absolute inset-0 flex items-center justify-center font-bold text-gray-200">
                    {Math.round(period.value)}%
                  </span>
                </div>
                <p className="text-xs text-gray-400 mt-2">{period.label}</p>
                <p className="text-xs text-gray-600">{period.time}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Weekly Reports */}
      {weeklyReports.length > 0 && (
        <Card title="Weekly Reports" subtitle="Historical data">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-700">
                  <th className="pb-2 font-medium">Week</th>
                  <th className="pb-2 font-medium text-right">Days</th>
                  <th className="pb-2 font-medium text-right">Avg Cal</th>
                  <th className="pb-2 font-medium text-right">Avg P</th>
                  <th className="pb-2 font-medium text-right">Avg C</th>
                  <th className="pb-2 font-medium text-right">Avg F</th>
                </tr>
              </thead>
              <tbody>
                {weeklyReports.slice(0, 8).map((report, index) => (
                  <tr key={index} className="border-b border-gray-800">
                    <td className="py-2 text-gray-300">
                      {report.week_start ? format(parseISO(report.week_start), 'MMM d') : '-'}
                    </td>
                    <td className="py-2 text-right text-gray-400">{report.days_logged}</td>
                    <td className="py-2 text-right text-orange-400">{report.avg_calories}</td>
                    <td className="py-2 text-right text-red-400">{report.avg_protein}g</td>
                    <td className="py-2 text-right text-blue-400">{report.avg_carbs}g</td>
                    <td className="py-2 text-right text-yellow-400">{report.avg_fat}g</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Monthly Reports */}
      {monthlyReports.length > 0 && (
        <Card title="Monthly Reports" subtitle="Long-term trends">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-700">
                  <th className="pb-2 font-medium">Month</th>
                  <th className="pb-2 font-medium text-right">Days</th>
                  <th className="pb-2 font-medium text-right">Avg Cal</th>
                  <th className="pb-2 font-medium text-right">Avg P</th>
                  <th className="pb-2 font-medium text-right">Avg C</th>
                  <th className="pb-2 font-medium text-right">Avg F</th>
                </tr>
              </thead>
              <tbody>
                {monthlyReports.slice(0, 6).map((report, index) => (
                  <tr key={index} className="border-b border-gray-800">
                    <td className="py-2 text-gray-300">
                      {report.month ? format(parseISO(report.month), 'MMM yyyy') : '-'}
                    </td>
                    <td className="py-2 text-right text-gray-400">{report.days_logged}</td>
                    <td className="py-2 text-right text-orange-400">{report.avg_calories}</td>
                    <td className="py-2 text-right text-red-400">{report.avg_protein}g</td>
                    <td className="py-2 text-right text-blue-400">{report.avg_carbs}g</td>
                    <td className="py-2 text-right text-yellow-400">{report.avg_fat}g</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
