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
