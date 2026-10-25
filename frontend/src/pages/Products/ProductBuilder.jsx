import { useEffect, useMemo, useRef, useState } from 'react';
import { Plus, Trash2, Search } from 'lucide-react';
import { Button } from '../../components/ui';
import { foodApi } from '../../api';
import { displayKcal, displayMacro } from '../../utils/format';
import { MACROS, ingredientTotals, perServing } from './productMath';

const MACRO_LABELS = { calories: 'Calories', protein: 'Protein', fat: 'Fat', carbohydrates: 'Carbs' };
const inputClass = 'w-full px-2 py-1.5 rounded-lg bg-gray-700 border border-gray-600 text-gray-100 text-sm focus:outline-none focus:border-primary-500';

let rowKey = 0;
const newRow = (ing = {}) => ({
  key: ++rowKey,
  name: ing.name ?? '',
  calories: String(ing.calories ?? 0),
  protein: String(ing.protein ?? 0),
  fat: String(ing.fat ?? 0),
  carbohydrates: String(ing.carbohydrates ?? 0),
  quantity: String(ing.quantity ?? 1),
});

function MacroLine({ label, values, testId }) {
  return (
    <div data-testid={testId}>
      <span className="text-gray-400">{label}: </span>
      {displayKcal(values.calories)} kcal · P {displayMacro(values.protein)}g · F {displayMacro(values.fat)}g · C {displayMacro(values.carbohydrates)}g
    </div>
  );
}

export default function ProductBuilder({ initial, onSave, onCancel }) {
  const [name, setName] = useState(initial?.name ?? '');
  const [servingsYield, setServingsYield] = useState(String(initial?.servings_yield ?? 1));
  const [rows, setRows] = useState(() => (initial?.ingredients ?? []).map(newRow));
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const searchTimer = useRef(null);

  const totals = useMemo(() => ingredientTotals(rows), [rows]);
  const serving = useMemo(() => perServing(totals, servingsYield), [totals, servingsYield]);

  useEffect(() => () => clearTimeout(searchTimer.current), []);

  const handleSearch = (value) => {
    setQuery(value);
    clearTimeout(searchTimer.current);
    if (value.trim().length < 2) {
      setResults([]);
      return;
    }
    searchTimer.current = setTimeout(async () => {
      try {
        const response = await foodApi.searchAllFoods(value.trim(), 8);
        setResults((response.results || []).filter((food) => !food.is_product));
      } catch (err) {
        console.error('Error searching foods:', err);
      }
    }, 250);
  };

  const addFromSearch = (food) => {
    setRows((current) => [...current, newRow({ ...food, carbohydrates: food.carbs, quantity: 1 })]);
    setQuery('');
    setResults([]);
  };

  const updateRow = (key, field, value) =>
    setRows((current) => current.map((row) => (row.key === key ? { ...row, [field]: value } : row)));

  const removeRow = (key) => setRows((current) => current.filter((row) => row.key !== key));

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!name.trim()) return setError('Name is required');
    if (!rows.length) return setError('Add at least one ingredient');
    if (rows.some((row) => !row.name.trim())) return setError('Every ingredient needs a name');
    if (rows.some((row) => !(Number(row.quantity) > 0))) return setError('Quantity must be greater than 0');
    if (!(Number(servingsYield) > 0)) return setError('Servings must be greater than 0');

    setError(null);
    setSaving(true);
    try {
      await onSave({
        name: name.trim(),
        servings_yield: Number(servingsYield),
        ingredients: rows.map((row) => ({
          name: row.name.trim(),
          ...Object.fromEntries(MACROS.map((m) => [m, Number(row[m]) || 0])),
          quantity: Number(row.quantity),
        })),
      });
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Failed to save product');
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <label className="md:col-span-2 text-sm text-gray-300">
          Product name
          <input className={`${inputClass} mt-1`} value={name} maxLength={200}
            onChange={(e) => setName(e.target.value)} placeholder="Chicken tortilla" />
        </label>
        <label className="text-sm text-gray-300">
          Makes N servings
          <input className={`${inputClass} mt-1`} type="number" min="0.01" max="100" step="0.5"
            value={servingsYield} onChange={(e) => setServingsYield(e.target.value)} />
        </label>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
        <input aria-label="Search your foods" className={`${inputClass} pl-9`} value={query}
          onChange={(e) => handleSearch(e.target.value)} placeholder="Add ingredient from your foods…" />
        {results.length > 0 && (
          <div className="absolute z-10 mt-1 w-full max-h-56 overflow-y-auto rounded-lg border border-gray-600 bg-gray-800 shadow-xl">
            {results.map((food) => (
              <button key={food.name} type="button" onClick={() => addFromSearch(food)}
                className="block w-full text-left px-3 py-2 text-sm text-gray-200 hover:bg-gray-700">
                {food.name} — {displayKcal(food.calories)} kcal
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="space-y-2">
        {rows.map((row) => (
          <div key={row.key} data-testid="ingredient-row" className="grid grid-cols-12 gap-2 items-center">
            <input aria-label="Ingredient name" className={`${inputClass} col-span-12 md:col-span-4`}
              value={row.name} maxLength={200} placeholder="Ingredient"
              onChange={(e) => updateRow(row.key, 'name', e.target.value)} />
            {MACROS.map((m) => (
              <input key={m} aria-label={MACRO_LABELS[m]} title={MACRO_LABELS[m]} type="number" min="0" step="0.1"
                className={`${inputClass} col-span-3 md:col-span-1`} value={row[m]}
                onChange={(e) => updateRow(row.key, m, e.target.value)} />
            ))}
            <input aria-label="Quantity" title="Quantity (servings)" type="number" min="0.01" step="0.25"
              className={`${inputClass} col-span-8 md:col-span-3`} value={row.quantity}
              onChange={(e) => updateRow(row.key, 'quantity', e.target.value)} />
            <button type="button" aria-label="Remove ingredient" onClick={() => removeRow(row.key)}
              className="col-span-4 md:col-span-1 text-red-400 hover:text-red-300 flex justify-center">
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
        <Button type="button" variant="ghost" size="sm" icon={Plus} onClick={() => setRows((r) => [...r, newRow()])}>
          Add manual ingredient
        </Button>
      </div>

      <div className="rounded-lg bg-gray-700/50 p-3 text-sm text-gray-200 space-y-1">
        <MacroLine label="Whole batch" values={totals} testId="batch-totals" />
        <MacroLine label="Per serving" values={serving} testId="per-serving" />
      </div>

      {error && <div role="alert" className="text-sm text-red-400">{error}</div>}

      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={saving}>Save product</Button>
      </div>
    </form>
  );
}
