import { useState, useEffect, useCallback } from 'react';
import {
  Dumbbell,
  Plus,
  Calendar,
  Clock,
  Flame,
  TrendingUp,
  ChevronRight,
  Play,
  CheckCircle,
  Timer,
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
import { format, parseISO } from 'date-fns';
import { Card, Button, Badge } from '../components/ui';
import { workoutApi } from '../api';

export default function WorkoutTracker() {
  const [workouts, setWorkouts] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchWorkoutData = useCallback(async () => {
    try {
      setLoading(true);
      const [workoutsRes, exercisesRes] = await Promise.all([
        workoutApi.getWorkouts({ days: 30 }),
        workoutApi.getExercises(),
      ]);
      setWorkouts(workoutsRes.workouts || []);
      setStats(workoutsRes.stats || null);
      setExercises(exercisesRes.exercises || []);
    } catch (err) {
      console.error('Error fetching workout data:', err);
      setError('Failed to load workout data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkoutData();
  }, [fetchWorkoutData]);

  const totalWorkouts = stats?.total_workouts || workouts.length;
  const avgDuration = stats?.avg_duration || (
    workouts.length > 0
      ? Math.round(workouts.reduce((sum, w) => sum + (w.duration || 0), 0) / workouts.length)
      : 0
  );
  const totalVolume = stats?.total_volume || workouts.reduce((sum, w) => sum + (w.volume || 0), 0);
  const currentStreak = stats?.current_streak || 0;

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Workout Tracker</h1>
          <p className="text-gray-400 mt-1">
            Track your strength training progress
          </p>
        </div>
        <Button icon={Plus}>Start Workout</Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : error ? (
        <Card className="text-center py-8">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-400">{error}</p>
          <Button variant="ghost" onClick={fetchWorkoutData} className="mt-4">
            Try Again
          </Button>
        </Card>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                  <Dumbbell className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">This Month</p>
                  <p className="text-2xl font-bold text-gray-100">
                    {totalWorkouts} workouts
                  </p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                  <Clock className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Avg Duration</p>
                  <p className="text-2xl font-bold text-gray-100">{avgDuration} min</p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-orange-600 flex items-center justify-center">
                  <Flame className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Total Volume</p>
                  <p className="text-2xl font-bold text-gray-100">
                    {(totalVolume / 1000).toFixed(1)}k kg
                  </p>
                </div>
              </div>
            </Card>
            <Card>
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Current Streak</p>
                  <p className="text-2xl font-bold text-gray-100">{currentStreak} days</p>
                </div>
              </div>
            </Card>
          </div>

          {/* Exercise Library */}
          {exercises.length > 0 && (
            <Card title="Exercise Library" subtitle="Available exercises">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {exercises.slice(0, 8).map((exercise) => (
                  <div
                    key={exercise.id}
                    className="p-4 rounded-xl border border-gray-700 hover:border-primary-500 hover:bg-gray-700/50 transition-all"
                  >
                    <h3 className="font-medium text-gray-100">{exercise.name}</h3>
                    <p className="text-sm text-gray-500 mt-1">{exercise.muscle_group}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Workout History */}
          <Card title="Recent Workouts" subtitle="Your training history" padding={false}>
            {workouts.length > 0 ? (
              <div className="divide-y divide-gray-700">
                {workouts.map((workout) => (
                  <div
                    key={workout.id}
                    className="p-4 flex items-center justify-between hover:bg-gray-700/30 transition-colors cursor-pointer group"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
                        <CheckCircle className="w-6 h-6 text-purple-400" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold text-gray-100">{workout.name}</h3>
                          <Badge variant="success" size="sm">
                            Completed
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-500">
                          {format(parseISO(workout.date), 'EEEE, MMMM d')}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="hidden md:flex items-center gap-6 text-sm text-gray-400">
                        <div className="flex items-center gap-1">
                          <Timer className="w-4 h-4" />
                          {workout.duration} min
                        </div>
                        <div className="flex items-center gap-1">
                          <Dumbbell className="w-4 h-4" />
                          {workout.exercises_count || 0} exercises
                        </div>
                        {workout.volume && (
                          <div>
                            {(workout.volume / 1000).toFixed(1)}k kg
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
                <p>No workouts logged yet</p>
                <Button
                  variant="ghost"
                  icon={Plus}
                  className="mt-4"
                >
                  Start your first workout
                </Button>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
