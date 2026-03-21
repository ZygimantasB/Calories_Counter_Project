import { Card } from './ui';

function getBmiCategory(bmi) {
  if (bmi == null) return { label: 'N/A', color: 'text-gray-400' };
  if (bmi < 18.5) return { label: 'Underweight', color: 'text-blue-400' };
  if (bmi < 25) return { label: 'Normal', color: 'text-green-400' };
  if (bmi < 30) return { label: 'Overweight', color: 'text-yellow-400' };
  return { label: 'Obese', color: 'text-red-400' };
}

export default function HealthMetrics({ stats }) {
  if (!stats) return null;

  const bmi = stats.bmi != null ? Number(stats.bmi) : null;
  const { label: categoryLabel, color: categoryColor } = getBmiCategory(bmi);

  return (
    <Card title="Health Metrics">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-700/50 rounded-xl p-4 text-center">
          <div className="text-4xl font-bold text-gray-100 mb-1">
            {bmi != null ? bmi.toFixed(1) : '--'}
          </div>
          <div className="text-sm text-gray-400">BMI</div>
        </div>
        <div className="bg-gray-700/50 rounded-xl p-4 text-center">
          <div className={`text-2xl font-bold ${categoryColor} mb-1`}>
            {categoryLabel}
          </div>
          <div className="text-sm text-gray-400">BMI Category</div>
        </div>
      </div>
    </Card>
  );
}
