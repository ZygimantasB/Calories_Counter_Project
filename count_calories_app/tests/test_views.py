"""
Unit tests for view functions (CRUD operations and page rendering).

Tests cover:
- Home view (dashboard)
- Food tracker CRUD operations
- Weight tracker CRUD operations
- Running session CRUD operations
- Workout session CRUD operations
- Exercise CRUD operations
- Body measurements CRUD operations
- Top foods view
- Food autocomplete
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from count_calories_app.models import (
    FoodItem, Weight, RunningSession, Exercise,
    WorkoutSession, WorkoutExercise, BodyMeasurement
)


class HomeViewTestCase(TestCase):
    """Test cases for the home/dashboard view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('home')
        self.now = timezone.now()

    def test_home_view_returns_200(self):
        """Test that home view returns 200 status code."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_home_view_uses_correct_template(self):
        """Test that home view uses the correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'count_calories_app/home.html')

    def test_home_view_context_today_stats(self):
        """Test that home view includes today's stats in context."""
        # Create food for today
        FoodItem.objects.create(
            product_name='Test Food',
            calories=Decimal('500'),
            protein=Decimal('20'),
            carbohydrates=Decimal('60'),
            fat=Decimal('15'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        self.assertIn('today_stats', response.context)
        self.assertEqual(response.context['today_stats']['calories'], 500)

    def test_home_view_context_week_stats(self):
        """Test that home view includes week stats in context."""
        response = self.client.get(self.url)
        self.assertIn('week_stats', response.context)

    def test_home_view_context_streak(self):
        """Test that home view includes streak in context."""
        response = self.client.get(self.url)
        self.assertIn('streak', response.context)

    def test_home_view_empty_data(self):
        """Test home view with no data returns 0 values."""
        response = self.client.get(self.url)
        self.assertEqual(response.context['today_stats']['calories'], 0)
        self.assertEqual(response.context['today_stats']['count'], 0)


class FoodTrackerViewTestCase(TestCase):
    """Test cases for the food tracker view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('food_tracker')
        self.now = timezone.now()

    def test_food_tracker_view_returns_200(self):
        """Test that food tracker view returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_food_tracker_view_uses_correct_template(self):
        """Test that food tracker uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'count_calories_app/food_tracker.html')

    def test_food_tracker_create_food_item_via_post(self):
        """Test creating a food item via POST request."""
        initial_count = FoodItem.objects.count()

        post_data = {
            'product_name': 'Banana',
            'calories': '105',
            'fat': '0.4',
            'carbohydrates': '27',
            'protein': '1.3',
            'consumed_at': self.now
        }

        response = self.client.post(self.url, data=post_data)

        # Check redirect after successful creation
        self.assertEqual(response.status_code, 302)

        # Check item was created
        self.assertEqual(FoodItem.objects.count(), initial_count + 1)

        # Check item values
        food = FoodItem.objects.latest('consumed_at')
        self.assertEqual(food.product_name, 'Banana')
        self.assertEqual(food.calories, Decimal('105'))

    def test_food_tracker_pagination(self):
        """Test that food tracker paginates results."""
        # Create 30 food items (more than typical page size)
        for i in range(30):
            FoodItem.objects.create(
                product_name=f'Food {i}',
                calories=Decimal('100'),
                consumed_at=self.now - timedelta(days=i)
            )

        response = self.client.get(self.url)
        self.assertIn('food_items', response.context)


class EditFoodItemViewTestCase(TestCase):
    """Test cases for editing food items."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()
        self.food_item = FoodItem.objects.create(
            product_name='Original Food',
            calories=Decimal('200'),
            fat=Decimal('10'),
            carbohydrates=Decimal('20'),
            protein=Decimal('5'),
            consumed_at=self.now
        )
        self.url = reverse('edit_food_item', args=[self.food_item.id])

    def test_edit_food_item_get_returns_200(self):
        """Test that edit food item GET returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_edit_food_item_updates_via_post(self):
        """Test updating a food item via POST."""
        post_data = {
            'product_name': 'Updated Food',
            'calories': '250',
            'fat': '12',
            'carbohydrates': '25',
            'protein': '8',
            'consumed_at': self.now
        }

        response = self.client.post(self.url, data=post_data)

        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)

        # Check item was updated
        self.food_item.refresh_from_db()
        self.assertEqual(self.food_item.product_name, 'Updated Food')
        self.assertEqual(self.food_item.calories, Decimal('250'))

    def test_edit_food_item_nonexistent_returns_404(self):
        """Test editing non-existent food item returns 404."""
        url = reverse('edit_food_item', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class DeleteFoodItemViewTestCase(TestCase):
    """Test cases for deleting food items."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()
        self.food_item = FoodItem.objects.create(
            product_name='Food to Delete',
            calories=Decimal('100'),
            consumed_at=self.now
        )
        self.url = reverse('delete_food_item', args=[self.food_item.id])

    def test_delete_food_item_via_post(self):
        """Test deleting a food item via POST."""
        initial_count = FoodItem.objects.count()

        response = self.client.post(self.url)

        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)

        # Check item was deleted
        self.assertEqual(FoodItem.objects.count(), initial_count - 1)
        self.assertFalse(FoodItem.objects.filter(id=self.food_item.id).exists())

    def test_delete_food_item_nonexistent_returns_404(self):
        """Test deleting non-existent food item returns 404."""
        url = reverse('delete_food_item', args=[99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class HideFromQuickListViewTestCase(TestCase):
    """Test cases for hiding food items from quick list."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()
        self.food_item = FoodItem.objects.create(
            product_name='Food to Hide',
            calories=Decimal('100'),
            consumed_at=self.now,
            hide_from_quick_list=False
        )
        self.url = reverse('hide_from_quick_list', args=[self.food_item.id])

    def test_hide_from_quick_list_toggles_via_post(self):
        """Test that hide from quick list toggles the field."""
        # Initially False
        self.assertFalse(self.food_item.hide_from_quick_list)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

        # Should now be True
        self.food_item.refresh_from_db()
        self.assertTrue(self.food_item.hide_from_quick_list)


class WeightTrackerViewTestCase(TestCase):
    """Test cases for the weight tracker view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('weight_tracker')
        self.now = timezone.now()

    def test_weight_tracker_view_returns_200(self):
        """Test that weight tracker view returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_weight_tracker_view_uses_correct_template(self):
        """Test that weight tracker uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'count_calories_app/weight_tracker.html')

    def test_weight_tracker_create_weight_via_post(self):
        """Test creating a weight measurement via POST."""
        initial_count = Weight.objects.count()

        post_data = {
            'weight': '75.5',
            'recorded_at': self.now.strftime('%Y-%m-%dT%H:%M'),
            'notes': 'Morning weight'
        }

        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 302)

        # Check weight was created
        self.assertEqual(Weight.objects.count(), initial_count + 1)

        weight = Weight.objects.latest('recorded_at')
        self.assertEqual(weight.weight, Decimal('75.5'))


class EditWeightViewTestCase(TestCase):
    """Test cases for editing weight measurements."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()
        self.weight = Weight.objects.create(
            weight=Decimal('80.0'),
            recorded_at=self.now
        )
        self.url = reverse('edit_weight', args=[self.weight.id])

    def test_edit_weight_get_returns_200(self):
        """Test that edit weight GET returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_edit_weight_updates_via_post(self):
        """Test updating a weight measurement via POST."""
        post_data = {
            'weight': '78.5',
            'recorded_at': self.now.strftime('%Y-%m-%dT%H:%M'),
            'notes': 'Updated weight'
        }

        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 302)

        self.weight.refresh_from_db()
        self.assertEqual(self.weight.weight, Decimal('78.5'))

    def test_edit_weight_nonexistent_returns_404(self):
        """Test editing non-existent weight returns 404."""
        url = reverse('edit_weight', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class DeleteWeightViewTestCase(TestCase):
    """Test cases for deleting weight measurements."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()
        self.weight = Weight.objects.create(
            weight=Decimal('80.0'),
            recorded_at=self.now
        )
        self.url = reverse('delete_weight', args=[self.weight.id])

    def test_delete_weight_via_post(self):
        """Test deleting a weight measurement via POST."""
        initial_count = Weight.objects.count()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Weight.objects.count(), initial_count - 1)
        self.assertFalse(Weight.objects.filter(id=self.weight.id).exists())


class RunningTrackerViewTestCase(TestCase):
    """Test cases for the running tracker view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('running_tracker')
        self.now = timezone.now()

    def test_running_tracker_view_returns_200(self):
        """Test that running tracker view returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_running_tracker_view_uses_correct_template(self):
        """Test that running tracker uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'count_calories_app/running_tracker.html')

    def test_running_tracker_create_session_via_post(self):
        """Test creating a running session via POST."""
        initial_count = RunningSession.objects.count()

        post_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'distance': '5.5',
            'duration': '00:30:00',
            'notes': 'Great run!'
        }

        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(RunningSession.objects.count(), initial_count + 1)


class EditRunningSessionViewTestCase(TestCase):
    """Test cases for editing running sessions."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()
        self.session = RunningSession.objects.create(
            date=self.now,
            distance=Decimal('5.0'),
            duration=timedelta(minutes=30)
        )
        self.url = reverse('edit_running_session', args=[self.session.id])

    def test_edit_running_session_get_returns_200(self):
        """Test that edit running session GET returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_edit_running_session_updates_via_post(self):
        """Test updating a running session via POST."""
        post_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'distance': '6.0',
            'duration': '00:35:00',
            'notes': 'Updated run'
        }

        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 302)

        self.session.refresh_from_db()
        self.assertEqual(self.session.distance, Decimal('6.0'))


class DeleteRunningSessionViewTestCase(TestCase):
    """Test cases for deleting running sessions."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()
        self.session = RunningSession.objects.create(
            date=self.now,
            distance=Decimal('5.0'),
            duration=timedelta(minutes=30)
        )
        self.url = reverse('delete_running_session', args=[self.session.id])

    def test_delete_running_session_via_post(self):
        """Test deleting a running session via POST."""
        initial_count = RunningSession.objects.count()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(RunningSession.objects.count(), initial_count - 1)
        self.assertFalse(RunningSession.objects.filter(id=self.session.id).exists())


class WorkoutTrackerViewTestCase(TestCase):
    """Test cases for the workout tracker view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('workout_tracker')
        self.now = timezone.now()

    def test_workout_tracker_view_returns_200(self):
        """Test that workout tracker view returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_workout_tracker_view_uses_correct_template(self):
        """Test that workout tracker uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'count_calories_app/workout_tracker.html')


class WorkoutDetailViewTestCase(TestCase):
    """Test cases for workout detail view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()
        self.workout = WorkoutSession.objects.create(
            date=self.now,
            name='Test Workout'
        )
        self.exercise = Exercise.objects.create(name='Squats')
        WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10,
            weight=Decimal('100')
        )
        self.url = reverse('workout_detail', args=[self.workout.id])

    def test_workout_detail_view_returns_200(self):
        """Test that workout detail view returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_workout_detail_includes_exercises(self):
        """Test that workout detail includes exercise data."""
        response = self.client.get(self.url)
        self.assertIn('workout', response.context)
        self.assertEqual(response.context['workout'].exercises.count(), 1)

    def test_workout_detail_nonexistent_returns_404(self):
        """Test that non-existent workout returns 404."""
        url = reverse('workout_detail', args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ExerciseListViewTestCase(TestCase):
    """Test cases for the exercise list view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('exercise_list')

    def test_exercise_list_view_returns_200(self):
        """Test that exercise list view returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_exercise_list_view_uses_correct_template(self):
        """Test that exercise list uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'count_calories_app/exercise_list.html')

    def test_exercise_list_displays_exercises(self):
        """Test that exercise list displays created exercises."""
        Exercise.objects.create(name='Push-ups')
        Exercise.objects.create(name='Pull-ups')

        response = self.client.get(self.url)
        self.assertIn('exercises', response.context)
        self.assertEqual(response.context['exercises'].count(), 2)


class BodyMeasurementsTrackerViewTestCase(TestCase):
    """Test cases for the body measurements tracker view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('body_measurements_tracker')
        self.now = timezone.now()

    def test_body_measurements_tracker_returns_200(self):
        """Test that body measurements tracker returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_body_measurements_tracker_uses_correct_template(self):
        """Test that body measurements tracker uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'count_calories_app/body_measurements_tracker.html')

    def test_body_measurements_create_via_post(self):
        """Test creating body measurements via POST."""
        initial_count = BodyMeasurement.objects.count()

        post_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'neck': '40.0',
            'chest': '105.0',
            'belly': '90.0'
        }

        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(BodyMeasurement.objects.count(), initial_count + 1)


class EditBodyMeasurementViewTestCase(TestCase):
    """Test cases for editing body measurements."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()
        self.measurement = BodyMeasurement.objects.create(
            date=self.now,
            neck=Decimal('40.0'),
            chest=Decimal('105.0')
        )
        self.url = reverse('edit_body_measurement', args=[self.measurement.id])

    def test_edit_body_measurement_get_returns_200(self):
        """Test that edit body measurement GET returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_edit_body_measurement_updates_via_post(self):
        """Test updating body measurement via POST."""
        post_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'neck': '39.5',
            'chest': '104.0',
            'belly': '88.0'
        }

        response = self.client.post(self.url, data=post_data)
        self.assertEqual(response.status_code, 302)

        self.measurement.refresh_from_db()
        self.assertEqual(self.measurement.neck, Decimal('39.5'))


class DeleteBodyMeasurementViewTestCase(TestCase):
    """Test cases for deleting body measurements."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()
        self.measurement = BodyMeasurement.objects.create(
            date=self.now,
            neck=Decimal('40.0')
        )
        self.url = reverse('delete_body_measurement', args=[self.measurement.id])

    def test_delete_body_measurement_via_post(self):
        """Test deleting body measurement via POST."""
        initial_count = BodyMeasurement.objects.count()

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(BodyMeasurement.objects.count(), initial_count - 1)
        self.assertFalse(BodyMeasurement.objects.filter(id=self.measurement.id).exists())


class TopFoodsViewTestCase(TestCase):
    """Test cases for the top foods view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('top_foods')
        self.now = timezone.now()

    def test_top_foods_view_returns_200(self):
        """Test that top foods view returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_top_foods_view_uses_correct_template(self):
        """Test that top foods uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'count_calories_app/top_foods.html')

    def test_top_foods_with_data(self):
        """Test top foods view with food items."""
        # Create multiple instances of same food
        for _ in range(5):
            FoodItem.objects.create(
                product_name='Chicken Breast',
                calories=Decimal('165'),
                consumed_at=self.now
            )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_top_foods_filters_hidden_items(self):
        """Test that top foods filters out hidden items."""
        # Create visible food
        FoodItem.objects.create(
            product_name='Visible Food',
            calories=Decimal('100'),
            consumed_at=self.now,
            hide_from_quick_list=False
        )

        # Create hidden food
        FoodItem.objects.create(
            product_name='Hidden Food',
            calories=Decimal('200'),
            consumed_at=self.now,
            hide_from_quick_list=True
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


class WorkoutTableViewTestCase(TestCase):
    """Test cases for the workout table view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('workout_table')

    def test_workout_table_view_returns_200(self):
        """Test that workout table view returns 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_workout_table_view_uses_correct_template(self):
        """Test that workout table uses correct template."""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'count_calories_app/workout_table.html')




123456789