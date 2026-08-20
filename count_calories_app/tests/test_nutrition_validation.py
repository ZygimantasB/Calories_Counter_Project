"""Guards against the AI writing implausible nutrition into the food log.

A banana was once logged at 15g protein because GeminiService accepted whatever
the model returned. Two independent checks now run on a lookup:

1. Atwater consistency -- protein*4 + carbs*4 + fat*9 should approximate the
   stated calories. Catches a model that contradicts itself.
2. Disagreement with history -- if the same food name was logged before with
   materially different values, say so. Catches a model that is internally
   consistent but factually wrong, which is exactly how 15g-protein bananas
   got in.

Both surface as warnings, not hard failures: alcohol, fibre and polyols all
break Atwater legitimately, and a portion size really can change.
Only physically impossible values (negatives) are rejected outright.
"""

import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from count_calories_app.models import FoodItem
from count_calories_app.services import GeminiService


def _mock_genai(mock_genai, payload):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps(payload)
    mock_client.models.generate_content.return_value = mock_response
    mock_genai.Client.return_value = mock_client


class AtwaterConsistencyTestCase(TestCase):
    @patch('count_calories_app.services.genai')
    def test_consistent_macros_produce_no_warning(self, mock_genai):
        _mock_genai(mock_genai, {
            'product_name': 'Banana', 'calories': 105,
            'protein': 1.3, 'fat': 0.4, 'carbohydrates': 27,
        })
        with self.settings(GEMINI_API_KEY='fake'):
            result = GeminiService.get_nutrition_info('Banana')
        self.assertTrue(result['success'])
        self.assertEqual(result['warnings'], [])

    @patch('count_calories_app.services.genai')
    def test_macros_contradicting_calories_warn(self, mock_genai):
        # 19.4*4 + 1.2*4 + 6*9 = 136 kcal, but 278 was claimed.
        _mock_genai(mock_genai, {
            'product_name': 'Omletas', 'calories': 278,
            'protein': 19.4, 'fat': 6, 'carbohydrates': 1.2,
        })
        with self.settings(GEMINI_API_KEY='fake'):
            result = GeminiService.get_nutrition_info('Omletas')
        self.assertTrue(result['success'], 'a warning must not block the lookup')
        self.assertEqual(len(result['warnings']), 1)
        self.assertIn('136', result['warnings'][0])
        self.assertIn('278', result['warnings'][0])

    @patch('count_calories_app.services.genai')
    def test_small_discrepancy_is_tolerated(self, mock_genai):
        _mock_genai(mock_genai, {
            'product_name': 'Oats', 'calories': 268.64,
            'protein': 11.28, 'fat': 5.6, 'carbohydrates': 43.28,
        })
        with self.settings(GEMINI_API_KEY='fake'):
            result = GeminiService.get_nutrition_info('Oats')
        self.assertEqual(result['warnings'], [])

    @patch('count_calories_app.services.genai')
    def test_negative_values_are_rejected(self, mock_genai):
        _mock_genai(mock_genai, {
            'product_name': 'Broken', 'calories': 100,
            'protein': -5, 'fat': 1, 'carbohydrates': 10,
        })
        with self.settings(GEMINI_API_KEY='fake'):
            result = GeminiService.get_nutrition_info('Broken')
        self.assertFalse(result['success'])
        self.assertIn('negative', result['error'].lower())

    @patch('count_calories_app.services.genai')
    def test_zero_calorie_foods_do_not_warn(self, mock_genai):
        _mock_genai(mock_genai, {
            'product_name': 'Water', 'calories': 0,
            'protein': 0, 'fat': 0, 'carbohydrates': 0,
        })
        with self.settings(GEMINI_API_KEY='fake'):
            result = GeminiService.get_nutrition_info('Water')
        self.assertTrue(result['success'])
        self.assertEqual(result['warnings'], [])


class DisagreesWithHistoryTestCase(TestCase):
    """The check that would actually have caught the 15g-protein banana."""

    def setUp(self):
        self.client = Client()
        FoodItem.objects.create(
            product_name='Bananas (1)', calories=Decimal('105'),
            protein=Decimal('1.3'), fat=Decimal('0.4'),
            carbohydrates=Decimal('27'), consumed_at=timezone.now(),
        )

    def _lookup(self, mock_genai, payload):
        _mock_genai(mock_genai, payload)
        with self.settings(GEMINI_API_KEY='fake'):
            response = self.client.post(
                reverse('gemini_nutrition'),
                data=json.dumps({'food_name': payload['product_name']}),
                content_type='application/json',
            )
        return response

    @patch('count_calories_app.services.genai')
    def test_warns_when_ai_contradicts_previous_entries(self, mock_genai):
        # Internally consistent (15*4 + 0.5*9 + 26*4 = 168.5) but 11x the
        # protein this food was logged with before.
        response = self._lookup(mock_genai, {
            'product_name': 'Bananas (1)', 'calories': 168.5,
            'protein': 15, 'fat': 0.5, 'carbohydrates': 26,
        })
        self.assertEqual(response.status_code, 200)
        warnings = json.loads(response.content)['warnings']
        self.assertTrue(any('previously' in w for w in warnings), warnings)
        self.assertTrue(any('1.3' in w for w in warnings), warnings)

    @patch('count_calories_app.services.genai')
    def test_no_warning_when_ai_agrees_with_history(self, mock_genai):
        response = self._lookup(mock_genai, {
            'product_name': 'Bananas (1)', 'calories': 105,
            'protein': 1.3, 'fat': 0.4, 'carbohydrates': 27,
        })
        self.assertEqual(json.loads(response.content)['warnings'], [])

    @patch('count_calories_app.services.genai')
    def test_no_warning_for_a_food_never_logged_before(self, mock_genai):
        response = self._lookup(mock_genai, {
            'product_name': 'Something New', 'calories': 200,
            'protein': 10, 'fat': 5, 'carbohydrates': 30,
        })
        self.assertEqual(json.loads(response.content)['warnings'], [])
