# Composite Products (Recipes) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the user define a product made of several ingredients (e.g. a chicken tortilla) once, and log it as a single summed food-diary row from both the Django site and the React SPA.

**Architecture:** New `Product` + `ProductIngredient` models and a pure math module (`count_calories_app/products.py`). JSON endpoints in a new `count_calories_app/views_products.py` serve both frontends. Logging copies the computed per-serving macros into an ordinary `FoodItem`, so analytics, charts and history are untouched. React gets a new `/products` page, an online/offline API pair (offline = stub), and recipe badges in Food Tracker quick-add/search.

**Tech Stack:** Django 6.0 / Python 3.14 / SQLite, Bootstrap 5 templates + vanilla JS, React 19 + Vite + Tailwind v4, Vitest + Testing Library.

**Spec:** `docs/superpowers/specs/2026-10-25-composite-products-design.md`

## Global Constraints

- Branch: `feature/composite-products`. Commit locally only — **never `git push`**.
- Do **not** stage or commit the user's unrelated `utils.py` change. Always `git add` explicit paths.
- Run Django commands with `.venv/bin/python` from the repo root; run npm from `frontend/`.
- Macro keys: products/ingredients use `calories, protein, fat, carbohydrates`; quick-add/search payloads keep the existing `calories, protein, carbs, fat`.
- Limits: name ≤ 200 chars (unique, case-insensitive); `servings_yield` > 0 and ≤ 100; 1–50 ingredients; ingredient calories 0–50000, protein/fat/carbohydrates 0–999.99; quantity > 0 and ≤ 1000; log `servings` > 0 and ≤ 100. Logged values that exceed `FoodItem` capacity (calories > 99999.99, other macros > 999.99) → 400.
- Errors: `{"success": false, "error": "<messages joined by '; '>"}` status 400; unknown id → 404 `{"success": false, "error": "Product not found"}`.
- Logging a product never mutates past `FoodItem` rows; editing/deleting a product never touches the diary.
- Offline (Android/SQLite) support is out of scope: `products.offline.js` rejects with `Error('Products are not available offline')`.
- React source changes have no effect at `/app/` until `npm run build`.
- No `alert()/confirm()` in new UI — use Bootstrap modals (Django) or inline confirm (React).

## File Map

| File | Status | Responsibility |
|---|---|---|
| `count_calories_app/models.py` | modify | `Product`, `ProductIngredient` models |
| `count_calories_app/migrations/00XX_product_productingredient.py` | create (generated) | schema |
| `count_calories_app/products.py` | create | pure nutrition math + serializer |
| `count_calories_app/views_products.py` | create | validation, product JSON API, `/products/` page, quick-add helper |
| `count_calories_app/urls.py` | modify | routes |
| `count_calories_app/views.py` | modify | merge products into `api_quick_add_foods` / `api_search_all_foods` |
| `count_calories_app/templates/count_calories_app/products.html` | create | Django My Products page + builder modal |
| `count_calories_app/templates/count_calories_app/food_tracker.html` | modify | "My Products" quick-log card |
| `templates/includes/navbar.html` | modify | nav link |
| `count_calories_app/tests/test_products.py` | create | all Django tests for this feature |
| `frontend/src/api/products.js`, `products.online.js`, `products.offline.js` | create | React API |
| `frontend/src/pages/Products/productMath.js` | create | client-side live totals |
| `frontend/src/pages/Products/ProductBuilder.jsx` | create | create/edit form |
| `frontend/src/pages/Products/index.jsx` | create | My Products page |
| `frontend/src/pages/Products/__tests__/*.test.{js,jsx}` | create | React tests |
| `frontend/src/pages/index.js`, `frontend/src/App.jsx`, `frontend/src/layouts/Sidebar.jsx` | modify | route + nav |
| `frontend/src/pages/FoodTracker.jsx` | modify | recipe badge + log via products API |

---

### Task 1: Models, migration and math module

**Files:**
- Modify: `count_calories_app/models.py` (append after `MealTemplateItem`, end of file)
- Create: `count_calories_app/products.py`
- Create: migration via `makemigrations`
- Test: `count_calories_app/tests/test_products.py`

**Interfaces:**
- Produces:
  - `Product(name: str unique, servings_yield: Decimal=1, created_at, updated_at)`, `related_name='ingredients'`
  - `ProductIngredient(product, name, calories, protein, fat, carbohydrates, quantity: Decimal=1, order: int=0)`
  - `products.MACROS = ('calories', 'protein', 'fat', 'carbohydrates')`
  - `products.ingredient_totals(ingredients: iterable[dict|ProductIngredient]) -> dict[str, Decimal]`
  - `products.per_serving(totals: dict, servings_yield) -> dict[str, Decimal]` (raises `ValueError` if yield ≤ 0)
  - `products.scaled(per_serving_values: dict, servings) -> dict[str, Decimal]` (raises `ValueError` if servings ≤ 0)
  - `products.serialize_product(product: Product) -> dict` with keys `id, name, servings_yield, ingredient_count, ingredients[{id,name,calories,protein,fat,carbohydrates,quantity}], totals, per_serving` (all numbers `float`)

- [ ] **Step 1: Write the failing tests**

Create `count_calories_app/tests/test_products.py`:

```python
"""Tests for composite products (recipes): math, models, API, pages."""

import json
from decimal import Decimal

from django.test import SimpleTestCase, TestCase, Client
from django.urls import reverse
from django.utils import timezone

from count_calories_app.models import FoodItem, Product, ProductIngredient
from count_calories_app.products import (
    ingredient_totals, per_serving, scaled, serialize_product,
)


def make_product(name='Chicken tortilla', servings_yield='1', ingredients=None):
    product = Product.objects.create(name=name, servings_yield=Decimal(servings_yield))
    if ingredients is None:
        ingredients = [
            {'name': 'Wrap', 'calories': '200', 'protein': '6', 'fat': '5', 'carbohydrates': '33', 'quantity': '1'},
            {'name': 'Chicken breast', 'calories': '330', 'protein': '62', 'fat': '7', 'carbohydrates': '0', 'quantity': '0.5'},
        ]
    for order, ing in enumerate(ingredients):
        ProductIngredient.objects.create(
            product=product, order=order, name=ing['name'],
            calories=Decimal(ing['calories']), protein=Decimal(ing['protein']),
            fat=Decimal(ing['fat']), carbohydrates=Decimal(ing['carbohydrates']),
            quantity=Decimal(ing['quantity']),
        )
    return product


class ProductMathTests(SimpleTestCase):
    def test_ingredient_totals_multiplies_by_quantity(self):
        totals = ingredient_totals([
            {'calories': 200, 'protein': 6, 'fat': 5, 'carbohydrates': 33, 'quantity': 1},
            {'calories': 330, 'protein': 62, 'fat': 7, 'carbohydrates': 0, 'quantity': '0.5'},
        ])
        self.assertEqual(totals, {
            'calories': Decimal('365.00'), 'protein': Decimal('37.00'),
            'fat': Decimal('8.50'), 'carbohydrates': Decimal('33.00'),
        })

    def test_ingredient_totals_empty_is_zero(self):
        self.assertEqual(ingredient_totals([])['calories'], Decimal('0.00'))

    def test_per_serving_divides_by_yield_and_rounds(self):
        totals = {'calories': Decimal('1000'), 'protein': Decimal('10'), 'fat': Decimal('1'), 'carbohydrates': Decimal('0')}
        result = per_serving(totals, 3)
        self.assertEqual(result['calories'], Decimal('333.33'))
        self.assertEqual(result['protein'], Decimal('3.33'))
        self.assertEqual(result['fat'], Decimal('0.33'))

    def test_per_serving_rejects_non_positive_yield(self):
        totals = {'calories': 1, 'protein': 1, 'fat': 1, 'carbohydrates': 1}
        with self.assertRaises(ValueError):
            per_serving(totals, 0)

    def test_scaled_multiplies_servings(self):
        ps = {'calories': Decimal('250'), 'protein': Decimal('20.5'), 'fat': Decimal('3'), 'carbohydrates': Decimal('10')}
        self.assertEqual(scaled(ps, '1.5')['protein'], Decimal('30.75'))

    def test_scaled_rejects_non_positive_servings(self):
        with self.assertRaises(ValueError):
            scaled({'calories': 1, 'protein': 1, 'fat': 1, 'carbohydrates': 1}, 0)


class ProductModelTests(TestCase):
    def test_serialize_product(self):
        product = make_product(servings_yield='2')
        data = serialize_product(product)
        self.assertEqual(data['name'], 'Chicken tortilla')
        self.assertEqual(data['servings_yield'], 2.0)
        self.assertEqual(data['ingredient_count'], 2)
        self.assertEqual([i['name'] for i in data['ingredients']], ['Wrap', 'Chicken breast'])
        self.assertEqual(data['totals']['calories'], 365.0)
        self.assertEqual(data['per_serving']['calories'], 182.5)
        self.assertEqual(data['per_serving']['fat'], 4.25)

    def test_deleting_product_cascades_ingredients(self):
        product = make_product()
        product.delete()
        self.assertEqual(ProductIngredient.objects.count(), 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python manage.py test count_calories_app.tests.test_products`
Expected: ERROR — `ImportError: cannot import name 'Product'`.

- [ ] **Step 3: Add the models**

Append to the end of `count_calories_app/models.py`:

```python


class Product(models.Model):
    """A user-defined composite product (recipe) made of several ingredients."""
    name = models.CharField(max_length=200, unique=True, help_text="Name logged to the food diary")
    servings_yield = models.DecimalField(max_digits=5, decimal_places=2, default=1, help_text="How many servings the ingredients make")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductIngredient(models.Model):
    """One ingredient of a Product. Macros are per ONE serving of the ingredient."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ingredients')
    name = models.CharField(max_length=200)
    calories = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    protein = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fat = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    carbohydrates = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quantity = models.DecimalField(max_digits=6, decimal_places=2, default=1, help_text="Servings of this ingredient used")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.quantity}× {self.name} ({self.product.name})"
```

- [ ] **Step 4: Create the math module**

Create `count_calories_app/products.py`:

```python
"""Nutrition math for composite products (recipes).

Pure functions over dicts or ProductIngredient objects so both the API and the
tests share one implementation. All results are Decimals rounded to 2 dp.
"""
from decimal import Decimal, ROUND_HALF_UP

MACROS = ('calories', 'protein', 'fat', 'carbohydrates')
_CENT = Decimal('0.01')


def _dec(value):
    return Decimal(str(value or 0))


def _get(obj, key):
    return obj[key] if isinstance(obj, dict) else getattr(obj, key)


def _round(values):
    return {m: values[m].quantize(_CENT, rounding=ROUND_HALF_UP) for m in MACROS}


def ingredient_totals(ingredients):
    """Sum of macro × quantity over all ingredients (the whole batch)."""
    totals = {m: Decimal('0') for m in MACROS}
    for ingredient in ingredients:
        quantity = _dec(_get(ingredient, 'quantity'))
        for m in MACROS:
            totals[m] += _dec(_get(ingredient, m)) * quantity
    return _round(totals)


def per_serving(totals, servings_yield):
    """Batch totals divided by the number of servings the batch makes."""
    servings_yield = _dec(servings_yield)
    if servings_yield <= 0:
        raise ValueError('servings_yield must be greater than 0')
    return _round({m: _dec(totals[m]) / servings_yield for m in MACROS})


def scaled(per_serving_values, servings):
    """Per-serving values multiplied by the number of servings being logged."""
    servings = _dec(servings)
    if servings <= 0:
        raise ValueError('servings must be greater than 0')
    return _round({m: _dec(per_serving_values[m]) * servings for m in MACROS})


def _floats(values):
    return {m: float(values[m]) for m in MACROS}


def serialize_product(product):
    """JSON-ready representation shared by the API and the quick-add helpers."""
    ingredients = list(product.ingredients.all())
    totals = ingredient_totals(ingredients)
    return {
        'id': product.id,
        'name': product.name,
        'servings_yield': float(product.servings_yield),
        'ingredient_count': len(ingredients),
        'ingredients': [
            {
                'id': ing.id,
                'name': ing.name,
                **_floats({m: getattr(ing, m) for m in MACROS}),
                'quantity': float(ing.quantity),
            }
            for ing in ingredients
        ],
        'totals': _floats(totals),
        'per_serving': _floats(per_serving(totals, product.servings_yield)),
    }
```

- [ ] **Step 5: Generate the migration**

Run: `.venv/bin/python manage.py makemigrations count_calories_app -n product_productingredient`
Expected: `Migrations for 'count_calories_app': ... - Create model Product - Create model ProductIngredient`

- [ ] **Step 6: Run tests to verify they pass**

Run: `.venv/bin/python manage.py test count_calories_app.tests.test_products`
Expected: `Ran 8 tests ... OK`

- [ ] **Step 7: Commit**

```bash
git add count_calories_app/models.py count_calories_app/products.py count_calories_app/migrations/*_product_productingredient.py count_calories_app/tests/test_products.py
git commit -m "feat(products): add Product/ProductIngredient models and nutrition math"
```

---

### Task 2: Product JSON API (CRUD + log)

**Files:**
- Create: `count_calories_app/views_products.py`
- Modify: `count_calories_app/urls.py` (import + routes after the `api/react/meal-templates/...` block, ~line 102)
- Test: `count_calories_app/tests/test_products.py` (append)

**Interfaces:**
- Consumes: Task 1 (`Product`, `ProductIngredient`, `MACROS`, `ingredient_totals`, `per_serving`, `scaled`, `serialize_product`)
- Produces (URL names): `api_products` GET, `api_add_product` POST, `api_update_product` PUT/PATCH `<int:product_id>`, `api_delete_product` DELETE `<int:product_id>`, `api_log_product` POST `<int:product_id>` body `{servings, date?}` → `{success, id, food:{id,name,calories,protein,carbs,fat,consumed_at}}`
- Produces: `views_products.FOOD_ITEM_LIMITS` (used by tests)

- [ ] **Step 1: Write the failing tests**

Append to `count_calories_app/tests/test_products.py`:

```python
def product_payload(**overrides):
    payload = {
        'name': 'Chicken tortilla',
        'servings_yield': 1,
        'ingredients': [
            {'name': 'Wrap', 'calories': 200, 'protein': 6, 'fat': 5, 'carbohydrates': 33, 'quantity': 1},
            {'name': 'Chicken breast', 'calories': 330, 'protein': 62, 'fat': 7, 'carbohydrates': 0, 'quantity': 0.5},
        ],
    }
    payload.update(overrides)
    return payload


class ProductApiTests(TestCase):
    def setUp(self):
        self.client = Client()

    def post_json(self, url, data):
        return self.client.post(url, json.dumps(data), content_type='application/json')

    def put_json(self, url, data):
        return self.client.put(url, json.dumps(data), content_type='application/json')

    # --- list / create ---
    def test_list_products(self):
        make_product()
        response = self.client.get(reverse('api_products'))
        self.assertEqual(response.status_code, 200)
        products = response.json()['products']
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]['per_serving']['calories'], 365.0)

    def test_create_product(self):
        response = self.post_json(reverse('api_add_product'), product_payload())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertEqual(body['product']['ingredient_count'], 2)
        self.assertEqual(Product.objects.get().ingredients.first().name, 'Wrap')

    def test_create_strips_name(self):
        self.post_json(reverse('api_add_product'), product_payload(name='  Burrito  '))
        self.assertTrue(Product.objects.filter(name='Burrito').exists())

    def assert_rejected(self, payload, fragment):
        response = self.post_json(reverse('api_add_product'), payload)
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertFalse(body['success'])
        self.assertIn(fragment, body['error'])
        self.assertEqual(Product.objects.count(), 0)

    def test_create_requires_name(self):
        self.assert_rejected(product_payload(name=''), 'name is required')

    def test_create_requires_ingredients(self):
        self.assert_rejected(product_payload(ingredients=[]), 'At least one ingredient')

    def test_create_rejects_zero_yield(self):
        self.assert_rejected(product_payload(servings_yield=0), 'Servings yield')

    def test_create_rejects_zero_quantity(self):
        payload = product_payload()
        payload['ingredients'][0]['quantity'] = 0
        self.assert_rejected(payload, 'quantity')

    def test_create_rejects_negative_macro(self):
        payload = product_payload()
        payload['ingredients'][0]['protein'] = -1
        self.assert_rejected(payload, 'protein')

    def test_create_rejects_oversized_macro(self):
        payload = product_payload()
        payload['ingredients'][0]['fat'] = 1000
        self.assert_rejected(payload, 'fat')

    def test_create_rejects_non_numeric_macro(self):
        payload = product_payload()
        payload['ingredients'][0]['calories'] = 'abc'
        self.assert_rejected(payload, 'calories')

    def test_create_rejects_per_serving_over_food_item_limit(self):
        payload = product_payload(ingredients=[
            {'name': 'Butter', 'calories': 100, 'protein': 0, 'fat': 999, 'carbohydrates': 0, 'quantity': 2},
        ])
        self.assert_rejected(payload, 'exceeds')

    def test_create_rejects_duplicate_name_case_insensitive(self):
        make_product(name='Chicken tortilla')
        response = self.post_json(reverse('api_add_product'), product_payload(name='CHICKEN TORTILLA'))
        self.assertEqual(response.status_code, 400)
        self.assertIn('already exists', response.json()['error'])

    def test_create_rejects_invalid_json(self):
        response = self.client.post(reverse('api_add_product'), 'not json', content_type='application/json')
        self.assertEqual(response.status_code, 400)

    # --- update / delete ---
    def test_update_replaces_ingredients(self):
        product = make_product()
        payload = product_payload(name='Veggie tortilla', servings_yield=2, ingredients=[
            {'name': 'Wrap', 'calories': 200, 'protein': 6, 'fat': 5, 'carbohydrates': 33, 'quantity': 2},
        ])
        response = self.put_json(reverse('api_update_product', args=[product.id]), payload)
        self.assertEqual(response.status_code, 200)
        product.refresh_from_db()
        self.assertEqual(product.name, 'Veggie tortilla')
        self.assertEqual(product.servings_yield, Decimal('2.00'))
        self.assertEqual(list(product.ingredients.values_list('name', flat=True)), ['Wrap'])
        self.assertEqual(response.json()['product']['per_serving']['calories'], 200.0)

    def test_update_keeps_own_name(self):
        product = make_product()
        response = self.put_json(reverse('api_update_product', args=[product.id]), product_payload())
        self.assertEqual(response.status_code, 200)

    def test_update_invalid_leaves_product_untouched(self):
        product = make_product()
        response = self.put_json(reverse('api_update_product', args=[product.id]), product_payload(ingredients=[]))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(product.ingredients.count(), 2)

    def test_update_unknown_returns_404(self):
        response = self.put_json(reverse('api_update_product', args=[9999]), product_payload())
        self.assertEqual(response.status_code, 404)

    def test_delete_product(self):
        product = make_product()
        response = self.client.delete(reverse('api_delete_product', args=[product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.exists())

    def test_delete_unknown_returns_404(self):
        self.assertEqual(self.client.delete(reverse('api_delete_product', args=[9999])).status_code, 404)

    # --- log ---
    def test_log_creates_one_food_item_with_per_serving_macros(self):
        product = make_product(servings_yield='2')
        response = self.post_json(reverse('api_log_product', args=[product.id]), {'servings': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FoodItem.objects.count(), 1)
        food = FoodItem.objects.get()
        self.assertEqual(food.product_name, 'Chicken tortilla')
        self.assertEqual(food.calories, Decimal('182.50'))
        self.assertEqual(food.protein, Decimal('18.50'))
        self.assertEqual(food.fat, Decimal('4.25'))
        self.assertEqual(food.carbohydrates, Decimal('16.50'))
        self.assertEqual(response.json()['food']['carbs'], 16.5)

    def test_log_scales_by_servings(self):
        product = make_product()
        self.post_json(reverse('api_log_product', args=[product.id]), {'servings': 1.5})
        self.assertEqual(FoodItem.objects.get().calories, Decimal('547.50'))

    def test_log_defaults_to_one_serving(self):
        product = make_product()
        self.post_json(reverse('api_log_product', args=[product.id]), {})
        self.assertEqual(FoodItem.objects.get().calories, Decimal('365.00'))

    def test_log_honours_date(self):
        product = make_product()
        self.post_json(reverse('api_log_product', args=[product.id]), {'servings': 1, 'date': '2026-01-15'})
        food = FoodItem.objects.get()
        self.assertEqual(timezone.localtime(food.consumed_at).date().isoformat(), '2026-01-15')

    def test_log_rejects_zero_servings(self):
        product = make_product()
        response = self.post_json(reverse('api_log_product', args=[product.id]), {'servings': 0})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(FoodItem.objects.exists())

    def test_log_rejects_overflow(self):
        product = make_product(ingredients=[
            {'name': 'Oil', 'calories': '900', 'protein': '0', 'fat': '100', 'carbohydrates': '0', 'quantity': '1'},
        ])
        response = self.post_json(reverse('api_log_product', args=[product.id]), {'servings': 20})
        self.assertEqual(response.status_code, 400)
        self.assertIn('exceeds', response.json()['error'])

    def test_log_unknown_returns_404(self):
        self.assertEqual(self.post_json(reverse('api_log_product', args=[9999]), {}).status_code, 404)

    # --- history is a snapshot ---
    def test_editing_or_deleting_product_keeps_logged_history(self):
        product = make_product()
        self.post_json(reverse('api_log_product', args=[product.id]), {'servings': 1})
        self.put_json(reverse('api_update_product', args=[product.id]), product_payload(
            name='Renamed', ingredients=[{'name': 'X', 'calories': 1, 'protein': 0, 'fat': 0, 'carbohydrates': 0, 'quantity': 1}],
        ))
        self.client.delete(reverse('api_delete_product', args=[product.id]))
        food = FoodItem.objects.get()
        self.assertEqual(food.product_name, 'Chicken tortilla')
        self.assertEqual(food.calories, Decimal('365.00'))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python manage.py test count_calories_app.tests.test_products`
Expected: ERRORs — `NoReverseMatch: Reverse for 'api_products' not found`.

- [ ] **Step 3: Implement the views**

Create `count_calories_app/views_products.py`:

```python
"""Composite products (recipes): JSON API shared by the Django and React frontends."""
import json
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import FoodItem, Product, ProductIngredient
from .products import MACROS, ingredient_totals, per_serving, scaled, serialize_product

logger = logging.getLogger(__name__)

# Per-ingredient input limits (protein/fat/carbs fields hold max 999.99).
INGREDIENT_LIMITS = {
    'calories': Decimal('50000'),
    'protein': Decimal('999.99'),
    'fat': Decimal('999.99'),
    'carbohydrates': Decimal('999.99'),
}
# Capacity of the FoodItem diary columns a logged product is written into.
FOOD_ITEM_LIMITS = {
    'calories': Decimal('99999.99'),
    'protein': Decimal('999.99'),
    'fat': Decimal('999.99'),
    'carbohydrates': Decimal('999.99'),
}
MAX_INGREDIENTS = 50
_CENT = Decimal('0.01')


def _to_decimal(value):
    """Parse a finite Decimal rounded to 2 dp, or None when the value is not a number."""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not number.is_finite():
        return None
    return number.quantize(_CENT, rounding=ROUND_HALF_UP)


def _json_body(request):
    try:
        data = json.loads(request.body or b'{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _error(message, status=400):
    return JsonResponse({'success': False, 'error': message}, status=status)


def _limit_errors(values, prefix):
    return [
        f'{prefix} {m} ({values[m]}) exceeds the food diary limit of {FOOD_ITEM_LIMITS[m]}'
        for m in MACROS if values[m] > FOOD_ITEM_LIMITS[m]
    ]


def _validate_product_data(data, product_id=None):
    """Validate a product payload and return (is_valid, errors, sanitized)."""
    errors = []
    sanitized = {}

    name = str(data.get('name') or '').strip()
    if not name:
        errors.append('Product name is required')
    elif len(name) > 200:
        errors.append('Product name must be 200 characters or less')
    elif Product.objects.filter(name__iexact=name).exclude(pk=product_id).exists():
        errors.append(f'A product named "{name}" already exists')
    sanitized['name'] = name

    servings_yield = _to_decimal(data.get('servings_yield', 1))
    if servings_yield is None or servings_yield <= 0 or servings_yield > 100:
        errors.append('Servings yield must be greater than 0 and at most 100')
    sanitized['servings_yield'] = servings_yield

    raw_ingredients = data.get('ingredients')
    if not isinstance(raw_ingredients, list) or not raw_ingredients:
        errors.append('At least one ingredient is required')
        raw_ingredients = []
    elif len(raw_ingredients) > MAX_INGREDIENTS:
        errors.append(f'A product can have at most {MAX_INGREDIENTS} ingredients')
        raw_ingredients = []

    ingredients = []
    for index, item in enumerate(raw_ingredients, start=1):
        if not isinstance(item, dict):
            errors.append(f'Ingredient {index} is invalid')
            continue
        ingredient_name = str(item.get('name') or '').strip()
        if not ingredient_name:
            errors.append(f'Ingredient {index}: name is required')
        elif len(ingredient_name) > 200:
            errors.append(f'Ingredient {index}: name must be 200 characters or less')
        clean = {'name': ingredient_name}
        for m in MACROS:
            value = _to_decimal(item.get(m) or 0)
            if value is None or value < 0 or value > INGREDIENT_LIMITS[m]:
                errors.append(f'Ingredient {index}: {m} must be between 0 and {INGREDIENT_LIMITS[m]}')
            clean[m] = value
        quantity = _to_decimal(item.get('quantity', 1))
        if quantity is None or quantity <= 0 or quantity > 1000:
            errors.append(f'Ingredient {index}: quantity must be greater than 0 and at most 1000')
        clean['quantity'] = quantity
        ingredients.append(clean)
    sanitized['ingredients'] = ingredients

    if not errors:
        serving = per_serving(ingredient_totals(ingredients), servings_yield)
        errors.extend(_limit_errors(serving, 'Per-serving'))

    return len(errors) == 0, errors, sanitized


def _save_ingredients(product, ingredients):
    ProductIngredient.objects.bulk_create([
        ProductIngredient(product=product, order=order, **ingredient)
        for order, ingredient in enumerate(ingredients)
    ])


def _parse_log_date(value):
    """YYYY-MM-DD → that day at the current time (same rule as api_add_food); otherwise now."""
    if value:
        try:
            day = datetime.strptime(str(value), '%Y-%m-%d').date()
            return timezone.make_aware(datetime.combine(day, datetime.now().time()))
        except ValueError:
            pass
    return timezone.now()


@require_http_methods(["GET"])
def api_products(request):
    """List all composite products with totals and per-serving macros."""
    products = Product.objects.prefetch_related('ingredients')
    return JsonResponse({'products': [serialize_product(p) for p in products]})


@require_http_methods(["POST"])
def api_add_product(request):
    """Create a composite product from a JSON payload."""
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body')
    is_valid, errors, clean = _validate_product_data(data)
    if not is_valid:
        return _error('; '.join(errors))
    with transaction.atomic():
        product = Product.objects.create(name=clean['name'], servings_yield=clean['servings_yield'])
        _save_ingredients(product, clean['ingredients'])
    return JsonResponse({'success': True, 'product': serialize_product(product)})


@require_http_methods(["PUT", "PATCH"])
def api_update_product(request, product_id):
    """Replace a product's name, yield and full ingredient list."""
    product = Product.objects.filter(pk=product_id).first()
    if product is None:
        return _error('Product not found', status=404)
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body')
    is_valid, errors, clean = _validate_product_data(data, product_id=product.id)
    if not is_valid:
        return _error('; '.join(errors))
    with transaction.atomic():
        product.name = clean['name']
        product.servings_yield = clean['servings_yield']
        product.save()
        product.ingredients.all().delete()
        _save_ingredients(product, clean['ingredients'])
    return JsonResponse({'success': True, 'product': serialize_product(product)})


@require_http_methods(["DELETE"])
def api_delete_product(request, product_id):
    """Delete a product. Diary entries already logged from it are kept."""
    deleted, _ = Product.objects.filter(pk=product_id).delete()
    if not deleted:
        return _error('Product not found', status=404)
    return JsonResponse({'success': True})


@require_http_methods(["POST"])
def api_log_product(request, product_id):
    """Log N servings of a product as ONE FoodItem with summed macros."""
    product = Product.objects.prefetch_related('ingredients').filter(pk=product_id).first()
    if product is None:
        return _error('Product not found', status=404)
    data = _json_body(request)
    if data is None:
        return _error('Invalid JSON body')

    servings = _to_decimal(data.get('servings', 1))
    if servings is None or servings <= 0 or servings > 100:
        return _error('Servings must be greater than 0 and at most 100')

    values = scaled(per_serving(ingredient_totals(product.ingredients.all()), product.servings_yield), servings)
    errors = _limit_errors(values, 'Logged')
    if errors:
        return _error('; '.join(errors))

    food = FoodItem.objects.create(
        product_name=product.name,
        consumed_at=_parse_log_date(data.get('date')),
        **values,
    )
    return JsonResponse({
        'success': True,
        'id': food.id,
        'food': {
            'id': food.id,
            'name': food.product_name,
            'calories': float(food.calories),
            'protein': float(food.protein),
            'carbs': float(food.carbohydrates),
            'fat': float(food.fat),
            'consumed_at': food.consumed_at.isoformat(),
        },
    })
```

- [ ] **Step 4: Wire the URLs**

In `count_calories_app/urls.py` change line 2 to:

```python
from . import views, views_products
```

and directly after the `path('api/react/meal-templates/<int:template_id>/delete/', ...)` line add:

```python
    path('api/react/products/', views_products.api_products, name='api_products'),
    path('api/react/products/add/', views_products.api_add_product, name='api_add_product'),
    path('api/react/products/<int:product_id>/update/', views_products.api_update_product, name='api_update_product'),
    path('api/react/products/<int:product_id>/delete/', views_products.api_delete_product, name='api_delete_product'),
    path('api/react/products/<int:product_id>/log/', views_products.api_log_product, name='api_log_product'),
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `.venv/bin/python manage.py test count_calories_app.tests.test_products`
Expected: `Ran 35 tests ... OK`

- [ ] **Step 6: Commit**

```bash
git add count_calories_app/views_products.py count_calories_app/urls.py count_calories_app/tests/test_products.py
git commit -m "feat(products): add product CRUD and log JSON API"
```

---

### Task 3: Products in quick-add and search

**Files:**
- Modify: `count_calories_app/views_products.py` (add helper)
- Modify: `count_calories_app/views.py` — imports (line ~12) and the bodies of `api_quick_add_foods` (~line 3813) and `api_search_all_foods` (~line 3836)
- Test: `count_calories_app/tests/test_products.py` (append)

**Interfaces:**
- Consumes: Task 2 (`views_products` module), Task 1 (`serialize_product`)
- Produces: `views_products.product_quick_entries(query: str = '', limit: int = 5) -> list[dict]`, each `{id: 'product-<pk>', name, calories, protein, carbs, fat, is_product: True, product_id: int, servings_yield: float}` (per-serving macros)
- Produces (response contract for Task 7): quick-add `foods[]` and search `results[]` may contain items with `is_product: true` and `product_id`, listed first.

- [ ] **Step 1: Write the failing tests**

Append to `count_calories_app/tests/test_products.py`:

```python
class ProductQuickAddIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.product = make_product(servings_yield='2')
        FoodItem.objects.create(product_name='Banana', calories=100, protein=1, fat=0, carbohydrates=25)
        # A diary row logged from the product earlier must not duplicate the product tile.
        FoodItem.objects.create(product_name='chicken tortilla', calories=182.5, protein=18.5, fat=4.25, carbohydrates=16.5)

    def test_quick_add_lists_products_first_and_dedupes(self):
        foods = self.client.get(reverse('api_quick_add_foods')).json()['foods']
        self.assertEqual(foods[0]['name'], 'Chicken tortilla')
        self.assertTrue(foods[0]['is_product'])
        self.assertEqual(foods[0]['product_id'], self.product.id)
        self.assertEqual(foods[0]['calories'], 182.5)
        self.assertEqual(foods[0]['carbs'], 16.5)
        names = [f['name'].lower() for f in foods]
        self.assertEqual(names.count('chicken tortilla'), 1)
        self.assertIn('banana', names)
        self.assertEqual(len({f['id'] for f in foods}), len(foods))

    def test_search_includes_matching_products(self):
        results = self.client.get(reverse('api_search_all_foods'), {'q': 'tort'}).json()['results']
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['is_product'])

    def test_search_excludes_non_matching_products(self):
        results = self.client.get(reverse('api_search_all_foods'), {'q': 'banana'}).json()['results']
        self.assertEqual([r['name'] for r in results], ['Banana'])
        self.assertFalse(results[0].get('is_product', False))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python manage.py test count_calories_app.tests.test_products.ProductQuickAddIntegrationTests`
Expected: FAIL — `KeyError: 'is_product'` / name mismatch.

- [ ] **Step 3: Add the helper**

Append to `count_calories_app/views_products.py`:

```python


def product_quick_entries(query='', limit=5):
    """Products shaped like quick-add/search rows (per-serving macros, 'carbs' key)."""
    products = Product.objects.prefetch_related('ingredients').order_by('-updated_at')
    if query:
        products = products.filter(name__icontains=query)
    entries = []
    for product in products[:limit]:
        data = serialize_product(product)
        serving = data['per_serving']
        entries.append({
            'id': f'product-{product.id}',
            'name': product.name,
            'calories': serving['calories'],
            'protein': serving['protein'],
            'carbs': serving['carbohydrates'],
            'fat': serving['fat'],
            'is_product': True,
            'product_id': product.id,
            'servings_yield': data['servings_yield'],
        })
    return entries
```

- [ ] **Step 4: Merge into the existing endpoints**

In `count_calories_app/views.py`, after line 14 (`from .services import GeminiService`) add:

```python
from .views_products import product_quick_entries
```

Replace the body of `api_quick_add_foods` from `# Transform to frontend-expected format` to the end of the function with:

```python
    # Composite products first; history rows sharing a product's name are dropped
    foods = product_quick_entries(limit=5)
    product_names = {food['name'].lower() for food in foods}
    for food in recent_foods:
        if food['product_name'].lower() in product_names:
            continue
        foods.append({
            'id': len(foods) + 1,  # Generate an ID for display purposes
            'name': food['product_name'],
            **_nutrition_payload(food),
        })

    return JsonResponse({
        'foods': foods
    })
```

In `api_search_all_foods`, replace the block from `# Transform to frontend-expected format` up to (not including) `return JsonResponse({` with:

```python
    # Matching composite products first, then history (deduplicated by name)
    results = product_quick_entries(query, limit)
    for entry in results:
        entry.update({'count': 0, 'last_used': None})
    product_names = {entry['name'].lower() for entry in results}
    for food in foods:
        if food['product_name'].lower() in product_names:
            continue
        results.append({
            'name': food['product_name'],
            **_nutrition_payload(food),
            'count': food['count'],
            'last_used': food['last_used'].isoformat() if food['last_used'] else None,
        })
    results = results[:limit]
```

- [ ] **Step 5: Run the feature tests and the existing quick-add regression tests**

Run: `.venv/bin/python manage.py test count_calories_app.tests.test_products count_calories_app.tests.test_bug_fixes`
Expected: all OK (`test_bug_fixes` has quick-add/search regression tests that must still pass).

- [ ] **Step 6: Commit**

```bash
git add count_calories_app/views.py count_calories_app/views_products.py count_calories_app/tests/test_products.py
git commit -m "feat(products): surface products in quick-add and food search"
```

---

### Task 4: Django "My Products" page, navbar and food-tracker card

**Files:**
- Modify: `count_calories_app/views_products.py` (page view)
- Modify: `count_calories_app/urls.py` (route)
- Create: `count_calories_app/templates/count_calories_app/products.html`
- Modify: `templates/includes/navbar.html` (Food Tracker dropdown, lines 12–22)
- Modify: `count_calories_app/templates/count_calories_app/food_tracker.html` (after the Meal Templates card, ~line 225; script at end of `{% block js_files %}`)
- Test: `count_calories_app/tests/test_products.py` (append)

**Interfaces:**
- Consumes: Task 2 endpoints; `/api/react/search-foods/?q=&limit=` (`results[]` with `name, calories, protein, carbs, fat, is_product?`)
- Produces: URL name `products_page` at `/products/`

- [ ] **Step 1: Write the failing tests**

Append to `count_calories_app/tests/test_products.py`:

```python
class ProductPageTests(TestCase):
    def test_products_page_renders_and_sets_csrf_cookie(self):
        response = Client().get(reverse('products_page'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'My Products')
        self.assertIn('csrftoken', response.cookies)

    def test_navbar_links_to_products(self):
        response = Client().get(reverse('food_tracker') + '?range=today')
        self.assertContains(response, reverse('products_page'))
        self.assertContains(response, 'id="productsQuickList"')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python manage.py test count_calories_app.tests.test_products.ProductPageTests`
Expected: ERROR — `NoReverseMatch: 'products_page'`.

- [ ] **Step 3: Add the page view and route**

In `count_calories_app/views_products.py` add to the imports:

```python
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
```

and append:

```python


@ensure_csrf_cookie
def products_page(request):
    """Django-template 'My Products' page; data is loaded from the JSON API."""
    return render(request, 'count_calories_app/products.html')
```

In `count_calories_app/urls.py`, after the `path('meal-templates/<int:template_id>/delete/', ...)` line add:

```python
    path('products/', views_products.products_page, name='products_page'),
```

- [ ] **Step 4: Create the template**

Create `count_calories_app/templates/count_calories_app/products.html`:

```html
{% extends "base.html" %}
{% load static %}

{% block title %}My Products{% endblock %}

{% block css_files %}
  {{ block.super }}
  <style>
    .product-card { transition: transform .15s; }
    .product-card:hover { transform: translateY(-2px); }
    .ing-row input { min-width: 0; }
    #searchResults { max-height: 220px; overflow-y: auto; }
  </style>
{% endblock %}

{% block content %}
<div class="container-fluid">

  <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
    <h1 class="h3 mb-0"><i class="fas fa-layer-group me-2 text-primary"></i>My Products</h1>
    <div class="d-flex gap-2">
      <a href="{% url 'food_tracker' %}?range=today" class="btn btn-outline-secondary btn-sm">
        <i class="fas fa-arrow-left me-1"></i>Back to Food Tracker
      </a>
      <button class="btn btn-primary btn-sm" id="newProductBtn">
        <i class="fas fa-plus me-1"></i>New product
      </button>
    </div>
  </div>

  <p class="text-muted small">Combine several foods into one product (e.g. a tortilla). Logging it adds a single diary entry with the summed nutrition.</p>

  <div class="row g-3" id="productsGrid">
    <div class="col-12 text-muted small">Loading…</div>
  </div>
</div>

<!-- Builder modal -->
<div class="modal fade" id="builderModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog modal-xl modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="builderTitle">New product</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <div class="row g-2 mb-3">
          <div class="col-md-8">
            <label class="form-label small" for="productName">Name</label>
            <input type="text" class="form-control" id="productName" maxlength="200" placeholder="Chicken tortilla">
          </div>
          <div class="col-md-4">
            <label class="form-label small" for="servingsYield">Makes N servings</label>
            <input type="number" class="form-control" id="servingsYield" min="0.01" max="100" step="0.5" value="1">
          </div>
        </div>

        <label class="form-label small" for="ingredientSearch">Add ingredient from your foods</label>
        <input type="text" class="form-control mb-1" id="ingredientSearch" placeholder="Search e.g. wrap, chicken…" autocomplete="off">
        <div class="list-group mb-3" id="searchResults"></div>

        <div class="table-responsive">
          <table class="table table-sm align-middle">
            <thead><tr>
              <th>Ingredient</th><th>kcal</th><th>P</th><th>F</th><th>C</th><th>Qty (servings)</th><th></th>
            </tr></thead>
            <tbody id="ingredientRows"></tbody>
          </table>
        </div>
        <button class="btn btn-outline-secondary btn-sm" id="addManualBtn"><i class="fas fa-plus me-1"></i>Add manual ingredient</button>

        <div class="card bg-light mt-3"><div class="card-body py-2 small" id="totalsPanel"></div></div>
        <div class="text-danger small mt-2" id="builderError"></div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-primary" id="saveProductBtn">Save product</button>
      </div>
    </div>
  </div>
</div>

<!-- Delete confirm modal -->
<div class="modal fade" id="deleteModal" tabindex="-1" aria-hidden="true">
  <div class="modal-dialog"><div class="modal-content">
    <div class="modal-body">Delete <strong id="deleteName"></strong>? Foods you already logged stay in your diary.</div>
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
      <button type="button" class="btn btn-danger" id="confirmDeleteBtn">Delete</button>
    </div>
  </div></div>
</div>

<div class="toast-container position-fixed bottom-0 end-0 p-3">
  <div id="toast" class="toast text-white" role="alert"><div class="toast-body" id="toastMsg"></div></div>
</div>
{% endblock %}

{% block js_files %}
{{ block.super }}
<script>
(function () {
  const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
  const MACROS = ['calories', 'protein', 'fat', 'carbohydrates'];
  const builder = new bootstrap.Modal(document.getElementById('builderModal'));
  const deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
  let products = [];
  let editingId = null;
  let deletingId = null;

  function el(tag, attrs = {}, children = []) {
    const node = document.createElement(tag);
    Object.entries(attrs).forEach(([k, v]) => {
      if (k === 'text') node.textContent = v;
      else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v);
    });
    children.forEach(c => node.appendChild(c));
    return node;
  }

  function showToast(msg, ok) {
    const t = document.getElementById('toast');
    t.classList.remove('bg-success', 'bg-danger');
    t.classList.add(ok ? 'bg-success' : 'bg-danger');
    document.getElementById('toastMsg').textContent = msg;
    bootstrap.Toast.getOrCreateInstance(t, {delay: 3000}).show();
  }

  async function api(url, method = 'GET', body) {
    const opts = {method, headers: {'X-CSRFToken': csrfToken}};
    if (body !== undefined) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const r = await fetch(url, opts);
    const data = await r.json();
    if (!r.ok || data.success === false) throw new Error(data.error || 'Request failed');
    return data;
  }

  const fmt = n => (Math.round(Number(n) * 10) / 10).toString();

  // ---------- list ----------
  async function loadProducts() {
    const grid = document.getElementById('productsGrid');
    try {
      products = (await api('/api/react/products/')).products;
    } catch (e) {
      grid.replaceChildren(el('div', {class: 'col-12 text-danger small', text: e.message}));
      return;
    }
    if (!products.length) {
      grid.replaceChildren(el('div', {class: 'col-12 text-muted', text: 'No products yet — click "New product" to build one.'}));
      return;
    }
    grid.replaceChildren(...products.map(renderCard));
  }

  function renderCard(p) {
    const ps = p.per_serving;
    const servings = el('input', {type: 'number', class: 'form-control form-control-sm', style: 'max-width:80px', min: '0.5', max: '100', step: '0.5', value: '1', 'aria-label': 'Servings'});
    return el('div', {class: 'col-md-6 col-xl-4'}, [
      el('div', {class: 'card shadow-sm product-card h-100'}, [
        el('div', {class: 'card-body'}, [
          el('h2', {class: 'h6 mb-1', text: p.name}),
          el('div', {class: 'small text-muted mb-2', text: `${p.ingredient_count} ingredients · makes ${fmt(p.servings_yield)} serving(s)`}),
          el('div', {class: 'small', text: `Per serving: ${Math.round(ps.calories)} kcal · P ${fmt(ps.protein)}g · F ${fmt(ps.fat)}g · C ${fmt(ps.carbohydrates)}g`}),
        ]),
        el('div', {class: 'card-footer d-flex gap-2 align-items-center'}, [
          servings,
          el('button', {class: 'btn btn-sm btn-success', text: 'Log', onclick: async e => {
            e.target.disabled = true;
            try {
              await api(`/api/react/products/${p.id}/log/`, 'POST', {servings: Number(servings.value)});
              showToast(`Logged ${servings.value} × ${p.name}`, true);
            } catch (err) { showToast(err.message, false); }
            e.target.disabled = false;
          }}),
          el('button', {class: 'btn btn-sm btn-outline-primary ms-auto', text: 'Edit', onclick: () => openBuilder(p)}),
          el('button', {class: 'btn btn-sm btn-outline-danger', text: 'Delete', onclick: () => {
            deletingId = p.id;
            document.getElementById('deleteName').textContent = p.name;
            deleteModal.show();
          }}),
        ]),
      ]),
    ]);
  }

  document.getElementById('confirmDeleteBtn').addEventListener('click', async () => {
    try {
      await api(`/api/react/products/${deletingId}/delete/`, 'DELETE');
      showToast('Product deleted', true);
      deleteModal.hide();
      loadProducts();
    } catch (err) { showToast(err.message, false); }
  });

  // ---------- builder ----------
  const rowsBody = document.getElementById('ingredientRows');

  function addRow(ing = {}) {
    const input = (field, attrs) => el('input', {class: 'form-control form-control-sm', 'data-field': field, ...attrs});
    const num = (field, value, attrs = {}) => input(field, {type: 'number', min: '0', step: '0.1', value: value ?? 0, ...attrs});
    const row = el('tr', {class: 'ing-row'}, [
      el('td', {}, [input('name', {type: 'text', maxlength: '200', value: ing.name || '', placeholder: 'Ingredient'})]),
      el('td', {}, [num('calories', ing.calories)]),
      el('td', {}, [num('protein', ing.protein)]),
      el('td', {}, [num('fat', ing.fat)]),
      el('td', {}, [num('carbohydrates', ing.carbohydrates)]),
      el('td', {}, [num('quantity', ing.quantity ?? 1, {min: '0.01', step: '0.25'})]),
      el('td', {}, [el('button', {class: 'btn btn-sm btn-link text-danger', 'aria-label': 'Remove', text: '✕', onclick: () => { row.remove(); renderTotals(); }})]),
    ]);
    row.addEventListener('input', renderTotals);
    rowsBody.appendChild(row);
    renderTotals();
  }

  function readIngredients() {
    return [...rowsBody.querySelectorAll('tr')].map(tr => {
      const get = f => tr.querySelector(`[data-field="${f}"]`).value;
      const ing = {name: get('name').trim(), quantity: Number(get('quantity'))};
      MACROS.forEach(m => { ing[m] = Number(get(m)) || 0; });
      return ing;
    });
  }

  function renderTotals() {
    const ings = readIngredients();
    const totals = Object.fromEntries(MACROS.map(m => [m, ings.reduce((s, i) => s + i[m] * (i.quantity || 0), 0)]));
    const y = Number(document.getElementById('servingsYield').value) || 0;
    const line = (label, t) => `${label}: ${Math.round(t.calories)} kcal · P ${fmt(t.protein)}g · F ${fmt(t.fat)}g · C ${fmt(t.carbohydrates)}g`;
    const per = y > 0 ? Object.fromEntries(MACROS.map(m => [m, totals[m] / y])) : null;
    const panel = document.getElementById('totalsPanel');
    panel.replaceChildren(
      el('div', {text: line('Whole batch', totals)}),
      el('div', {class: 'fw-bold', text: per ? line('Per serving', per) : 'Per serving: set servings above 0'}),
    );
  }
  document.getElementById('servingsYield').addEventListener('input', renderTotals);

  function openBuilder(product = null) {
    editingId = product ? product.id : null;
    document.getElementById('builderTitle').textContent = product ? `Edit ${product.name}` : 'New product';
    document.getElementById('productName').value = product ? product.name : '';
    document.getElementById('servingsYield').value = product ? product.servings_yield : 1;
    document.getElementById('builderError').textContent = '';
    document.getElementById('ingredientSearch').value = '';
    document.getElementById('searchResults').replaceChildren();
    rowsBody.replaceChildren();
    (product ? product.ingredients : []).forEach(addRow);
    renderTotals();
    builder.show();
  }

  document.getElementById('newProductBtn').addEventListener('click', () => openBuilder());
  document.getElementById('addManualBtn').addEventListener('click', () => addRow());

  let searchTimer = null;
  document.getElementById('ingredientSearch').addEventListener('input', e => {
    clearTimeout(searchTimer);
    const q = e.target.value.trim();
    const box = document.getElementById('searchResults');
    if (q.length < 2) { box.replaceChildren(); return; }
    searchTimer = setTimeout(async () => {
      try {
        const data = await api(`/api/react/search-foods/?q=${encodeURIComponent(q)}&limit=8`);
        box.replaceChildren(...data.results.filter(r => !r.is_product).map(r => el('button', {
          type: 'button', class: 'list-group-item list-group-item-action small',
          text: `${r.name} — ${Math.round(r.calories)} kcal · P ${fmt(r.protein)} · F ${fmt(r.fat)} · C ${fmt(r.carbs)}`,
          onclick: () => {
            addRow({name: r.name, calories: r.calories, protein: r.protein, fat: r.fat, carbohydrates: r.carbs, quantity: 1});
            box.replaceChildren();
            e.target.value = '';
          },
        })));
      } catch (err) { box.replaceChildren(el('div', {class: 'text-danger small', text: err.message})); }
    }, 250);
  });

  document.getElementById('saveProductBtn').addEventListener('click', async () => {
    const payload = {
      name: document.getElementById('productName').value.trim(),
      servings_yield: Number(document.getElementById('servingsYield').value),
      ingredients: readIngredients(),
    };
    const errorBox = document.getElementById('builderError');
    if (!payload.name) { errorBox.textContent = 'Name is required'; return; }
    if (!payload.ingredients.length) { errorBox.textContent = 'Add at least one ingredient'; return; }
    try {
      if (editingId) await api(`/api/react/products/${editingId}/update/`, 'PUT', payload);
      else await api('/api/react/products/add/', 'POST', payload);
      builder.hide();
      showToast('Product saved', true);
      loadProducts();
    } catch (err) { errorBox.textContent = err.message; }
  });

  loadProducts();
})();
</script>
{% endblock %}
```

- [ ] **Step 5: Add the navbar link**

In `templates/includes/navbar.html`, change the Food Tracker toggle condition (line 12) to also match products:

```html
          <a class="nav-link dropdown-toggle {% if '/food_tracker' in request.path or '/meal-templates' in request.path or '/products' in request.path %}active{% endif %}" href="#" role="button" data-bs-toggle="dropdown">
```

and after the Meal Templates `</a></li>` (line 21) add:

```html
            <li><a class="dropdown-item {% if '/products' in request.path %}active{% endif %}" href="{% url 'products_page' %}">
              <i class="fas fa-layer-group me-1"></i>My Products
            </a></li>
```

- [ ] **Step 6: Add the food-tracker quick-log card**

In `count_calories_app/templates/count_calories_app/food_tracker.html`, directly after the closing `</div>` of the `<!-- ══ Meal Templates ══ -->` card add:

```html
      <!-- ══ My Products ══ -->
      <div class="card shadow-sm rounded mb-3">
        <div class="card-header bg-primary text-white d-flex align-items-center justify-content-between">
          <h2 class="h6 mb-0"><i class="fas fa-layer-group me-1"></i>My Products</h2>
          <a href="{% url 'products_page' %}" class="btn btn-sm btn-light py-0 px-2">Manage</a>
        </div>
        <div class="card-body py-2" id="productsQuickList"
             data-log-date="{% if selected_date %}{{ selected_date|date:'Y-m-d' }}{% endif %}">
          <span class="text-muted small">Loading…</span>
        </div>
      </div>
```

At the end of `{% block js_files %}` (just before its `{% endblock %}`) add:

```html
<script>
(function () {
  const box = document.getElementById('productsQuickList');
  if (!box) return;
  const token = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
  const logDate = box.dataset.logDate || null;

  fetch('/api/react/products/').then(r => r.json()).then(({products}) => {
    if (!products.length) {
      box.innerHTML = '<span class="text-muted small">No products yet. Use "Manage" to build one.</span>';
      return;
    }
    box.replaceChildren(...products.map(p => {
      const row = document.createElement('div');
      row.className = 'd-flex align-items-center gap-2 mb-1';
      const label = document.createElement('span');
      label.className = 'small flex-grow-1 text-truncate';
      label.textContent = `${p.name} · ${Math.round(p.per_serving.calories)} kcal`;
      const servings = document.createElement('input');
      Object.assign(servings, {type: 'number', min: '0.5', max: '100', step: '0.5', value: '1'});
      servings.className = 'form-control form-control-sm';
      servings.style.maxWidth = '70px';
      servings.setAttribute('aria-label', `Servings of ${p.name}`);
      const btn = document.createElement('button');
      btn.className = 'btn btn-sm btn-outline-primary py-0';
      btn.textContent = 'Log';
      btn.addEventListener('click', async () => {
        btn.disabled = true;
        const r = await fetch(`/api/react/products/${p.id}/log/`, {
          method: 'POST',
          headers: {'X-CSRFToken': token, 'Content-Type': 'application/json'},
          body: JSON.stringify({servings: Number(servings.value), ...(logDate && {date: logDate})}),
        });
        const data = await r.json();
        if (data.success) { location.reload(); return; }
        btn.disabled = false;
        label.textContent = data.error || 'Failed to log';
        label.classList.add('text-danger');
      });
      row.append(label, servings, btn);
      return row;
    }));
  }).catch(() => { box.innerHTML = '<span class="text-danger small">Could not load products.</span>'; });
})();
</script>
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `.venv/bin/python manage.py test count_calories_app.tests.test_products`
Expected: OK.

- [ ] **Step 8: Manual smoke check**

Run `.venv/bin/python manage.py runserver 8005`, open `http://127.0.0.1:8005/products/`. Create "Chicken tortilla" from 2 searched foods + 1 manual row, check live totals, save, log 1 serving. Then open `http://127.0.0.1:8005/food_tracker/?range=today`, confirm it appears in the diary as one row, and log from the My Products card. Stop the server.

- [ ] **Step 9: Commit**

```bash
git add count_calories_app/views_products.py count_calories_app/urls.py count_calories_app/templates/count_calories_app/products.html count_calories_app/templates/count_calories_app/food_tracker.html templates/includes/navbar.html count_calories_app/tests/test_products.py
git commit -m "feat(products): add Django My Products page and food tracker quick-log"
```

---

### Task 5: React products API and client-side math

**Files:**
- Create: `frontend/src/api/products.js`, `frontend/src/api/products.online.js`, `frontend/src/api/products.offline.js`
- Create: `frontend/src/pages/Products/productMath.js`
- Test: `frontend/src/pages/Products/__tests__/productMath.test.js`, `frontend/src/api/__tests__/products.test.js`

**Interfaces:**
- Consumes: Task 2 endpoints
- Produces:
  - `productsApi.list() -> Promise<{products}>`, `.create(payload)`, `.update(id, payload)`, `.delete(id)`, `.log(id, servings = 1, date = null)` — each resolves with the response JSON
  - `productsAvailable: boolean` (false offline and in test mode)
  - `productMath.MACROS`, `ingredientTotals(rows) -> {calories, protein, fat, carbohydrates}`, `perServing(totals, servingsYield)` (zeros when yield ≤ 0), `scaled(perServingValues, servings)` — numbers rounded to 2 dp

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/pages/Products/__tests__/productMath.test.js`:

```js
import { describe, it, expect } from 'vitest';
import { ingredientTotals, perServing, scaled } from '../productMath.js';

const rows = [
  { name: 'Wrap', calories: 200, protein: 6, fat: 5, carbohydrates: 33, quantity: 1 },
  { name: 'Chicken', calories: '330', protein: '62', fat: '7', carbohydrates: '0', quantity: '0.5' },
];

describe('productMath', () => {
  it('sums macros times quantity', () => {
    expect(ingredientTotals(rows)).toEqual({ calories: 365, protein: 37, fat: 8.5, carbohydrates: 33 });
  });

  it('treats blank or invalid values as zero', () => {
    expect(ingredientTotals([{ calories: '', protein: 'x', fat: null, carbohydrates: undefined, quantity: 2 }]))
      .toEqual({ calories: 0, protein: 0, fat: 0, carbohydrates: 0 });
  });

  it('divides by yield and rounds to 2 dp', () => {
    expect(perServing({ calories: 1000, protein: 10, fat: 1, carbohydrates: 0 }, 3))
      .toEqual({ calories: 333.33, protein: 3.33, fat: 0.33, carbohydrates: 0 });
  });

  it('returns zeros for a non-positive yield', () => {
    expect(perServing({ calories: 100, protein: 1, fat: 1, carbohydrates: 1 }, 0))
      .toEqual({ calories: 0, protein: 0, fat: 0, carbohydrates: 0 });
  });

  it('scales by servings', () => {
    expect(scaled({ calories: 250, protein: 20.5, fat: 3, carbohydrates: 10 }, 1.5).protein).toBe(30.75);
  });
});
```

Create `frontend/src/api/__tests__/products.test.js`:

```js
import { describe, it, expect } from 'vitest';

describe('products API selector', () => {
  it('uses the offline stub in test mode and reports products unavailable', async () => {
    const { productsApi, productsAvailable } = await import('../products');
    const { default: productsOffline } = await import('../products.offline');
    expect(productsApi).toBe(productsOffline);
    expect(productsAvailable).toBe(false);
  });

  it('offline stub rejects every call', async () => {
    const { default: productsOffline } = await import('../products.offline');
    await expect(productsOffline.list()).rejects.toThrow('Products are not available offline');
    await expect(productsOffline.log(1)).rejects.toThrow('Products are not available offline');
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run (from `frontend/`): `npx vitest run src/pages/Products src/api/__tests__/products.test.js`
Expected: FAIL — `Failed to resolve import "../productMath.js"` / `"../products"`.

- [ ] **Step 3: Implement the math**

Create `frontend/src/pages/Products/productMath.js`:

```js
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
```

- [ ] **Step 4: Implement the API modules**

Create `frontend/src/api/products.online.js`:

```js
// Online (browser) composite-products API — talks to the Django backend via axios.
import apiClient from './client';

export const productsApi = {
  list: async () => {
    const response = await apiClient.get('/api/react/products/');
    return response.data;
  },
  create: async (payload) => {
    const response = await apiClient.post('/api/react/products/add/', payload);
    return response.data;
  },
  update: async (productId, payload) => {
    const response = await apiClient.put(`/api/react/products/${productId}/update/`, payload);
    return response.data;
  },
  delete: async (productId) => {
    const response = await apiClient.delete(`/api/react/products/${productId}/delete/`);
    return response.data;
  },
  log: async (productId, servings = 1, date = null) => {
    const response = await apiClient.post(`/api/react/products/${productId}/log/`, { servings, ...(date && { date }) });
    return response.data;
  },
};

export default productsApi;
```

Create `frontend/src/api/products.offline.js`:

```js
// Offline composite-products API: not supported yet (phase 2). Same signatures as online.
const unavailable = () => Promise.reject(new Error('Products are not available offline'));

export const productsApi = {
  list: unavailable,
  create: unavailable,
  update: unavailable,
  delete: unavailable,
  log: unavailable,
};

export default productsApi;
```

Create `frontend/src/api/products.js`:

```js
const isOffline = import.meta.env.BASE_URL === './' || import.meta.env.VITE_OFFLINE === 'true' || import.meta.env.MODE === 'test';

import productsOffline from './products.offline';
import productsOnline from './products.online';

export const productsAvailable = !isOffline;
export const productsApi = isOffline ? productsOffline : productsOnline;
export default productsApi;
```

- [ ] **Step 5: Run tests to verify they pass**

Run (from `frontend/`): `npx vitest run src/pages/Products src/api/__tests__/products.test.js`
Expected: 7 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api/products.js frontend/src/api/products.online.js frontend/src/api/products.offline.js frontend/src/api/__tests__/products.test.js frontend/src/pages/Products/productMath.js frontend/src/pages/Products/__tests__/productMath.test.js
git commit -m "feat(react): add products API and client-side product math"
```

---

### Task 6: React "My Products" page and builder

**Files:**
- Create: `frontend/src/pages/Products/ProductBuilder.jsx`
- Create: `frontend/src/pages/Products/index.jsx`
- Modify: `frontend/src/pages/index.js` (add export)
- Modify: `frontend/src/App.jsx` (import + route after `top-foods`)
- Modify: `frontend/src/layouts/Sidebar.jsx` (icon import + nav item)
- Test: `frontend/src/pages/Products/__tests__/ProductBuilder.test.jsx`, `frontend/src/pages/Products/__tests__/Products.test.jsx`

**Interfaces:**
- Consumes: Task 5 (`productsApi`, `productsAvailable`, `ingredientTotals`, `perServing`); `foodApi.searchAllFoods(query, limit) -> {results: [{name, calories, protein, carbs, fat, is_product?}]}`
- Produces: `<ProductBuilder initial={product|null} onSave={async (payload) => void} onCancel={() => void} />`, where `payload = {name, servings_yield, ingredients:[{name, calories, protein, fat, carbohydrates, quantity}]}` (numbers); default export page `Products` at route `/products`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/pages/Products/__tests__/ProductBuilder.test.jsx`:

```jsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../../../api', () => ({
  foodApi: { searchAllFoods: vi.fn() },
}));

import { foodApi } from '../../../api';
import ProductBuilder from '../ProductBuilder';

describe('ProductBuilder', () => {
  beforeEach(() => {
    foodApi.searchAllFoods.mockReset();
    foodApi.searchAllFoods.mockResolvedValue({
      results: [{ name: 'Wrap', calories: 200, protein: 6, carbs: 33, fat: 5 }],
    });
  });

  it('adds an ingredient from search and updates totals', async () => {
    const user = userEvent.setup();
    render(<ProductBuilder initial={null} onSave={vi.fn()} onCancel={vi.fn()} />);

    await user.type(screen.getByLabelText('Search your foods'), 'wr');
    await user.click(await screen.findByRole('button', { name: /Wrap — 200 kcal/ }));

    expect(screen.getByDisplayValue('Wrap')).toBeInTheDocument();
    expect(screen.getByTestId('per-serving')).toHaveTextContent('200 kcal');
  });

  it('adds and removes manual rows', async () => {
    const user = userEvent.setup();
    render(<ProductBuilder initial={null} onSave={vi.fn()} onCancel={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: 'Add manual ingredient' }));
    await user.click(screen.getByRole('button', { name: 'Add manual ingredient' }));
    expect(screen.getAllByLabelText('Ingredient name')).toHaveLength(2);

    await user.click(screen.getAllByRole('button', { name: 'Remove ingredient' })[0]);
    expect(screen.getAllByLabelText('Ingredient name')).toHaveLength(1);
  });

  it('blocks submit without a name or ingredients', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    render(<ProductBuilder initial={null} onSave={onSave} onCancel={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: 'Save product' }));
    expect(screen.getByRole('alert')).toHaveTextContent('Name is required');
    expect(onSave).not.toHaveBeenCalled();
  });

  it('submits a numeric payload, dividing totals by yield', async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<ProductBuilder initial={null} onSave={onSave} onCancel={vi.fn()} />);

    await user.type(screen.getByLabelText('Product name'), 'Tortilla');
    const yieldInput = screen.getByLabelText('Makes N servings');
    await user.clear(yieldInput);
    await user.type(yieldInput, '2');
    await user.click(screen.getByRole('button', { name: 'Add manual ingredient' }));
    const row = screen.getAllByTestId('ingredient-row')[0];
    await user.type(within(row).getByLabelText('Ingredient name'), 'Cheese');
    const kcal = within(row).getByLabelText('Calories');
    await user.clear(kcal);
    await user.type(kcal, '100');

    expect(screen.getByTestId('per-serving')).toHaveTextContent('50 kcal');
    await user.click(screen.getByRole('button', { name: 'Save product' }));

    expect(onSave).toHaveBeenCalledWith({
      name: 'Tortilla',
      servings_yield: 2,
      ingredients: [{ name: 'Cheese', calories: 100, protein: 0, fat: 0, carbohydrates: 0, quantity: 1 }],
    });
  });

  it('prefills when editing', () => {
    const initial = {
      id: 3, name: 'Burrito', servings_yield: 1,
      ingredients: [{ id: 9, name: 'Beans', calories: 120, protein: 7, fat: 1, carbohydrates: 20, quantity: 2 }],
    };
    render(<ProductBuilder initial={initial} onSave={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByDisplayValue('Burrito')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Beans')).toBeInTheDocument();
    expect(screen.getByTestId('per-serving')).toHaveTextContent('240 kcal');
  });
});
```

Create `frontend/src/pages/Products/__tests__/Products.test.jsx`:

```jsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

vi.mock('../../../api/products', () => ({
  productsApi: {
    list: vi.fn(), create: vi.fn(), update: vi.fn(), delete: vi.fn(), log: vi.fn(),
  },
}));
vi.mock('../../../api', () => ({ foodApi: { searchAllFoods: vi.fn() } }));

import { productsApi } from '../../../api/products';
import Products from '../index';

const product = {
  id: 1, name: 'Chicken tortilla', servings_yield: 2, ingredient_count: 2,
  ingredients: [],
  totals: { calories: 365, protein: 37, fat: 8.5, carbohydrates: 33 },
  per_serving: { calories: 182.5, protein: 18.5, fat: 4.25, carbohydrates: 16.5 },
};

describe('Products page', () => {
  beforeEach(() => {
    Object.values(productsApi).forEach((fn) => fn.mockReset());
    productsApi.list.mockResolvedValue({ products: [product] });
    productsApi.log.mockResolvedValue({ success: true });
    productsApi.delete.mockResolvedValue({ success: true });
  });

  it('renders products from the API', async () => {
    render(<Products />);
    expect(await screen.findByText('Chicken tortilla')).toBeInTheDocument();
    expect(screen.getByText(/183 kcal/)).toBeInTheDocument();
  });

  it('logs the chosen servings', async () => {
    const user = userEvent.setup();
    render(<Products />);
    const servings = await screen.findByLabelText('Servings of Chicken tortilla');
    await user.clear(servings);
    await user.type(servings, '1.5');
    await user.click(screen.getByRole('button', { name: 'Log' }));
    expect(productsApi.log).toHaveBeenCalledWith(1, 1.5, expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/));
  });

  it('deletes after inline confirm', async () => {
    const user = userEvent.setup();
    render(<Products />);
    await user.click(await screen.findByRole('button', { name: 'Delete' }));
    await user.click(screen.getByRole('button', { name: 'Confirm delete' }));
    expect(productsApi.delete).toHaveBeenCalledWith(1);
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run (from `frontend/`): `npx vitest run src/pages/Products`
Expected: FAIL — `Failed to resolve import "../ProductBuilder"` / `"../index"`.

- [ ] **Step 3: Implement the builder**

Create `frontend/src/pages/Products/ProductBuilder.jsx`:

```jsx
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
```

- [ ] **Step 4: Implement the page**

Create `frontend/src/pages/Products/index.jsx`:

```jsx
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
```

Note: `Button` spreads `...props`, so `aria-label="Confirm delete"` reaches the `<button>`. `displayKcal` (in `frontend/src/utils/format.js`) rounds to an integer string, so 182.5 renders as `183`.

- [ ] **Step 5: Wire route and sidebar**

`frontend/src/pages/index.js`, add:

```js
export { default as Products } from './Products';
```

`frontend/src/App.jsx`: add `Products,` to the `./pages` import list, and after `<Route path="top-foods" element={<TopFoods />} />` add:

```jsx
          <Route path="products" element={<Products />} />
```

`frontend/src/layouts/Sidebar.jsx`: add `Layers,` to the lucide import list, add `import { productsAvailable } from '../api/products';` below the imports, and change `navigation` to:

```js
const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Food Tracker', href: '/food', icon: Utensils },
  ...(productsAvailable ? [{ name: 'My Products', href: '/products', icon: Layers }] : []),
  { name: 'Weight Tracker', href: '/weight', icon: Scale },
  { name: 'Workout Tracker', href: '/workout', icon: Dumbbell },
  { name: 'Running Tracker', href: '/running', icon: Activity },
  { name: 'Body Measurements', href: '/body-measurements', icon: Ruler },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Top Foods', href: '/top-foods', icon: Trophy },
  { name: 'Settings', href: '/settings', icon: Settings },
];
```

- [ ] **Step 6: Run tests to verify they pass**

Run (from `frontend/`): `npx vitest run src/pages/Products`
Expected: all PASS (5 math + 5 builder + 3 page).

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/Products frontend/src/pages/index.js frontend/src/App.jsx frontend/src/layouts/Sidebar.jsx
git commit -m "feat(react): add My Products page with ingredient builder"
```

---

### Task 7: Food Tracker integration, build and full verification

**Files:**
- Modify: `frontend/src/pages/FoodTracker.jsx` (imports ~line 39; `handleDbQuickAdd` ~line 272; `handleQuickAdd` ~line 489; search result row ~line 630–660; quick-add tile ~line 992–1005)
- Build output: `static/react/` (regenerated)

**Interfaces:**
- Consumes: Task 3 response contract (`is_product`, `product_id`), Task 5 `productsApi.log(id, servings, date)`

- [ ] **Step 1: Import the products API**

After `import { foodApi, settingsApi } from '../api';` add:

```js
import { productsApi } from '../api/products';
```

- [ ] **Step 2: Route product clicks through the log endpoint**

At the start of the `try {` block in **both** `handleDbQuickAdd` and `handleQuickAdd` insert:

```js
      if (food.is_product) {
        await productsApi.log(food.product_id, 1, format(selectedDate, 'yyyy-MM-dd'));
        fetchFoodItems();
        return;
      }
```

- [ ] **Step 3: Show a Recipe badge and hide "Edit" for products**

In the database-search result row, replace

```jsx
                        <div className="font-medium text-gray-100 truncate">
                          {food.name}
                        </div>
```

with

```jsx
                        <div className="font-medium text-gray-100 truncate flex items-center gap-2">
                          {food.name}
                          {food.is_product && <Badge variant="purple" size="sm">Recipe</Badge>}
                        </div>
```

and wrap that row's Edit `<Button ... onClick={() => handleDbEditAdd(food)}>…</Button>` in `{!food.is_product && ( … )}`.

In the Quick Add tile, replace

```jsx
                    <div className="text-sm font-medium text-gray-100 group-hover:text-primary-400 truncate">
                      {food.name}
                    </div>
```

with

```jsx
                    <div className="text-sm font-medium text-gray-100 group-hover:text-primary-400 truncate">
                      {food.name}
                    </div>
                    {food.is_product && <Badge variant="purple" size="sm" className="mt-1">Recipe</Badge>}
```

(`Badge` is already imported from `../components/ui`.)

- [ ] **Step 4: Run the full frontend suite and lint**

Run (from `frontend/`): `npm test -- --run`
Expected: all tests pass.

- [ ] **Step 5: Build the React app**

Run (from `frontend/`): `npm run build`
Expected: build succeeds and writes to `../static/react/`.

- [ ] **Step 6: Run the full Django suite**

Run: `.venv/bin/python manage.py test count_calories_app`
Expected: all tests pass (existing ~369 plus the new ones), 0 failures.

- [ ] **Step 7: Manual end-to-end check (React)**

With `.venv/bin/python manage.py runserver 8005` running, open `http://127.0.0.1:8005/app/#/products`. Create a product, log 1.5 servings, and confirm it shows as one row on `#/food`. Check the quick-add tile has the Recipe badge and logs 1 serving on click, and that searching the product name shows the badge with no Edit button. Stop the server.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/pages/FoodTracker.jsx static/react
git commit -m "feat(react): log composite products from Food Tracker quick-add and search"
```

(If `git status` shows old hashed files under `static/react/assets` as deleted, `git add static/react` stages those deletions too, matching how earlier build commits were made.)

---

## Done criteria

- Both test suites green; React rebuilt.
- `/products/` (Django) and `/app/#/products` (React) can create, edit, delete and log products; food tracker quick-log works on both.
- A logged product is one `FoodItem`; editing or deleting a product leaves history unchanged.
- Nothing pushed; `utils.py` untouched.
