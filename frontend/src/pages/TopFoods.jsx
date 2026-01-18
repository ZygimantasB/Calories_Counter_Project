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
import { foodApi } from '../api';

export default function TopFoods() {
  const [activeTab, setActiveTab] = useState('calories');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const fetchTopFoods = useCallback(async () => {
    try {
      setLoading(true);
      const response = await foodApi.getTopFoods({ days: 30 });
      setData(response);
    } catch (err) {
      console.error('Error fetching top foods:', err);
      setError('Failed to load top foods');
    } finally {
      setLoading(false);
    }
  }, []);

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

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Top Foods</h1>
        <p className="text-gray-400 mt-1">
          Your most consumed foods and nutrition sources
        </p>
      </div>

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
          {/* Summary Stats */}
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

          {/* Top Foods List */}
          <Card title="Rankings" subtitle="Based on your food log" padding={false}>
            {getActiveData().length > 0 ? (
              <div className="divide-y divide-gray-700">
                {getActiveData().map((food, index) => {
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
