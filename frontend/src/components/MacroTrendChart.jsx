import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card } from './ui';

export default function MacroTrendChart({ data }) {
  if (!data || data.length === 0) return null;

  const chartData = data.labels.map((label, i) => ({
    date: label.slice(5),
    protein: data.protein?.[i] ?? 0,
    carbs: data.carbs?.[i] ?? 0,
    fat: data.fat?.[i] ?? 0,
  }));

  return (
    <Card title="Macro Intake Trend">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
          <YAxis stroke="#9ca3af" fontSize={12} unit="g" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            formatter={(value, name) => [`${value}g`, name.charAt(0).toUpperCase() + name.slice(1)]}
          />
          <Legend
            wrapperStyle={{ fontSize: '12px', color: '#9ca3af' }}
            formatter={(value) => value.charAt(0).toUpperCase() + value.slice(1)}
          />
          <Line
            type="monotone"
            dataKey="protein"
            stroke="#ef4444"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="carbs"
            stroke="#f97316"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="fat"
            stroke="#eab308"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}
