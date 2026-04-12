import { useState, useEffect, useMemo } from 'react';
import { format, parseISO, startOfISOWeek, endOfISOWeek } from 'date-fns';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, ReferenceLine, Cell,
} from 'recharts';
import { GitCompare } from 'lucide-react';
import { Card, Button } from '../../components/ui';
import { weightApi } from '../../api';
import {
  MEASUREMENT_FIELDS, getISOWeekKey, groupByWeek,
  resolveSnapshot, computeDeltas, computeSummary,
} from './compareUtils.js';

// ---------------------------------------------------------------------------
// Field metadata
// ---------------------------------------------------------------------------

const FIELD_META = {
  neck:          { label: 'Neck',        group: 'core' },
  chest:         { label: 'Chest',       group: 'core' },
  belly:         { label: 'Belly/Waist', group: 'core' },
  butt:          { label: 'Butt/Glutes', group: 'core' },
  left_biceps:   { label: 'L. Biceps',   group: 'arms' },
  right_biceps:  { label: 'R. Biceps',   group: 'arms' },
  left_triceps:  { label: 'L. Triceps',  group: 'arms' },
  right_triceps: { label: 'R. Triceps',  group: 'arms' },
  left_forearm:  { label: 'L. Forearm',  group: 'arms' },
  right_forearm: { label: 'R. Forearm',  group: 'arms' },
  left_thigh:    { label: 'L. Thigh',    group: 'legs' },
  right_thigh:   { label: 'R. Thigh',    group: 'legs' },
  left_lower_leg:  { label: 'L. Calf',   group: 'legs' },
  right_lower_leg: { label: 'R. Calf',   group: 'legs' },
};

const MODES = [
  { id: 'date',   label: 'Date vs Date' },
  { id: 'week',   label: 'Week vs Week' },
  { id: 'period', label: 'Period vs Period' },
];

const STRATEGIES = [
  { id: 'latest',    label: 'Latest entry' },
  { id: 'average',   label: 'Average' },
  { id: 'firstlast', label: 'First vs Last' },
];

// ---------------------------------------------------------------------------
// Helper to build the initial enabled state
// ---------------------------------------------------------------------------

function buildInitialEnabled() {
  const enabled = { _weight: true };
  for (const field of MEASUREMENT_FIELDS) {
    enabled[field] = true;
  }
  return enabled;
}

// ---------------------------------------------------------------------------
// DatePicker sub-component
// ---------------------------------------------------------------------------

function DatePicker({ measurements, value, onChange, label }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-gray-400">{label}</label>
      <select
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
        className="bg-gray-700 border border-gray-600 text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        <option value="">-- Select date --</option>
        {measurements.map((m) => (
          <option key={m.id} value={m.id}>
            {m.date ? format(parseISO(m.date), 'MMM d, yyyy') : `Entry #${m.id}`}
          </option>
        ))}
      </select>
    </div>
  );
}

// ---------------------------------------------------------------------------
// WeekPicker sub-component
// ---------------------------------------------------------------------------

function WeekPicker({ measurements, value, onChange, label }) {
  const weekGroups = useMemo(() => groupByWeek(measurements), [measurements]);

  const sortedWeekKeys = useMemo(() =>
    Object.keys(weekGroups).sort((a, b) => b.localeCompare(a)),
  [weekGroups]);

  function weekRangeLabel(weekKey) {
    // weekKey is like "2025-W17"
    const [yearStr, wStr] = weekKey.split('-W');
    const year = parseInt(yearStr, 10);
    const week = parseInt(wStr, 10);
    // Build a date from year+week: find Monday of that ISO week
    // Use a simple approach: Jan 4 is always in week 1 of its year
    const jan4 = new Date(year, 0, 4);
    const jan4DayOfWeek = jan4.getDay() === 0 ? 7 : jan4.getDay(); // Mon=1 … Sun=7
    const mondayOfWeek1 = new Date(jan4);
    mondayOfWeek1.setDate(jan4.getDate() - (jan4DayOfWeek - 1));
    const monday = new Date(mondayOfWeek1);
    monday.setDate(mondayOfWeek1.getDate() + (week - 1) * 7);
    const sunday = new Date(monday);
    sunday.setDate(monday.getDate() + 6);

    const fmtMonday = format(monday, 'MMM d');
    const fmtSunday = format(sunday, 'MMM d, yyyy');
    const count = weekGroups[weekKey].length;
    return `${fmtMonday}–${fmtSunday} (${count} ${count === 1 ? 'entry' : 'entries'})`;
  }

  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-gray-400">{label}</label>
      <select
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value || null)}
        className="bg-gray-700 border border-gray-600 text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        <option value="">-- Select week --</option>
        {sortedWeekKeys.map((wk) => (
          <option key={wk} value={wk}>
            {weekRangeLabel(wk)}
          </option>
        ))}
      </select>
    </div>
  );
}

// ---------------------------------------------------------------------------
// PeriodPicker sub-component
// ---------------------------------------------------------------------------

function PeriodPicker({ value, onChange, label }) {
  const start = value?.start ?? '';
  const end   = value?.end   ?? '';

  function handleStart(e) {
    onChange({ start: e.target.value, end });
  }
  function handleEnd(e) {
    onChange({ start, end: e.target.value });
  }

  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-gray-400">{label}</label>
      <div className="flex gap-2">
        <input
          type="date"
          value={start}
          onChange={handleStart}
          className="bg-gray-700 border border-gray-600 text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <span className="self-center text-gray-400 text-sm">to</span>
        <input
          type="date"
          value={end}
          onChange={handleEnd}
          className="bg-gray-700 border border-gray-600 text-gray-100 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SummaryCard sub-component
// ---------------------------------------------------------------------------

function SummaryCard({ summary }) {
  const { weightChange, totalCmLost, improved, worsened } = summary;

  const tiles = [
    {
      label: 'Weight Change',
      value: weightChange != null
        ? `${weightChange > 0 ? '+' : ''}${weightChange} kg`
        : 'N/A',
      color: weightChange == null
        ? 'text-gray-400'
        : weightChange < 0
          ? 'text-green-400'
          : weightChange > 0
            ? 'text-red-400'
            : 'text-gray-300',
    },
    {
      label: 'Total cm Lost',
      value: `${totalCmLost} cm`,
      color: totalCmLost > 0 ? 'text-green-400' : 'text-gray-400',
    },
    {
      label: 'Improved',
      value: improved,
      color: improved > 0 ? 'text-green-400' : 'text-gray-400',
    },
    {
      label: 'Worsened',
      value: worsened,
      color: worsened > 0 ? 'text-red-400' : 'text-gray-400',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {tiles.map((t) => (
        <div
          key={t.label}
          className="bg-gray-750 border border-gray-700 rounded-xl p-4 flex flex-col gap-1"
        >
          <span className="text-xs text-gray-400 font-medium">{t.label}</span>
          <span className={`text-2xl font-bold ${t.color}`}>{t.value}</span>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// FieldFilter sub-component
// ---------------------------------------------------------------------------

const GROUP_LABELS = { core: 'Core', arms: 'Arms', legs: 'Legs' };
const GROUPS = ['core', 'arms', 'legs'];

function FieldFilter({ enabled, onChange }) {
  function toggle(field) {
    onChange({ ...enabled, [field]: !enabled[field] });
  }

  function toggleGroup(group) {
    const fields = MEASUREMENT_FIELDS.filter((f) => FIELD_META[f]?.group === group);
    const allOn = fields.every((f) => enabled[f]);
    const next = { ...enabled };
    for (const f of fields) next[f] = !allOn;
    onChange(next);
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Weight toggle */}
      <label className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
        <input
          type="checkbox"
          checked={enabled._weight}
          onChange={() => toggle('_weight')}
          className="w-4 h-4 rounded accent-primary-500"
        />
        <span className="font-medium">Weight</span>
      </label>

      {/* Measurement groups */}
      {GROUPS.map((group) => {
        const fields = MEASUREMENT_FIELDS.filter((f) => FIELD_META[f]?.group === group);
        const allOn = fields.every((f) => enabled[f]);
        return (
          <div key={group}>
            <label className="flex items-center gap-2 text-sm font-semibold text-gray-200 cursor-pointer mb-1">
              <input
                type="checkbox"
                checked={allOn}
                onChange={() => toggleGroup(group)}
                className="w-4 h-4 rounded accent-primary-500"
              />
              {GROUP_LABELS[group]}
            </label>
            <div className="ml-6 grid grid-cols-2 sm:grid-cols-3 gap-1">
              {fields.map((f) => (
                <label
                  key={f}
                  className="flex items-center gap-1.5 text-xs text-gray-400 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={enabled[f]}
                    onChange={() => toggle(f)}
                    className="w-3.5 h-3.5 rounded accent-primary-500"
                  />
                  {FIELD_META[f].label}
                </label>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ComparisonTable sub-component
// ---------------------------------------------------------------------------

function ComparisonTable({ sideA, sideB, deltas, enabled, labelA, labelB }) {
  const activeFields = MEASUREMENT_FIELDS.filter((f) => enabled[f]);

  function fmt(val) {
    if (val == null) return <span className="text-gray-500">—</span>;
    return `${val} cm`;
  }

  function deltaCell(field) {
    const d = deltas[field];
    if (d == null) return <span className="text-gray-500">—</span>;
    if (d < 0) return <span className="text-green-400">{d} cm</span>;
    if (d > 0) return <span className="text-red-400">+{d} cm</span>;
    return <span className="text-gray-400">0 cm</span>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-2 px-3 text-gray-400 font-medium">Measurement</th>
            <th className="text-right py-2 px-3 text-blue-400 font-medium">{labelA}</th>
            <th className="text-right py-2 px-3 text-purple-400 font-medium">{labelB}</th>
            <th className="text-right py-2 px-3 text-gray-400 font-medium">Change</th>
          </tr>
        </thead>
        <tbody>
          {enabled._weight && (
            <tr className="border-b border-gray-800 hover:bg-gray-750">
              <td className="py-2 px-3 text-gray-300 font-medium">Weight</td>
              <td className="py-2 px-3 text-right text-gray-200">
                {sideA._weight != null ? `${sideA._weight} kg` : <span className="text-gray-500">—</span>}
              </td>
              <td className="py-2 px-3 text-right text-gray-200">
                {sideB._weight != null ? `${sideB._weight} kg` : <span className="text-gray-500">—</span>}
              </td>
              <td className="py-2 px-3 text-right">
                {(() => {
                  if (sideA._weight == null || sideB._weight == null) return <span className="text-gray-500">—</span>;
                  const d = parseFloat((sideB._weight - sideA._weight).toFixed(2));
                  if (d < 0) return <span className="text-green-400">{d} kg</span>;
                  if (d > 0) return <span className="text-red-400">+{d} kg</span>;
                  return <span className="text-gray-400">0 kg</span>;
                })()}
              </td>
            </tr>
          )}
          {activeFields.map((field) => (
            <tr key={field} className="border-b border-gray-800 hover:bg-gray-750">
              <td className="py-2 px-3 text-gray-300">{FIELD_META[field]?.label ?? field}</td>
              <td className="py-2 px-3 text-right text-gray-200">{fmt(sideA[field])}</td>
              <td className="py-2 px-3 text-right text-gray-200">{fmt(sideB[field])}</td>
              <td className="py-2 px-3 text-right">{deltaCell(field)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main CompareTab component
// ---------------------------------------------------------------------------

export default function CompareTab({ measurements }) {
  const [mode,      setMode]      = useState('date');
  const [strategy,  setStrategy]  = useState('latest');
  const [selectorA, setSelectorA] = useState(null);
  const [selectorB, setSelectorB] = useState(null);
  const [result,    setResult]    = useState(null);
  const [weightItems, setWeightItems] = useState([]);
  const [enabled,   setEnabled]   = useState(buildInitialEnabled);

  // Fetch weight items on mount
  useEffect(() => {
    weightApi.getWeightItems()
      .then((data) => setWeightItems(data?.items ?? []))
      .catch(() => setWeightItems([]));
  }, []);

  // Reset selectors / result when mode changes
  function handleModeChange(newMode) {
    setMode(newMode);
    setSelectorA(null);
    setSelectorB(null);
    setResult(null);
  }

  // Determine if Compare button should be enabled
  function isValid(sel) {
    if (!sel) return false;
    if (mode === 'period') {
      return sel.start && sel.end;
    }
    return true;
  }
  const canCompare = isValid(selectorA) && isValid(selectorB);

  // Find weight for a measurement date
  function findWeight(dateStr) {
    if (!dateStr) return null;
    const prefix = dateStr.substring(0, 10);
    const item = weightItems.find(
      (w) => w.recorded_at && w.recorded_at.substring(0, 10) === prefix
    );
    return item?.weight ?? null;
  }

  function handleCompare() {
    const snapA = resolveSnapshot(measurements, mode, selectorA, strategy);
    const snapB = resolveSnapshot(measurements, mode, selectorB, strategy);

    if (!snapA || !snapB) {
      setResult({ error: 'No data found for one or both selections. Please choose different dates/weeks.' });
      return;
    }

    // For firstlast strategy, snapA/snapB are {first, last} objects
    const resolvedA = snapA.last ?? snapA;
    const resolvedB = snapB.last ?? snapB;

    const deltas = computeDeltas(resolvedA, resolvedB, MEASUREMENT_FIELDS);

    const weightA = findWeight(resolvedA.date);
    const weightB = findWeight(resolvedB.date);

    const summary = computeSummary(deltas, weightA, weightB);

    const labelA = resolvedA.date
      ? format(parseISO(resolvedA.date), 'MMM d, yyyy')
      : 'Side A';
    const labelB = resolvedB.date
      ? format(parseISO(resolvedB.date), 'MMM d, yyyy')
      : 'Side B';

    setResult({
      sideA: { ...resolvedA, _weight: weightA },
      sideB: { ...resolvedB, _weight: weightB },
      deltas,
      summary,
      labelA,
      labelB,
    });
  }

  // Empty state
  if (measurements.length < 2) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <GitCompare className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <p className="text-gray-400 text-lg">
            Add at least 2 measurements to use the Compare tab.
          </p>
        </div>
      </div>
    );
  }

  // Chart data (only enabled fields)
  const activeFields = MEASUREMENT_FIELDS.filter((f) => enabled[f]);

  const groupedChartData = result && !result.error
    ? activeFields.map((field) => ({
        name: FIELD_META[field]?.label ?? field,
        [result.labelA]: result.sideA[field] ?? null,
        [result.labelB]: result.sideB[field] ?? null,
      })).filter((d) => d[result.labelA] != null || d[result.labelB] != null)
    : [];

  const deltaChartData = result && !result.error
    ? activeFields
        .filter((f) => result.deltas[f] != null)
        .map((field) => ({
          name: FIELD_META[field]?.label ?? field,
          delta: result.deltas[field],
        }))
    : [];

  // ---------------------------------------------------------------------------
  // Selector pair rendering helpers
  // ---------------------------------------------------------------------------

  function renderSelectorPair() {
    if (mode === 'date') {
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <DatePicker
            measurements={measurements}
            value={selectorA}
            onChange={setSelectorA}
            label="Side A"
          />
          <DatePicker
            measurements={measurements}
            value={selectorB}
            onChange={setSelectorB}
            label="Side B"
          />
        </div>
      );
    }

    if (mode === 'week') {
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <WeekPicker
            measurements={measurements}
            value={selectorA}
            onChange={setSelectorA}
            label="Side A"
          />
          <WeekPicker
            measurements={measurements}
            value={selectorB}
            onChange={setSelectorB}
            label="Side B"
          />
        </div>
      );
    }

    if (mode === 'period') {
      return (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <PeriodPicker
            value={selectorA}
            onChange={setSelectorA}
            label="Side A (period)"
          />
          <PeriodPicker
            value={selectorB}
            onChange={setSelectorB}
            label="Side B (period)"
          />
        </div>
      );
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="flex flex-col gap-6">
      {/* Controls card */}
      <Card title="Compare Snapshots">
        <div className="flex flex-col gap-5">
          {/* Mode selector */}
          <div className="flex flex-col gap-2">
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
              Compare by
            </span>
            <div className="flex gap-2 flex-wrap">
              {MODES.map((m) => (
                <button
                  key={m.id}
                  onClick={() => handleModeChange(m.id)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    mode === m.id
                      ? 'bg-primary-500 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {/* Strategy selector (hidden for 'date' mode) */}
          {mode !== 'date' && (
            <div className="flex flex-col gap-2">
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                Strategy
              </span>
              <div className="flex gap-2 flex-wrap">
                {STRATEGIES.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setStrategy(s.id)}
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      strategy === s.id
                        ? 'bg-primary-500 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Selector pair */}
          {renderSelectorPair()}

          {/* Compare button */}
          <div>
            <Button
              onClick={handleCompare}
              disabled={!canCompare}
              icon={GitCompare}
            >
              Compare
            </Button>
          </div>
        </div>
      </Card>

      {/* Error state */}
      {result?.error && (
        <Card>
          <p className="text-red-400 text-sm">{result.error}</p>
        </Card>
      )}

      {/* Results */}
      {result && !result.error && (
        <>
          {/* 1. Summary card */}
          <Card title="Summary">
            <SummaryCard summary={result.summary} />
          </Card>

          {/* 2. Field filter */}
          <Card title="Fields">
            <FieldFilter enabled={enabled} onChange={setEnabled} />
          </Card>

          {/* 3. Comparison table */}
          <Card title={`${result.labelA}  vs  ${result.labelB}`}>
            <ComparisonTable
              sideA={result.sideA}
              sideB={result.sideB}
              deltas={result.deltas}
              enabled={enabled}
              labelA={result.labelA}
              labelB={result.labelB}
            />
          </Card>

          {/* 4. Grouped bar chart */}
          {groupedChartData.length > 0 && (
            <Card title="Side A vs Side B (cm)">
              <ResponsiveContainer width="100%" height={320}>
                <BarChart
                  data={groupedChartData}
                  margin={{ top: 10, right: 20, left: 0, bottom: 60 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#9ca3af', fontSize: 11 }}
                    angle={-40}
                    textAnchor="end"
                  />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                    labelStyle={{ color: '#f3f4f6' }}
                  />
                  <Legend
                    wrapperStyle={{ paddingTop: 16, color: '#d1d5db', fontSize: 12 }}
                  />
                  <Bar dataKey={result.labelA} fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey={result.labelB} fill="#a855f7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          {/* 5. Delta bar chart */}
          {deltaChartData.length > 0 && (
            <Card title="Net Change (cm)">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={deltaChartData}
                  margin={{ top: 10, right: 20, left: 0, bottom: 60 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#9ca3af', fontSize: 11 }}
                    angle={-40}
                    textAnchor="end"
                  />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                    labelStyle={{ color: '#f3f4f6' }}
                    formatter={(v) => [`${v} cm`, 'Delta']}
                  />
                  <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="4 2" />
                  <Bar dataKey="delta" radius={[4, 4, 0, 0]}>
                    {deltaChartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          entry.delta < 0
                            ? '#22c55e'
                            : entry.delta > 0
                              ? '#ef4444'
                              : '#6b7280'
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
