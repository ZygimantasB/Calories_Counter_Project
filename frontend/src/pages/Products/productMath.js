// Composite product nutrition math — mirrors count_calories_app/products.py.
// Used only for live totals in the builder; the server computes logged values.

export const MACROS = ['calories', 'protein', 'fat', 'carbohydrates'];

const num = (value) => {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
};

const round2 = (n) => Math.round((n + Number.EPSILON) * 100) / 100;

const mapMacros = (fn) => Object.fromEntries(MACROS.map((m) => [m, round2(fn(m))]));

export function ingredientTotals(ingredients) {
  return mapMacros((m) => ingredients.reduce((sum, ing) => sum + num(ing[m]) * num(ing.quantity), 0));
}

export function perServing(totals, servingsYield) {
  const y = num(servingsYield);
  return mapMacros((m) => (y > 0 ? num(totals[m]) / y : 0));
}

export function scaled(perServingValues, servings) {
  return mapMacros((m) => num(perServingValues[m]) * num(servings));
}
