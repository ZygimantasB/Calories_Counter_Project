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
  GitCompare,
  Search,
  X,
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
import { analyticsApi, foodApi } from '../api';

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

// Generate list of months from Jan 2024 to current month
function generateMonths() {
  const months = [];
  const now = new Date();
  let year = 2024;
  let month = 1;
  while (year < now.getFullYear() || (year === now.getFullYear() && month <= now.getMonth() + 1)) {
    const value = `${year}-${String(month).padStart(2, '0')}`;
    const label = new Date(year, month - 1, 1).toLocaleString('default', { month: 'long', year: 'numeric' });
    months.push({ value, label });
    month++;
    if (month > 12) { month = 1; year++; }
  }
  return months.reverse();
}

const ALL_MONTHS = generateMonths();

function getDelta(a, b) {
  if (a == null || b == null) return null;
  return b - a;
}

function DeltaBadge({ delta, unit = '', lowerIsBetter = false }) {
  if (delta == null) return null;
  const isPositive = delta > 0;
  const isGood = lowerIsBetter ? !isPositive : isPositive;
  if (delta === 0) return <span className="text-xs text-gray-500 ml-1">0{unit}</span>;
  return (
    <span className={`text-xs ml-1 flex items-center gap-0.5 ${isGood ? 'text-green-400' : 'text-red-400'}`}>
      {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
      {isPositive ? '+' : ''}{typeof delta === 'number' ? (Number.isInteger(delta) ? delta : delta.toFixed(1)) : delta}{unit}
    </span>
  );
}

function MonthCompareTab() {
  const now = new Date();
  const currentMonthVal = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  const prevMonth = now.getMonth() === 0
    ? `${now.getFullYear() - 1}-12`
    : `${now.getFullYear()}-${String(now.getMonth()).padStart(2, '0')}`;

  const [monthA, setMonthA] = useState(prevMonth);
  const [monthB, setMonthB] = useState(currentMonthVal);
  const [compareData, setCompareData] = useState(null);
  const [comparing, setComparing] = useState(false);
  const [compareError, setCompareError] = useState(null);

  const handleCompare = async () => {
    try {
      setComparing(true);
      setCompareError(null);
      const result = await analyticsApi.getMonthCompare(monthA, monthB);
      setCompareData(result);
    } catch (err) {
      console.error('Error fetching month compare:', err);
      setCompareError('Failed to load comparison data');
    } finally {
      setComparing(false);
    }
  };

  const mA = compareData?.month_a;
  const mB = compareData?.month_b;

  const formatMonth = (str) => {
    if (!str) return '';
    const [y, m] = str.split('-');
    return new Date(parseInt(y), parseInt(m) - 1, 1).toLocaleString('default', { month: 'long', year: 'numeric' });
  };

  return (
    <div className="space-y-6">
      {/* Selectors */}
      <Card title="Compare Months" subtitle="Select two months to compare nutrition data">
        <div className="flex flex-col sm:flex-row gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">Month A</label>
            <select
              value={monthA}
              onChange={(e) => setMonthA(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-primary-500"
            >
              {ALL_MONTHS.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm text-gray-400 mb-1">Month B</label>
            <select
              value={monthB}
              onChange={(e) => setMonthB(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-gray-200 focus:outline-none focus:border-primary-500"
            >
              {ALL_MONTHS.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleCompare}
            disabled={comparing || monthA === monthB}
            className="px-6 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            {comparing ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
            {comparing ? 'Comparing...' : 'Compare'}
          </button>
        </div>
        {monthA === monthB && (
          <p className="text-sm text-yellow-400 mt-2">Please select two different months to compare.</p>
        )}
      </Card>

      {compareError && (
        <Card className="text-center py-8">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
          <p className="text-gray-400">{compareError}</p>
        </Card>
      )}

      {compareData && mA && mB && (
        <>
          {/* Overview Cards */}
          <div>
            <h2 className="text-lg font-semibold text-gray-200 mb-4">Overview Comparison</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Days Logged */}
              <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
                <p className="text-sm text-gray-400 mb-2">Days Logged</p>
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mA.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{mA.days_logged}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mB.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{mB.days_logged}</p>
                    <DeltaBadge delta={getDelta(mA.days_logged, mB.days_logged)} />
                  </div>
                </div>
              </Card>

              {/* Avg Calories */}
              <Card className="bg-gradient-to-br from-orange-500/10 to-orange-600/5 border-orange-500/20">
                <p className="text-sm text-gray-400 mb-2">Avg Daily Calories</p>
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mA.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{mA.avg_calories}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mB.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{mB.avg_calories}</p>
                    <DeltaBadge delta={getDelta(mA.avg_calories, mB.avg_calories)} unit=" kcal" />
                  </div>
                </div>
              </Card>

              {/* Total Calories */}
              <Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20">
                <p className="text-sm text-gray-400 mb-2">Total Calories</p>
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mA.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{Math.round(mA.total_calories).toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mB.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{Math.round(mB.total_calories).toLocaleString()}</p>
                    <DeltaBadge delta={getDelta(mA.total_calories, mB.total_calories)} unit=" kcal" />
                  </div>
                </div>
              </Card>

              {/* Avg Protein */}
              <Card className="bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/20">
                <p className="text-sm text-gray-400 mb-2">Avg Daily Protein</p>
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mA.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{mA.avg_protein}g</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mB.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{mB.avg_protein}g</p>
                    <DeltaBadge delta={getDelta(mA.avg_protein, mB.avg_protein)} unit="g" />
                  </div>
                </div>
              </Card>

              {/* Avg Fat */}
              <Card className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 border-yellow-500/20">
                <p className="text-sm text-gray-400 mb-2">Avg Daily Fat</p>
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mA.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{mA.avg_fat}g</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mB.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{mB.avg_fat}g</p>
                    <DeltaBadge delta={getDelta(mA.avg_fat, mB.avg_fat)} unit="g" lowerIsBetter />
                  </div>
                </div>
              </Card>

              {/* Avg Carbs */}
              <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
                <p className="text-sm text-gray-400 mb-2">Avg Daily Carbs</p>
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mA.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{mA.avg_carbs}g</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500 mb-0.5">{formatMonth(mB.month)}</p>
                    <p className="text-2xl font-bold text-gray-100">{mB.avg_carbs}g</p>
                    <DeltaBadge delta={getDelta(mA.avg_carbs, mB.avg_carbs)} unit="g" />
                  </div>
                </div>
              </Card>
            </div>
          </div>

          {/* Weight Comparison */}
          {(mA.weight || mB.weight) && (
            <Card title="Weight Comparison" subtitle="Body weight data for each month">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[{ data: mA, label: formatMonth(mA.month) }, { data: mB, label: formatMonth(mB.month) }].map(({ data: md, label }) => (
                  <div key={label} className="bg-gray-800/50 rounded-lg p-4">
                    <p className="font-semibold text-gray-200 mb-3">{label}</p>
                    {md.weight ? (
                      <div className="grid grid-cols-3 gap-3 text-center">
                        <div>
                          <p className="text-lg font-bold text-primary-400">{md.weight.avg} kg</p>
                          <p className="text-xs text-gray-500">Avg</p>
                        </div>
                        <div>
                          <p className="text-lg font-bold text-gray-200">{md.weight.start} kg</p>
                          <p className="text-xs text-gray-500">Start</p>
                        </div>
                        <div>
                          <p className="text-lg font-bold text-gray-200">{md.weight.end} kg</p>
                          <p className="text-xs text-gray-500">End</p>
                        </div>
                        <div>
                          <p className={`text-lg font-bold ${md.weight.change < 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {md.weight.change > 0 ? '+' : ''}{md.weight.change} kg
                          </p>
                          <p className="text-xs text-gray-500">Change</p>
                        </div>
                        <div>
                          <p className="text-lg font-bold text-blue-400">{md.weight.min} kg</p>
                          <p className="text-xs text-gray-500">Min</p>
                        </div>
                        <div>
                          <p className="text-lg font-bold text-orange-400">{md.weight.max} kg</p>
                          <p className="text-xs text-gray-500">Max</p>
                        </div>
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">No weight data recorded</p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Top Foods Comparison */}
          {(mA.top_foods?.length > 0 || mB.top_foods?.length > 0) && (
            <Card title="Top Foods Comparison" subtitle="Most frequently eaten foods">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[{ data: mA, label: formatMonth(mA.month) }, { data: mB, label: formatMonth(mB.month) }].map(({ data: md, label }) => (
                  <div key={label}>
                    <p className="font-semibold text-gray-300 mb-3">{label}</p>
                    {md.top_foods?.length > 0 ? (
                      <div className="space-y-2">
                        {md.top_foods.map((food, idx) => (
                          <div key={idx} className="flex items-center justify-between py-1.5 border-b border-gray-800">
                            <div className="flex items-center gap-2 min-w-0">
                              <span className="text-xs text-gray-600 w-5 shrink-0">{idx + 1}.</span>
                              <span className="text-sm text-gray-200 truncate">{food.product_name}</span>
                            </div>
                            <div className="flex items-center gap-3 shrink-0 ml-2">
                              <span className="text-xs text-gray-400">{food.count}x</span>
                              <span className="text-xs text-orange-400">{Math.round(food.total_cal)} kcal</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">No food data</p>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}

      {!compareData && !comparing && !compareError && (
        <Card className="text-center py-12">
          <GitCompare className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">Select two months and click Compare to see the breakdown.</p>
        </Card>
      )}
    </div>
  );
}

function YearlyTrendsTab() {
  const currentYear = new Date().getFullYear();
  const [selectedYear, setSelectedYear] = useState('last12');
  const [trendsData, setTrendsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTrends = useCallback(async (year) => {
    try {
      setLoading(true);
      setError(null);
      const result = await analyticsApi.getYearlyTrends(year);
      setTrendsData(result);
    } catch (err) {
      console.error('Error fetching yearly trends:', err);
      setError('Failed to load yearly trends data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTrends(selectedYear);
  }, [fetchTrends, selectedYear]);

  const months = trendsData?.months || [];
  const activeMonths = months.filter((m) => m.days_logged > 0);

  const totalDaysLogged = months.reduce((sum, m) => sum + m.days_logged, 0);
  const totalCalories = months.reduce((sum, m) => sum + m.total_calories, 0);
  const totalProtein = months.reduce((sum, m) => sum + (m.avg_protein * m.days_logged), 0);
  const mostConsistentMonth = months.reduce(
    (best, m) => (m.consistency > (best?.consistency || 0) ? m : best),
    null
  );

  const yearButtons = [
    { value: 'last12', label: 'Last 12 Months' },
    { value: String(currentYear), label: String(currentYear) },
    { value: String(currentYear - 1), label: String(currentYear - 1) },
  ];

  return (
    <div className="space-y-6">
      {/* Year Selector */}
      <div className="flex items-center gap-2 flex-wrap">
        {yearButtons.map((btn) => (
          <button
            key={btn.value}
            onClick={() => setSelectedYear(btn.value)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              selectedYear === btn.value
                ? 'bg-primary-600 text-white shadow-sm'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-gray-100'
            }`}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      )}

      {error && !loading && (
        <Card className="text-center py-8">
          <AlertCircle className="w-10 h-10 text-red-500 mx-auto mb-3" />
          <p className="text-gray-400">{error}</p>
          <button
            onClick={() => fetchTrends(selectedYear)}
            className="mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-lg text-sm"
          >
            Try Again
          </button>
        </Card>
      )}

      {!loading && !error && trendsData && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Days Logged</p>
                  <p className="text-3xl font-bold text-gray-100">{totalDaysLogged}</p>
                  <p className="text-xs text-gray-500">{activeMonths.length} active months</p>
                </div>
                <Calendar className="w-10 h-10 text-green-500 opacity-50" />
              </div>
            </Card>

            <Card className="bg-gradient-to-br from-orange-500/10 to-orange-600/5 border-orange-500/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Calories</p>
                  <p className="text-3xl font-bold text-gray-100">{Math.round(totalCalories / 1000).toLocaleString()}k</p>
                  <p className="text-xs text-gray-500">{Math.round(totalCalories).toLocaleString()} kcal</p>
                </div>
                <Flame className="w-10 h-10 text-orange-500 opacity-50" />
              </div>
            </Card>

            <Card className="bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Total Protein</p>
                  <p className="text-3xl font-bold text-gray-100">{Math.round(totalProtein / 1000).toLocaleString()}k<span className="text-lg">g</span></p>
                  <p className="text-xs text-gray-500">{Math.round(totalProtein).toLocaleString()}g total</p>
                </div>
                <Beef className="w-10 h-10 text-red-500 opacity-50" />
              </div>
            </Card>

            <Card className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 border-yellow-500/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-400">Most Consistent</p>
                  {mostConsistentMonth ? (
                    <>
                      <p className="text-xl font-bold text-gray-100">
                        {mostConsistentMonth.month_name} {mostConsistentMonth.year}
                      </p>
                      <p className="text-xs text-gray-500">{mostConsistentMonth.consistency}% logged</p>
                    </>
                  ) : (
                    <p className="text-gray-500 text-sm">No data</p>
                  )}
                </div>
                <Trophy className="w-10 h-10 text-yellow-500 opacity-50" />
              </div>
            </Card>
          </div>

          {/* Monthly Breakdown Table */}
          <Card title="Monthly Breakdown" subtitle="Detailed nutrition and weight data per month">
            {months.length === 0 ? (
              <p className="text-gray-500 text-sm text-center py-8">No data available for this period.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 border-b border-gray-700">
                      <th className="pb-3 pr-4 font-medium whitespace-nowrap">Month</th>
                      <th className="pb-3 pr-4 font-medium whitespace-nowrap text-right">Days</th>
                      <th className="pb-3 pr-4 font-medium whitespace-nowrap text-right">Consistency</th>
                      <th className="pb-3 pr-4 font-medium whitespace-nowrap text-right">Avg Cal</th>
                      <th className="pb-3 pr-4 font-medium whitespace-nowrap text-right">Avg Protein</th>
                      <th className="pb-3 pr-4 font-medium whitespace-nowrap text-right">Avg Fat</th>
                      <th className="pb-3 pr-4 font-medium whitespace-nowrap text-right">Avg Carbs</th>
                      <th className="pb-3 pr-4 font-medium whitespace-nowrap text-right">Avg Weight</th>
                      <th className="pb-3 pr-4 font-medium whitespace-nowrap text-right">Weight Delta</th>
                      <th className="pb-3 font-medium whitespace-nowrap">Top Food</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {months.map((m) => (
                      <tr key={m.month} className={`hover:bg-gray-800/50 transition-colors ${m.days_logged === 0 ? 'opacity-40' : ''}`}>
                        <td className="py-3 pr-4 font-medium text-gray-200 whitespace-nowrap">
                          {m.month_name} {m.year}
                        </td>
                        <td className="py-3 pr-4 text-right text-gray-300 whitespace-nowrap">
                          {m.days_logged}<span className="text-gray-600">/{m.days_in_month}</span>
                        </td>
                        <td className="py-3 pr-4 text-right whitespace-nowrap">
                          <span className={`font-medium ${m.consistency >= 80 ? 'text-green-400' : m.consistency >= 50 ? 'text-yellow-400' : 'text-gray-400'}`}>
                            {m.consistency}%
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-right text-orange-400 whitespace-nowrap">
                          {m.days_logged ? m.avg_calories.toLocaleString() : '—'}
                        </td>
                        <td className="py-3 pr-4 text-right text-red-400 whitespace-nowrap">
                          {m.days_logged ? `${m.avg_protein}g` : '—'}
                        </td>
                        <td className="py-3 pr-4 text-right text-yellow-400 whitespace-nowrap">
                          {m.days_logged ? `${m.avg_fat}g` : '—'}
                        </td>
                        <td className="py-3 pr-4 text-right text-blue-400 whitespace-nowrap">
                          {m.days_logged ? `${m.avg_carbs}g` : '—'}
                        </td>
                        <td className="py-3 pr-4 text-right text-gray-300 whitespace-nowrap">
                          {m.avg_weight != null ? `${m.avg_weight} kg` : '—'}
                        </td>
                        <td className="py-3 pr-4 text-right whitespace-nowrap">
                          {m.weight_delta != null ? (
                            <span className={m.weight_delta < 0 ? 'text-green-400' : m.weight_delta > 0 ? 'text-red-400' : 'text-gray-500'}>
                              {m.weight_delta > 0 ? '+' : ''}{m.weight_delta} kg
                            </span>
                          ) : '—'}
                        </td>
                        <td className="py-3 text-gray-400 max-w-[160px] truncate">
                          {m.top_food || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}

const PRODUCT_SLOTS = ['Product A', 'Product B', 'Product C (optional)'];

function ProductCompareTab() {
  const [compareProducts, setCompareProducts] = useState([null, null, null]);
  const [compareSearches, setCompareSearches] = useState(['', '', '']);
  const [compareResults, setCompareResults] = useState([[], [], []]);
  const [compareData, setCompareData] = useState(null);
  const [searching, setSearching] = useState([false, false, false]);
  const [openDropdown, setOpenDropdown] = useState(null);

  const handleCompareSearch = async (index, query) => {
    const updatedSearches = [...compareSearches];
    updatedSearches[index] = query;
    setCompareSearches(updatedSearches);

    if (query.length < 2) {
      const updatedResults = [...compareResults];
      updatedResults[index] = [];
      setCompareResults(updatedResults);
      return;
    }

    const updatedSearching = [...searching];
    updatedSearching[index] = true;
    setSearching(updatedSearching);

    try {
      const data = await foodApi.searchAllFoods(query, 5);
      const results = [...compareResults];
      results[index] = data?.results || data || [];
      setCompareResults(results);
      setOpenDropdown(index);
    } catch (err) {
      console.error('Error searching foods:', err);
    } finally {
      const doneSearching = [...searching];
      doneSearching[index] = false;
      setSearching(doneSearching);
    }
  };

  const selectCompareProduct = (index, product) => {
    const updated = [...compareProducts];
    updated[index] = product;
    setCompareProducts(updated);

    const updatedSearches = [...compareSearches];
    updatedSearches[index] = product.name;
    setCompareSearches(updatedSearches);

    const updatedResults = [...compareResults];
    updatedResults[index] = [];
    setCompareResults(updatedResults);

    setOpenDropdown(null);
    setCompareData(null);
  };

  const clearProduct = (index) => {
    const updated = [...compareProducts];
    updated[index] = null;
    setCompareProducts(updated);

    const updatedSearches = [...compareSearches];
    updatedSearches[index] = '';
    setCompareSearches(updatedSearches);

    setCompareData(null);
  };

  const canCompare = compareProducts[0] !== null && compareProducts[1] !== null;
  const activeProducts = compareProducts.filter(Boolean);

  const handleCompare = () => {
    if (!canCompare) return;
    setCompareData(activeProducts);
  };

  // Build chart data from selected products
  const chartData = compareData
    ? [
        { macro: 'Calories', ...Object.fromEntries(compareData.map((p) => [p.name, p.calories])) },
        { macro: 'Protein (g)', ...Object.fromEntries(compareData.map((p) => [p.name, p.protein])) },
        { macro: 'Carbs (g)', ...Object.fromEntries(compareData.map((p) => [p.name, p.carbs])) },
        { macro: 'Fat (g)', ...Object.fromEntries(compareData.map((p) => [p.name, p.fat])) },
      ]
    : [];

  const barColors = [COLORS.primary, COLORS.protein, COLORS.success];

  return (
    <div className="space-y-6">
      <Card title="Product Compare" subtitle="Search 2–3 foods and compare their nutritional values side by side">
        <div className="space-y-4">
          {PRODUCT_SLOTS.map((label, index) => (
            <div key={index} className="relative">
              <label className="block text-sm text-gray-400 mb-1">{label}</label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <div className="absolute inset-y-0 left-3 flex items-center pointer-events-none">
                    {searching[index]
                      ? <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                      : <Search className="w-4 h-4 text-gray-400" />
                    }
                  </div>
                  <input
                    type="text"
                    value={compareSearches[index]}
                    onChange={(e) => handleCompareSearch(index, e.target.value)}
                    onFocus={() => compareResults[index].length > 0 && setOpenDropdown(index)}
                    placeholder={`Search for ${label.toLowerCase()}...`}
                    className="w-full bg-gray-700 border border-gray-600 rounded-lg pl-10 pr-3 py-2 text-gray-200 placeholder-gray-500 focus:outline-none focus:border-primary-500"
                  />
                  {openDropdown === index && compareResults[index].length > 0 && (
                    <div className="absolute z-10 top-full mt-1 left-0 right-0 bg-gray-800 border border-gray-600 rounded-lg shadow-xl max-h-48 overflow-y-auto">
                      {compareResults[index].map((food, i) => (
                        <button
                          key={i}
                          onClick={() => selectCompareProduct(index, food)}
                          className="w-full text-left px-4 py-2.5 hover:bg-gray-700 transition-colors border-b border-gray-700 last:border-0"
                        >
                          <span className="text-sm text-gray-200">{food.name}</span>
                          <span className="text-xs text-gray-500 ml-2">{food.calories} kcal · P:{food.protein}g · C:{food.carbs}g · F:{food.fat}g</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {compareProducts[index] && (
                  <button
                    onClick={() => clearProduct(index)}
                    className="px-2 py-2 text-gray-400 hover:text-gray-200 bg-gray-700 rounded-lg transition-colors"
                    title="Clear"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
              {compareProducts[index] && (
                <p className="text-xs text-green-400 mt-1">
                  Selected: {compareProducts[index].name}
                </p>
              )}
            </div>
          ))}

          <button
            onClick={handleCompare}
            disabled={!canCompare}
            className="px-6 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <GitCompare className="w-4 h-4" />
            Compare
          </button>

          {!canCompare && (
            <p className="text-xs text-yellow-400">Select at least 2 products to compare.</p>
          )}
        </div>
      </Card>

      {compareData && (
        <>
          {/* Side-by-side nutrition cards */}
          <div>
            <h2 className="text-lg font-semibold text-gray-200 mb-4">Nutrition Comparison</h2>
            <div className={`grid grid-cols-1 sm:grid-cols-${compareData.length} gap-4`}>
              {compareData.map((product, idx) => (
                <Card key={idx} className="bg-gradient-to-br from-primary-500/10 to-primary-600/5 border-primary-500/20">
                  <p className="font-semibold text-gray-100 mb-4 truncate" title={product.name}>{product.name}</p>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400 flex items-center gap-1.5">
                        <Flame className="w-3.5 h-3.5 text-orange-400" /> Calories
                      </span>
                      <span className="font-bold text-orange-400">{product.calories} kcal</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400 flex items-center gap-1.5">
                        <Beef className="w-3.5 h-3.5 text-red-400" /> Protein
                      </span>
                      <span className="font-bold text-red-400">{product.protein}g</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400 flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5 text-blue-400" /> Carbs
                      </span>
                      <span className="font-bold text-blue-400">{product.carbs}g</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400 flex items-center gap-1.5">
                        <Scale className="w-3.5 h-3.5 text-yellow-400" /> Fat
                      </span>
                      <span className="font-bold text-yellow-400">{product.fat}g</span>
                    </div>
                    <div className="flex justify-between items-center border-t border-gray-700 pt-3">
                      <span className="text-sm text-gray-400 flex items-center gap-1.5">
                        <Trophy className="w-3.5 h-3.5 text-purple-400" /> Times eaten
                      </span>
                      <span className="font-bold text-purple-400">{product.count}x</span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Bar chart comparison */}
          <Card title="Macro Breakdown Chart" subtitle="Side-by-side comparison across all macros">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
                <XAxis dataKey="macro" tick={{ fill: COLORS.text, fontSize: 12 }} />
                <YAxis tick={{ fill: COLORS.text, fontSize: 12 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                  labelStyle={{ color: '#f3f4f6' }}
                  itemStyle={{ color: '#9ca3af' }}
                />
                <Legend />
                {compareData.map((product, idx) => (
                  <Bar key={idx} dataKey={product.name} fill={barColors[idx % barColors.length]} radius={[4, 4, 0, 0]} maxBarSize={60} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </>
      )}

      {!compareData && (
        <Card className="text-center py-12">
          <Search className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400">Search for foods above and click Compare to see a side-by-side breakdown.</p>
        </Card>
      )}
    </div>
  );
}

export default function Analytics() {
  const [activeTab, setActiveTab] = useState('overview');
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
        {activeTab === 'overview' && (
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
        )}
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-1 p-1 bg-gray-800 rounded-xl border border-gray-700 w-fit">
        {[
          { value: 'overview', label: 'Overview', icon: BarChart3 },
          { value: 'month_compare', label: 'Month Compare', icon: GitCompare },
          { value: 'yearly_trends', label: 'Yearly Trends', icon: TrendingUp },
          { value: 'product_compare', label: 'Product Compare', icon: Search },
        ].map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            onClick={() => setActiveTab(value)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === value
                ? 'bg-primary-600 text-white shadow-sm'
                : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Month Compare Tab */}
      {activeTab === 'month_compare' && <MonthCompareTab />}

      {/* Yearly Trends Tab */}
      {activeTab === 'yearly_trends' && <YearlyTrendsTab />}

      {/* Product Compare Tab */}
      {activeTab === 'product_compare' && <ProductCompareTab />}

      {/* Overview Tab */}
      {activeTab === 'overview' && <>

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

      </> /* end overview tab */}
    </div>
  );
}
