// The ONLY online feature: AI nutrition lookup. Everything else is fully offline.
// Calls the deployed Django/Gemini endpoint — the API key stays server-side.
// Configure the host via VITE_GEMINI_URL at build time; without it, the feature
// reports as unavailable (offline) instead of throwing.
const GEMINI_URL = import.meta.env.VITE_GEMINI_URL || '';

export async function getGeminiNutrition(query) {
  if (!GEMINI_URL) {
    const err = new Error('AI lookup is not configured for the offline app.');
    err.code = 'not_configured';
    throw err;
  }
  const res = await fetch(GEMINI_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ food_name: query }),
  });
  if (!res.ok) {
    const err = new Error('AI nutrition lookup failed.');
    err.code = 'gemini_api_error';
    throw err;
  }
  return res.json();
}
