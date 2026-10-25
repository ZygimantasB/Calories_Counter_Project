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
