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
  Heart,
  Target,
  X,
  Loader2,
  AlertCircle,
  Check,
  Trash2,
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
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { Card, Button, Badge, ProgressBar } from '../components/ui';
import { runningApi } from '../api';

export default function RunningTracker() {
  const [runHistory, setRunHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [addLoading, setAddLoading] = useState(false);
  const [timeRange, setTimeRange] = useState('month');

  const [newRun, setNewRun] = useState({
    distance: '',
    duration: '',
    date: format(new Date(), 'yyyy-MM-dd'),
    notes: '',
  });

  const fetchRunningData = useCallback(async () => {
    try {
      setLoading(true);
      const daysMap = { week: 7, month: 30, '3months': 90, '6months': 180, year: 365, all: 9999 };
      const days = daysMap[timeRange] || 30;
      const response = await runningApi.getRunningItems({ days });
      setRunHistory(response.sessions || []);
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

  const totalDistance = stats?.total_distance || runHistory.reduce((sum, r) => sum + (r.distance || 0), 0);
  const totalRuns = stats?.total_runs || runHistory.length;
  const avgPace = stats?.avg_pace || '--:--';
  const totalCalories = stats?.total_calories || runHistory.reduce((sum, r) => sum + (r.calories || 0), 0);
  const weeklyGoal = stats?.weekly_goal || 25;
  const weeklyProgress = (totalDistance / weeklyGoal) * 100;

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
                    {runHistory.reduce((sum, r) => sum + (r.duration || 0), 0)}
                  </div>
                  <div className="text-sm text-white/70">Minutes</div>
                </div>
              </div>
            </div>
          </Card>

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
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="hidden md:flex items-center gap-6 text-sm text-gray-400">
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {run.duration} min
                        </div>
                        {run.calories && (
                          <div className="flex items-center gap-1">
                            <Flame className="w-4 h-4" />
                            {run.calories} kcal
                          </div>
                        )}
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-600 group-hover:text-gray-400" />
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
    </div>
  );
}
