import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from 'recharts';
import { Card } from './ui';

// Macro colors (match the Macronutrient Trends chart convention)
const MACROS = [
  { key: 'protein', label: 'Protein', color: '#ef4444' }, // red, bottom band
  { key: 'carbs', label: 'Carbs', color: '#3b82f6' }, // blue, middle
  { key: 'fat', label: 'Fat', color: '#eab308' }, // yellow, top
];

function MacroTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;

  const row = payload[0].payload;
  const total = MACROS.reduce((sum, m) => sum + (row[m.key] || 0), 0);

  return (
    <div
      style={{
        backgroundColor: '#1f2937',
        border: '1px solid #374151',
        borderRadius: '8px',
        padding: '8px 12px',
        fontSize: '12px',
        color: '#e5e7eb',
      }}
    >
      <div style={{ marginBottom: 4, fontWeight: 600 }}>{label}</div>
      {MACROS.map((m) => (
        <div key={m.key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: m.color,
              display: 'inline-block',
            }}
          />
          <span>
            {m.label}: {Math.round(row[m.key] || 0)} kcal
            {row[`${m.key}_g`] !== undefined ? ` (${row[`${m.key}_g`]} g)` : ''}
          </span>
        </div>
      ))}
      <div style={{ marginTop: 4, borderTop: '1px solid #374151', paddingTop: 4 }}>
        Total: {Math.round(total)} kcal
      </div>
    </div>
  );
}

export default function CalorieTrendChart({ data, target }) {
  if (!data || !data.labels || data.labels.length === 0) return null;

  const chartData = data.labels.map((label, i) => ({
    date: label.slice(5),
    protein: data.protein_calories?.[i] ?? 0,
    carbs: data.carbs_calories?.[i] ?? 0,
    fat: data.fat_calories?.[i] ?? 0,
    protein_g: data.protein_grams?.[i],
    carbs_g: data.carbs_grams?.[i],
    fat_g: data.fat_grams?.[i],
  }));

  return (
    <Card title="Calorie Intake Trend">
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            {MACROS.map((m) => (
              <linearGradient key={m.key} id={`colorCal-${m.key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={m.color} stopOpacity={0.5} />
                <stop offset="95%" stopColor={m.color} stopOpacity={0.05} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
          <YAxis stroke="#9ca3af" fontSize={12} />
          <Tooltip content={<MacroTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {target && (
            <ReferenceLine
              y={target}
              stroke="#22c55e"
              strokeDasharray="5 5"
              label={{ value: 'Target', fill: '#22c55e', fontSize: 12 }}
            />
          )}
          {MACROS.map((m) => (
            <Area
              key={m.key}
              type="monotone"
              dataKey={m.key}
              name={m.label}
              stackId="cal"
              stroke={m.color}
              fill={`url(#colorCal-${m.key})`}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
