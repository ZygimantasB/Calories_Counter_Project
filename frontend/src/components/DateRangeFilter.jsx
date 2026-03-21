import { useState } from 'react';
import { format, startOfWeek, endOfWeek, startOfMonth, endOfMonth } from 'date-fns';

const presets = [
  { label: 'Today', filter: { type: 'today' } },
  { label: 'This Week', filter: { type: 'range_name', name: 'week' } },
  { label: 'This Month', filter: { type: 'range_name', name: 'month' } },
  { label: '7 Days', filter: { type: 'days', days: 7 } },
  { label: '30 Days', filter: { type: 'days', days: 30 } },
  { label: '90 Days', filter: { type: 'days', days: 90 } },
  { label: '6 Months', filter: { type: 'days', days: 180 } },
  { label: '1 Year', filter: { type: 'days', days: 365 } },
  { label: 'All', filter: { type: 'days', days: 'all' } },
];

function isPresetActive(value, preset) {
  const f = preset.filter;
  if (f.type !== value.type) return false;
  if (f.type === 'today') return true;
  if (f.type === 'range_name') return f.name === value.name;
  if (f.type === 'days') return f.days === value.days;
  return false;
}

export default function DateRangeFilter({ value, onChange, showDatePicker = true }) {
  const today = format(new Date(), 'yyyy-MM-dd');
  const [customStart, setCustomStart] = useState(value?.startDate || today);
  const [customEnd, setCustomEnd] = useState(value?.endDate || today);

  const handlePreset = (filter) => {
    onChange(filter);
  };

  const handleApplyCustomRange = () => {
    if (customStart && customEnd) {
      onChange({ type: 'range', startDate: customStart, endDate: customEnd });
    }
  };

  const handleDatePickerChange = (e) => {
    if (e.target.value) {
      onChange({ type: 'date', date: e.target.value });
    }
  };

  const isCustomRangeActive = value?.type === 'range';
  const isDateActive = value?.type === 'date';

  return (
    <div className="space-y-3">
      {/* Preset Buttons */}
      <div className="flex flex-wrap gap-1.5">
        {presets.map((preset) => {
          const active = isPresetActive(value, preset);
          return (
            <button
              key={preset.label}
              onClick={() => handlePreset(preset.filter)}
              className={`px-3 py-1.5 text-xs font-medium rounded-full transition-all ${
                active
                  ? 'bg-primary-500 text-white shadow-sm'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {preset.label}
            </button>
          );
        })}
      </div>

      {/* Custom Range + Single Date Picker */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Custom Date Range */}
        <div
          className={`flex items-center gap-2 p-2 rounded-lg border transition-colors ${
            isCustomRangeActive
              ? 'border-primary-500 bg-primary-500/10'
              : 'border-gray-600 bg-gray-700/50'
          }`}
        >
          <span className="text-xs text-gray-400 whitespace-nowrap">Range:</span>
          <input
            type="date"
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
            className="text-xs bg-transparent text-gray-200 border-none outline-none cursor-pointer"
          />
          <span className="text-xs text-gray-500">–</span>
          <input
            type="date"
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
            className="text-xs bg-transparent text-gray-200 border-none outline-none cursor-pointer"
          />
          <button
            onClick={handleApplyCustomRange}
            className="px-2 py-0.5 text-xs font-medium rounded bg-primary-500 text-white hover:bg-primary-600 transition-colors"
          >
            Apply
          </button>
        </div>

        {/* Single Date Picker */}
        {showDatePicker && (
          <div
            className={`flex items-center gap-2 p-2 rounded-lg border transition-colors ${
              isDateActive
                ? 'border-primary-500 bg-primary-500/10'
                : 'border-gray-600 bg-gray-700/50'
            }`}
          >
            <span className="text-xs text-gray-400 whitespace-nowrap">Date:</span>
            <input
              type="date"
              value={value?.type === 'date' ? value.date : today}
              onChange={handleDatePickerChange}
              className="text-xs bg-transparent text-gray-200 border-none outline-none cursor-pointer"
            />
          </div>
        )}
      </div>
    </div>
  );
}
