import { useState, useEffect, useCallback } from 'react';
import { BookMarked, Save, Play, Trash2, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import Card from './ui/Card';
import { mealTemplatesApi } from '../api/mealTemplates';
import { format } from 'date-fns';

export default function MealTemplates({ onApplied }) {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [templateName, setTemplateName] = useState('');
  const [saveLoading, setSaveLoading] = useState(false);
  const [applyingId, setApplyingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const [message, setMessage] = useState(null); // { type: 'success'|'error', text: string }

  const fetchTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const data = await mealTemplatesApi.list();
      setTemplates(data.templates || []);
    } catch {
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3500);
  };

  const handleSave = async () => {
    const name = templateName.trim();
    if (!name) return;
    setSaveLoading(true);
    try {
      const result = await mealTemplatesApi.save(name);
      if (result.success) {
        showMessage('success', `Saved "${name}" with ${result.items_count} item${result.items_count !== 1 ? 's' : ''}`);
        setTemplateName('');
        await fetchTemplates();
      } else {
        showMessage('error', result.message || 'Failed to save template');
      }
    } catch (err) {
      const msg =
        err?.response?.data?.message ||
        (err?.response?.status === 404
          ? 'No food items found for today'
          : 'Failed to save template');
      showMessage('error', msg);
    } finally {
      setSaveLoading(false);
    }
  };

  const handleApply = async (template) => {
    setApplyingId(template.id);
    try {
      const result = await mealTemplatesApi.apply(template.id);
      if (result.success) {
        showMessage('success', `Applied "${template.name}" — logged ${result.items_logged} item${result.items_logged !== 1 ? 's' : ''} to today`);
        if (onApplied) onApplied();
      } else {
        showMessage('error', 'Failed to apply template');
      }
    } catch {
      showMessage('error', 'Failed to apply template');
    } finally {
      setApplyingId(null);
    }
  };

  const handleDelete = async (template) => {
    setDeletingId(template.id);
    try {
      await mealTemplatesApi.delete(template.id);
      setTemplates((prev) => prev.filter((t) => t.id !== template.id));
      showMessage('success', `Deleted "${template.name}"`);
    } catch {
      showMessage('error', 'Failed to delete template');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <Card title="Meal Templates" subtitle="Save today's foods and re-apply them on any day">
      {/* Save Today Section */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-4">
        <div className="flex-1">
          <label className="block text-sm text-gray-400 mb-1">Template name</label>
          <input
            type="text"
            value={templateName}
            onChange={(e) => setTemplateName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            placeholder="e.g. High Protein Day"
            className="w-full px-3 py-2 rounded-lg border border-gray-600 bg-gray-700 text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        <div className="sm:mt-6">
          <button
            onClick={handleSave}
            disabled={saveLoading || !templateName.trim()}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition-colors"
          >
            {saveLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {saveLoading ? 'Saving…' : 'Save Today'}
          </button>
        </div>
      </div>

      {/* Status Message */}
      {message && (
        <div
          className={`flex items-center gap-2 text-sm mb-4 ${
            message.type === 'success' ? 'text-green-400' : 'text-red-400'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle className="w-4 h-4 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
          )}
          {message.text}
        </div>
      )}

      {/* Template List */}
      {loading ? (
        <div className="flex items-center justify-center py-6 text-gray-500">
          <Loader2 className="w-5 h-5 animate-spin mr-2" />
          Loading templates…
        </div>
      ) : templates.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-6 text-gray-500 gap-2">
          <BookMarked className="w-8 h-8 opacity-40" />
          <p className="text-sm">No templates saved yet</p>
        </div>
      ) : (
        <div className="divide-y divide-gray-700">
          {templates.map((template) => (
            <div
              key={template.id}
              className="py-3 flex items-center justify-between gap-3 first:pt-0 last:pb-0"
            >
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-100 truncate">{template.name}</p>
                <p className="text-xs text-gray-500 mt-0.5">
                  {template.items_count} item{template.items_count !== 1 ? 's' : ''} &middot;{' '}
                  {Math.round(template.total_calories)} kcal &middot;{' '}
                  {format(new Date(template.created_at), 'MMM d, yyyy')}
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => handleApply(template)}
                  disabled={applyingId === template.id}
                  title="Apply to today"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-green-700/30 hover:bg-green-700/50 text-green-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {applyingId === template.id ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Play className="w-3.5 h-3.5" />
                  )}
                  Apply
                </button>
                <button
                  onClick={() => handleDelete(template)}
                  disabled={deletingId === template.id}
                  title="Delete template"
                  className="flex items-center justify-center p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-400/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {deletingId === template.id ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
