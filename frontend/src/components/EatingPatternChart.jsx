import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Card } from './ui';

const HOUR_LABELS = [
  '12a', '1a', '2a', '3a', '4a', '5a', '6a', '7a',
  '8a', '9a', '10a', '11a', '12p', '1p', '2p', '3p',
  '4p', '5p', '6p', '7p', '8p', '9p', '10p', '11p',
];

export default function EatingPatternChart({ data }) {
  if (!data) return null;

  const chartData = (data.hours || []).map((hour, i) => ({
    hour: HOUR_LABELS[hour] || `${hour}:00`,
    calories: data.calories?.[i] ?? 0,
  }));

  const hasData = chartData.some((d) => d.calories > 0);
  if (!hasData) return null;

  return (
    <Card title="Eating Pattern by Hour" subtitle="Calorie distribution across the day">
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} barSize={14}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
          <XAxis dataKey="hour" stroke="#9ca3af" fontSize={11} />
          <YAxis stroke="#9ca3af" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            formatter={(value) => [`${value} kcal`, 'Calories']}
          />
          <Bar dataKey="calories" fill="#0ea5e9" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}
