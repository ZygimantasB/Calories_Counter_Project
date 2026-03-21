import { Card } from './ui';

export default function WeightProjections({ stats }) {
  if (!stats) return null;

  const projectedWeight = stats.projected_weight != null ? Number(stats.projected_weight).toFixed(1) : '--';
  const weeksToGoal = stats.weeks_to_goal && Number(stats.weeks_to_goal) > 0
    ? `${Number(stats.weeks_to_goal).toFixed(1)} weeks`
    : 'N/A';
  const goalDate = stats.goal_date || 'N/A';

  return (
    <Card title="Weight Projections">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-700/50 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-gray-100 mb-1">
            {projectedWeight !== '--' ? `${projectedWeight} kg` : '--'}
          </div>
          <div className="text-sm text-gray-400">Projected (4 weeks)</div>
        </div>
        <div className="bg-gray-700/50 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-blue-400 mb-1">
            {weeksToGoal}
          </div>
          <div className="text-sm text-gray-400">Time to Goal</div>
        </div>
        <div className="bg-gray-700/50 rounded-xl p-4 text-center">
          <div className="text-2xl font-bold text-purple-400 mb-1">
            {goalDate}
          </div>
          <div className="text-sm text-gray-400">Goal Date</div>
        </div>
      </div>
    </Card>
  );
}
