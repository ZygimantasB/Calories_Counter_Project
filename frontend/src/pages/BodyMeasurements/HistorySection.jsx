import { useState } from 'react';
import {
  Edit2,
  Trash2,
  Loader2,
  Plus,
  Table as TableIcon,
  LayoutGrid,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  TrendingUp,
  TrendingDown,
  Minus,
  CalendarDays,
  ListChecks,
} from 'lucide-react';
import { format, parseISO, formatDistanceToNow, differenceInCalendarDays } from 'date-fns';
import { Card, Button } from '../../components/ui';
import { changeQuality, navyBodyFat } from './bodyComposition';

const ITEMS_PER_PAGE = 10;
const GROUPS = [
  { id: 'core', label: 'Core' },
  { id: 'arms', label: 'Arms' },
  { id: 'legs', label: 'Legs' },
];

function bodyFatFor(m, settings) {
  if (!m || !settings) return null;
  return navyBodyFat({
    gender: settings.gender,
    height: settings.height,
    neck: m.neck,
    waist: m.belly,
    hip: m.butt,
  });
}

// Small colored delta, goal-aware. `dir` overrides field goal for derived metrics.
function DeltaPill({ label, value, change, unit = '', dir }) {
  let quality = 'neutral';
  if (change !== null && change !== 0) {
    if (dir === 'lower') quality = change < 0 ? 'good' : 'bad';
    else if (dir === 'higher') quality = change > 0 ? 'good' : 'bad';
  }
  const color =
    quality === 'good' ? 'text-green-400' : quality === 'bad' ? 'text-red-400' : 'text-gray-400';
  const Icon = change === null || change === 0 ? Minus : change > 0 ? TrendingUp : TrendingDown;
  return (
    <div className="flex flex-col">
      <span className="text-[11px] uppercase tracking-wide text-gray-500">{label}</span>
      <span className={`flex items-center gap-1 text-sm font-semibold ${color}`}>
        <Icon className="w-3.5 h-3.5" />
        {change === null ? '—' : `${change > 0 ? '+' : ''}${change}${unit}`}
      </span>
    </div>
  );
}

function StatChip({ field, label, value, change }) {
  const q = changeQuality(field, change);
  const color = q === 'good' ? 'text-green-400' : q === 'bad' ? 'text-red-400' : 'text-gray-400';
  const Icon = change === null || change === 0 ? Minus : change > 0 ? TrendingUp : TrendingDown;
  return (
    <div className="flex items-center justify-between rounded-lg bg-gray-700/40 px-3 py-2">
      <span className="text-xs text-gray-400">{label}</span>
      <span className="flex items-center gap-1.5 text-sm text-gray-100 tabular-nums">
        {value != null ? `${value}` : '--'}
        {change !== null && change !== 0 && (
          <span className={`text-[11px] ${color}`}>
            {change > 0 ? '+' : ''}{change}
          </span>
        )}
        <Icon className={`w-3.5 h-3.5 ${color}`} />
      </span>
    </div>
  );
}

function TimelineCard({ measurement, previous, allMeasurements, settings, expanded, onToggle, onEdit, onDelete, deleting }) {
  const change = (field) => {
    const v = measurement[field];
    const p = previous?.[field];
    if (v == null || p == null) return null;
    return parseFloat((v - p).toFixed(1));
  };

  const bf = bodyFatFor(measurement, settings);
  const bfPrev = bodyFatFor(previous, settings);
  const bfChange = bf !== null && bfPrev !== null ? Math.round((bf - bfPrev) * 10) / 10 : null;

  // Count how many measurements were recorded this entry
  const recordedCount = Object.keys(allMeasurements).filter((k) => measurement[k] != null).length;

  return (
    <div className="rounded-xl border border-gray-700/70 bg-gray-800/40 overflow-hidden transition-colors hover:border-gray-600">
      {/* Header (click to expand) */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-4 p-4 text-left"
      >
        <ChevronDown
          className={`w-4 h-4 text-gray-500 shrink-0 transition-transform ${expanded ? 'rotate-0' : '-rotate-90'}`}
        />
        <div className="min-w-0">
          <div className="font-semibold text-gray-100">
            {format(parseISO(measurement.date), 'MMM d, yyyy')}
          </div>
          <div className="text-xs text-gray-500">
            {formatDistanceToNow(parseISO(measurement.date), { addSuffix: true })} · {recordedCount} metrics
          </div>
        </div>

        {/* Summary deltas vs previous */}
        <div className="ml-auto hidden sm:flex items-center gap-5 pr-2">
          <DeltaPill label="Waist" change={change('belly')} unit="" dir="lower" />
          <DeltaPill label="Chest" change={change('chest')} unit="" dir="higher" />
          {bfChange !== null && <DeltaPill label="Body Fat" change={bfChange} unit="%" dir="lower" />}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
          <button
            onClick={() => onEdit(measurement)}
            className="p-2 rounded-lg text-gray-400 hover:text-primary-400 hover:bg-gray-700"
            title="Edit"
          >
            <Edit2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(measurement.id)}
            disabled={deleting === measurement.id}
            className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-red-500/10 disabled:opacity-50"
            title="Delete"
          >
            {deleting === measurement.id ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
          </button>
        </div>
      </button>

      {/* Mobile summary row */}
      <div className="sm:hidden flex items-center gap-5 px-4 pb-3 -mt-1">
        <DeltaPill label="Waist" change={change('belly')} dir="lower" />
        <DeltaPill label="Chest" change={change('chest')} dir="higher" />
        {bfChange !== null && <DeltaPill label="BF" change={bfChange} unit="%" dir="lower" />}
      </div>

      {/* Expanded: all measurements grouped */}
      {expanded && (
        <div className="border-t border-gray-700/70 p-4 space-y-4">
          {GROUPS.map((g) => {
            const fields = Object.entries(allMeasurements).filter(([, c]) => c.group === g.id);
            return (
              <div key={g.id}>
                <div className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-2">
                  {g.label}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {fields.map(([key, cfg]) => (
                    <StatChip
                      key={key}
                      field={key}
                      label={cfg.label}
                      value={measurement[key]}
                      change={change(key)}
                    />
                  ))}
                </div>
              </div>
            );
          })}
          {measurement.notes && (
            <div className="text-sm text-gray-400 border-t border-gray-700/70 pt-3">
              <span className="text-gray-500">Notes: </span>
              {measurement.notes}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function HistorySection({ measurements, allMeasurements, settings, onEdit, onDelete, deleting, onAddNew }) {
  const [view, setView] = useState('timeline');
  const [currentPage, setCurrentPage] = useState(1);
  const [expandedIds, setExpandedIds] = useState(() => new Set());

  const totalPages = Math.ceil(measurements.length / ITEMS_PER_PAGE);
  const pageStart = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginated = measurements.slice(pageStart, pageStart + ITEMS_PER_PAGE);

  // Index by id for O(1) previous-entry lookup across pages
  const indexById = new Map(measurements.map((m, i) => [m.id, i]));

  const toggleExpand = (id) =>
    setExpandedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const allExpanded = paginated.length > 0 && paginated.every((m) => expandedIds.has(m.id));
  const toggleExpandAll = () =>
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (allExpanded) paginated.forEach((m) => next.delete(m.id));
      else paginated.forEach((m) => next.add(m.id));
      return next;
    });

  // --- Summary header stats (over the whole loaded range) ---
  const chronological = [...measurements].reverse();
  const oldest = chronological[0];
  const latest = chronological[chronological.length - 1];
  const netChange = (field) => {
    const withField = measurements.filter((m) => m[field] != null);
    if (withField.length < 2) return null;
    return parseFloat((withField[0][field] - withField[withField.length - 1][field]).toFixed(1));
  };
  const bfLatest = bodyFatFor(latest, settings);
  const bfOldest = bodyFatFor(oldest, settings);
  const bfNet = bfLatest !== null && bfOldest !== null ? Math.round((bfLatest - bfOldest) * 10) / 10 : null;
  const spanDays = oldest && latest ? differenceInCalendarDays(parseISO(latest.date), parseISO(oldest.date)) : 0;

  if (measurements.length === 0) {
    return (
      <Card title="Measurement History">
        <div className="p-8 text-center text-gray-500">
          <p>No measurements recorded yet</p>
          <Button variant="ghost" icon={Plus} onClick={onAddNew} className="mt-4">
            Add your first measurement
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary header */}
      <Card>
        <div className="flex flex-wrap items-center gap-x-8 gap-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-primary-500/15 flex items-center justify-center">
              <ListChecks className="w-5 h-5 text-primary-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-100 leading-none">{measurements.length}</div>
              <div className="text-xs text-gray-500 mt-1">entries</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gray-700/60 flex items-center justify-center">
              <CalendarDays className="w-5 h-5 text-gray-400" />
            </div>
            <div>
              <div className="text-sm font-semibold text-gray-100 leading-tight">
                {oldest && format(parseISO(oldest.date), 'MMM d, yyyy')} – {latest && format(parseISO(latest.date), 'MMM d, yyyy')}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">{spanDays} days tracked</div>
            </div>
          </div>
          <div className="flex items-center gap-6 ml-auto">
            <DeltaPill label="Waist net" change={netChange('belly')} dir="lower" />
            <DeltaPill label="Chest net" change={netChange('chest')} dir="higher" />
            {bfNet !== null && <DeltaPill label="Body Fat net" change={bfNet} unit="%" dir="lower" />}
          </div>
        </div>
      </Card>

      {/* Main history card */}
      <Card
        title="Measurement History"
        action={
          <div className="flex items-center gap-2">
            {view === 'timeline' && (
              <Button variant="outline" size="sm" onClick={toggleExpandAll}>
                {allExpanded ? 'Collapse all' : 'Expand all'}
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setView(view === 'timeline' ? 'table' : 'timeline')}
            >
              {view === 'timeline' ? (
                <><TableIcon className="w-4 h-4 mr-2" />Table</>
              ) : (
                <><LayoutGrid className="w-4 h-4 mr-2" />Timeline</>
              )}
            </Button>
          </div>
        }
        padding={false}
      >
        {view === 'timeline' ? (
          <div className="p-4 space-y-3">
            {paginated.map((m) => {
              const gi = indexById.get(m.id);
              const previous = gi != null ? measurements[gi + 1] : null;
              return (
                <TimelineCard
                  key={m.id}
                  measurement={m}
                  previous={previous}
                  allMeasurements={allMeasurements}
                  settings={settings}
                  expanded={expandedIds.has(m.id)}
                  onToggle={() => toggleExpand(m.id)}
                  onEdit={onEdit}
                  onDelete={onDelete}
                  deleting={deleting}
                />
              );
            })}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-700/50 border-b border-gray-700 sticky top-0">
                <tr>
                  {['Date', 'Neck', 'Chest', 'Belly', 'Biceps (L/R)', 'Triceps (L/R)', 'Forearm (L/R)', 'Thigh (L/R)', 'Calf (L/R)', 'Butt'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase whitespace-nowrap">{h}</th>
                  ))}
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {paginated.map((m) => (
                  <tr key={m.id} className="hover:bg-gray-700/30">
                    <td className="px-4 py-3 font-medium text-gray-100 whitespace-nowrap">
                      {format(parseISO(m.date), 'yyyy-MM-dd')}
                    </td>
                    <td className="px-4 py-3 text-gray-300">{m.neck ?? '--'}</td>
                    <td className="px-4 py-3 text-gray-300">{m.chest ?? '--'}</td>
                    <td className="px-4 py-3 text-gray-300">{m.belly ?? '--'}</td>
                    <td className="px-4 py-3 text-gray-300 whitespace-nowrap">{m.left_biceps ?? '--'}/{m.right_biceps ?? '--'}</td>
                    <td className="px-4 py-3 text-gray-300 whitespace-nowrap">{m.left_triceps ?? '--'}/{m.right_triceps ?? '--'}</td>
                    <td className="px-4 py-3 text-gray-300 whitespace-nowrap">{m.left_forearm ?? '--'}/{m.right_forearm ?? '--'}</td>
                    <td className="px-4 py-3 text-gray-300 whitespace-nowrap">{m.left_thigh ?? '--'}/{m.right_thigh ?? '--'}</td>
                    <td className="px-4 py-3 text-gray-300 whitespace-nowrap">{m.left_lower_leg ?? '--'}/{m.right_lower_leg ?? '--'}</td>
                    <td className="px-4 py-3 text-gray-300">{m.butt ?? '--'}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button onClick={() => onEdit(m)} className="p-1.5 rounded-lg hover:bg-gray-600 text-gray-400 hover:text-gray-200">
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => onDelete(m.id)}
                          disabled={deleting === m.id}
                          className="p-1.5 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400"
                        >
                          {deleting === m.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
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
            <button onClick={() => setCurrentPage(1)} disabled={currentPage === 1}
              className="px-3 py-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed">First</button>
            <button onClick={() => setCurrentPage((p) => Math.max(1, p - 1))} disabled={currentPage === 1}
              className="px-3 py-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"><ChevronLeft className="w-4 h-4" /></button>
            <span className="px-4 py-1 text-gray-300">Page {currentPage} of {totalPages}</span>
            <button onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}
              className="px-3 py-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"><ChevronRight className="w-4 h-4" /></button>
            <button onClick={() => setCurrentPage(totalPages)} disabled={currentPage === totalPages}
              className="px-3 py-1 rounded bg-gray-700 text-gray-300 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed">Last</button>
          </div>
        )}
      </Card>
    </div>
  );
}
