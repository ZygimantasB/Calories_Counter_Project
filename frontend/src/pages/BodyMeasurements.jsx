import { useState, useEffect, useCallback } from 'react';
import {
  Ruler,
  Plus,
  TrendingDown,
  TrendingUp,
  Minus,
  Calendar,
  Edit2,
  Trash2,
  X,
  Download,
  Loader2,
  AlertCircle,
  Check,
  LayoutGrid,
  Table,
  BarChart3,
  LineChart as LineChartIcon,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import { Card, Button, Badge } from '../components/ui';
import { bodyMeasurementsApi } from '../api';

// All measurement fields matching the Django template
const allMeasurements = {
  // Core measurements
  neck: { label: 'Neck', color: '#0ea5e9', group: 'core' },
  chest: { label: 'Chest', color: '#ef4444', group: 'core' },
  belly: { label: 'Belly/Waist', color: '#f97316', group: 'core' },
  butt: { label: 'Butt/Glutes', color: '#eab308', group: 'core' },
  // Arms
  left_biceps: { label: 'Left Biceps', color: '#22c55e', group: 'arms' },
  right_biceps: { label: 'Right Biceps', color: '#16a34a', group: 'arms' },
  left_triceps: { label: 'Left Triceps', color: '#14b8a6', group: 'arms' },
  right_triceps: { label: 'Right Triceps', color: '#0d9488', group: 'arms' },
  left_forearm: { label: 'Left Forearm', color: '#06b6d4', group: 'arms' },
  right_forearm: { label: 'Right Forearm', color: '#0891b2', group: 'arms' },
  // Legs
  left_thigh: { label: 'Left Thigh', color: '#8b5cf6', group: 'legs' },
  right_thigh: { label: 'Right Thigh', color: '#7c3aed', group: 'legs' },
  left_lower_leg: { label: 'Left Calf', color: '#a855f7', group: 'legs' },
  right_lower_leg: { label: 'Right Calf', color: '#9333ea', group: 'legs' },
};

// Time range options
const timeRanges = [
  { label: 'Last 30 Days', value: 30 },
  { label: 'Last 90 Days', value: 90 },
  { label: 'Last 6 Months', value: 180 },
  { label: 'Last Year', value: 365 },
  { label: 'All Time', value: 'all' },
];

const ITEMS_PER_PAGE = 10;

export default function BodyMeasurements() {
  const [measurements, setMeasurements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingMeasurement, setEditingMeasurement] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('all');
  const [chartType, setChartType] = useState('line');
  const [timeRange, setTimeRange] = useState(365);
  const [historyView, setHistoryView] = useState('timeline'); // 'timeline' or 'table'
  const [currentPage, setCurrentPage] = useState(1);
  const [formData, setFormData] = useState({});
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(null);

  const fetchMeasurements = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await bodyMeasurementsApi.getMeasurements({
        days: timeRange === 'all' ? 9999 : timeRange
      });
      // The API returns 'items', not 'measurements'
      setMeasurements(response.items || response.measurements || []);
    } catch (err) {
      console.error('Error fetching measurements:', err);
      setError('Failed to load measurements');
    } finally {
      setLoading(false);
    }
  }, [timeRange]);

  useEffect(() => {
    fetchMeasurements();
  }, [fetchMeasurements]);

  // Get latest measurement
  const latestMeasurement = measurements[0] || {};
  const previousMeasurement = measurements[1] || {};

  // Calculate change between measurements
  const getChange = (field) => {
    const current = latestMeasurement[field];
    const previous = previousMeasurement[field];
    if (!current || !previous) return null;
    return parseFloat((current - previous).toFixed(1));
  };

  // Get trend icon
  const getTrendIcon = (change) => {
    if (change === null || change === 0) return <Minus className="w-4 h-4 text-gray-400" />;
    if (change > 0) return <TrendingUp className="w-4 h-4 text-green-400" />;
    return <TrendingDown className="w-4 h-4 text-red-400" />;
  };

  // Get trend color
  const getTrendColor = (change) => {
    if (change === null || change === 0) return 'text-gray-400';
    if (change > 0) return 'text-green-400';
    return 'text-red-400';
  };

  // Prepare chart data
  const chartData = [...measurements].reverse().map((m) => ({
    date: m.date ? format(parseISO(m.date), 'MMM d') : '',
    ...Object.keys(allMeasurements).reduce((acc, key) => {
      acc[key] = m[key] || null;
      return acc;
    }, {}),
  }));

  // Pagination
  const totalPages = Math.ceil(measurements.length / ITEMS_PER_PAGE);
  const paginatedMeasurements = measurements.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE
  );

  // Handle form input change
  const handleFormChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value === '' ? null : parseFloat(value),
    }));
  };

  // Handle add measurement
  const handleAddMeasurement = async () => {
    try {
      setSaving(true);
      await bodyMeasurementsApi.addMeasurement({
        date: formData.date || new Date().toISOString(),
        ...formData,
      });
      setShowAddModal(false);
      setFormData({});
      await fetchMeasurements();
    } catch (err) {
      console.error('Error adding measurement:', err);
      alert('Failed to add measurement');
    } finally {
      setSaving(false);
    }
  };

  // Handle edit measurement
  const handleEditMeasurement = async () => {
    if (!editingMeasurement) return;
    try {
      setSaving(true);
      await bodyMeasurementsApi.editMeasurement(editingMeasurement.id, formData);
      setShowEditModal(false);
      setEditingMeasurement(null);
      setFormData({});
      await fetchMeasurements();
    } catch (err) {
      console.error('Error editing measurement:', err);
      alert('Failed to update measurement');
    } finally {
      setSaving(false);
    }
  };

  // Handle delete measurement
  const handleDeleteMeasurement = async (id) => {
    if (!confirm('Are you sure you want to delete this measurement?')) return;
    try {
      setDeleting(id);
      await bodyMeasurementsApi.deleteMeasurement(id);
      await fetchMeasurements();
    } catch (err) {
      console.error('Error deleting measurement:', err);
      alert('Failed to delete measurement');
    } finally {
      setDeleting(null);
    }
  };

  // Open edit modal
  const openEditModal = (measurement) => {
    setEditingMeasurement(measurement);
    setFormData({
      date: measurement.date,
      ...Object.keys(allMeasurements).reduce((acc, key) => {
        acc[key] = measurement[key];
        return acc;
      }, {}),
      notes: measurement.notes,
    });
    setShowEditModal(true);
  };

  // Handle export CSV
  const handleExportCsv = async () => {
    try {
      const blob = await bodyMeasurementsApi.exportCsv();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'body-measurements.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } catch (err) {
      console.error('Error exporting CSV:', err);
    }
  };

  // Render chart
  const renderChart = () => {
    if (chartData.length === 0) {
      return (
        <div className="h-80 flex items-center justify-center text-gray-500">
          No measurement data to display
        </div>
      );
    }

    const ChartComponent = chartType === 'line' ? LineChart : BarChart;
    const DataComponent = chartType === 'line' ? Line : Bar;

    const metricsToShow = selectedMetric === 'all'
      ? Object.keys(allMeasurements)
      : [selectedMetric];

    return (
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ChartComponent data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="date"
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#9ca3af', fontSize: 11 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              label={{ value: 'cm', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1f2937',
                border: '1px solid #374151',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#f3f4f6' }}
            />
            {selectedMetric === 'all' && <Legend />}
            {metricsToShow.map((key) => (
              <DataComponent
                key={key}
                type="monotone"
                dataKey={key}
                name={allMeasurements[key]?.label || key}
                stroke={allMeasurements[key]?.color || '#0ea5e9'}
                fill={allMeasurements[key]?.color || '#0ea5e9'}
                strokeWidth={2}
                dot={chartType === 'line' ? { r: 3 } : undefined}
                connectNulls
              />
            ))}
          </ChartComponent>
        </ResponsiveContainer>
      </div>
    );
  };

  // Render measurement form (used in both Add and Edit modals)
  const renderMeasurementForm = (isEdit = false) => (
    <div className="space-y-6">
      {/* Date */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Date and Time</label>
        <input
          type="datetime-local"
          value={formData.date ? formData.date.slice(0, 16) : format(new Date(), "yyyy-MM-dd'T'HH:mm")}
          onChange={(e) => setFormData((prev) => ({ ...prev, date: e.target.value }))}
          className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Core Measurements */}
      <div>
        <h4 className="text-md font-semibold text-gray-200 mb-3 border-b border-gray-600 pb-2">
          Core Measurements
        </h4>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(allMeasurements)
            .filter(([_, config]) => config.group === 'core')
            .map(([key, config]) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  {config.label} (cm)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={formData[key] || ''}
                  onChange={(e) => handleFormChange(key, e.target.value)}
                  placeholder="0.0"
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            ))}
        </div>
      </div>

      {/* Arms */}
      <div>
        <h4 className="text-md font-semibold text-gray-200 mb-3 border-b border-gray-600 pb-2">
          Arms
        </h4>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(allMeasurements)
            .filter(([_, config]) => config.group === 'arms')
            .map(([key, config]) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  {config.label} (cm)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={formData[key] || ''}
                  onChange={(e) => handleFormChange(key, e.target.value)}
                  placeholder="0.0"
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            ))}
        </div>
      </div>

      {/* Legs */}
      <div>
        <h4 className="text-md font-semibold text-gray-200 mb-3 border-b border-gray-600 pb-2">
          Legs
        </h4>
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(allMeasurements)
            .filter(([_, config]) => config.group === 'legs')
            .map(([key, config]) => (
              <div key={key}>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  {config.label} (cm)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={formData[key] || ''}
                  onChange={(e) => handleFormChange(key, e.target.value)}
                  placeholder="0.0"
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            ))}
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Notes</label>
        <textarea
          value={formData.notes || ''}
          onChange={(e) => setFormData((prev) => ({ ...prev, notes: e.target.value }))}
          placeholder="Optional notes about these measurements"
          rows={3}
          className="w-full px-4 py-2.5 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Submit Button */}
      <Button
        className="w-full"
        size="lg"
        onClick={isEdit ? handleEditMeasurement : handleAddMeasurement}
        disabled={saving}
      >
        {saving ? (
          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
        ) : (
          <Check className="w-4 h-4 mr-2" />
        )}
        {isEdit ? 'Update Measurements' : 'Save Measurements'}
      </Button>
    </div>
  );

  return (
    <div className="space-y-6 animate-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Body Measurements Tracker</h1>
          <p className="text-gray-400 mt-1">Track your body composition progress</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" icon={Download} onClick={handleExportCsv}>
            Download CSV
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-700">
        <nav className="flex gap-4">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
            { id: 'history', label: 'History', icon: Calendar },
            { id: 'add', label: 'Add New', icon: Plus },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary-500 animate-spin" />
        </div>
      ) : error ? (
        <Card className="text-center py-8">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-400">{error}</p>
          <Button variant="ghost" onClick={fetchMeasurements} className="mt-4">
            Try Again
          </Button>
        </Card>
      ) : (
        <>
          {/* Dashboard Tab */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              {/* Time Range Buttons */}
              <div className="flex flex-wrap gap-2">
                {timeRanges.map((range) => (
                  <button
                    key={range.value}
                    onClick={() => setTimeRange(range.value)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      timeRange === range.value
                        ? 'bg-primary-500 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {range.label}
                  </button>
                ))}
              </div>

              {/* Chart Card */}
              <Card
                title="Body Measurements Progress"
                action={
                  <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-400">Chart Type</span>
                      <select
                        value={chartType}
                        onChange={(e) => setChartType(e.target.value)}
                        className="px-3 py-1.5 text-sm border border-gray-600 bg-gray-700 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="line">Line Chart</option>
                        <option value="bar">Bar Chart</option>
                      </select>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-400">Measurement Type</span>
                      <select
                        value={selectedMetric}
                        onChange={(e) => setSelectedMetric(e.target.value)}
                        className="px-3 py-1.5 text-sm border border-gray-600 bg-gray-700 text-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                      >
                        <option value="all">All Measurements</option>
                        <optgroup label="Core">
                          {Object.entries(allMeasurements)
                            .filter(([_, config]) => config.group === 'core')
                            .map(([key, config]) => (
                              <option key={key} value={key}>{config.label}</option>
                            ))}
                        </optgroup>
                        <optgroup label="Arms">
                          {Object.entries(allMeasurements)
                            .filter(([_, config]) => config.group === 'arms')
                            .map(([key, config]) => (
                              <option key={key} value={key}>{config.label}</option>
                            ))}
                        </optgroup>
                        <optgroup label="Legs">
                          {Object.entries(allMeasurements)
                            .filter(([_, config]) => config.group === 'legs')
                            .map(([key, config]) => (
                              <option key={key} value={key}>{config.label}</option>
                            ))}
                        </optgroup>
                      </select>
                    </div>
                  </div>
                }
              >
                {renderChart()}
              </Card>

              {/* Latest Measurements */}
              {latestMeasurement.date && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-200 mb-4">
                    Latest Measurements ({format(parseISO(latestMeasurement.date), 'MMMM d, yyyy')})
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Core */}
                    <Card>
                      <h4 className="text-md font-semibold text-gray-200 mb-4 border-b border-gray-600 pb-2">
                        Core
                      </h4>
                      <div className="space-y-3">
                        {Object.entries(allMeasurements)
                          .filter(([_, config]) => config.group === 'core')
                          .map(([key, config]) => {
                            const value = latestMeasurement[key];
                            const change = getChange(key);
                            return (
                              <div key={key} className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">{config.label}</span>
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-gray-100">
                                    {value ? `${value} cm` : '--'}
                                  </span>
                                  {change !== null && (
                                    <span className={`flex items-center text-xs ${getTrendColor(change)}`}>
                                      {getTrendIcon(change)}
                                    </span>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </Card>

                    {/* Arms */}
                    <Card>
                      <h4 className="text-md font-semibold text-gray-200 mb-4 border-b border-gray-600 pb-2">
                        Arms
                      </h4>
                      <div className="space-y-3">
                        {Object.entries(allMeasurements)
                          .filter(([_, config]) => config.group === 'arms')
                          .map(([key, config]) => {
                            const value = latestMeasurement[key];
                            const change = getChange(key);
                            return (
                              <div key={key} className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">{config.label}</span>
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-gray-100">
                                    {value ? `${value} cm` : '--'}
                                  </span>
                                  {change !== null && (
                                    <span className={`flex items-center text-xs ${getTrendColor(change)}`}>
                                      {getTrendIcon(change)}
                                    </span>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </Card>

                    {/* Legs */}
                    <Card>
                      <h4 className="text-md font-semibold text-gray-200 mb-4 border-b border-gray-600 pb-2">
                        Legs
                      </h4>
                      <div className="space-y-3">
                        {Object.entries(allMeasurements)
                          .filter(([_, config]) => config.group === 'legs')
                          .map(([key, config]) => {
                            const value = latestMeasurement[key];
                            const change = getChange(key);
                            return (
                              <div key={key} className="flex items-center justify-between">
                                <span className="text-sm text-gray-400">{config.label}</span>
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-gray-100">
                                    {value ? `${value} cm` : '--'}
                                  </span>
                                  {change !== null && (
                                    <span className={`flex items-center text-xs ${getTrendColor(change)}`}>
                                      {getTrendIcon(change)}
                                    </span>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </Card>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <div className="space-y-4">
              <Card
                title="Measurement History"
                action={
                  <Button
                    variant={historyView === 'table' ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setHistoryView(historyView === 'timeline' ? 'table' : 'timeline')}
                  >
                    {historyView === 'timeline' ? (
                      <>
                        <Table className="w-4 h-4 mr-2" />
                        Toggle Table View
                      </>
                    ) : (
                      <>
                        <LayoutGrid className="w-4 h-4 mr-2" />
                        Toggle Timeline View
                      </>
                    )}
                  </Button>
                }
                padding={false}
              >
                {measurements.length > 0 ? (
                  <>
                    {historyView === 'timeline' ? (
                      // Timeline View
                      <div className="divide-y divide-gray-700">
                        {paginatedMeasurements.map((measurement, index) => {
                          const prevMeasurement = measurements[measurements.indexOf(measurement) + 1];
                          return (
                            <div key={measurement.id} className="p-4 hover:bg-gray-700/30">
                              <div className="flex items-center justify-between mb-3">
                                <h5 className="font-semibold text-gray-100">
                                  {format(parseISO(measurement.date), 'MMMM d, yyyy')}
                                </h5>
                                <div className="flex gap-1">
                                  <button
                                    onClick={() => openEditModal(measurement)}
                                    className="px-3 py-1 text-sm rounded bg-primary-600 text-white hover:bg-primary-500"
                                  >
                                    <Edit2 className="w-3 h-3 inline mr-1" />
                                    Edit
                                  </button>
                                  <button
                                    onClick={() => handleDeleteMeasurement(measurement.id)}
                                    disabled={deleting === measurement.id}
                                    className="px-3 py-1 text-sm rounded bg-red-600 text-white hover:bg-red-500 disabled:opacity-50"
                                  >
                                    {deleting === measurement.id ? (
                                      <Loader2 className="w-3 h-3 inline animate-spin" />
                                    ) : (
                                      <>
                                        <Trash2 className="w-3 h-3 inline mr-1" />
                                        Delete
                                      </>
                                    )}
                                  </button>
                                </div>
                              </div>
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                {['chest', 'belly', 'left_biceps', 'right_biceps'].map((key) => {
                                  const value = measurement[key];
                                  const prevValue = prevMeasurement?.[key];
                                  const change = value && prevValue ? parseFloat((value - prevValue).toFixed(1)) : null;
                                  return (
                                    <div key={key} className="flex items-center justify-between bg-gray-700/30 rounded px-3 py-2">
                                      <span className="text-gray-400">{allMeasurements[key]?.label}:</span>
                                      <span className="flex items-center gap-1 text-gray-100">
                                        {value ? `${value} cm` : '--'}
                                        {change !== null && (
                                          <span className={getTrendColor(change)}>
                                            {getTrendIcon(change)}
                                          </span>
                                        )}
                                      </span>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      // Table View
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-700/50 border-b border-gray-700">
                            <tr>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Date</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Neck</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Chest</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Belly</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Biceps (L/R)</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Triceps (L/R)</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Forearm (L/R)</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Thigh (L/R)</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Calf (L/R)</th>
                              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase">Butt</th>
                              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase">Actions</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-700">
                            {paginatedMeasurements.map((m) => (
                              <tr key={m.id} className="hover:bg-gray-700/30">
                                <td className="px-4 py-3 font-medium text-gray-100">
                                  {format(parseISO(m.date), 'yyyy-MM-dd')}
                                </td>
                                <td className="px-4 py-3 text-gray-300">{m.neck || '--'}</td>
                                <td className="px-4 py-3 text-gray-300">{m.chest || '--'}</td>
                                <td className="px-4 py-3 text-gray-300">{m.belly || '--'}</td>
                                <td className="px-4 py-3 text-gray-300">
                                  {m.left_biceps || '--'}/{m.right_biceps || '--'}
                                </td>
                                <td className="px-4 py-3 text-gray-300">
                                  {m.left_triceps || '--'}/{m.right_triceps || '--'}
                                </td>
                                <td className="px-4 py-3 text-gray-300">
                                  {m.left_forearm || '--'}/{m.right_forearm || '--'}
                                </td>
                                <td className="px-4 py-3 text-gray-300">
                                  {m.left_thigh || '--'}/{m.right_thigh || '--'}
                                </td>
                                <td className="px-4 py-3 text-gray-300">
                                  {m.left_lower_leg || '--'}/{m.right_lower_leg || '--'}
                                </td>
                                <td className="px-4 py-3 text-gray-300">{m.butt || '--'}</td>
                                <td className="px-4 py-3 text-right">
                                  <div className="flex items-center justify-end gap-1">
                                    <button
                                      onClick={() => openEditModal(m)}
                                      className="p-1.5 rounded-lg hover:bg-gray-600 text-gray-400 hover:text-gray-200"
                                    >
                                      <Edit2 className="w-4 h-4" />
                                    </button>
                                    <button
                                      onClick={() => handleDeleteMeasurement(m.id)}
                                      disabled={deleting === m.id}
                                      className="p-1.5 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400"
                                    >
                                      {deleting === m.id ? (
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                      ) : (
                                        <Trash2 className="w-4 h-4" />
                                      )}
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex items-center justify-center gap-2 p-4 border-t border-gray-700">
                        <button
                          onClick={() => setCurrentPage(1)}
                          disabled={currentPage === 1}
                          className="px-3 py-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          First
                        </button>
                        <button
                          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                          disabled={currentPage === 1}
                          className="px-3 py-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <ChevronLeft className="w-4 h-4" />
                        </button>
                        <span className="px-4 py-1 text-gray-300">
                          Page {currentPage} of {totalPages}
                        </span>
                        <button
                          onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                          disabled={currentPage === totalPages}
                          className="px-3 py-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setCurrentPage(totalPages)}
                          disabled={currentPage === totalPages}
                          className="px-3 py-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          Last
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="p-8 text-center text-gray-500">
                    <p>No measurements recorded yet</p>
                    <Button
                      variant="ghost"
                      icon={Plus}
                      onClick={() => setActiveTab('add')}
                      className="mt-4"
                    >
                      Add your first measurement
                    </Button>
                  </div>
                )}
              </Card>
            </div>
          )}

          {/* Add New Tab */}
          {activeTab === 'add' && (
            <Card title="Add New Measurements">
              {renderMeasurementForm(false)}
            </Card>
          )}
        </>
      )}

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4">
          <div className="bg-gray-800 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto animate-in border border-gray-700">
            <div className="p-4 border-b border-gray-700 flex items-center justify-between sticky top-0 bg-gray-800">
              <h2 className="text-lg font-semibold text-gray-100">
                Edit Measurements
              </h2>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingMeasurement(null);
                  setFormData({});
                }}
                className="p-2 rounded-lg hover:bg-gray-700 text-gray-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6">
              {renderMeasurementForm(true)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
