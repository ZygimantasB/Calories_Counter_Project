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
  X,
  Pencil,
  Trash2,
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

const emptyForm = {
  name: '',
  date: format(new Date(), 'yyyy-MM-dd'),
  notes: '',
};

export default function WorkoutTracker() {
  const [workouts, setWorkouts] = useState([]);
  const [exercises, setExercises] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Add modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [addForm, setAddForm] = useState(emptyForm);
  const [addLoading, setAddLoading] = useState(false);

  // Edit modal
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState(null);
  const [editLoading, setEditLoading] = useState(false);

  // Delete confirm (workout)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  // Exercise library management
  const [showLibraryModal, setShowLibraryModal] = useState(false);
  const [exForm, setExForm] = useState({ name: '', muscle_group: '', description: '' });
  const [exAddLoading, setExAddLoading] = useState(false);
  const [exAddError, setExAddError] = useState(null);
  const [deletingExerciseId, setDeletingExerciseId] = useState(null);

  const fetchWorkoutData = useCallback(async () => {
    try {
      setLoading(true);
      const [workoutsRes, exercisesRes] = await Promise.all([
        workoutApi.getWorkouts({ days: 30 }),
        workoutApi.getExercises(),
      ]);
      setWorkouts(workoutsRes.items || workoutsRes.workouts || []);
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

  const handleAddWorkout = async (e) => {
    e.preventDefault();
    try {
      setAddLoading(true);
      await workoutApi.add({
        name: addForm.name || 'Workout',
        date: addForm.date ? addForm.date + 'T00:00:00' : undefined,
        notes: addForm.notes,
      });
      setShowAddModal(false);
      setAddForm(emptyForm);
      fetchWorkoutData();
    } catch (err) {
      console.error('Error adding workout:', err);
    } finally {
      setAddLoading(false);
    }
  };

  const openEditModal = (workout) => {
    setEditForm({
      id: workout.id,
      name: workout.name || '',
      date: workout.date ? workout.date.split('T')[0] : format(new Date(), 'yyyy-MM-dd'),
      notes: workout.notes || '',
    });
    setShowEditModal(true);
  };

  const handleEditWorkout = async (e) => {
    e.preventDefault();
    if (!editForm) return;
    try {
      setEditLoading(true);
      await workoutApi.update(editForm.id, {
        name: editForm.name || 'Workout',
        date: editForm.date ? editForm.date + 'T00:00:00' : undefined,
        notes: editForm.notes,
      });
      setShowEditModal(false);
      setEditForm(null);
      fetchWorkoutData();
    } catch (err) {
      console.error('Error updating workout:', err);
    } finally {
      setEditLoading(false);
    }
  };

  const handleDeleteWorkout = async (workoutId) => {
    try {
      await workoutApi.delete(workoutId);
      setShowDeleteConfirm(null);
      fetchWorkoutData();
    } catch (err) {
      console.error('Error deleting workout:', err);
    }
  };

  const handleAddExercise = async (e) => {
    e.preventDefault();
    setExAddError(null);
    try {
      setExAddLoading(true);
      await workoutApi.addExerciseToLibrary({
        name: exForm.name,
        muscle_group: exForm.muscle_group,
        description: exForm.description,
      });
      setExForm({ name: '', muscle_group: '', description: '' });
      fetchWorkoutData();
    } catch (err) {
      setExAddError(err?.response?.data?.message || 'Failed to add exercise');
    } finally {
      setExAddLoading(false);
    }
  };

  const handleDeleteExercise = async (exerciseId) => {
    try {
      setDeletingExerciseId(exerciseId);
      await workoutApi.deleteExerciseFromLibrary(exerciseId);
      fetchWorkoutData();
    } catch (err) {
      console.error('Error deleting exercise:', err);
    } finally {
      setDeletingExerciseId(null);
    }
  };

  // Group exercises by muscle group
  const exercisesByGroup = exercises.reduce((acc, ex) => {
    const group = ex.muscle_group || 'Other';
    if (!acc[group]) acc[group] = [];
    acc[group].push(ex);
    return acc;
  }, {});

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
        <Button icon={Plus} onClick={() => setShowAddModal(true)}>Start Workout</Button>
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
          <Card
            title="Exercise Library"
            subtitle={`${exercises.length} exercise${exercises.length !== 1 ? 's' : ''} available`}
          >
            <div className="space-y-4">
              {/* Add Exercise Form */}
              <form onSubmit={handleAddExercise} className="p-4 bg-gray-700/40 rounded-xl border border-gray-600 space-y-3">
                <h3 className="text-sm font-semibold text-gray-300">Add Exercise</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <input
                      type="text"
                      value={exForm.name}
                      onChange={(e) => setExForm({ ...exForm, name: e.target.value })}
                      placeholder="Exercise name *"
                      required
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 text-sm"
                    />
                  </div>
                  <div>
                    <input
                      type="text"
                      value={exForm.muscle_group}
                      onChange={(e) => setExForm({ ...exForm, muscle_group: e.target.value })}
                      placeholder="Muscle group (e.g. Chest)"
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 text-sm"
                    />
                  </div>
                  <div>
                    <input
                      type="text"
                      value={exForm.description}
                      onChange={(e) => setExForm({ ...exForm, description: e.target.value })}
                      placeholder="Description (optional)"
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 text-sm"
                    />
                  </div>
                </div>
                {exAddError && (
                  <p className="text-sm text-red-400">{exAddError}</p>
                )}
                <div className="flex justify-end">
                  <Button type="submit" icon={Plus} disabled={exAddLoading} size="sm">
                    {exAddLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Add Exercise'}
                  </Button>
                </div>
              </form>

              {/* Exercise List grouped by muscle group */}
              {exercises.length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(exercisesByGroup).sort(([a], [b]) => a.localeCompare(b)).map(([group, groupExercises]) => (
                    <div key={group}>
                      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">{group}</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                        {groupExercises.map((exercise) => (
                          <div
                            key={exercise.id}
                            className="flex items-center justify-between p-3 rounded-xl border border-gray-700 hover:border-gray-600 hover:bg-gray-700/30 transition-all group"
                          >
                            <div className="min-w-0 flex-1">
                              <h3 className="font-medium text-gray-100 text-sm truncate">{exercise.name}</h3>
                              {exercise.description && (
                                <p className="text-xs text-gray-500 mt-0.5 truncate">{exercise.description}</p>
                              )}
                            </div>
                            <button
                              onClick={() => handleDeleteExercise(exercise.id)}
                              disabled={deletingExerciseId === exercise.id}
                              className="ml-2 p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-colors opacity-0 group-hover:opacity-100 flex-shrink-0"
                              title="Delete exercise"
                            >
                              {deletingExerciseId === exercise.id
                                ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                : <Trash2 className="w-3.5 h-3.5" />
                              }
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-gray-500 py-4 text-sm">No exercises in the library yet. Add one above.</p>
              )}
            </div>
          </Card>

          {/* Workout History */}
          <Card title="Recent Workouts" subtitle="Your training history" padding={false}>
            {workouts.length > 0 ? (
              <div className="divide-y divide-gray-700">
                {workouts.map((workout) => (
                  <div
                    key={workout.id}
                    className="p-4 flex items-center justify-between hover:bg-gray-700/30 transition-colors group"
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
                          {workout.date ? format(parseISO(workout.date), 'EEEE, MMMM d') : 'Unknown date'}
                        </p>
                        {workout.notes && (
                          <p className="text-xs text-gray-600 mt-0.5 truncate max-w-xs">{workout.notes}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="hidden md:flex items-center gap-6 text-sm text-gray-400">
                        <div className="flex items-center gap-1">
                          <Timer className="w-4 h-4" />
                          {workout.duration || 0} min
                        </div>
                        <div className="flex items-center gap-1">
                          <Dumbbell className="w-4 h-4" />
                          {workout.exercise_count || workout.exercises_count || 0} exercises
                        </div>
                        {workout.total_volume > 0 && (
                          <div>
                            {(workout.total_volume / 1000).toFixed(1)}k kg
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => openEditModal(workout)}
                        className="p-1.5 rounded-lg text-gray-500 hover:text-blue-400 hover:bg-blue-500/10 transition-colors opacity-0 group-hover:opacity-100"
                        title="Edit workout"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => setShowDeleteConfirm(workout.id)}
                        className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors opacity-0 group-hover:opacity-100"
                        title="Delete workout"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
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
                  onClick={() => setShowAddModal(true)}
                >
                  Start your first workout
                </Button>
              </div>
            )}
          </Card>
        </>
      )}

      {/* Add Workout Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-md shadow-2xl border border-gray-700">
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-gray-100">Log Workout</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-gray-700 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddWorkout} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Workout Name
                </label>
                <input
                  type="text"
                  value={addForm.name}
                  onChange={(e) => setAddForm({ ...addForm, name: e.target.value })}
                  placeholder="e.g. Push Day, Leg Day..."
                  className="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={addForm.date}
                  onChange={(e) => setAddForm({ ...addForm, date: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-xl text-gray-100 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={addForm.notes}
                  onChange={(e) => setAddForm({ ...addForm, notes: e.target.value })}
                  placeholder="How did it go?"
                  rows={3}
                  className="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 resize-none"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={addLoading}
                  className="flex-1"
                >
                  {addLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Log Workout'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Workout Modal */}
      {showEditModal && editForm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-md shadow-2xl border border-gray-700">
            <div className="flex items-center justify-between p-6 border-b border-gray-700">
              <h2 className="text-lg font-semibold text-gray-100">Edit Workout</h2>
              <button
                onClick={() => { setShowEditModal(false); setEditForm(null); }}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-200 hover:bg-gray-700 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleEditWorkout} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Workout Name
                </label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  placeholder="e.g. Push Day, Leg Day..."
                  className="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={editForm.date}
                  onChange={(e) => setEditForm({ ...editForm, date: e.target.value })}
                  className="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-xl text-gray-100 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Notes (optional)
                </label>
                <textarea
                  value={editForm.notes}
                  onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                  placeholder="How did it go?"
                  rows={3}
                  className="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 resize-none"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() => { setShowEditModal(false); setEditForm(null); }}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={editLoading}
                  className="flex-1"
                >
                  {editLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Changes'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-sm shadow-2xl border border-gray-700 p-6">
            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
                <Trash2 className="w-6 h-6 text-red-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-100 mb-2">Delete Workout</h3>
              <p className="text-gray-400 text-sm mb-6">
                Are you sure you want to delete this workout? This action cannot be undone.
              </p>
              <div className="flex gap-3">
                <Button
                  variant="ghost"
                  onClick={() => setShowDeleteConfirm(null)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <button
                  onClick={() => handleDeleteWorkout(showDeleteConfirm)}
                  className="flex-1 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl font-medium transition-colors"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
