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

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const daysMap = { week: 7, month: 30, '3months': 90, '6months': 180, year: 365, all: 'all' };
        const days = daysMap[timeRange] || 30;
        // Fetch calories trend
        const caloriesTrend = await foodApi.getCaloriesTrend(days);
        if (caloriesTrend && caloriesTrend.data) {
          setCaloriesData(caloriesTrend.data.map(item => ({
            date: item.date,
            calories: item.calories,
            target: 2500,
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

  // Mock data for now - will be replaced with real API data
  const todayStats = {
    calories: 1850,
    caloriesTarget: 2500,
    protein: 95,
    proteinTarget: 150,
    carbs: 180,
    carbsTarget: 300,
    fat: 55,
    fatTarget: 70,
  };

  const weeklyStats = {
    workouts: 3,
    runs: 2,
    avgCalories: 2150,
    daysLogged: 5,
  };

  const mockRecentMeals = [
    { id: 1, name: 'Grilled Chicken Salad', calories: 450, time: '12:30 PM' },
    { id: 2, name: 'Protein Shake', calories: 280, time: '10:00 AM' },
    { id: 3, name: 'Oatmeal with Berries', calories: 350, time: '8:00 AM' },
  ];

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
          <Badge className="bg-green-500/20 text-green-400 border-0 px-3 py-1">
            <Zap className="w-3.5 h-3.5 mr-1" />
            5 day streak
          </Badge>
          <span className="text-sm text-gray-500">
            {format(new Date(), 'EEEE, MMMM d')}
          </span>
        </div>
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

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Calories Today"
          value={`${todayStats.calories}`}
          subtitle={`${caloriesPercentage}% of daily goal`}
          icon={Flame}
          color="orange"
          trend="up"
          trendValue="+12%"
        />
        <StatCard
          title="Protein"
          value={`${todayStats.protein}g`}
          subtitle={`${Math.round((todayStats.protein / todayStats.proteinTarget) * 100)}% of goal`}
          icon={Beef}
          color="red"
          trend="up"
          trendValue="+8%"
        />
        <StatCard
          title="Current Weight"
          value="75.5 kg"
          subtitle="Lost 0.5kg this week"
          icon={Scale}
          color="blue"
          trend="down"
          trendValue="-0.7%"
        />
        <StatCard
          title="Workouts"
          value={weeklyStats.workouts}
          subtitle="This week"
          icon={Dumbbell}
          color="purple"
          trend="up"
          trendValue="+1"
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
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={caloriesData.length > 0 ? caloriesData : [
                { date: 'Mon', calories: 2100, target: 2500 },
                { date: 'Tue', calories: 2350, target: 2500 },
                { date: 'Wed', calories: 1980, target: 2500 },
                { date: 'Thu', calories: 2450, target: 2500 },
                { date: 'Fri', calories: 2200, target: 2500 },
                { date: 'Sat', calories: 2600, target: 2500 },
                { date: 'Sun', calories: 1850, target: 2500 },
              ]}>
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
                  domain={[1500, 3000]}
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
            {mockRecentMeals.map((meal) => (
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
            ))}
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
                <Badge className="bg-green-500/20 text-green-400 border-0">3/4</Badge>
              </div>
              <ProgressBar
                value={3}
                max={4}
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
                <Badge className="bg-blue-500/20 text-blue-400 border-0">1/2</Badge>
              </div>
              <ProgressBar
                value={1}
                max={2}
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
                    Calorie Goal Days
                  </span>
                </div>
                <Badge className="bg-purple-500/20 text-purple-400 border-0">5/7</Badge>
              </div>
              <ProgressBar
                value={5}
                max={7}
                color="purple"
                showValue={false}
                size="lg"
              />
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
