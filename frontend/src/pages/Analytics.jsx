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
  ComposedChart,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { format, subDays } from 'date-fns';
import { Card, Badge, Button, ProgressBar } from '../components/ui';
import { analyticsApi } from '../api';

export default function Analytics() {
  const [timeRange, setTimeRange] = useState('week');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const daysMap = { week: 7, month: 30, '3months': 90, year: 365 };
      const days = daysMap[timeRange] || 7;
      const response = await analyticsApi.getAnalytics({ days });
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

  const weeklySummary = data?.weekly_summary || {
    thisWeek: { avgCalories: 0, avgProtein: 0, workouts: 0, runs: 0, daysLogged: 0 },
    lastWeek: { avgCalories: 0, avgProtein: 0, workouts: 0, runs: 0, daysLogged: 0 },
  };
  const goals = data?.goals || [];
  const streaks = data?.streaks || { currentStreak: 0, longestStreak: 0, totalDaysLogged: 0, perfectWeeks: 0 };
  const caloriesData = data?.calories_trend || [];
  const macrosData = data?.macros_trend || [];
  const weightData = data?.weight_trend || [];
  const workoutData = data?.workout_distribution || [];

  const caloriesDiff = weeklySummary.thisWeek.avgCalories - weeklySummary.lastWeek.avgCalories;
  const proteinDiff = weeklySummary.thisWeek.avgProtein - weeklySummary.lastWeek.avgProtein;
  const workoutsDiff = weeklySummary.thisWeek.workouts - weeklySummary.lastWeek.workouts;

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Analytics</h1>
          <p className="text-gray-400 mt-1">
            Deep insights into your health journey
          </p>
        </div>
        <div className="flex items-center gap-2 p-1 bg-gray-700 rounded-lg">
          {['week', 'month', '3months', 'year'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                timeRange === range
                  ? 'bg-gray-600 text-gray-100 shadow-sm'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {range === 'week'
                ? 'Week'
                : range === 'month'
                ? 'Month'
                : range === '3months'
                ? '3 Months'
                : 'Year'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : error ? (
        <Card className="text-center py-8">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-400">{error}</p>
          <Button variant="ghost" onClick={fetchAnalytics} className="mt-4">
            Try Again
          </Button>
        </Card>
      ) : (
        <>
          {/* Weekly Comparison */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-gradient-to-br from-purple-500 to-purple-600 border-0 text-white">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-white/90">This Week</h3>
                  <p className="text-sm text-white/70">Weekly summary</p>
                </div>
                <Badge className="bg-white/20 text-white border-0">
                  <Zap className="w-3.5 h-3.5 mr-1" />
                  {streaks.currentStreak} day streak
                </Badge>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white/10 rounded-xl p-4">
                  <div className="text-2xl font-bold">
                    {weeklySummary.thisWeek.avgCalories}
                  </div>
                  <div className="text-sm text-white/70">Avg Calories</div>
                  <div
                    className={`text-xs mt-1 flex items-center gap-1 ${
                      caloriesDiff >= 0 ? 'text-green-300' : 'text-red-300'
                    }`}
                  >
                    {caloriesDiff >= 0 ? (
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    ) : (
                      <ArrowDownRight className="w-3.5 h-3.5" />
                    )}
                    {Math.abs(caloriesDiff)} vs last week
                  </div>
                </div>
                <div className="bg-white/10 rounded-xl p-4">
                  <div className="text-2xl font-bold">
                    {weeklySummary.thisWeek.avgProtein}g
                  </div>
                  <div className="text-sm text-white/70">Avg Protein</div>
                  <div
                    className={`text-xs mt-1 flex items-center gap-1 ${
                      proteinDiff >= 0 ? 'text-green-300' : 'text-red-300'
                    }`}
                  >
                    {proteinDiff >= 0 ? (
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    ) : (
                      <ArrowDownRight className="w-3.5 h-3.5" />
                    )}
                    {Math.abs(proteinDiff)}g vs last week
                  </div>
                </div>
                <div className="bg-white/10 rounded-xl p-4">
                  <div className="text-2xl font-bold">
                    {weeklySummary.thisWeek.workouts}
                  </div>
                  <div className="text-sm text-white/70">Workouts</div>
                  <div
                    className={`text-xs mt-1 flex items-center gap-1 ${
                      workoutsDiff >= 0 ? 'text-green-300' : 'text-red-300'
                    }`}
                  >
                    {workoutsDiff >= 0 ? (
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    ) : (
                      <ArrowDownRight className="w-3.5 h-3.5" />
                    )}
                    {Math.abs(workoutsDiff)} vs last week
                  </div>
                </div>
                <div className="bg-white/10 rounded-xl p-4">
                  <div className="text-2xl font-bold">
                    {weeklySummary.thisWeek.daysLogged}/7
                  </div>
                  <div className="text-sm text-white/70">Days Logged</div>
                  <div className="text-xs mt-1 text-white/50">
                    {Math.round((weeklySummary.thisWeek.daysLogged / 7) * 100)}%
                    consistency
                  </div>
                </div>
              </div>
            </Card>

            {/* Goal Progress */}
            <Card title="Goal Progress" subtitle="Track your targets">
              <div className="space-y-4">
                {goals.length > 0 ? goals.map((goal) => {
                  const progress = Math.round((goal.current / goal.target) * 100);
                  const isComplete = progress >= 100;
                  const Icon = goal.name.includes('Calorie') ? Flame :
                               goal.name.includes('Protein') ? Beef :
                               goal.name.includes('Workout') ? Dumbbell : Activity;

                  return (
                    <div key={goal.name}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center">
                            <Icon className="w-4 h-4 text-gray-400" />
                          </div>
                          <span className="font-medium text-gray-100">
                            {goal.name}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          {isComplete && (
                            <Badge variant="success" size="sm">
                              Complete
                            </Badge>
                          )}
                          <span className="text-sm text-gray-400">
                            {goal.current} / {goal.target}
                          </span>
                        </div>
                      </div>
                      <ProgressBar
                        value={goal.current}
                        max={goal.target}
                        color={isComplete ? 'green' : 'primary'}
                        showValue={false}
                      />
                    </div>
                  );
                }) : (
                  <div className="text-center py-8 text-gray-500">
                    No goals set yet
                  </div>
                )}
              </div>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Calories Chart */}
            <Card title="Calories Trend" subtitle="Daily calorie intake">
              {caloriesData.length > 0 ? (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={caloriesData}>
                      <defs>
                        <linearGradient id="caloriesGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="day"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#9ca3af', fontSize: 12 }}
                      />
                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#9ca3af', fontSize: 12 }}
                        domain={[1500, 3000]}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="calories"
                        stroke="#f97316"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#caloriesGradient)"
                      />
                      <Line
                        type="monotone"
                        dataKey="target"
                        stroke="#6b7280"
                        strokeWidth={2}
                        strokeDasharray="5 5"
                        dot={false}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-72 flex items-center justify-center text-gray-500">
                  No calorie data to display
                </div>
              )}
            </Card>

            {/* Macros Trend */}
            <Card title="Macros Trend" subtitle="Nutrient breakdown over time">
              {macrosData.length > 0 ? (
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={macrosData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="date"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#9ca3af', fontSize: 12 }}
                      />
                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#9ca3af', fontSize: 12 }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                        }}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="protein"
                        stroke="#ef4444"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="carbs"
                        stroke="#f97316"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="fat"
                        stroke="#eab308"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <div className="h-72 flex items-center justify-center text-gray-500">
                  No macros data to display
                </div>
              )}
            </Card>
          </div>

          {/* Streaks & Achievements */}
          <Card title="Streaks & Achievements" subtitle="Your consistency">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-orange-500/10 border border-orange-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-5 h-5 text-orange-400" />
                  <span className="text-sm font-medium text-gray-400">
                    Current Streak
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-100">
                  {streaks.currentStreak}
                </div>
                <div className="text-sm text-gray-500">days</div>
              </div>
              <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <Award className="w-5 h-5 text-purple-400" />
                  <span className="text-sm font-medium text-gray-400">
                    Best Streak
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-100">
                  {streaks.longestStreak}
                </div>
                <div className="text-sm text-gray-500">days</div>
              </div>
              <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="w-5 h-5 text-blue-400" />
                  <span className="text-sm font-medium text-gray-400">
                    Total Days
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-100">
                  {streaks.totalDaysLogged}
                </div>
                <div className="text-sm text-gray-500">logged</div>
              </div>
              <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-5 h-5 text-green-400" />
                  <span className="text-sm font-medium text-gray-400">
                    Perfect Weeks
                  </span>
                </div>
                <div className="text-3xl font-bold text-gray-100">
                  {streaks.perfectWeeks}
                </div>
                <div className="text-sm text-gray-500">completed</div>
              </div>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
