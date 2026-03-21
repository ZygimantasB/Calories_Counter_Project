import { format, parseISO } from 'date-fns';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Card } from './ui';

export default function WeightChangeAnalysis({ stats, entries }) {
  if (!stats || !entries) return null;

  const changeRate = stats.change_rate ?? 0;

  // Determine trend label and color
  let trendLabel = 'Stable';
  let trendColor = 'text-gray-400';
  if (changeRate < -0.01) {
    trendLabel = 'Losing';
    trendColor = 'text-green-400';
  } else if (changeRate > 0.01) {
    trendLabel = 'Gaining';
    trendColor = 'text-red-400';
  }

  // Compute day-to-day changes from entries (entries are newest-first, reverse for chronological)
  const chronological = [...entries].reverse();
  const changeData = [];
  for (let i = 1; i < chronological.length; i++) {
    const change = parseFloat(
      (chronological[i].weight - chronological[i - 1].weight).toFixed(2)
    );
    changeData.push({
      date: format(parseISO(chronological[i].recorded_at), 'MMM dd'),
      change,
    });
  }

  return (
    <Card title="Weight Change Analysis" subtitle="Last 90 Days">
      {/* Stat cards row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-700/50 rounded-xl p-4 text-center">
          <div className={`text-2xl font-bold ${changeRate <= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {changeRate > 0 ? '+' : ''}{changeRate.toFixed(2)} kg/week
          </div>
          <div className="text-sm text-gray-400 mt-1">Change Rate</div>
        </div>
        <div className="bg-gray-700/50 rounded-xl p-4 text-center">
          <div className={`text-2xl font-bold ${trendColor}`}>
            {trendLabel}
          </div>
          <div className="text-sm text-gray-400 mt-1">Trend</div>
        </div>
        <div className="bg-gray-700/50 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-gray-100">
            {stats.consistency != null ? Number(stats.consistency).toFixed(2) : '--'} kg
          </div>
          <div className="text-sm text-gray-400 mt-1">Consistency (SD)</div>
        </div>
      </div>

      {/* Weight Changes bar chart */}
      <div>
        <h4 className="text-sm font-medium text-gray-400 mb-3">
          Weight Changes Between Measurements
        </h4>
        {changeData.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={changeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
              <YAxis stroke="#9ca3af" fontSize={12} tickFormatter={(v) => `${v > 0 ? '+' : ''}${v}`} />
              <Tooltip
                formatter={(value) => [`${value > 0 ? '+' : ''}${value} kg`, 'Change']}
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                }}
              />
              <Bar dataKey="change">
                {changeData.map((entry, i) => (
                  <Cell key={i} fill={entry.change > 0 ? '#ef4444' : '#22c55e'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-40 flex items-center justify-center text-gray-500 text-sm">
            Not enough data to show changes
          </div>
        )}
      </div>
    </Card>
  );
}
