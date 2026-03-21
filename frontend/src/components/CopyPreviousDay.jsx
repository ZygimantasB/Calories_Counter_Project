import { useState } from 'react';
import { Copy, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import Card from './ui/Card';
import { foodApi } from '../api';
import { format, subDays } from 'date-fns';

export default function CopyPreviousDay({ onCopied }) {
  const defaultDate = format(subDays(new Date(), 1), 'yyyy-MM-dd');
  const [sourceDate, setSourceDate] = useState(defaultDate);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);

  const handleCopy = async () => {
    if (!sourceDate) return;
    setLoading(true);
    setSuccess(null);
    setError(null);
    try {
      const result = await foodApi.copyDayFoods(sourceDate);
      setSuccess(`Copied ${result.copied_count} item${result.copied_count !== 1 ? 's' : ''} to today`);
      if (onCopied) onCopied();
    } catch (err) {
      const msg =
        err?.response?.data?.message ||
        (err?.response?.status === 404
          ? 'No food items found for that date'
          : 'Failed to copy items');
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Copy a Previous Day">
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
        <div className="flex-1">
          <label className="block text-sm text-gray-400 mb-1">Source date</label>
          <input
            type="date"
            value={sourceDate}
            max={format(subDays(new Date(), 1), 'yyyy-MM-dd')}
            onChange={(e) => {
              setSourceDate(e.target.value);
              setSuccess(null);
              setError(null);
            }}
            className="w-full px-3 py-2 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div className="sm:mt-6">
          <button
            onClick={handleCopy}
            disabled={loading || !sourceDate}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition-colors"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
            {loading ? 'Copying…' : 'Copy to Today'}
          </button>
        </div>
      </div>

      {success && (
        <div className="mt-3 flex items-center gap-2 text-sm text-green-400">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          {success}
        </div>
      )}

      {error && (
        <div className="mt-3 flex items-center gap-2 text-sm text-red-400">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}
    </Card>
  );
}
