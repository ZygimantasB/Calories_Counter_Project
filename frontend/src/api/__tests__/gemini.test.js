import { describe, it, expect, vi, afterEach } from 'vitest';
import { getGeminiNutrition } from '../gemini';

afterEach(() => { vi.restoreAllMocks(); });

describe('getGeminiNutrition', () => {
  it('normalises Django { success, data:{ product_name, carbohydrates } } to flat shape', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, data: { product_name: 'Chicken breast', calories: 330, fat: 7.2, carbohydrates: 0, protein: 62 } }),
    });
    const r = await getGeminiNutrition('200g chicken breast');
    expect(r).toMatchObject({ success: true, name: 'Chicken breast', calories: 330, protein: 62, carbs: 0, fat: 7.2 });
    // Posts food_name (not ?q=) — the bug that broke the old React lookup.
    const [, opts] = global.fetch.mock.calls[0];
    expect(opts.method).toBe('POST');
    expect(JSON.parse(opts.body)).toEqual({ food_name: '200g chicken breast' });
  });

  it('surfaces the server error message', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ error: 'Invalid Gemini API key', code: 'invalid_api_key' }),
    });
    await expect(getGeminiNutrition('x')).rejects.toThrow('Invalid Gemini API key');
  });

  it('rejects an empty query without calling the network', async () => {
    global.fetch = vi.fn();
    await expect(getGeminiNutrition('   ')).rejects.toThrow();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('reports a friendly message when the network is unreachable', async () => {
    global.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));
    await expect(getGeminiNutrition('apple')).rejects.toThrow(/internet connection/i);
  });
});
