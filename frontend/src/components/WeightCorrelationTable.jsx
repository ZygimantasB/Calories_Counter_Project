import { useState, useEffect } from 'react';
import { Card } from './ui';
import apiClient from '../api/client';

export default function WeightCorrelationTable({ days = 90 }) {
  const [data, setData] = useState(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setPage(1);
  }, [days]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await apiClient.get('/api/weight-calories-correlation/', {
          params: { days, page, per_page: 10 }
        });
        setData(response.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [days, page]);

  const totalPages = data?.pagination?.total_pages ?? 1;
  const rows = data?.correlation_data ?? [];

  return (
    <Card title="Weight Changes vs. Calorie Intake" subtitle="Correlation between calorie intake and weight changes between consecutive measurements">
      {loading ? (
        <div className="flex items-center justify-center py-10">
          <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : rows.length === 0 ? (
        <div className="py-10 text-center text-gray-500">
          Not enough weight entries to show correlation data. Log at least two weight entries.
        </div>
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">Period</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">Weight Change</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">Days</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">Total Calories</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((item, i) => (
                  <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="py-3 px-4 text-gray-300">{item.start_date} to {item.end_date}</td>
                    <td className={`py-3 px-4 font-bold ${item.weight_change > 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {item.weight_change > 0 ? '+' : ''}{item.weight_change.toFixed(2)} kg
                    </td>
                    <td className="py-3 px-4 text-gray-300">{item.days_between} {item.days_between === 1 ? 'day' : 'days'}</td>
                    <td className="py-3 px-4 text-gray-300">{Math.round(item.total_calories).toLocaleString()} kcal</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-4">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
                className="px-3 py-1 rounded bg-gray-700 text-gray-300 disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-3 py-1 text-gray-400">Page {page} of {totalPages}</span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
                className="px-3 py-1 rounded bg-gray-700 text-gray-300 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </Card>
  );
}
