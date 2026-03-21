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

export default function CalorieTrendChart({ data, target }) {
  if (!data || data.length === 0) return null;

  const chartData = data.labels.map((label, i) => ({
    date: label.slice(5),
    calories: data.data[i],
  }));

  return (
    <Card title="Calorie Intake Trend">
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="colorCal" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
          <YAxis stroke="#9ca3af" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
          />
          {target && (
            <ReferenceLine
              y={target}
              stroke="#22c55e"
              strokeDasharray="5 5"
              label={{ value: 'Target', fill: '#22c55e', fontSize: 12 }}
            />
          )}
          <Area
            type="monotone"
            dataKey="calories"
            stroke="#0ea5e9"
            fill="url(#colorCal)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
