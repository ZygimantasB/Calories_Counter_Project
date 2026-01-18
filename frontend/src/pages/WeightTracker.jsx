import { useState, useEffect, useCallback } from 'react';
import {
  Scale,
  Plus,
  TrendingDown,
  TrendingUp,
  Target,
  Calendar,
  Edit2,
  Trash2,
  X,
  Loader2,
  AlertCircle,
  Check,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { format, subDays, parseISO } from 'date-fns';
import { Card, Button, Badge, ProgressBar } from '../components/ui';
import { weightApi } from '../api';

export default function WeightTracker() {
  const [weightData, setWeightData] = useState([]);
  const [weightEntries, setWeightEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  // Modal states
  const [showAddModal, setShowAddModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [timeRange, setTimeRange] = useState('month');

  // Form states
  const [newWeight, setNewWeight] = useState({
    weight: '',
    date: format(new Date(), 'yyyy-MM-dd'),
    note: '',
  });
  const [addLoading, setAddLoading] = useState(false);

  // Fetch weight data
  const fetchWeightData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const daysMap = { week: 7, month: 30, '3months': 90, '6months': 180, year: 365, all: 'all' };
      const days = daysMap[timeRange] || 30;
      const response = await weightApi.getWeightItems({ days });

      setWeightEntries(response.items || []);
      setStats(response.stats || null);

      // Transform for chart (backend returns recorded_at, not date)
      const chartData = (response.items || [])
        .map(entry => ({
          date: format(parseISO(entry.recorded_at), 'MMM dd'),
          fullDate: entry.recorded_at,
          weight: entry.weight,
        }))
        .reverse();
      setWeightData(chartData);
    } catch (err) {
      console.error('Error fetching weight data:', err);
      setError('Failed to load weight data');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchWeightData();
  }, [fetchWeightData]);

  // Add weight entry
  const handleAddWeight = async (e) => {
    e.preventDefault();
    try {
      setAddLoading(true);
      await weightApi.addWeight({
        weight: parseFloat(newWeight.weight),
        date: newWeight.date,
        note: newWeight.note,
      });
      setShowAddModal(false);
      setNewWeight({
        weight: '',
        date: format(new Date(), 'yyyy-MM-dd'),
        note: '',
      });
      fetchWeightData();
    } catch (err) {
      console.error('Error adding weight:', err);
    } finally {
      setAddLoading(false);
    }
  };

  // Delete weight entry
  const handleDeleteWeight = async (weightId) => {
    try {
      await weightApi.deleteWeight(weightId);
      setShowDeleteConfirm(null);
      fetchWeightData();
    } catch (err) {
      console.error('Error deleting weight:', err);
    }
  };

  const currentWeight = stats?.current_weight || (weightData.length > 0 ? weightData[weightData.length - 1]?.weight : 0);
  const startWeight = stats?.start_weight || (weightData.length > 0 ? weightData[0]?.weight : 0);
  const weightChange = stats?.change || (currentWeight - startWeight);
  const goalWeight = stats?.goal_weight || 72;
  const progressToGoal = startWeight !== goalWeight
    ? ((startWeight - currentWeight) / (startWeight - goalWeight)) * 100
    : 0;

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Weight Tracker</h1>
          <p className="text-gray-400 mt-1">Track your body weight over time</p>
        </div>
        <Button icon={Plus} onClick={() => setShowAddModal(true)}>
          Log Weight
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : error ? (
        <Card className="text-center py-8">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-400">{error}</p>
          <Button variant="ghost" onClick={fetchWeightData} className="mt-4">
            Try Again
          </Button>
        </Card>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                  <Scale className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Current Weight</p>
                  <p className="text-2xl font-bold text-gray-100">
                    {currentWeight ? currentWeight.toFixed(1) : '--'} kg
                  </p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-4">
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br ${
                    weightChange < 0
                      ? 'from-green-500 to-green-600'
                      : 'from-red-500 to-red-600'
                  } flex items-center justify-center`}
                >
                  {weightChange < 0 ? (
                    <TrendingDown className="w-6 h-6 text-white" />
                  ) : (
                    <TrendingUp className="w-6 h-6 text-white" />
                  )}
                </div>
                <div>
                  <p className="text-sm text-gray-400">Change</p>
                  <p
                    className={`text-2xl font-bold ${
                      weightChange < 0 ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    {weightChange > 0 ? '+' : ''}
                    {weightChange ? weightChange.toFixed(1) : '--'} kg
                  </p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                  <Target className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Goal Weight</p>
                  <p className="text-2xl font-bold text-gray-100">{goalWeight} kg</p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center">
                  <Calendar className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">To Goal</p>
                  <p className="text-2xl font-bold text-gray-100">
                    {currentWeight ? (currentWeight - goalWeight).toFixed(1) : '--'} kg
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Progress to Goal */}
          <Card>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-gray-100">Progress to Goal</h3>
                <p className="text-sm text-gray-400">
                  {startWeight ? startWeight.toFixed(1) : '--'} kg → {goalWeight} kg
                </p>
              </div>
              <Badge variant={progressToGoal >= 100 ? 'success' : 'info'}>
                {Math.max(0, Math.min(progressToGoal, 100)).toFixed(0)}% complete
              </Badge>
            </div>
            <ProgressBar
              value={Math.max(0, Math.min(progressToGoal, 100))}
              max={100}
              color={progressToGoal >= 100 ? 'green' : 'blue'}
              size="lg"
              showValue={false}
            />
            <div className="flex justify-between mt-2 text-sm text-gray-500">
              <span>Start: {startWeight ? startWeight.toFixed(1) : '--'} kg</span>
              <span>Goal: {goalWeight} kg</span>
            </div>
          </Card>

          {/* Weight Chart */}
          <Card
            title="Weight Trend"
            action={
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
            }
          >
            {weightData.length > 0 ? (
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={weightData}>
                    <defs>
                      <linearGradient id="weightGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                      </linearGradient>
                    </defs>
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
                      domain={['dataMin - 1', 'dataMax + 1']}
                      tickFormatter={(value) => `${value.toFixed(1)}`}
                    />
                    <Tooltip
                      formatter={(value) => [`${value.toFixed(2)} kg`, 'Weight']}
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                      }}
                    />
                    <ReferenceLine
                      y={goalWeight}
                      stroke="#22c55e"
                      strokeDasharray="5 5"
                      label={{
                        value: 'Goal',
                        position: 'right',
                        fill: '#22c55e',
                        fontSize: 12,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="weight"
                      stroke="#0ea5e9"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#weightGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-80 flex items-center justify-center text-gray-500">
                No weight data to display
              </div>
            )}
          </Card>

          {/* Recent Entries */}
          <Card title="Recent Entries" subtitle="Your weight log history" padding={false}>
            {weightEntries.length > 0 ? (
              <div className="divide-y divide-gray-700">
                {weightEntries.map((entry) => (
                  <div
                    key={entry.id}
                    className="p-4 flex items-center justify-between hover:bg-gray-700/30 transition-colors group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                        <Scale className="w-5 h-5 text-blue-400" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-100">{entry.weight} kg</p>
                        <p className="text-sm text-gray-500">
                          {format(parseISO(entry.recorded_at), 'EEEE, MMMM d')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {entry.notes && (
                        <span className="text-sm text-gray-400">{entry.notes}</span>
                      )}
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                        <button
                          onClick={() => setShowDeleteConfirm(entry.id)}
                          className="p-1.5 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-gray-500">
                <p>No weight entries yet</p>
                <Button
                  variant="ghost"
                  icon={Plus}
                  onClick={() => setShowAddModal(true)}
                  className="mt-4"
                >
                  Log your first weight
                </Button>
              </div>
            )}
          </Card>
        </>
      )}

      {/* Add Weight Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-md animate-in border border-gray-700">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-100">Log Weight</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-2 rounded-lg hover:bg-gray-700 text-gray-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddWeight} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Weight (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  placeholder="75.0"
                  value={newWeight.weight}
                  onChange={(e) => setNewWeight({ ...newWeight, weight: e.target.value })}
                  className="w-full px-4 py-3 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 text-center text-2xl font-semibold focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Date</label>
                <input
                  type="date"
                  value={newWeight.date}
                  onChange={(e) => setNewWeight({ ...newWeight, date: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Note (optional)</label>
                <input
                  type="text"
                  placeholder="Morning weigh-in, after workout, etc."
                  value={newWeight.note}
                  onChange={(e) => setNewWeight({ ...newWeight, note: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <Button type="submit" className="w-full" size="lg" disabled={addLoading}>
                {addLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Check className="w-4 h-4 mr-2" />
                )}
                Save Entry
              </Button>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-sm overflow-hidden animate-in border border-gray-700">
            <div className="p-6 text-center">
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                <Trash2 className="w-6 h-6 text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-100 mb-2">Delete Weight Entry?</h3>
              <p className="text-gray-400 mb-6">
                This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <Button
                  variant="ghost"
                  className="flex-1"
                  onClick={() => setShowDeleteConfirm(null)}
                >
                  Cancel
                </Button>
                <Button
                  variant="danger"
                  className="flex-1 bg-red-500 hover:bg-red-600"
                  onClick={() => handleDeleteWeight(showDeleteConfirm)}
                >
                  Delete
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
