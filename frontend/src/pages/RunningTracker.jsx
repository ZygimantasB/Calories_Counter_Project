import { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  Plus,
  MapPin,
  Clock,
  Flame,
  TrendingUp,
  Timer,
  ChevronRight,
  Target,
  X,
  Loader2,
  AlertCircle,
  Check,
  Trash2,
  Edit2,
  Zap,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { Card, Button, Badge } from '../components/ui';
import { runningApi } from '../api';

export default function RunningTracker() {
  const [runHistory, setRunHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addLoading, setAddLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('month');

  // Edit/delete state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [editRun, setEditRun] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  const [newRun, setNewRun] = useState({
    distance: '',
    duration: '',
    date: format(new Date(), 'yyyy-MM-dd'),
    notes: '',
  });

  const fetchRunningData = useCallback(async () => {
    try {
      setLoading(true);
      const daysMap = { week: 7, month: 30, '3months': 90, '6months': 180, year: 365, all: 'all' };
      const days = daysMap[timeRange] || 30;
      const response = await runningApi.getRunningItems({ days });
      setRunHistory(response.items || []);
      setStats(response.stats || null);
    } catch (err) {
      console.error('Error fetching running data:', err);
      setError('Failed to load running data');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchRunningData();
  }, [fetchRunningData]);

  const handleAddRun = async (e) => {
    e.preventDefault();
    try {
      setAddLoading(true);
      await runningApi.addSession({
        distance: parseFloat(newRun.distance),
        duration: parseInt(newRun.duration),
        date: newRun.date,
        notes: newRun.notes,
      });
      setShowAddModal(false);
      setNewRun({
        distance: '',
        duration: '',
        date: format(new Date(), 'yyyy-MM-dd'),
        notes: '',
      });
      fetchRunningData();
    } catch (err) {
      console.error('Error adding run:', err);
    } finally {
      setAddLoading(false);
    }
  };

  const openEditModal = (run) => {
    setEditRun({
      id: run.id,
      distance: run.distance,
      duration: run.duration_minutes || '',
      date: run.date ? run.date.split('T')[0] : format(new Date(), 'yyyy-MM-dd'),
      notes: run.notes || '',
    });
    setShowEditModal(true);
  };

  const handleEditRun = async (e) => {
    e.preventDefault();
    if (!editRun) return;
    try {
      setEditLoading(true);
      const durationStr = `${editRun.duration}:00`;
      await runningApi.update(editRun.id, {
        distance: parseFloat(editRun.distance),
        duration: durationStr,
        date: editRun.date + 'T00:00:00',
        notes: editRun.notes,
      });
      setShowEditModal(false);
      setEditRun(null);
      fetchRunningData();
    } catch (err) {
      console.error('Error updating run:', err);
    } finally {
      setEditLoading(false);
    }
  };

  const handleDeleteRun = async (sessionId) => {
    try {
      await runningApi.delete(sessionId);
      setShowDeleteConfirm(null);
      fetchRunningData();
    } catch (err) {
      console.error('Error deleting run:', err);
    }
  };

  // Computed stats
  const totalDistance = stats?.total_distance || runHistory.reduce((sum, r) => sum + (r.distance || 0), 0);
  const totalRuns = stats?.total_runs || runHistory.length;
  const avgSpeed = stats?.avg_speed || 0;
  const avgPace = avgSpeed > 0
    ? `${Math.floor(60 / avgSpeed)}:${String(Math.round((60 / avgSpeed % 1) * 60)).padStart(2, '0')}`
    : '--:--';
  const totalCalories = Math.round(totalDistance * 60);
  const weeklyGoal = stats?.weekly_goal || 25;
  const weeklyProgress = (totalDistance / weeklyGoal) * 100;

  // Extended performance metrics
  const longestRun = runHistory.length > 0
    ? Math.max(...runHistory.map(r => parseFloat(r.distance) || 0))
    : 0;

  const sortedByDate = [...runHistory].sort((a, b) => new Date(a.date) - new Date(b.date));
  let paceImprovement = null;
  if (sortedByDate.length >= 2) {
    const firstPace = sortedByDate[0].duration_minutes && parseFloat(sortedByDate[0].distance) > 0
      ? sortedByDate[0].duration_minutes / parseFloat(sortedByDate[0].distance)
      : null;
    const lastPace = sortedByDate[sortedByDate.length - 1].duration_minutes && parseFloat(sortedByDate[sortedByDate.length - 1].distance) > 0
      ? sortedByDate[sortedByDate.length - 1].duration_minutes / parseFloat(sortedByDate[sortedByDate.length - 1].distance)
      : null;
    if (firstPace && lastPace && firstPace > 0) {
      paceImprovement = ((firstPace - lastPace) / firstPace * 100).toFixed(1);
    }
  }

  const fastestPaceRun = runHistory.reduce((best, r) => {
    if (!r.duration_minutes || !parseFloat(r.distance)) return best;
    const pace = r.duration_minutes / parseFloat(r.distance);
    if (!best || pace < best) return pace;
    return best;
  }, null);

  const fastestPaceStr = fastestPaceRun
    ? `${Math.floor(fastestPaceRun)}:${String(Math.round((fastestPaceRun % 1) * 60)).padStart(2, '0')}`
    : '--:--';

  let daySpan = 1;
  if (sortedByDate.length >= 2) {
    const first = new Date(sortedByDate[0].date);
    const last = new Date(sortedByDate[sortedByDate.length - 1].date);
    daySpan = Math.max(1, (last - first) / (1000 * 60 * 60 * 24));
  }
  const avgWeeklyDistance = daySpan > 0 ? (totalDistance / (daySpan / 7)).toFixed(1) : totalDistance.toFixed(1);
  const avgMonthlyDistance = daySpan > 0 ? (totalDistance / (daySpan / 30)).toFixed(1) : totalDistance.toFixed(1);

  // Chart data
  const distanceChartData = sortedByDate.map(r => ({
    date: format(parseISO(r.date), 'MMM d'),
    distance: parseFloat(r.distance) || 0,
  }));

  const durationChartData = sortedByDate.map(r => ({
    date: format(parseISO(r.date), 'MMM d'),
    duration: r.duration_minutes || 0,
  }));

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Running Tracker</h1>
          <p className="text-gray-400 mt-1">Track your runs and improve your pace</p>
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
          <Button icon={Plus} onClick={() => setShowAddModal(true)}>
            Log Run
          </Button>
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
          <Button variant="ghost" onClick={fetchRunningData} className="mt-4">
            Try Again
          </Button>
        </Card>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
                  <MapPin className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Total Distance</p>
                  <p className="text-2xl font-bold text-gray-100">
                    {totalDistance.toFixed(1)} km
                  </p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Total Runs</p>
                  <p className="text-2xl font-bold text-gray-100">{totalRuns}</p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center">
                  <Timer className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Avg Pace</p>
                  <p className="text-2xl font-bold text-gray-100">{avgPace}/km</p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center">
                  <Flame className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Calories Burned</p>
                  <p className="text-2xl font-bold text-gray-100">
                    {totalCalories.toLocaleString()}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Extended Performance Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            <Card>
              <div className="flex flex-col gap-1">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center mb-1">
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                </div>
                <p className="text-xs text-gray-400">Pace Improvement</p>
                <p className="text-xl font-bold text-gray-100">
                  {paceImprovement !== null
                    ? `${paceImprovement > 0 ? '+' : ''}${paceImprovement}%`
                    : '--'}
                </p>
              </div>
            </Card>
            <Card>
              <div className="flex flex-col gap-1">
                <div className="w-8 h-8 rounded-lg bg-yellow-500/20 flex items-center justify-center mb-1">
                  <Zap className="w-4 h-4 text-yellow-400" />
                </div>
                <p className="text-xs text-gray-400">Fastest Pace</p>
                <p className="text-xl font-bold text-gray-100">{fastestPaceStr}/km</p>
              </div>
            </Card>
            <Card>
              <div className="flex flex-col gap-1">
                <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center mb-1">
                  <MapPin className="w-4 h-4 text-purple-400" />
                </div>
                <p className="text-xs text-gray-400">Longest Run</p>
                <p className="text-xl font-bold text-gray-100">{longestRun.toFixed(1)} km</p>
              </div>
            </Card>
            <Card>
              <div className="flex flex-col gap-1">
                <div className="w-8 h-8 rounded-lg bg-sky-500/20 flex items-center justify-center mb-1">
                  <Target className="w-4 h-4 text-sky-400" />
                </div>
                <p className="text-xs text-gray-400">Avg Weekly</p>
                <p className="text-xl font-bold text-gray-100">{avgWeeklyDistance} km</p>
              </div>
            </Card>
            <Card>
              <div className="flex flex-col gap-1">
                <div className="w-8 h-8 rounded-lg bg-pink-500/20 flex items-center justify-center mb-1">
                  <Clock className="w-4 h-4 text-pink-400" />
                </div>
                <p className="text-xs text-gray-400">Avg Monthly</p>
                <p className="text-xl font-bold text-gray-100">{avgMonthlyDistance} km</p>
              </div>
            </Card>
          </div>

          {/* Weekly Goal Progress */}
          <Card className="bg-gradient-to-br from-green-500 to-green-600 border-0 text-white">
            <div className="flex flex-col md:flex-row md:items-center gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="w-5 h-5" />
                  <span className="text-sm font-medium text-white/80">Weekly Goal</span>
                </div>
                <div className="flex items-baseline gap-3">
                  <span className="text-4xl font-bold">{totalDistance.toFixed(1)}</span>
                  <span className="text-xl text-white/70">/ {weeklyGoal} km</span>
                </div>
                <div className="mt-4">
                  <div className="h-3 bg-white/20 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-white rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(weeklyProgress, 100)}%` }}
                    />
                  </div>
                  <p className="text-sm text-white/70 mt-2">
                    {weeklyGoal - totalDistance > 0
                      ? `${(weeklyGoal - totalDistance).toFixed(1)} km to go`
                      : 'Goal achieved!'}
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-2xl font-bold">{totalRuns}</div>
                  <div className="text-sm text-white/70">Runs</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{avgPace}</div>
                  <div className="text-sm text-white/70">Avg Pace</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {runHistory.reduce((sum, r) => sum + (r.duration_minutes || 0), 0)}
                  </div>
                  <div className="text-sm text-white/70">Minutes</div>
                </div>
              </div>
            </div>
          </Card>

          {/* Charts Row */}
          {distanceChartData.length > 1 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Distance Over Time */}
              <Card title="Distance Over Time">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={distanceChartData}>
                      <defs>
                        <linearGradient id="distanceGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="date"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#9ca3af', fontSize: 11 }}
                      />
                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#9ca3af', fontSize: 11 }}
                        tickFormatter={(v) => `${v}km`}
                      />
                      <Tooltip
                        formatter={(value) => [`${value.toFixed(2)} km`, 'Distance']}
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="distance"
                        stroke="#0ea5e9"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#distanceGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>

              {/* Duration Over Time */}
              <Card title="Duration Over Time">
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={durationChartData}>
                      <defs>
                        <linearGradient id="durationGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="date"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#9ca3af', fontSize: 11 }}
                      />
                      <YAxis
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#9ca3af', fontSize: 11 }}
                        tickFormatter={(v) => `${v}m`}
                      />
                      <Tooltip
                        formatter={(value) => [`${value} min`, 'Duration']}
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: '1px solid #374151',
                          borderRadius: '8px',
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="duration"
                        stroke="#22c55e"
                        strokeWidth={2}
                        fillOpacity={1}
                        fill="url(#durationGradient)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </div>
          )}

          {/* Recent Runs */}
          <Card title="Recent Runs" subtitle="Your running history" padding={false}>
            {runHistory.length > 0 ? (
              <div className="divide-y divide-gray-700">
                {runHistory.map((run) => (
                  <div
                    key={run.id}
                    className="p-4 flex items-center justify-between hover:bg-gray-700/30 transition-colors group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center">
                        <Activity className="w-6 h-6 text-green-400" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-gray-100">
                            {run.distance} km Run
                          </h3>
                          {run.pace && (
                            <Badge variant="success" size="sm">
                              {run.pace}/km
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-500">
                          {format(parseISO(run.date), 'EEEE, MMMM d')}
                        </p>
                        {run.notes && (
                          <p className="text-xs text-gray-500 mt-0.5">{run.notes}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="hidden md:flex items-center gap-6 text-sm text-gray-400">
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {run.duration_minutes} min
                        </div>
                        <div className="flex items-center gap-1">
                          <Flame className="w-4 h-4" />
                          {Math.round(run.distance * 60)} kcal
                        </div>
                      </div>
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                        <button
                          onClick={() => openEditModal(run)}
                          className="p-1.5 rounded-lg hover:bg-blue-500/20 text-gray-400 hover:text-blue-400"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm(run.id)}
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
                <p>No running sessions yet</p>
                <Button
                  variant="ghost"
                  icon={Plus}
                  onClick={() => setShowAddModal(true)}
                  className="mt-4"
                >
                  Log your first run
                </Button>
              </div>
            )}
          </Card>
        </>
      )}

      {/* Add Run Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-md animate-in border border-gray-700">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-100">Log Run</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-2 rounded-lg hover:bg-gray-700 text-gray-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddRun} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Distance (km)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder="5.0"
                    value={newRun.distance}
                    onChange={(e) => setNewRun({ ...newRun, distance: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Duration (min)
                  </label>
                  <input
                    type="number"
                    placeholder="30"
                    value={newRun.duration}
                    onChange={(e) => setNewRun({ ...newRun, duration: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Date</label>
                <input
                  type="date"
                  value={newRun.date}
                  onChange={(e) => setNewRun({ ...newRun, date: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Notes (optional)
                </label>
                <input
                  type="text"
                  placeholder="How did it go?"
                  value={newRun.notes}
                  onChange={(e) => setNewRun({ ...newRun, notes: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <Button type="submit" className="w-full" size="lg" disabled={addLoading}>
                {addLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Check className="w-4 h-4 mr-2" />
                )}
                Save Run
              </Button>
            </form>
          </div>
        </div>
      )}

      {/* Edit Run Modal */}
      {showEditModal && editRun && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-md animate-in border border-gray-700">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-100">Edit Run</h2>
              <button
                onClick={() => { setShowEditModal(false); setEditRun(null); }}
                className="p-2 rounded-lg hover:bg-gray-700 text-gray-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleEditRun} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Distance (km)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder="5.0"
                    value={editRun.distance}
                    onChange={(e) => setEditRun({ ...editRun, distance: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Duration (min)
                  </label>
                  <input
                    type="number"
                    placeholder="30"
                    value={editRun.duration}
                    onChange={(e) => setEditRun({ ...editRun, duration: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Date</label>
                <input
                  type="date"
                  value={editRun.date}
                  onChange={(e) => setEditRun({ ...editRun, date: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Notes (optional)
                </label>
                <input
                  type="text"
                  placeholder="How did it go?"
                  value={editRun.notes}
                  onChange={(e) => setEditRun({ ...editRun, notes: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <Button type="submit" className="w-full" size="lg" disabled={editLoading}>
                {editLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Check className="w-4 h-4 mr-2" />
                )}
                Update Run
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
              <h3 className="text-lg font-semibold text-gray-100 mb-2">Delete Run?</h3>
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
                  onClick={() => handleDeleteRun(showDeleteConfirm)}
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
