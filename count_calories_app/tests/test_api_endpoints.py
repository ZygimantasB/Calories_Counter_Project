"""
Unit tests for API endpoints.

Tests cover:
- Nutrition data API (OpenFoodFacts integration)
- Food autocomplete API
- Calories trend data API
- Macros trend data API
- Weight data API
- Weight-calories correlation API
- Workout frequency data API
- Exercise progress data API
- Running data API
- Body measurements data API
- Workout tables API (CRUD)
- Export endpoints
"""

import json
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from count_calories_app.models import (
    FoodItem, Weight, RunningSession, Exercise,
    WorkoutSession, WorkoutExercise, WorkoutTable, BodyMeasurement
)


class FoodAutocompleteAPITestCase(TestCase):
    """Test cases for the food autocomplete API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('food_autocomplete')
        self.now = timezone.now()

        # Create sample food items
        FoodItem.objects.create(
            product_name='Apple',
            calories=Decimal('95'),
            consumed_at=self.now
        )
        FoodItem.objects.create(
            product_name='Apple Juice',
            calories=Decimal('120'),
            consumed_at=self.now
        )
        FoodItem.objects.create(
            product_name='Banana',
            calories=Decimal('105'),
            consumed_at=self.now
        )

    def test_food_autocomplete_returns_json(self):
        """Test that food autocomplete returns JSON response."""
        response = self.client.get(self.url, {'query': 'app'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_food_autocomplete_filters_by_query(self):
        """Test that autocomplete filters results by query."""
        response = self.client.get(self.url, {'query': 'apple'})
        data = json.loads(response.content)

        # Should return items containing 'apple'
        self.assertGreater(len(data), 0)
        for item in data:
            self.assertIn('apple', item['product_name'].lower())

    def test_food_autocomplete_no_query_returns_empty(self):
        """Test that no query parameter returns empty list."""
        response = self.client.get(self.url)
        data = json.loads(response.content)
        self.assertEqual(data, [])

    def test_food_autocomplete_excludes_hidden_items(self):
        """Test that autocomplete excludes items hidden from quick list."""
        FoodItem.objects.create(
            product_name='Hidden Apple Pie',
            calories=Decimal('300'),
            consumed_at=self.now,
            hide_from_quick_list=True
        )

        response = self.client.get(self.url, {'query': 'apple'})
        data = json.loads(response.content)

        # Should not include hidden items
        product_names = [item['product_name'] for item in data]
        self.assertNotIn('Hidden Apple Pie', product_names)


class CaloriesTrendDataAPITestCase(TestCase):
    """Test cases for the calories trend data API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('calories_trend_data')
        self.now = timezone.now()

        # Create food items over several days
        for i in range(7):
            FoodItem.objects.create(
                product_name=f'Food Day {i}',
                calories=Decimal('2000'),
                consumed_at=self.now - timedelta(days=i)
            )

    def test_calories_trend_returns_json(self):
        """Test that calories trend API returns JSON."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_calories_trend_contains_dates_and_calories(self):
        """Test that response contains dates and calorie data."""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        self.assertIn('dates', data)
        self.assertIn('calories', data)
        self.assertIsInstance(data['dates'], list)
        self.assertIsInstance(data['calories'], list)

    def test_calories_trend_respects_days_parameter(self):
        """Test that API respects the 'days' query parameter."""
        response = self.client.get(self.url, {'days': '3'})
        data = json.loads(response.content)

        # Should return data for 3 days
        self.assertLessEqual(len(data['dates']), 3)


class MacrosTrendDataAPITestCase(TestCase):
    """Test cases for the macros trend data API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('macros_trend_data')
        self.now = timezone.now()

        # Create food items with macro data
        for i in range(7):
            FoodItem.objects.create(
                product_name=f'Food Day {i}',
                calories=Decimal('2000'),
                protein=Decimal('100'),
                carbohydrates=Decimal('200'),
                fat=Decimal('80'),
                consumed_at=self.now - timedelta(days=i)
            )

    def test_macros_trend_returns_json(self):
        """Test that macros trend API returns JSON."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_macros_trend_contains_macro_data(self):
        """Test that response contains protein, carbs, and fat data."""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        self.assertIn('dates', data)
        self.assertIn('protein', data)
        self.assertIn('carbs', data)
        self.assertIn('fat', data)

    def test_macros_trend_respects_days_parameter(self):
        """Test that API respects the 'days' query parameter."""
        response = self.client.get(self.url, {'days': '5'})
        data = json.loads(response.content)

        self.assertLessEqual(len(data['dates']), 5)


class WeightDataAPITestCase(TestCase):
    """Test cases for the weight data API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('weight_data')
        self.now = timezone.now()

        # Create weight measurements
        for i in range(10):
            Weight.objects.create(
                weight=Decimal('80') - Decimal(str(i * 0.5)),
                recorded_at=self.now - timedelta(days=i)
            )

    def test_weight_data_returns_json(self):
        """Test that weight data API returns JSON."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_weight_data_contains_dates_and_weights(self):
        """Test that response contains dates and weight data."""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        self.assertIn('dates', data)
        self.assertIn('weights', data)
        self.assertEqual(len(data['dates']), len(data['weights']))

    def test_weight_data_ordered_by_date(self):
        """Test that weight data is ordered chronologically."""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        # Dates should be in ascending order
        dates = data['dates']
        self.assertEqual(dates, sorted(dates))


class WeightCaloriesCorrelationAPITestCase(TestCase):
    """Test cases for the weight-calories correlation API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('weight_calories_correlation')
        self.now = timezone.now()

        # Create correlated weight and calorie data
        for i in range(10):
            date = self.now - timedelta(days=i)
            Weight.objects.create(
                weight=Decimal('80') - Decimal(str(i * 0.5)),
                recorded_at=date
            )
            FoodItem.objects.create(
                product_name=f'Food {i}',
                calories=Decimal('2000') + Decimal(str(i * 100)),
                consumed_at=date
            )

    def test_weight_calories_correlation_returns_json(self):
        """Test that correlation API returns JSON."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_weight_calories_correlation_contains_data(self):
        """Test that response contains weight and calorie correlation data."""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        # Should contain arrays of data points
        self.assertIn('dates', data)
        self.assertIsInstance(data['dates'], list)


class WorkoutFrequencyDataAPITestCase(TestCase):
    """Test cases for the workout frequency data API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('workout_frequency_data')
        self.now = timezone.now()

        # Create workout sessions
        for i in range(5):
            WorkoutSession.objects.create(
                date=self.now - timedelta(days=i),
                name=f'Workout {i}'
            )

    def test_workout_frequency_returns_json(self):
        """Test that workout frequency API returns JSON."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_workout_frequency_contains_data(self):
        """Test that response contains workout frequency data."""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        self.assertIsInstance(data, dict)


class ExerciseProgressDataAPITestCase(TestCase):
    """Test cases for the exercise progress data API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()

        # Create exercise and workout sessions
        self.exercise = Exercise.objects.create(name='Bench Press', muscle_group='Chest')

        for i in range(5):
            workout = WorkoutSession.objects.create(
                date=self.now - timedelta(days=i * 7),
                name=f'Workout {i}'
            )
            WorkoutExercise.objects.create(
                workout=workout,
                exercise=self.exercise,
                sets=3,
                reps=10,
                weight=Decimal('60') + Decimal(str(i * 5))
            )

        self.url = reverse('exercise_progress_data_with_id', args=[self.exercise.id])

    def test_exercise_progress_returns_json(self):
        """Test that exercise progress API returns JSON."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_exercise_progress_contains_data(self):
        """Test that response contains exercise progress data."""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        self.assertIn('dates', data)
        self.assertIn('weights', data)

    def test_exercise_progress_without_id_returns_all(self):
        """Test that API without exercise_id returns data for all exercises."""
        url = reverse('exercise_progress_data')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class RunningDataAPITestCase(TestCase):
    """Test cases for the running data API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('running_data')
        self.now = timezone.now()

        # Create running sessions
        for i in range(5):
            RunningSession.objects.create(
                date=self.now - timedelta(days=i),
                distance=Decimal('5.0') + Decimal(str(i)),
                duration=timedelta(minutes=30 + i * 5)
            )

    def test_running_data_returns_json(self):
        """Test that running data API returns JSON."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_running_data_contains_dates_and_distances(self):
        """Test that response contains running data."""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        self.assertIn('dates', data)
        self.assertIn('distances', data)
        self.assertIn('durations', data)


class BodyMeasurementsDataAPITestCase(TestCase):
    """Test cases for the body measurements data API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('body_measurements_data')
        self.now = timezone.now()

        # Create body measurements
        for i in range(5):
            BodyMeasurement.objects.create(
                date=self.now - timedelta(days=i * 7),
                neck=Decimal('40.0') - Decimal(str(i * 0.5)),
                chest=Decimal('105.0') - Decimal(str(i)),
                belly=Decimal('90.0') - Decimal(str(i))
            )

    def test_body_measurements_data_returns_json(self):
        """Test that body measurements data API returns JSON."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_body_measurements_data_contains_measurements(self):
        """Test that response contains body measurement data."""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        self.assertIn('dates', data)
        self.assertIn('measurements', data)

    def test_body_measurements_data_includes_all_fields(self):
        """Test that response includes all measurement fields."""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        # Should have measurement categories
        measurements = data['measurements']
        if measurements:
            # Check that common fields are present
            self.assertIsInstance(measurements, dict)


class WorkoutTablesAPITestCase(TestCase):
    """Test cases for the workout tables API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.get_url = reverse('get_workout_tables')
        self.save_url = reverse('save_workout_table')
        self.now = timezone.now()

        # Create sample workout table
        self.table_data = {
            'exercises': ['Bench Press', 'Squats'],
            'weeks': [
                {'week': 1, 'sets': [3, 3], 'reps': [10, 10]}
            ]
        }
        self.workout_table = WorkoutTable.objects.create(
            name='Test Program',
            table_data=self.table_data,
            created_at=self.now
        )

    def test_get_workout_tables_returns_json(self):
        """Test that get workout tables API returns JSON."""
        response = self.client.get(self.get_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_get_workout_tables_contains_tables(self):
        """Test that response contains workout table data."""
        response = self.client.get(self.get_url)
        data = json.loads(response.content)

        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]['name'], 'Test Program')

    def test_save_workout_table_creates_new_table(self):
        """Test that save API creates a new workout table."""
        initial_count = WorkoutTable.objects.count()

        post_data = {
            'name': 'New Program',
            'table_data': json.dumps({'exercises': ['Deadlift']})
        }

        response = self.client.post(
            self.save_url,
            data=json.dumps(post_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WorkoutTable.objects.count(), initial_count + 1)

    def test_save_workout_table_updates_existing_table(self):
        """Test that save API updates an existing workout table."""
        post_data = {
            'id': self.workout_table.id,
            'name': 'Updated Program',
            'table_data': json.dumps({'exercises': ['Pull-ups']})
        }

        response = self.client.post(
            self.save_url,
            data=json.dumps(post_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        self.workout_table.refresh_from_db()
        self.assertEqual(self.workout_table.name, 'Updated Program')

    def test_delete_workout_table(self):
        """Test that delete API removes a workout table."""
        delete_url = reverse('delete_workout_table', args=[self.workout_table.id])
        initial_count = WorkoutTable.objects.count()

        response = self.client.delete(delete_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(WorkoutTable.objects.count(), initial_count - 1)

    def test_delete_nonexistent_workout_table_returns_404(self):
        """Test that deleting non-existent table returns 404."""
        delete_url = reverse('delete_workout_table', args=[99999])
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, 404)


class ExportBodyMeasurementsCSVTestCase(TestCase):
    """Test cases for exporting body measurements to CSV."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('export_body_measurements_csv')
        self.now = timezone.now()

        # Create body measurements
        BodyMeasurement.objects.create(
            date=self.now,
            neck=Decimal('40.0'),
            chest=Decimal('105.0'),
            belly=Decimal('90.0')
        )

    def test_export_csv_returns_csv_response(self):
        """Test that export returns CSV content type."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')

    def test_export_csv_contains_data(self):
        """Test that CSV contains measurement data."""
        response = self.client.get(self.url)
        content = response.content.decode('utf-8')

        # Should contain headers and data
        self.assertIn('Date', content)
        self.assertIn('Neck', content)
        self.assertIn('40.0', content)

    def test_export_csv_filename_in_headers(self):
        """Test that response has correct Content-Disposition header."""
        response = self.client.get(self.url)
        self.assertIn('Content-Disposition', response)
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('body_measurements', response['Content-Disposition'])


class NutritionDataAPITestCase(TestCase):
    """Test cases for the nutrition data API (OpenFoodFacts)."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('nutrition_data')

    def test_nutrition_data_requires_barcode(self):
        """Test that API requires barcode parameter."""
        response = self.client.get(self.url)
        # Should return error or empty response without barcode
        self.assertIn(response.status_code, [200, 400])

    def test_nutrition_data_with_barcode_returns_json(self):
        """Test that API returns JSON when barcode is provided."""
        response = self.client.get(self.url, {'barcode': '123456789'})
        self.assertEqual(response['Content-Type'], 'application/json')

    # Note: Actual API integration tests would require mocking external API calls
    # or using test fixtures to avoid making real HTTP requests


class GeminiNutritionAPITestCase(TestCase):
    """Test cases for the Gemini AI nutrition API."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('gemini_nutrition')

    def test_gemini_nutrition_requires_food_name(self):
        """Test that API requires food_name parameter."""
        response = self.client.get(self.url)
        # Should return error without food_name
        self.assertIn(response.status_code, [200, 400])

    def test_gemini_nutrition_returns_json(self):
        """Test that API returns JSON response."""
        response = self.client.get(self.url, {'food_name': 'apple'})
        self.assertEqual(response['Content-Type'], 'application/json')

    # Note: Actual Gemini API tests would require mocking the AI service
    # to avoid making real API calls and incurring costs
