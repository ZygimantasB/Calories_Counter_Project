import { useState, useEffect } from 'react';
import {
  Flame,
  Beef,
  Wheat,
  Droplets,
  Scale,
  Dumbbell,
  Activity,
  TrendingUp,
  TrendingDown,
  Calendar,
  Target,
  Zap,
  Utensils,
  AlertTriangle,
  AlertCircle,
  Info,
  X,
  Shield,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { format } from 'date-fns';
import { StatCard, Card, ProgressBar, Badge } from '../components/ui';
import { foodApi, weightApi } from '../api';
import settingsApi from '../api/settings';

const CHART_COLORS = {
  primary: '#0ea5e9',
  protein: '#ef4444',
  carbs: '#f97316',
  fat: '#eab308',
  grid: '#374151',
  text: '#9ca3af',
};

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [caloriesData, setCaloriesData] = useState([]);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('month');
  const [dismissedWarnings, setDismissedWarnings] = useState([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const daysMap = { week: 7, month: 30, '3months': 90, '6months': 180, year: 365, all: 'all' };
        const days = daysMap[timeRange] || 30;

        // Fetch dashboard data and calories trend in parallel
        const [dashboard, caloriesTrend] = await Promise.all([
          foodApi.getDashboard(),
          foodApi.getCaloriesTrend(days),
        ]);

        setDashboardData(dashboard);

        // Use 'trend' array for React format, fallback to building from labels/data arrays
        if (caloriesTrend && caloriesTrend.trend && caloriesTrend.trend.length > 0) {
          setCaloriesData(caloriesTrend.trend.map(item => ({
            date: item.date,
            calories: item.calories,
            target: dashboard?.goals?.daily_calories || 2500,
          })));
        } else if (caloriesTrend && caloriesTrend.labels && caloriesTrend.data) {
          // Fallback: build from labels + data arrays
          setCaloriesData(caloriesTrend.labels.map((label, index) => ({
            date: label,
            calories: caloriesTrend.data[index] || 0,
            target: dashboard?.goals?.daily_calories || 2500,
          })));
        }
        setLoading(false);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data');
        setLoading(false);
      }
    };
    fetchDashboardData();
  }, [timeRange]);

  // Use real data from API or fallback to defaults
  const todayStats = {
    calories: dashboardData?.today?.calories || 0,
    caloriesTarget: dashboardData?.goals?.daily_calories || 2500,
    protein: dashboardData?.today?.protein || 0,
    proteinTarget: dashboardData?.goals?.daily_protein || 150,
    carbs: dashboardData?.today?.carbs || 0,
    carbsTarget: dashboardData?.goals?.daily_carbs || 300,
    fat: dashboardData?.today?.fat || 0,
    fatTarget: dashboardData?.goals?.daily_fat || 70,
  };

  const weeklyStats = {
    workouts: dashboardData?.week?.workouts || 0,
    runs: dashboardData?.week?.runs || 0,
    avgCalories: Math.round((dashboardData?.week?.calories || 0) / 7),
    daysLogged: dashboardData?.today?.count || 0,
  };

  const warnings = (dashboardData?.warnings || []).filter(
    w => !dismissedWarnings.includes(w.type)
  );

  const recentMeals = (dashboardData?.recent_foods || []).map(food => ({
    id: food.id,
    name: food.product_name,
    calories: food.calories,
    time: food.consumed_at ? format(new Date(food.consumed_at), 'h:mm a') : '',
  }));

  const [updatingGoal, setUpdatingGoal] = useState(false);

  const handleGoalChange = async (goal) => {
    if (updatingGoal || goal === dashboardData?.goals?.fitness_goal) return;
    try {
      setUpdatingGoal(true);
      await settingsApi.updateFitnessGoal(goal);
      // Refetch dashboard data
      const dashboard = await foodApi.getDashboard();
      setDashboardData(dashboard);
    } catch (err) {
      console.error('Error updating fitness goal:', err);
    } finally {
      setUpdatingGoal(false);
    }
  };

  const dismissWarning = (type) => {
    setDismissedWarnings(prev => [...prev, type]);
  };

  const getWarningIcon = (severity) => {
    switch (severity) {
      case 'error': return AlertCircle;
      case 'warning': return AlertTriangle;
      default: return Info;
    }
  };

  const getWarningStyles = (severity) => {
    switch (severity) {
      case 'error': return 'bg-red-500/10 border-red-500/30 text-red-400';
      case 'warning': return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400';
      default: return 'bg-blue-500/10 border-blue-500/30 text-blue-400';
    }
  };

  // MacroProgressBar component
  const MacroProgressBar = ({ label, current, target, unit, color, icon }) => {
    const percentage = target > 0 ? Math.round((current / target) * 100) : 0;
    const remaining = target - current;
    const exceeded = current > target;

    const colorClasses = {
      orange: { bar: 'bg-orange-500', text: 'text-orange-400', bg: 'bg-orange-500/20' },
      red: { bar: 'bg-red-500', text: 'text-red-400', bg: 'bg-red-500/20' },
      blue: { bar: 'bg-blue-500', text: 'text-blue-400', bg: 'bg-blue-500/20' },
      yellow: { bar: 'bg-yellow-500', text: 'text-yellow-400', bg: 'bg-yellow-500/20' },
    };

    const colors = colorClasses[color] || colorClasses.blue;
    const barColor = exceeded ? 'bg-red-500' : percentage > 90 ? 'bg-yellow-500' : colors.bar;

    return (
      <div>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className={colors.text}>{icon}</span>
            <span className="font-medium text-gray-200">{label}</span>
          </div>
          <span className={`text-sm font-medium ${exceeded ? 'text-red-400' : 'text-gray-400'}`}>
            {exceeded ? `${percentage}% of target` : `${Math.round(remaining)}${unit} left`}
          </span>
        </div>
        <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${barColor}`}
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>
        <div className="flex justify-between mt-1.5 text-xs text-gray-500">
          <span>{Math.round(current)}{unit}</span>
          <span>{target}{unit}</span>
        </div>
      </div>
    );
  };

  const macrosPieData = [
    { name: 'Protein', value: todayStats.protein * 4, color: CHART_COLORS.protein },
    { name: 'Carbs', value: todayStats.carbs * 4, color: CHART_COLORS.carbs },
    { name: 'Fat', value: todayStats.fat * 9, color: CHART_COLORS.fat },
  ];

  const caloriesPercentage = Math.round(
    (todayStats.calories / todayStats.caloriesTarget) * 100
  );

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-xl">
          <p className="text-gray-300 text-sm mb-1">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm font-medium" style={{ color: entry.color }}>
              {entry.name}: {entry.value} {entry.name === 'calories' ? 'kcal' : ''}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-6 animate-in">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Welcome back! Here&apos;s your health overview for today.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 p-1 bg-gray-700 rounded-lg">
            {['week', 'month', '3months', '6months', 'year', 'all'].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                  timeRange === range
                    ? 'bg-gray-600 text-gray-100 shadow-sm'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                {range === 'week'
                  ? '1W'
                  : range === 'month'
                  ? '1M'
                  : range === '3months'
                  ? '3M'
                  : range === '6months'
                  ? '6M'
                  : range === 'year'
                  ? '1Y'
                  : 'All'}
              </button>
            ))}
          </div>
          {dashboardData?.streak > 0 && (
            <Badge className="bg-green-500/20 text-green-400 border-0 px-3 py-1">
              <Zap className="w-3.5 h-3.5 mr-1" />
              {dashboardData.streak} day streak
            </Badge>
          )}
          <span className="text-sm text-gray-500">
            {format(new Date(), 'EEEE, MMMM d')}
          </span>
        </div>
      </div>

      {/* Macro Warnings */}
      {warnings.length > 0 && (
        <div className="space-y-3">
          {warnings.map((warning) => {
            const WarningIcon = getWarningIcon(warning.severity);
            return (
              <div
                key={warning.type}
                className={`flex items-center justify-between p-4 rounded-xl border ${getWarningStyles(warning.severity)}`}
              >
                <div className="flex items-center gap-3">
                  <WarningIcon className="w-5 h-5 flex-shrink-0" />
                  <div>
                    <p className="font-medium">{warning.message}</p>
                    <p className="text-sm opacity-80">
                      Current: {warning.current} / Target: {warning.target}
                      {warning.type !== 'calories' && 'g'}
                      {warning.type === 'calories' && ' kcal'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => dismissWarning(warning.type)}
                  className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Fitness Goal Selector */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { key: 'maintain', label: 'Maintain', icon: Scale, color: 'blue', border: 'border-blue-500', bg: 'bg-blue-500/20', text: 'text-blue-400' },
          { key: 'bulk', label: 'Gain Mass', icon: Dumbbell, color: 'green', border: 'border-green-500', bg: 'bg-green-500/20', text: 'text-green-400' },
          { key: 'cut', label: 'Lose Fat', icon: Flame, color: 'orange', border: 'border-orange-500', bg: 'bg-orange-500/20', text: 'text-orange-400' },
          { key: 'ripped', label: 'Get Ripped', icon: Shield, color: 'red', border: 'border-red-500', bg: 'bg-red-500/20', text: 'text-red-400' },
        ].map(({ key, label, icon: Icon, border, bg, text }) => {
          const isActive = dashboardData?.goals?.fitness_goal === key;
          return (
            <button
              key={key}
              onClick={() => handleGoalChange(key)}
              disabled={updatingGoal}
              className={`flex items-center gap-2 px-4 py-3 rounded-xl border-2 transition-all ${
                isActive
                  ? `${border} ${bg} ${text}`
                  : 'border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600 hover:text-gray-300'
              } ${updatingGoal ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <Icon className="w-4 h-4" />
              <span className="text-sm font-medium">{label}</span>
            </button>
          );
        })}
      </div>

      {/* Today's Progress Card */}
      <Card className="bg-gradient-to-br from-primary-600 to-primary-700 border-0 text-white">
        <div className="flex flex-col lg:flex-row lg:items-center gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-5 h-5" />
              <span className="text-sm font-medium text-white/80">
                Today&apos;s Goal Progress
              </span>
            </div>
            <div className="flex items-baseline gap-3">
              <span className="text-5xl font-bold">{todayStats.calories}</span>
              <span className="text-xl text-white/70">
                / {todayStats.caloriesTarget} kcal
              </span>
            </div>
            <div className="mt-4">
              <div className="h-3 bg-white/20 rounded-full overflow-hidden">
                <div
                  className="h-full bg-white rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(caloriesPercentage, 100)}%` }}
                />
              </div>
              <p className="text-sm text-white/70 mt-2">
                {todayStats.caloriesTarget - todayStats.calories > 0
                  ? `${todayStats.caloriesTarget - todayStats.calories} calories remaining`
                  : 'Goal reached!'}
              </p>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4 lg:gap-6">
            <div className="text-center bg-white/10 rounded-xl p-4">
              <div className="text-2xl font-bold">{todayStats.protein}g</div>
              <div className="text-sm text-white/70">Protein</div>
            </div>
            <div className="text-center bg-white/10 rounded-xl p-4">
              <div className="text-2xl font-bold">{todayStats.carbs}g</div>
              <div className="text-sm text-white/70">Carbs</div>
            </div>
            <div className="text-center bg-white/10 rounded-xl p-4">
              <div className="text-2xl font-bold">{todayStats.fat}g</div>
              <div className="text-sm text-white/70">Fat</div>
            </div>
          </div>
        </div>
      </Card>

      {/* Macro Progress Bars */}
      <Card title="Nutrition Progress" subtitle="Today's intake vs targets">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Calories Progress */}
          <MacroProgressBar
            label="Calories"
            current={todayStats.calories}
            target={todayStats.caloriesTarget}
            unit="kcal"
            color="orange"
            icon={<Flame className="w-4 h-4" />}
          />
          {/* Protein Progress */}
          <MacroProgressBar
            label="Protein"
            current={todayStats.protein}
            target={todayStats.proteinTarget}
            unit="g"
            color="red"
            icon={<Beef className="w-4 h-4" />}
          />
          {/* Carbs Progress */}
          <MacroProgressBar
            label="Carbs"
            current={todayStats.carbs}
            target={todayStats.carbsTarget}
            unit="g"
            color="blue"
            icon={<Wheat className="w-4 h-4" />}
          />
          {/* Fat Progress */}
          <MacroProgressBar
            label="Fat"
            current={todayStats.fat}
            target={todayStats.fatTarget}
            unit="g"
            color="yellow"
            icon={<Droplets className="w-4 h-4" />}
          />
        </div>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Calories Today"
          value={`${todayStats.calories}`}
          subtitle={`${caloriesPercentage}% of daily goal`}
          icon={Flame}
          color="orange"
          trend={dashboardData?.comparison?.calories_percent ? (dashboardData.comparison.calories_percent >= 0 ? 'up' : 'down') : undefined}
          trendValue={dashboardData?.comparison?.calories_percent ? `${dashboardData.comparison.calories_percent > 0 ? '+' : ''}${dashboardData.comparison.calories_percent}%` : undefined}
        />
        <StatCard
          title="Protein"
          value={`${todayStats.protein}g`}
          subtitle={`${Math.round((todayStats.protein / todayStats.proteinTarget) * 100)}% of goal`}
          icon={Beef}
          color="red"
          trend={dashboardData?.comparison?.protein_percent ? (dashboardData.comparison.protein_percent >= 0 ? 'up' : 'down') : undefined}
          trendValue={dashboardData?.comparison?.protein_percent ? `${dashboardData.comparison.protein_percent > 0 ? '+' : ''}${dashboardData.comparison.protein_percent}%` : undefined}
        />
        <StatCard
          title="Current Weight"
          value={dashboardData?.weight?.current ? `${dashboardData.weight.current} kg` : '--'}
          subtitle={dashboardData?.weight?.change
            ? `${dashboardData.weight.change > 0 ? 'Gained' : 'Lost'} ${Math.abs(dashboardData.weight.change)}kg this week`
            : 'No previous data'}
          icon={Scale}
          color="blue"
          trend={dashboardData?.weight?.change ? (dashboardData.weight.change > 0 ? 'up' : 'down') : undefined}
          trendValue={dashboardData?.weight?.change ? `${dashboardData.weight.change > 0 ? '+' : ''}${dashboardData.weight.change}kg` : undefined}
        />
        <StatCard
          title="Workouts"
          value={weeklyStats.workouts}
          subtitle="This week"
          icon={Dumbbell}
          color="purple"
          trend={dashboardData?.comparison?.workouts_diff ? (dashboardData.comparison.workouts_diff >= 0 ? 'up' : 'down') : undefined}
          trendValue={dashboardData?.comparison?.workouts_diff !== undefined ? `${dashboardData.comparison.workouts_diff > 0 ? '+' : ''}${dashboardData.comparison.workouts_diff}` : undefined}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calories Trend Chart */}
        <Card
          title="Calories Trend"
          subtitle="Last 14 days"
          className="lg:col-span-2"
        >
          <div className="h-72">
            {caloriesData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={caloriesData}>
                <defs>
                  <linearGradient id="colorCalories" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.4} />
                    <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: CHART_COLORS.text, fontSize: 12 }}
                  domain={['auto', 'auto']}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="calories"
                  stroke={CHART_COLORS.primary}
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorCalories)"
                />
                <Area
                  type="monotone"
                  dataKey="target"
                  stroke="#6b7280"
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  fillOpacity={0}
                />
              </AreaChart>
            </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">
                No calorie data available
              </div>
            )}
          </div>
        </Card>

        {/* Macros Breakdown */}
        <Card title="Today's Macros" subtitle="Calorie breakdown">
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={macrosPieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  dataKey="value"
                  strokeWidth={0}
                >
                  {macrosPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => [`${Math.round(value)} kcal`, '']}
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 mt-2">
            {macrosPieData.map((entry) => (
              <div key={entry.name} className="flex items-center gap-1.5">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-xs text-gray-400">{entry.name}</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Recent Activity Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Meals */}
        <Card title="Recent Meals" subtitle="Today's food log">
          <div className="space-y-3">
            {recentMeals.length > 0 ? (
              recentMeals.map((meal) => (
                <div
                  key={meal.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-700/50 hover:bg-gray-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center">
                      <Utensils className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-100">{meal.name}</p>
                      <p className="text-sm text-gray-500">{meal.time}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-100">
                      {meal.calories} kcal
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-6 text-gray-500">
                <Utensils className="w-10 h-10 mx-auto mb-2 opacity-50" />
                <p>No meals logged yet today</p>
              </div>
            )}
          </div>
          <a
            href="/app/food"
            className="block w-full mt-4 py-2.5 text-sm font-medium text-primary-400 hover:text-primary-300 hover:bg-gray-700/50 rounded-lg transition-colors text-center"
          >
            View all meals
          </a>
        </Card>

        {/* Weekly Goals */}
        <Card title="Weekly Goals" subtitle="Track your progress">
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-green-500/10 border border-green-500/20">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-green-500 flex items-center justify-center">
                    <Dumbbell className="w-4 h-4 text-white" />
                  </div>
                  <span className="font-medium text-gray-100">
                    Weekly Workouts
                  </span>
                </div>
                <Badge className="bg-green-500/20 text-green-400 border-0">
                  {weeklyStats.workouts}/{dashboardData?.goals?.weekly_workouts || 4}
                </Badge>
              </div>
              <ProgressBar
                value={weeklyStats.workouts}
                max={dashboardData?.goals?.weekly_workouts || 4}
                color="green"
                showValue={false}
                size="lg"
              />
            </div>
            <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center">
                    <Activity className="w-4 h-4 text-white" />
                  </div>
                  <span className="font-medium text-gray-100">Weekly Runs</span>
                </div>
                <Badge className="bg-blue-500/20 text-blue-400 border-0">
                  {weeklyStats.runs}/{dashboardData?.goals?.weekly_runs || 2}
                </Badge>
              </div>
              <ProgressBar
                value={weeklyStats.runs}
                max={dashboardData?.goals?.weekly_runs || 2}
                color="blue"
                showValue={false}
                size="lg"
              />
            </div>
            <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-purple-500 flex items-center justify-center">
                    <Target className="w-4 h-4 text-white" />
                  </div>
                  <span className="font-medium text-gray-100">
                    Today&apos;s Meals Logged
                  </span>
                </div>
                <Badge className="bg-purple-500/20 text-purple-400 border-0">{dashboardData?.today?.count || 0}</Badge>
              </div>
              <p className="text-sm text-gray-400">
                You&apos;ve logged {dashboardData?.today?.count || 0} meals today
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
