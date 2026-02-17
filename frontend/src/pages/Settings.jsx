import { useState, useEffect, useCallback } from 'react';
import {
  Settings as SettingsIcon,
  User,
  Palette,
  Database,
  Bell,
  Save,
  Download,
  Loader2,
  AlertCircle,
  Check,
  Target,
  Activity,
  Scale,
  Ruler,
  Flame,
} from 'lucide-react';
import { Card, Button } from '../components/ui';
import { settingsApi } from '../api';

const SECTIONS = [
  { id: 'profile', label: 'Profile & Goals', icon: User },
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'data', label: 'Data Management', icon: Database },
  { id: 'notifications', label: 'Notifications', icon: Bell },
];

const WEEKDAYS = [
  { value: 'monday', label: 'Mon' },
  { value: 'tuesday', label: 'Tue' },
  { value: 'wednesday', label: 'Wed' },
  { value: 'thursday', label: 'Thu' },
  { value: 'friday', label: 'Fri' },
  { value: 'saturday', label: 'Sat' },
  { value: 'sunday', label: 'Sun' },
];

export default function Settings() {
  const [section, setSection] = useState('profile');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [settings, setSettings] = useState(null);
  const [choices, setChoices] = useState(null);
  const [recommendedMacros, setRecommendedMacros] = useState(null);
  const [effectiveTargets, setEffectiveTargets] = useState(null);

  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true);
      const response = await settingsApi.getSettings();
      setSettings({
        profile: response.profile,
        appearance: response.appearance,
        notifications: response.notifications,
      });
      setChoices(response.choices);
      setRecommendedMacros(response.recommended_macros);
      setEffectiveTargets(response.effective_targets);
    } catch (err) {
      console.error('Error fetching settings:', err);
      setError('Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const handleSave = async (sectionKey) => {
    try {
      setSaving(true);
      setError(null);
      const dataToUpdate = { [sectionKey]: settings[sectionKey] };
      const response = await settingsApi.updateSettings(dataToUpdate);

      if (sectionKey === 'profile') {
        if (response.bmr) {
          setSettings(prev => ({
            ...prev,
            profile: { ...prev.profile, bmr: response.bmr }
          }));
        }
        if (response.recommended_macros) {
          setRecommendedMacros(response.recommended_macros);
        }
        if (response.effective_targets) {
          setEffectiveTargets(response.effective_targets);
        }
      }

      setSuccess(`${sectionKey.charAt(0).toUpperCase() + sectionKey.slice(1)} settings saved successfully!`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Error saving settings:', err);
      setError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleExport = (type) => {
    settingsApi.exportData(type, type === 'all' ? 'json' : 'csv');
  };

  const updateProfile = (field, value) => {
    setSettings(prev => ({
      ...prev,
      profile: { ...prev.profile, [field]: value }
    }));
  };

  const updateAppearance = (field, value) => {
    setSettings(prev => ({
      ...prev,
      appearance: { ...prev.appearance, [field]: value }
    }));
  };

  const updateNotifications = (field, value) => {
    setSettings(prev => ({
      ...prev,
      notifications: { ...prev.notifications, [field]: value }
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-primary-500/10 rounded-lg">
          <SettingsIcon className="w-6 h-6 text-primary-500" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-gray-400 text-sm">Manage your profile, preferences, and data</p>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <span className="text-red-400">{error}</span>
        </div>
      )}
      {success && (
        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4 flex items-center gap-3">
          <Check className="w-5 h-5 text-green-400" />
          <span className="text-green-400">{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <Card className="p-4 sticky top-4">
            <nav className="space-y-1">
              {SECTIONS.map(({ id, label, icon: Icon }) => (
                <button
                  key={id}
                  onClick={() => setSection(id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    section === id
                      ? 'bg-primary-500 text-white'
                      : 'text-gray-400 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{label}</span>
                </button>
              ))}
            </nav>
          </Card>
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <Card className="p-6">
            {section === 'profile' && settings && (
              <ProfileSection
                settings={settings.profile}
                choices={choices}
                recommendedMacros={recommendedMacros}
                onChange={updateProfile}
                onSave={() => handleSave('profile')}
                saving={saving}
              />
            )}
            {section === 'appearance' && settings && (
              <AppearanceSection
                settings={settings.appearance}
                choices={choices}
                onChange={updateAppearance}
                onSave={() => handleSave('appearance')}
                saving={saving}
              />
            )}
            {section === 'data' && (
              <DataSection onExport={handleExport} />
            )}
            {section === 'notifications' && settings && (
              <NotificationsSection
                settings={settings.notifications}
                onChange={updateNotifications}
                onSave={() => handleSave('notifications')}
                saving={saving}
              />
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}

function ProfileSection({ settings, choices, recommendedMacros, onChange, onSave, saving }) {
  const isAutoMacros = settings.use_auto_macros;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-gray-700 pb-4">
        <div className="flex items-center gap-3">
          <User className="w-5 h-5 text-primary-400" />
          <h2 className="text-xl font-semibold text-white">Profile & Goals</h2>
        </div>
      </div>

      {/* BMR Display */}
      {settings.bmr && (
        <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-xl p-6 text-white">
          <div className="flex items-center gap-3 mb-2">
            <Flame className="w-6 h-6" />
            <span className="text-sm opacity-90">Your Estimated Daily Calorie Needs (TDEE)</span>
          </div>
          <div className="text-3xl font-bold">{settings.bmr} kcal</div>
          <p className="text-sm opacity-80 mt-1">Based on your profile and activity level</p>
        </div>
      )}

      {/* Personal Info */}
      <div className="space-y-4">
        <h3 className="flex items-center gap-2 text-lg font-medium text-white">
          <User className="w-4 h-4 text-gray-400" />
          Personal Info
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Name</label>
            <input
              type="text"
              value={settings.name || ''}
              onChange={(e) => onChange('name', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="Your name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Age</label>
            <input
              type="number"
              value={settings.age || ''}
              onChange={(e) => onChange('age', e.target.value ? parseInt(e.target.value) : null)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              min="1"
              max="120"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Gender</label>
            <select
              value={settings.gender}
              onChange={(e) => onChange('gender', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {choices?.genders?.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Height (cm)</label>
            <input
              type="number"
              value={settings.height || ''}
              onChange={(e) => onChange('height', e.target.value ? parseFloat(e.target.value) : null)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              step="0.1"
              min="50"
              max="300"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Current Weight (kg)</label>
            <input
              type="number"
              value={settings.current_weight || ''}
              onChange={(e) => onChange('current_weight', e.target.value ? parseFloat(e.target.value) : null)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              step="0.1"
              min="20"
              max="500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Activity Level</label>
            <select
              value={settings.activity_level}
              onChange={(e) => onChange('activity_level', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {choices?.activity_levels?.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Fitness Goal */}
      <div className="space-y-4">
        <h3 className="flex items-center gap-2 text-lg font-medium text-white">
          <Target className="w-4 h-4 text-gray-400" />
          Fitness Goal
        </h3>

        {/* Fitness Goal Selector */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {choices?.fitness_goals?.map(opt => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange('fitness_goal', opt.value)}
              className={`p-4 rounded-xl border-2 transition-all ${
                settings.fitness_goal === opt.value
                  ? 'border-primary-500 bg-primary-500/10'
                  : 'border-gray-600 bg-gray-700/50 hover:border-gray-500'
              }`}
            >
              <div className="text-2xl mb-2">
                {opt.value === 'bulk' ? '💪' : opt.value === 'cut' ? '🔥' : opt.value === 'ripped' ? '⚡' : '⚖️'}
              </div>
              <div className={`font-medium ${settings.fitness_goal === opt.value ? 'text-primary-400' : 'text-white'}`}>
                {opt.label}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {opt.value === 'bulk' ? 'TDEE + 300 kcal surplus' :
                 opt.value === 'cut' ? 'TDEE - 500 kcal deficit' :
                 opt.value === 'ripped' ? 'TDEE - 750 kcal aggressive cut' :
                 'Maintain at TDEE'}
              </div>
            </button>
          ))}
        </div>

        {/* Auto-calculate macros toggle */}
        <div className="flex items-center justify-between bg-gray-700/30 rounded-lg p-4 mt-4">
          <div>
            <div className="font-medium text-white">Auto-calculate Macros</div>
            <div className="text-sm text-gray-400">
              Automatically set macro targets based on your fitness goal and body weight
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.use_auto_macros}
              onChange={(e) => onChange('use_auto_macros', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-500/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
          </label>
        </div>

        {/* Recommended Macros Display */}
        {isAutoMacros && recommendedMacros && (
          <div className="bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Activity className="w-5 h-5 text-green-400" />
              <span className="font-medium text-green-400">Recommended Macros for {recommendedMacros.goal === 'bulk' ? 'Bulking' : recommendedMacros.goal === 'cut' ? 'Cutting' : recommendedMacros.goal === 'ripped' ? 'Get Ripped' : 'Maintenance'}</span>
            </div>
            <p className="text-sm text-gray-300 mb-4">{recommendedMacros.description}</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-800/50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-orange-400">{recommendedMacros.calories}</div>
                <div className="text-xs text-gray-400">Calories</div>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-red-400">{recommendedMacros.protein}g</div>
                <div className="text-xs text-gray-400">Protein</div>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-blue-400">{recommendedMacros.carbs}g</div>
                <div className="text-xs text-gray-400">Carbs</div>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-yellow-400">{recommendedMacros.fat}g</div>
                <div className="text-xs text-gray-400">Fat</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Goals */}
      <div className="space-y-4">
        <h3 className="flex items-center gap-2 text-lg font-medium text-white">
          <Scale className="w-4 h-4 text-gray-400" />
          Weight & Workout Goals
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Daily Calorie Target</label>
            <input
              type="number"
              value={settings.daily_calorie_target || ''}
              onChange={(e) => onChange('daily_calorie_target', parseInt(e.target.value) || 2000)}
              disabled={isAutoMacros}
              className={`w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                isAutoMacros
                  ? 'bg-gray-800 border-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-700 border-gray-600 text-white'
              }`}
              min="500"
              max="10000"
            />
            {isAutoMacros && <p className="text-xs text-gray-500 mt-1">Auto-calculated from fitness goal</p>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Target Weight (kg)</label>
            <input
              type="number"
              value={settings.target_weight || ''}
              onChange={(e) => onChange('target_weight', e.target.value ? parseFloat(e.target.value) : null)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              step="0.1"
              min="20"
              max="500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Weekly Workout Goal</label>
            <input
              type="number"
              value={settings.weekly_workout_goal || ''}
              onChange={(e) => onChange('weekly_workout_goal', parseInt(e.target.value) || 3)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
              min="0"
              max="14"
            />
          </div>
        </div>
      </div>

      {/* Macro Targets */}
      <div className="space-y-4">
        <h3 className="flex items-center gap-2 text-lg font-medium text-white">
          <Activity className="w-4 h-4 text-gray-400" />
          Macro Targets (Daily)
          {isAutoMacros && <span className="text-xs text-gray-500 ml-2">(Auto-calculated)</span>}
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Protein (g)</label>
            <input
              type="number"
              value={settings.protein_target || ''}
              onChange={(e) => onChange('protein_target', parseInt(e.target.value) || 150)}
              disabled={isAutoMacros}
              className={`w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                isAutoMacros
                  ? 'bg-gray-800 border-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-700 border-gray-600 text-white'
              }`}
              min="0"
              max="500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Carbohydrates (g)</label>
            <input
              type="number"
              value={settings.carbs_target || ''}
              onChange={(e) => onChange('carbs_target', parseInt(e.target.value) || 200)}
              disabled={isAutoMacros}
              className={`w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                isAutoMacros
                  ? 'bg-gray-800 border-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-700 border-gray-600 text-white'
              }`}
              min="0"
              max="1000"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Fat (g)</label>
            <input
              type="number"
              value={settings.fat_target || ''}
              onChange={(e) => onChange('fat_target', parseInt(e.target.value) || 65)}
              disabled={isAutoMacros}
              className={`w-full border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                isAutoMacros
                  ? 'bg-gray-800 border-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gray-700 border-gray-600 text-white'
              }`}
              min="0"
              max="500"
            />
          </div>
        </div>
      </div>

      <Button onClick={onSave} disabled={saving} className="mt-6">
        {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
        Save Profile
      </Button>
    </div>
  );
}

function AppearanceSection({ settings, choices, onChange, onSave, saving }) {
  const colorOptions = [
    { value: 'blue', color: '#3b82f6' },
    { value: 'green', color: '#10b981' },
    { value: 'purple', color: '#8b5cf6' },
    { value: 'orange', color: '#f97316' },
    { value: 'pink', color: '#ec4899' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-gray-700 pb-4">
        <div className="flex items-center gap-3">
          <Palette className="w-5 h-5 text-primary-400" />
          <h2 className="text-xl font-semibold text-white">Appearance</h2>
        </div>
      </div>

      {/* Theme */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-white">Theme</h3>
        <select
          value={settings.theme}
          onChange={(e) => onChange('theme', e.target.value)}
          className="w-full max-w-xs bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {choices?.themes?.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <p className="text-sm text-gray-500">Theme changes will apply to the traditional dashboard</p>
      </div>

      {/* Chart Color */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-white">Chart Color</h3>
        <div className="flex gap-3">
          {colorOptions.map(({ value, color }) => (
            <button
              key={value}
              onClick={() => onChange('chart_color', value)}
              className={`w-10 h-10 rounded-full border-4 transition-transform hover:scale-110 ${
                settings.chart_color === value ? 'border-white' : 'border-transparent'
              }`}
              style={{ backgroundColor: color }}
              title={value.charAt(0).toUpperCase() + value.slice(1)}
            />
          ))}
        </div>
      </div>

      {/* Default Date Range */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-white">Default Date Range for Analytics</h3>
        <select
          value={settings.default_date_range}
          onChange={(e) => onChange('default_date_range', parseInt(e.target.value))}
          className="w-full max-w-xs bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {choices?.date_ranges?.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      <Button onClick={onSave} disabled={saving} className="mt-6">
        {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
        Save Appearance
      </Button>
    </div>
  );
}

function DataSection({ onExport }) {
  const exportOptions = [
    { type: 'food', label: 'Food Log', description: 'All your food entries with nutritional information', icon: '🍽️' },
    { type: 'weight', label: 'Weight History', description: 'All your weight measurements over time', icon: '⚖️' },
    { type: 'workout', label: 'Workout History', description: 'All your workouts with exercises, sets, and reps', icon: '💪' },
    { type: 'running', label: 'Running Sessions', description: 'All your runs with distance and duration', icon: '🏃' },
    { type: 'body', label: 'Body Measurements', description: 'All your body measurement records', icon: '📏' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-gray-700 pb-4">
        <div className="flex items-center gap-3">
          <Database className="w-5 h-5 text-primary-400" />
          <h2 className="text-xl font-semibold text-white">Data Management</h2>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium text-white">Export Your Data</h3>
        <p className="text-gray-400">Download your data in CSV or JSON format for backup or analysis.</p>

        <div className="space-y-3 mt-4">
          {exportOptions.map(({ type, label, description, icon }) => (
            <div
              key={type}
              className="flex items-center justify-between bg-gray-700/50 rounded-lg p-4 hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center gap-4">
                <span className="text-2xl">{icon}</span>
                <div>
                  <h4 className="font-medium text-white">{label}</h4>
                  <p className="text-sm text-gray-400">{description}</p>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onExport(type)}
              >
                <Download className="w-4 h-4 mr-2" />
                CSV
              </Button>
            </div>
          ))}

          {/* Export All */}
          <div className="bg-gradient-to-r from-primary-500/20 to-primary-600/20 border border-primary-500/30 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="text-2xl">📦</span>
              <div>
                <h4 className="font-medium text-white">Export All Data</h4>
                <p className="text-sm text-gray-300">Complete backup of all your data in JSON format</p>
              </div>
            </div>
            <Button
              onClick={() => onExport('all')}
            >
              <Download className="w-4 h-4 mr-2" />
              JSON
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

function NotificationsSection({ settings, onChange, onSave, saving }) {
  const toggleDay = (day) => {
    const currentDays = settings.workout_reminder_days || [];
    const newDays = currentDays.includes(day)
      ? currentDays.filter(d => d !== day)
      : [...currentDays, day];
    onChange('workout_reminder_days', newDays);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between border-b border-gray-700 pb-4">
        <div className="flex items-center gap-3">
          <Bell className="w-5 h-5 text-primary-400" />
          <h2 className="text-xl font-semibold text-white">Notification Preferences</h2>
        </div>
      </div>

      <p className="text-gray-400">Set up reminder preferences for future mobile app integration.</p>

      {/* Meal Reminders */}
      <div className="bg-gray-700/30 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">🍽️</span>
            <div>
              <h4 className="font-medium text-white">Meal Logging Reminders</h4>
              <p className="text-sm text-gray-400">Get reminded to log your meals</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.meal_reminder_enabled}
              onChange={(e) => onChange('meal_reminder_enabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-500/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
          </label>
        </div>
        {settings.meal_reminder_enabled && (
          <div className="grid grid-cols-3 gap-4 pt-2">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Breakfast</label>
              <input
                type="time"
                value={settings.meal_reminder_times?.[0] || '08:00'}
                onChange={(e) => {
                  const times = [...(settings.meal_reminder_times || ['08:00', '12:00', '18:00'])];
                  times[0] = e.target.value;
                  onChange('meal_reminder_times', times);
                }}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Lunch</label>
              <input
                type="time"
                value={settings.meal_reminder_times?.[1] || '12:00'}
                onChange={(e) => {
                  const times = [...(settings.meal_reminder_times || ['08:00', '12:00', '18:00'])];
                  times[1] = e.target.value;
                  onChange('meal_reminder_times', times);
                }}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Dinner</label>
              <input
                type="time"
                value={settings.meal_reminder_times?.[2] || '18:00'}
                onChange={(e) => {
                  const times = [...(settings.meal_reminder_times || ['08:00', '12:00', '18:00'])];
                  times[2] = e.target.value;
                  onChange('meal_reminder_times', times);
                }}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
              />
            </div>
          </div>
        )}
      </div>

      {/* Workout Reminders */}
      <div className="bg-gray-700/30 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">💪</span>
            <div>
              <h4 className="font-medium text-white">Workout Reminders</h4>
              <p className="text-sm text-gray-400">Get reminded on your workout days</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.workout_reminder_enabled}
              onChange={(e) => onChange('workout_reminder_enabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-500/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
          </label>
        </div>
        {settings.workout_reminder_enabled && (
          <div className="space-y-4 pt-2">
            <div className="max-w-xs">
              <label className="block text-sm text-gray-400 mb-1">Reminder Time</label>
              <input
                type="time"
                value={settings.workout_reminder_time || '17:00'}
                onChange={(e) => onChange('workout_reminder_time', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-2">Reminder Days</label>
              <div className="flex flex-wrap gap-2">
                {WEEKDAYS.map(({ value, label }) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => toggleDay(value)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      settings.workout_reminder_days?.includes(value)
                        ? 'bg-primary-500 text-white'
                        : 'bg-gray-600 text-gray-300 hover:bg-gray-500'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Weight Reminders */}
      <div className="bg-gray-700/30 rounded-lg p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl">⚖️</span>
            <div>
              <h4 className="font-medium text-white">Weight Logging Reminder</h4>
              <p className="text-sm text-gray-400">Daily reminder to log your weight</p>
            </div>
          </div>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={settings.weight_reminder_enabled}
              onChange={(e) => onChange('weight_reminder_enabled', e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-500/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-500"></div>
          </label>
        </div>
        {settings.weight_reminder_enabled && (
          <div className="max-w-xs pt-2">
            <label className="block text-sm text-gray-400 mb-1">Reminder Time</label>
            <input
              type="time"
              value={settings.weight_reminder_time || '07:00'}
              onChange={(e) => onChange('weight_reminder_time', e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white text-sm"
            />
          </div>
        )}
      </div>

      <Button onClick={onSave} disabled={saving} className="mt-6">
        {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
        Save Notifications
      </Button>
    </div>
  );
}
