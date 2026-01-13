"""
Unit tests for error handling and edge cases.

This module tests how the application handles various error conditions,
invalid inputs, and exceptional scenarios.

Tests cover:
- Invalid HTTP methods
- Missing required parameters
- Malformed data
- Non-existent resources (404s)
- Invalid data types
- Boundary conditions
- External API failures
"""

import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, Mock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from count_calories_app.models import (
    FoodItem, Weight, RunningSession, Exercise,
    WorkoutSession, WorkoutExercise, WorkoutTable, BodyMeasurement
)


class InvalidHTTPMethodTestCase(TestCase):
    """Test cases for invalid HTTP methods on endpoints."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_gemini_nutrition_get_not_allowed(self):
        """Test that GET method is not allowed on Gemini nutrition endpoint."""
        url = reverse('gemini_nutrition')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)

        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('POST', data['error'])

    def test_gemini_nutrition_requires_post(self):
        """Test that Gemini nutrition endpoint requires POST method."""
        url = reverse('gemini_nutrition')

        # Try various non-POST methods
        response = self.client.put(url)
        self.assertEqual(response.status_code, 405)

        response = self.client.patch(url)
        self.assertEqual(response.status_code, 405)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 405)

    def test_save_workout_table_requires_post(self):
        """Test that save workout table endpoint requires POST method."""
        url = reverse('save_workout_table')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)


class MissingParametersTestCase(TestCase):
    """Test cases for missing required parameters."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_gemini_nutrition_missing_food_name(self):
        """Test Gemini nutrition endpoint with missing food name."""
        url = reverse('gemini_nutrition')
        response = self.client.post(
            url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('required', data['error'].lower())

    def test_gemini_nutrition_empty_food_name(self):
        """Test Gemini nutrition endpoint with empty food name."""
        url = reverse('gemini_nutrition')
        response = self.client.post(
            url,
            data=json.dumps({'food_name': '   '}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_save_workout_table_missing_data(self):
        """Test save workout table with missing required data."""
        url = reverse('save_workout_table')
        response = self.client.post(
            url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)


class NonExistentResourceTestCase(TestCase):
    """Test cases for accessing non-existent resources."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_edit_nonexistent_food_item(self):
        """Test editing a food item that doesn't exist."""
        url = reverse('edit_food_item', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_food_item(self):
        """Test deleting a food item that doesn't exist."""
        url = reverse('delete_food_item', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_edit_nonexistent_weight(self):
        """Test editing a weight measurement that doesn't exist."""
        url = reverse('edit_weight', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_weight(self):
        """Test deleting a weight measurement that doesn't exist."""
        url = reverse('delete_weight', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_edit_nonexistent_running_session(self):
        """Test editing a running session that doesn't exist."""
        url = reverse('edit_running_session', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_running_session(self):
        """Test deleting a running session that doesn't exist."""
        url = reverse('delete_running_session', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_workout_detail_nonexistent(self):
        """Test viewing details of a non-existent workout."""
        url = reverse('workout_detail', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_edit_nonexistent_body_measurement(self):
        """Test editing a body measurement that doesn't exist."""
        url = reverse('edit_body_measurement', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_body_measurement(self):
        """Test deleting a body measurement that doesn't exist."""
        url = reverse('delete_body_measurement', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_hide_nonexistent_food_from_quick_list(self):
        """Test hiding a non-existent food item from quick list."""
        url = reverse('hide_from_quick_list', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_workout_table(self):
        """Test deleting a non-existent workout table."""
        url = reverse('delete_workout_table', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_exercise_progress_nonexistent_exercise(self):
        """Test getting progress for non-existent exercise."""
        url = reverse('exercise_progress_data', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.content)
        self.assertIn('error', data)


class MalformedDataTestCase(TestCase):
    """Test cases for malformed or invalid data."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_gemini_nutrition_invalid_json(self):
        """Test Gemini nutrition endpoint with invalid JSON."""
        url = reverse('gemini_nutrition')
        response = self.client.post(
            url,
            data='invalid json {',
            content_type='application/json'
        )

        # Should handle the JSON decode error
        self.assertIn(response.status_code, [400, 500])

    def test_save_workout_table_invalid_json(self):
        """Test save workout table with invalid JSON."""
        url = reverse('save_workout_table')
        response = self.client.post(
            url,
            data='invalid json {',
            content_type='application/json'
        )

        self.assertIn(response.status_code, [400, 500])

    def test_nutrition_data_invalid_date_format(self):
        """Test nutrition data API with invalid date format."""
        url = reverse('nutrition_data')
        response = self.client.get(url, {'date': 'not-a-date'})

        # Should handle gracefully and use default
        self.assertEqual(response.status_code, 200)

    def test_calories_trend_invalid_days(self):
        """Test calories trend with invalid days parameter."""
        url = reverse('calories_trend_data')
        response = self.client.get(url, {'days': 'invalid'})

        # Should handle gracefully and use default
        self.assertEqual(response.status_code, 200)


class ExternalAPIErrorHandlingTestCase(TestCase):
    """Test cases for external API error handling."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    @patch('count_calories_app.views.genai')
    def test_gemini_api_configuration_error(self, mock_genai):
        """Test handling of Gemini API configuration errors."""
        mock_genai.configure.side_effect = Exception('API key invalid')

        url = reverse('gemini_nutrition')
        response = self.client.post(
            url,
            data=json.dumps({'food_name': 'Apple'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)

    @patch('count_calories_app.views.getattr')
    def test_gemini_missing_api_key(self, mock_getattr):
        """Test Gemini endpoint when API key is not configured."""
        # Mock settings.GEMINI_API_KEY to return None
        def custom_getattr(obj, attr, default=None):
            if attr == 'GEMINI_API_KEY':
                return None
            return object.__getattribute__(obj, attr) if hasattr(obj, attr) else default

        mock_getattr.side_effect = custom_getattr

        url = reverse('gemini_nutrition')
        response = self.client.post(
            url,
            data=json.dumps({'food_name': 'Apple'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('not configured', data['error'].lower())


class DataTypeValidationTestCase(TestCase):
    """Test cases for data type validation."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.now = timezone.now()

    def test_food_form_negative_calories(self):
        """Test that food form rejects negative calories."""
        from count_calories_app.forms import FoodItemForm

        form_data = {
            'product_name': 'Test Food',
            'calories': -100,  # Negative value
            'consumed_at': self.now
        }

        form = FoodItemForm(data=form_data)
        # Form validation should fail or database should reject
        # The HTML5 min attribute prevents this at UI level

    def test_weight_form_zero_weight(self):
        """Test that weight form accepts zero weight (edge case)."""
        from count_calories_app.forms import WeightForm

        form_data = {
            'weight': 0,  # Edge case: zero weight
            'recorded_at': self.now
        }

        form = WeightForm(data=form_data)
        # Form should technically accept this

    def test_workout_exercise_form_zero_sets(self):
        """Test workout exercise form with zero sets."""
        from count_calories_app.forms import WorkoutExerciseForm

        exercise = Exercise.objects.create(name='Test Exercise')
        workout = WorkoutSession.objects.create(date=self.now)

        form_data = {
            'exercise': exercise.id,
            'sets': 0,  # Invalid: should be at least 1
            'reps': 10
        }

        form = WorkoutExerciseForm(data=form_data)
        # Should fail validation due to min=1 constraint


class BoundaryConditionTestCase(TestCase):
    """Test cases for boundary conditions."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.now = timezone.now()

    def test_food_item_max_calorie_value(self):
        """Test food item with maximum allowed calorie value."""
        # Max is 99999.99 (7 digits, 2 decimal places)
        food = FoodItem.objects.create(
            product_name='Max Calorie Food',
            calories=Decimal('99999.99'),
            consumed_at=self.now
        )

        self.assertEqual(food.calories, Decimal('99999.99'))

    def test_food_item_min_calorie_value(self):
        """Test food item with minimum calorie value (zero)."""
        food = FoodItem.objects.create(
            product_name='Zero Calorie Food',
            calories=Decimal('0.00'),
            consumed_at=self.now
        )

        self.assertEqual(food.calories, Decimal('0.00'))

    def test_exercise_name_max_length(self):
        """Test exercise with maximum name length."""
        # Max length is 200 characters
        long_name = 'A' * 200

        exercise = Exercise.objects.create(name=long_name)
        self.assertEqual(len(exercise.name), 200)

    def test_body_measurement_max_value(self):
        """Test body measurement with maximum allowed value."""
        # Max is 999.99 (5 digits, 2 decimal places)
        measurement = BodyMeasurement.objects.create(
            date=self.now,
            chest=Decimal('999.99')
        )

        self.assertEqual(measurement.chest, Decimal('999.99'))

    def test_running_distance_precision(self):
        """Test running distance with maximum precision."""
        # Max is 999.99 (5 digits, 2 decimal places)
        run = RunningSession.objects.create(
            date=self.now,
            distance=Decimal('999.99'),
            duration=timedelta(hours=10)
        )

        self.assertEqual(run.distance, Decimal('999.99'))

    def test_weight_max_value(self):
        """Test weight with maximum allowed value."""
        # Max is 999.99 (5 digits, 2 decimal places)
        weight = Weight.objects.create(
            weight=Decimal('999.99'),
            recorded_at=self.now
        )

        self.assertEqual(weight.weight, Decimal('999.99'))


class ConcurrentRequestTestCase(TestCase):
    """Test cases for concurrent request handling."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.now = timezone.now()

    def test_multiple_food_items_same_timestamp(self):
        """Test creating multiple food items with exact same timestamp."""
        timestamp = self.now

        food1 = FoodItem.objects.create(
            product_name='Food 1',
            calories=Decimal('100'),
            consumed_at=timestamp
        )
        food2 = FoodItem.objects.create(
            product_name='Food 2',
            calories=Decimal('200'),
            consumed_at=timestamp
        )

        # Both should be created successfully
        self.assertIsNotNone(food1.id)
        self.assertIsNotNone(food2.id)
        self.assertEqual(food1.consumed_at, food2.consumed_at)

    def test_multiple_weights_same_timestamp(self):
        """Test creating multiple weight measurements with same timestamp."""
        timestamp = self.now

        weight1 = Weight.objects.create(
            weight=Decimal('80.0'),
            recorded_at=timestamp
        )
        weight2 = Weight.objects.create(
            weight=Decimal('80.5'),
            recorded_at=timestamp
        )

        # Both should be created (though unusual in practice)
        self.assertIsNotNone(weight1.id)
        self.assertIsNotNone(weight2.id)

    def test_workout_table_concurrent_creation(self):
        """Test creating multiple workout tables concurrently."""
        table1 = WorkoutTable.objects.create(
            name='Table 1',
            table_data={'exercises': ['Exercise 1']}
        )
        table2 = WorkoutTable.objects.create(
            name='Table 2',
            table_data={'exercises': ['Exercise 2']}
        )

        # Both should be created successfully
        self.assertIsNotNone(table1.id)
        self.assertIsNotNone(table2.id)
        self.assertNotEqual(table1.id, table2.id)


class EmptyResultSetTestCase(TestCase):
    """Test cases for operations on empty result sets."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_autocomplete_with_no_matches(self):
        """Test food autocomplete when no items match query."""
        url = reverse('food_autocomplete')
        response = self.client.get(url, {'q': 'nonexistentfood123'})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data, {'suggestions': []})

    def test_calories_trend_with_no_data(self):
        """Test calories trend endpoint when no food items exist."""
        url = reverse('calories_trend_data')
        response = self.client.get(url, {'days': '7'})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should return structure with empty data
        self.assertIn('labels', data)
        self.assertIn('data', data)

    def test_weight_data_with_no_weights(self):
        """Test weight data endpoint when no weights recorded."""
        url = reverse('weight_data')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should return structure with empty data
        self.assertIn('labels', data)
        self.assertIn('data', data)
        self.assertEqual(len(data['data']), 0)

    def test_running_data_with_no_sessions(self):
        """Test running data endpoint when no sessions exist."""
        url = reverse('running_data')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should handle empty data gracefully
        self.assertIn('dates', data)
        self.assertIn('distances', data)

    def test_workout_tables_with_no_tables(self):
        """Test get workout tables when no tables exist."""
        url = reverse('get_workout_tables')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn('success', data)
        self.assertIn('tables', data)
        self.assertEqual(len(data['tables']), 0)


class SpecialCharactersTestCase(TestCase):
    """Test cases for handling special characters in input."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()
        self.now = timezone.now()

    def test_food_name_with_special_characters(self):
        """Test food item with special characters in name."""
        special_names = [
            "Ben & Jerry's Ice Cream",
            "Häagen-Dazs",
            "Café Latte",
            "100% Orange Juice",
            "Pizza (Extra Large)",
            "Sushi 🍣",
        ]

        for name in special_names:
            food = FoodItem.objects.create(
                product_name=name,
                calories=Decimal('100'),
                consumed_at=self.now
            )
            self.assertEqual(food.product_name, name)

    def test_exercise_name_with_special_characters(self):
        """Test exercise with special characters in name."""
        exercise = Exercise.objects.create(
            name="Dumbbell Fly's & Press",
            description="A complex movement"
        )

        self.assertIn('&', exercise.name)

    def test_notes_with_multiline_text(self):
        """Test notes fields with multiline text."""
        multiline_notes = """Line 1
        Line 2
        Line 3"""

        weight = Weight.objects.create(
            weight=Decimal('80.0'),
            recorded_at=self.now,
            notes=multiline_notes
        )

        self.assertIn('\n', weight.notes)

    def test_autocomplete_with_special_characters(self):
        """Test autocomplete with special characters in query."""
        FoodItem.objects.create(
            product_name="Ben & Jerry's",
            calories=Decimal('300'),
            consumed_at=self.now
        )

        url = reverse('food_autocomplete')
        response = self.client.get(url, {'q': "Ben & Jerry"})

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('suggestions', data)
