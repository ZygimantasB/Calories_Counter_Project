import { useState, useEffect, useCallback } from 'react';
import {
  Trophy,
  Flame,
  Beef,
  Wheat,
  Droplets,
  TrendingUp,
  Star,
  Award,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Card, Badge, Button } from '../components/ui';
import CSVDownloadButton from '../components/CSVDownloadButton';
import DateRangeFilter from '../components/DateRangeFilter';
import { foodApi } from '../api';

function filterToDays(filter) {
  if (!filter) return 30;
  if (filter.type === 'days') return filter.days;
  if (filter.type === 'today') return 1;
  if (filter.type === 'range_name') {
    if (filter.name === 'week') return 7;
    if (filter.name === 'month') return 30;
  }
  return 30;
}

export default function TopFoods() {
  const [activeTab, setActiveTab] = useState('calories');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [dateFilter, setDateFilter] = useState({ type: 'days', days: 30 });
  const [sortBy, setSortBy] = useState('calories');
  const [sortDir, setSortDir] = useState('desc');

  const days = filterToDays(dateFilter);

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortDir((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(field);
      setSortDir('desc');
    }
  };

  const fetchTopFoods = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await foodApi.getTopFoods({ days, sort: sortBy });
      setData(response);
    } catch (err) {
      console.error('Error fetching top foods:', err);
      setError('Failed to load top foods');
    } finally {
      setLoading(false);
    }
  }, [days, sortBy]);

  useEffect(() => {
    fetchTopFoods();
  }, [fetchTopFoods]);

  const tabs = [
    { id: 'calories', label: 'By Calories', icon: Flame, color: 'orange' },
    { id: 'protein', label: 'By Protein', icon: Beef, color: 'red' },
    { id: 'frequency', label: 'Most Frequent', icon: TrendingUp, color: 'blue' },
  ];

  const getActiveData = () => {
    if (!data) return [];
    switch (activeTab) {
      case 'protein':
        return data.by_protein || [];
      case 'frequency':
        return data.by_frequency || [];
      default:
        return data.by_calories || [];
    }
  };

  // Unified list combining all foods from all lists (by_calories is most complete)
  const allFoods = data?.by_calories || [];

  // Client-side sort the active list by sortBy / sortDir
  const sortedActiveData = [...getActiveData()].sort((a, b) => {
    let aVal, bVal;
    switch (sortBy) {
      case 'name':
        aVal = (a.name || '').toLowerCase();
        bVal = (b.name || '').toLowerCase();
        return sortDir === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      case 'count':
        aVal = a.count || 0;
        bVal = b.count || 0;
        break;
      case 'protein':
        aVal = a.total_protein || 0;
        bVal = b.total_protein || 0;
        break;
      case 'fat':
        aVal = a.total_fat || 0;
        bVal = b.total_fat || 0;
        break;
      case 'carbs':
        aVal = a.total_carbs || 0;
        bVal = b.total_carbs || 0;
        break;
      case 'calories':
      default:
        aVal = a.total_calories || 0;
        bVal = b.total_calories || 0;
        break;
    }
    return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const getRankBadge = (index) => {
    if (index === 0) return { variant: 'warning', icon: Trophy };
    if (index === 1) return { variant: 'default', icon: Award };
    if (index === 2) return { variant: 'info', icon: Star };
    return null;
  };

  const topCalories = data?.by_calories?.[0];
  const topProtein = data?.by_protein?.[0];
  const topFrequent = data?.by_frequency?.[0];

  const chartData = (data?.by_calories || []).slice(0, 5).map((food) => ({
    name: food.name.length > 12 ? food.name.substring(0, 12) + '...' : food.name,
    calories: food.total_calories || 0,
  }));

  // Summary statistics computed from all by_calories entries
  const uniqueFoodsCount = allFoods.length;
  const totalTimesEaten = allFoods.reduce((sum, f) => sum + (f.count || 0), 0);
  const totalCalories = allFoods.reduce((sum, f) => sum + (f.total_calories || 0), 0);
  const totalProtein = allFoods.reduce((sum, f) => sum + (f.total_protein || 0), 0);
  const totalFat = allFoods.reduce((sum, f) => sum + (f.total_fat || 0), 0);
  const totalCarbs = allFoods.reduce((sum, f) => sum + (f.total_carbs || 0), 0);

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Top Foods</h1>
          <p className="text-gray-400 mt-1">
            Your most consumed foods and nutrition sources
          </p>
        </div>
        <CSVDownloadButton
          endpoint="/top_foods/"
          params={{ days: String(days) }}
        />
      </div>

      {/* Date Range Filter */}
      <Card>
        <DateRangeFilter
          value={dateFilter}
          onChange={setDateFilter}
          showDatePicker={false}
        />
      </Card>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : error ? (
        <Card className="text-center py-8">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-400">{error}</p>
          <Button variant="ghost" onClick={fetchTopFoods} className="mt-4">
            Try Again
          </Button>
        </Card>
      ) : (
        <>
          {/* Summary Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-gray-700/50 rounded-xl p-3 text-center">
              <div className="text-xl font-bold text-gray-100">{uniqueFoodsCount}</div>
              <div className="text-xs text-gray-400">Unique Foods</div>
            </div>
            <div className="bg-gray-700/50 rounded-xl p-3 text-center">
              <div className="text-xl font-bold text-gray-100">{totalTimesEaten}</div>
              <div className="text-xs text-gray-400">Times Eaten</div>
            </div>
            <div className="bg-gray-700/50 rounded-xl p-3 text-center">
              <div className="text-xl font-bold text-orange-400">{totalCalories.toLocaleString()}</div>
              <div className="text-xs text-gray-400">Total Calories</div>
            </div>
            <div className="bg-gray-700/50 rounded-xl p-3 text-center">
              <div className="text-xl font-bold text-red-400">{Math.round(totalProtein).toLocaleString()}g</div>
              <div className="text-xs text-gray-400">Total Protein</div>
            </div>
            <div className="bg-gray-700/50 rounded-xl p-3 text-center">
              <div className="text-xl font-bold text-yellow-400">{Math.round(totalFat).toLocaleString()}g</div>
              <div className="text-xs text-gray-400">Total Fat</div>
            </div>
            <div className="bg-gray-700/50 rounded-xl p-3 text-center">
              <div className="text-xl font-bold text-blue-400">{Math.round(totalCarbs).toLocaleString()}g</div>
              <div className="text-xs text-gray-400">Total Carbs</div>
            </div>
          </div>

          {/* Top-3 Highlight Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-gradient-to-br from-orange-500 to-orange-600 border-0 text-white">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
                  <Flame className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-white/80">Top Calorie Source</p>
                  <p className="text-xl font-bold">{topCalories?.name || 'N/A'}</p>
                  <p className="text-sm text-white/70">
                    {topCalories?.total_calories?.toLocaleString() || 0} kcal total
                  </p>
                </div>
              </div>
            </Card>
            <Card className="bg-gradient-to-br from-red-500 to-red-600 border-0 text-white">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
                  <Beef className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-white/80">Top Protein Source</p>
                  <p className="text-xl font-bold">{topProtein?.name || 'N/A'}</p>
                  <p className="text-sm text-white/70">
                    {topProtein?.total_protein?.toLocaleString() || 0}g protein total
                  </p>
                </div>
              </div>
            </Card>
            <Card className="bg-gradient-to-br from-blue-500 to-blue-600 border-0 text-white">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-white/80">Most Frequent</p>
                  <p className="text-xl font-bold">{topFrequent?.name || 'N/A'}</p>
                  <p className="text-sm text-white/70">
                    {topFrequent?.count || 0} times logged
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Chart */}
          <Card title="Calorie Distribution" subtitle="Total calories from top foods">
            {chartData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis
                      type="number"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#9ca3af', fontSize: 12 }}
                      tickFormatter={(value) => `${(value / 1000).toFixed(1)}k`}
                    />
                    <YAxis
                      type="category"
                      dataKey="name"
                      axisLine={false}
                      tickLine={false}
                      tick={{ fill: '#9ca3af', fontSize: 12 }}
                      width={100}
                    />
                    <Tooltip
                      formatter={(value) => [`${value.toLocaleString()} kcal`, 'Calories']}
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                      }}
                    />
                    <Bar dataKey="calories" fill="#f97316" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-gray-500">
                No food data to display
              </div>
            )}
          </Card>

          {/* Tab Navigation */}
          <div className="flex gap-2 p-1 bg-gray-700 rounded-lg w-fit">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all ${
                  activeTab === tab.id
                    ? 'bg-gray-600 text-gray-100 shadow-sm'
                    : 'text-gray-400 hover:text-gray-200'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Sort Controls */}
          <div className="flex flex-wrap gap-2 mb-4">
            {['count', 'name', 'calories', 'protein', 'fat', 'carbs'].map((field) => (
              <button
                key={field}
                onClick={() => handleSort(field)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  sortBy === field
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
              >
                {field.charAt(0).toUpperCase() + field.slice(1)}
                {sortBy === field && (sortDir === 'asc' ? ' \u2191' : ' \u2193')}
              </button>
            ))}
          </div>

          {/* Top Foods List */}
          <Card title="Rankings" subtitle="Based on your food log" padding={false}>
            {sortedActiveData.length > 0 ? (
              <div className="divide-y divide-gray-700">
                {sortedActiveData.map((food, index) => {
                  const rankBadge = getRankBadge(index);

                  return (
                    <div
                      key={food.name}
                      className="p-4 flex items-center justify-between hover:bg-gray-700/30 transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <div
                          className={`w-10 h-10 rounded-lg flex items-center justify-center font-bold ${
                            index === 0
                              ? 'bg-yellow-500/20 text-yellow-400'
                              : index === 1
                              ? 'bg-gray-500/20 text-gray-400'
                              : index === 2
                              ? 'bg-orange-500/20 text-orange-400'
                              : 'bg-gray-700 text-gray-500'
                          }`}
                        >
                          {index + 1}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-gray-100">{food.name}</h3>
                            {rankBadge && (
                              <rankBadge.icon className="w-4 h-4 text-yellow-400" />
                            )}
                          </div>
                          <p className="text-sm text-gray-500">
                            Logged {food.count} times
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        {activeTab === 'calories' && (
                          <>
                            <p className="font-semibold text-gray-100">
                              {food.total_calories?.toLocaleString() || 0} kcal
                            </p>
                            <p className="text-sm text-gray-500">
                              {food.avg_calories || 0} kcal/serving
                            </p>
                          </>
                        )}
                        {activeTab === 'protein' && (
                          <>
                            <p className="font-semibold text-gray-100">
                              {food.total_protein || 0}g protein
                            </p>
                            <p className="text-sm text-gray-500">
                              {food.avg_protein || 0}g/serving
                            </p>
                          </>
                        )}
                        {activeTab === 'frequency' && (
                          <>
                            <p className="font-semibold text-gray-100">
                              {food.count} times
                            </p>
                            <p className="text-sm text-gray-500">
                              {food.total_calories?.toLocaleString() || 0} kcal total
                            </p>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500">
                <p>No food data available</p>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
