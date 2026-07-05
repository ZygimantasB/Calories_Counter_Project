import { format, parseISO } from 'date-fns';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
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

  // Cumulative change from the first weigh-in in the window (baseline = 0).
  // entries are newest-first, so reverse for chronological order.
  const chronological = [...entries].reverse();
  const baseline = chronological.length > 0 ? chronological[0].weight : 0;
  const cumData = chronological.map((e) => ({
    date: format(parseISO(e.recorded_at), 'MMM dd'),
    weight: e.weight,
    cum: parseFloat((e.weight - baseline).toFixed(2)),
  }));

  // Split-color offset: red above baseline (net gain), green below (net loss).
  const cumValues = cumData.map((d) => d.cum);
  const cumMax = Math.max(0, ...cumValues);
  const cumMin = Math.min(0, ...cumValues);
  const gradientOffset =
    cumMax <= 0 ? 0 : cumMin >= 0 ? 1 : cumMax / (cumMax - cumMin);

  const CumTooltip = ({ active, payload }) => {
    if (!active || !payload || payload.length === 0) return null;
    const d = payload[0].payload;
    const gained = d.cum > 0;
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
        <div style={{ fontWeight: 600, marginBottom: 2 }}>{d.date}</div>
        <div>{Number(d.weight).toFixed(1)} kg</div>
        <div style={{ color: gained ? '#f87171' : '#4ade80' }}>
          {gained ? '+' : ''}{d.cum.toFixed(2)} kg since start
        </div>
      </div>
    );
  };

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

      {/* Cumulative weight change area chart */}
      <div>
        <h4 className="text-sm font-medium text-gray-400 mb-3">
          Cumulative Weight Change{' '}
          <span className="text-gray-500 font-normal">(net kg since start)</span>
        </h4>
        {cumData.length > 1 ? (
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={cumData}>
              <defs>
                <linearGradient id="cumFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset={gradientOffset} stopColor="#ef4444" stopOpacity={0.5} />
                  <stop offset={gradientOffset} stopColor="#22c55e" stopOpacity={0.5} />
                </linearGradient>
                <linearGradient id="cumStroke" x1="0" y1="0" x2="0" y2="1">
                  <stop offset={gradientOffset} stopColor="#ef4444" stopOpacity={1} />
                  <stop offset={gradientOffset} stopColor="#22c55e" stopOpacity={1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
              <YAxis
                stroke="#9ca3af"
                fontSize={12}
                tickFormatter={(v) => `${v > 0 ? '+' : ''}${v}`}
              />
              <Tooltip content={<CumTooltip />} />
              <ReferenceLine y={0} stroke="#6b7280" strokeWidth={1.5} />
              <Area
                type="monotone"
                dataKey="cum"
                stroke="url(#cumStroke)"
                strokeWidth={2}
                fill="url(#cumFill)"
                baseValue={0}
              />
            </AreaChart>
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
