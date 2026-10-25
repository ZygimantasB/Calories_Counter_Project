import { useCallback, useEffect, useState } from 'react';
import { format } from 'date-fns';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { Card, Button } from '../../components/ui';
import { productsApi } from '../../api/products';
import { displayKcal, displayMacro } from '../../utils/format';
import ProductBuilder from './ProductBuilder';

function ProductCard({ product, onEdit, onDeleted, onMessage }) {
  const [servings, setServings] = useState('1');
  const [confirming, setConfirming] = useState(false);
  const ps = product.per_serving;

  const handleLog = async () => {
    try {
      await productsApi.log(product.id, Number(servings), format(new Date(), 'yyyy-MM-dd'));
      onMessage({ ok: true, text: `Logged ${servings} × ${product.name}` });
    } catch (err) {
      onMessage({ ok: false, text: err.response?.data?.error || err.message });
    }
  };

  const handleDelete = async () => {
    try {
      await productsApi.delete(product.id);
      onDeleted();
    } catch (err) {
      onMessage({ ok: false, text: err.response?.data?.error || err.message });
    }
  };

  return (
    <Card hover>
      <div className="space-y-3">
        <div>
          <h2 className="text-base font-semibold text-gray-100">{product.name}</h2>
          <p className="text-xs text-gray-500">
            {product.ingredient_count} ingredients · makes {product.servings_yield} serving(s)
          </p>
        </div>
        <p className="text-sm text-gray-300">
          {displayKcal(ps.calories)} kcal · P {displayMacro(ps.protein)}g · F {displayMacro(ps.fat)}g · C {displayMacro(ps.carbohydrates)}g
          <span className="text-gray-500"> per serving</span>
        </p>
        <div className="flex items-center gap-2 flex-wrap">
          <input aria-label={`Servings of ${product.name}`} type="number" min="0.5" max="100" step="0.5"
            value={servings} onChange={(e) => setServings(e.target.value)}
            className="w-20 px-2 py-1.5 rounded-lg bg-gray-700 border border-gray-600 text-gray-100 text-sm" />
          <Button size="sm" onClick={handleLog} disabled={!(Number(servings) > 0)}>Log</Button>
          <div className="ml-auto flex gap-1">
            <Button size="sm" variant="ghost" icon={Pencil} onClick={() => onEdit(product)}>Edit</Button>
            {confirming ? (
              <>
                <Button size="sm" variant="danger" onClick={handleDelete} aria-label="Confirm delete">Yes, delete</Button>
                <Button size="sm" variant="ghost" onClick={() => setConfirming(false)}>Cancel</Button>
              </>
            ) : (
              <Button size="sm" variant="ghost" icon={Trash2} onClick={() => setConfirming(true)}>Delete</Button>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

export default function Products() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(undefined); // undefined = closed, null = new, object = edit
  const [message, setMessage] = useState(null);

  const load = useCallback(async () => {
    try {
      const data = await productsApi.list();
      setProducts(data.products || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load products');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = async (payload) => {
    if (editing) await productsApi.update(editing.id, payload);
    else await productsApi.create(payload);
    setEditing(undefined);
    setMessage({ ok: true, text: 'Product saved' });
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">My Products</h1>
          <p className="text-sm text-gray-400">Combine several foods into one product and log it as a single entry.</p>
        </div>
        {editing === undefined && (
          <Button icon={Plus} onClick={() => setEditing(null)}>New product</Button>
        )}
      </div>

      {message && (
        <div role="status" className={`text-sm ${message.ok ? 'text-green-400' : 'text-red-400'}`}>{message.text}</div>
      )}

      {editing !== undefined && (
        <Card title={editing ? `Edit ${editing.name}` : 'New product'}>
          <ProductBuilder key={editing?.id ?? 'new'} initial={editing} onSave={handleSave}
            onCancel={() => setEditing(undefined)} />
        </Card>
      )}

      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : error ? (
        <p className="text-red-400">{error}</p>
      ) : products.length === 0 ? (
        <p className="text-gray-500">No products yet — click “New product” to build one.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {products.map((product) => (
            <ProductCard key={product.id} product={product} onEdit={setEditing}
              onDeleted={load} onMessage={setMessage} />
          ))}
        </div>
      )}
    </div>
  );
}
