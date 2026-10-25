# Composite Products (Recipes) — Design

**Date:** 2026-10-25
**Status:** Approved (brainstorming)
**Branch:** `feature/composite-products`

## Problem

Some foods are made from several products — e.g. a chicken tortilla = wrap + chicken
breast + cheese + sauce. Today every diary entry (`FoodItem`) is a flat row with
per-serving macros, so the user must add up ingredients by hand each time.

## Goal

Let the user define a **composite product** once (name, ingredients with quantities,
"makes N servings") and log it in one click, on both the Django site and the React SPA.

## Decisions (from brainstorming)

| Topic | Decision |
|---|---|
| Diary representation | **One row, summed.** Logging creates a single ordinary `FoodItem`. |
| Ingredient amounts | **Servings multiplier** (e.g. 0.5× chicken breast). No grams. |
| Ingredient sources | Pick from food history (copies latest macros) **or** type macros manually. |
| Batch yield | Product has `servings_yield` (default 1). Logging uses totals ÷ yield × servings logged. |
| UI placement | Dedicated "My Products" page in both frontends + log from food tracker quick-add/search. |
| Offline Android app | **Out of scope for v1.** Offline API stub rejects; nav item hidden offline. Phase 2. |
| Architecture | New `Product` + `ProductIngredient` models; log = snapshot into `FoodItem`. |

Rejected: extending `MealTemplate` (mixes concepts); FK from `FoodItem` to product with
live macros (rewrites history, breaks every `Sum()` aggregate).

## Non-goals

- Grams / per-100 g nutrition.
- Gemini lookup inside the builder.
- Nested products (a product as an ingredient of another product).
- Linking ingredients back to `FoodItem` rows (no catalog exists to link to).
- Offline (SQLite) support — follow-up spec.

## 1. Data model (`count_calories_app/models.py`)

```python
class Product(models.Model):
    name = CharField(max_length=200, unique=True)
    servings_yield = DecimalField(max_digits=5, decimal_places=2, default=1)  # > 0
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    class Meta: ordering = ['name']

class ProductIngredient(models.Model):
    product = ForeignKey(Product, on_delete=CASCADE, related_name='ingredients')
    name = CharField(max_length=200)
    calories = DecimalField(max_digits=7, decimal_places=2, default=0)   # per 1 serving of ingredient
    protein = DecimalField(max_digits=5, decimal_places=2, default=0)
    fat = DecimalField(max_digits=5, decimal_places=2, default=0)
    carbohydrates = DecimalField(max_digits=5, decimal_places=2, default=0)
    quantity = DecimalField(max_digits=6, decimal_places=2, default=1)   # servings multiplier > 0
    order = PositiveSmallIntegerField(default=0)
    class Meta: ordering = ['order', 'id']
```

One migration. No changes to `FoodItem`.

## 2. Math module (`count_calories_app/products.py`)

Pure functions, no ORM access inside the math, used by every endpoint:

- `ingredient_totals(ingredients) -> dict` — Σ(macro × quantity) over ingredient dicts/objects;
  keys `calories, protein, fat, carbohydrates`; rounded to 2 dp.
- `per_serving(totals, servings_yield) -> dict` — totals ÷ yield (yield must be > 0).
- `scaled(per_serving, servings) -> dict` — per_serving × servings logged.
- `serialize_product(product) -> dict` — `{id, name, servings_yield, ingredients:[...],
  totals, per_serving, ingredient_count}`.

Since products are made of other foods, the `FoodItem` field limits still apply. A computed
log value that exceeds them (calories ≥ 100000, other macros ≥ 1000) is rejected with a 400 error.

React mirrors the math in `frontend/src/pages/Products/productMath.js` (for live totals only;
the server is the source of truth for logged values).

## 3. API (`count_calories_app/views_products.py`, wired in `count_calories_app/urls.py`)

| Method | URL | Name | Body / response |
|---|---|---|---|
| GET | `/api/react/products/` | `api_products` | `{products: [serialized...]}` |
| POST | `/api/react/products/add/` | `api_add_product` | body `{name, servings_yield, ingredients:[{name, calories, protein, fat, carbohydrates, quantity}]}` → `{success, product}` |
| PUT | `/api/react/products/<id>/update/` | `api_update_product` | same body; replaces name, yield, and **whole** ingredient list in `transaction.atomic()` → `{success, product}` |
| DELETE | `/api/react/products/<id>/delete/` | `api_delete_product` | `{success}`; past `FoodItem` rows untouched |
| POST | `/api/react/products/<id>/log/` | `api_log_product` | body `{servings: 1, date?: 'YYYY-MM-DD'}` → creates one `FoodItem(product_name=product.name, ...scaled)` → `{success, id, food}` |

Validation (`_validate_product_data`, same style as `_validate_food_data`, returns
`(is_valid, errors, sanitized)`):
- name required, ≤ 200 chars, unique (case-insensitive; excluding self on update);
- `servings_yield` > 0 and ≤ 100;
- 1–50 ingredients; each name required ≤ 200; calories 0–50000, protein/fat/carbohydrates
  0–999.99 (field limits); quantity > 0 and ≤ 1000;
- log `servings` > 0 and ≤ 100; date parsed like `api_add_food` (invalid → now).

Errors return `{success: false, error: "<joined messages>"}` with status 400; unknown id → 404.
These endpoints follow the existing `/api/react/*` CSRF pattern (Axios interceptor; Django
pages send `X-CSRFToken` from `getCookie('csrftoken')`).

**Quick-add / search integration:**
- `api_quick_add_foods` — prepend up to 5 products (most recently updated) as
  `{name, calories, protein, carbs, fat, is_product: true, product_id, servings_yield}` with
  per-serving macros; drop history entries whose name equals a product name (case-insensitive).
- `api_search_all_foods` — include products whose name matches `q`, same shape, listed first.
- Builder ingredient search reuses `/api/react/search-foods/` in **both** frontends
  (`/api/food-autocomplete/` returns names only, no macros). No new endpoint.

## 4. Django templates UI

- **New page** `/products/` → view `products_page` (in `views_products.py`), template
  `count_calories_app/templates/count_calories_app/products.html`, `@ensure_csrf_cookie`.
  Layout follows `meal_templates.html`.
  - Product cards: name, per-serving kcal / P / F / C, "makes N", ingredient count;
    buttons **Log** (servings input, default 1), **Edit**, **Delete** (Bootstrap modal confirm,
    no `confirm()`).
  - **Builder** (Bootstrap modal used for create and edit): name, "makes N servings",
    ingredient rows [name (suggestions from `/api/react/search-foods/`, selecting fills macros),
    kcal, P, F, C, quantity, remove], "+ Add ingredient", **live totals panel**
    (whole batch + per serving). Save → `fetch` JSON to the API.
- **`food_tracker.html`:** "My products" block beside quick-add: select + servings input +
  Log button → `/api/react/products/<id>/log/` with the page's selected date, then reload.
- **`templates/includes/navbar.html`:** add "My Products" link.

## 5. React UI

- `frontend/src/api/products.js` (online/offline selector like `food.js`),
  `products.online.js` (`list, create, update, delete, log`),
  `products.offline.js` (each method rejects `new Error('Products are not available offline')`).
- `frontend/src/pages/Products/`:
  - `Products.jsx` — list cards, Log (servings stepper, 0.5 steps), Edit, Delete (inline confirm).
  - `ProductBuilder.jsx` — form component (create/edit); ingredient rows with search-as-you-type
    via `foodApi.searchAllFoods` (debounced) or manual entry; live totals via `productMath.js`.
  - `productMath.js` — `ingredientTotals`, `perServing`, `scaled` (mirror of `products.py`).
- `App.jsx`: route `products`. `layouts/Sidebar.jsx`: "My Products" item, omitted when offline.
- `FoodTracker.jsx`: quick-add/search results with `is_product` show a "Recipe" badge;
  clicking logs **1 serving** via `productsApi.log(product_id, 1, date)` then refreshes
  (other amounts: servings stepper on the My Products page).
- Finish with `npm run build` (output to `static/react/`).

## 6. Error handling

- API errors are shown as the page's existing toast/alert pattern on both frontends.
- Builder blocks submit client-side for empty name / no ingredients / quantity ≤ 0, but the
  server validation is authoritative.
- Deleting a product never affects logged history; logged entries remain editable as normal
  `FoodItem`s.

## 7. Testing

**Django** — `count_calories_app/tests/test_products.py`:
- math: totals with quantities, yield division, scaling, rounding, yield ≤ 0 rejected;
- create/update/delete/list happy paths; update replaces ingredients atomically;
- validation: missing name, duplicate name (case-insensitive), zero ingredients, negative
  macros, quantity 0, yield 0, oversized values → 400;
- log: creates exactly one `FoodItem` with correct scaled macros and name; honours `date`;
  404 for unknown id; overflow of field limits → 400;
- editing/deleting a product leaves previously logged `FoodItem` unchanged;
- quick-add and search include products with `is_product: true` and de-duplicate by name;
- `/products/` page renders 200 and sets the CSRF cookie.

**React** (Vitest; note `MODE === 'test'` selects offline APIs, so tests `vi.mock` the
products API module):
- `productMath.test.js`;
- `ProductBuilder.test.jsx`: add/remove rows, totals update, submit payload shape, validation;
- `Products.test.jsx`: renders list from mocked API, log calls `productsApi.log`.

Full suites must stay green: `python manage.py test count_calories_app` and `npm test`.

## Phase 2 (separate spec)

Offline SQLite tables + `frontend/src/logic/products.js` implementation for the Android app.
