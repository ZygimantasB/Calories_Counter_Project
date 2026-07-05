// The ONE online feature: AI nutrition lookup. You describe a food, Gemini fills
// in calories/protein/carbs/fat. Everything else in the app is fully offline.
//
// Endpoint resolution:
//   - VITE_GEMINI_URL   → absolute URL (use this for the offline Android build)
//   - else same-origin  → (VITE_API_URL || '') + '/api/gemini-nutrition/'  (web app)
//
// The Django endpoint is POST { food_name } and is CSRF-protected, returning
// { success, data: { product_name, calories, fat, carbohydrates, protein } }.
// The API key stays on the server — never shipped in the app.

const ENDPOINT = import.meta.env.VITE_GEMINI_URL
  || ((import.meta.env.VITE_API_URL || '') + '/api/gemini-nutrition/');

function getCookie(name) {
  const hit = document.cookie.split(';').map((c) => c.trim()).find((c) => c.startsWith(`${name}=`));
  return hit ? decodeURIComponent(hit.slice(name.length + 1)) : null;
}

function fail(message, code) {
  const err = new Error(message);
  err.code = code;
  return err;
}

/**
 * Look up nutrition for a free-text food description.
 * Returns { success, name, calories, protein, carbs, fat } on success; throws on failure.
 */
export async function getGeminiNutrition(query) {
  const foodName = String(query || '').trim();
  if (!foodName) throw fail('Please describe a food first.', 'empty');

  const headers = { 'Content-Type': 'application/json' };
  const csrf = getCookie('csrftoken');
  if (csrf) headers['X-CSRFToken'] = csrf;

  let res;
  try {
    res = await fetch(ENDPOINT, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify({ food_name: foodName }),
    });
  } catch {
    throw fail('Could not reach the AI service — check your internet connection.', 'network');
  }

  let payload = null;
  try { payload = await res.json(); } catch { /* non-JSON response */ }

  if (!res.ok || !payload || payload.success === false) {
    throw fail((payload && payload.error) || 'AI lookup failed. Please try again.', (payload && payload.code) || 'gemini_api_error');
  }

  // Normalise Django's { success, data:{ product_name, carbohydrates, … } }
  // into the flat { name, carbs, … } shape the FoodTracker expects.
  const d = payload.data || payload;
  const round1 = (v) => Math.round((Number(v) || 0) * 10) / 10;
  return {
    success: true,
    name: d.product_name ?? d.name ?? foodName,
    calories: Math.round(Number(d.calories) || 0),
    protein: round1(d.protein),
    carbs: round1(d.carbohydrates ?? d.carbs),
    fat: round1(d.fat),
  };
}
