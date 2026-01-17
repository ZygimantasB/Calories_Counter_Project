"""
Unit tests for utility functions and helper methods.

This module tests complex business logic, calculations, and utility functions
that are used across the application but may not be directly tested through
view or model tests.

Tests cover:
- Date range calculations and parsing
- Streak calculation logic
- Statistical calculations (averages, correlations)
- Data aggregation and transformation
- Edge cases in business logic
"""

import json
from datetime import datetime, timedelta, time
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from count_calories_app.models import (
    FoodItem, Weight, RunningSession, Exercise,
    WorkoutSession, WorkoutExercise, BodyMeasurement
)


class StreakCalculationTestCase(TestCase):
    """Test cases for streak calculation logic in home view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('home')
        self.now = timezone.now()

    def test_streak_zero_when_no_food_logged(self):
        """Test that streak is 0 when no food items exist."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('streak', response.context)
        self.assertEqual(response.context['streak'], 0)

    def test_streak_one_when_only_today_has_food(self):
        """Test that streak is 1 when only today has food logged."""
        # Create food item for today
        FoodItem.objects.create(
            product_name='Test Food',
            calories=Decimal('100'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        self.assertEqual(response.context['streak'], 1)

    def test_streak_counts_consecutive_days(self):
        """Test that streak correctly counts consecutive days with food."""
        # Create food items for last 5 consecutive days
        for i in range(5):
            day = self.now - timedelta(days=i)
            FoodItem.objects.create(
                product_name=f'Food Day {i}',
                calories=Decimal('100'),
                consumed_at=day
            )

        response = self.client.get(self.url)
        self.assertEqual(response.context['streak'], 5)

    def test_streak_breaks_on_missing_day(self):
        """Test that streak breaks when a day is skipped."""
        # Create food for today
        FoodItem.objects.create(
            product_name='Today Food',
            calories=Decimal('100'),
            consumed_at=self.now
        )

        # Skip yesterday, create food 2 days ago
        two_days_ago = self.now - timedelta(days=2)
        FoodItem.objects.create(
            product_name='Old Food',
            calories=Decimal('100'),
            consumed_at=two_days_ago
        )

        response = self.client.get(self.url)
        # Streak should only be 1 (today) since yesterday was skipped
        self.assertEqual(response.context['streak'], 1)

    def test_streak_with_multiple_items_same_day(self):
        """Test that multiple items on same day count as one streak day."""
        # Create 3 food items today at different times
        for hour in [8, 12, 18]:
            food_time = self.now.replace(hour=hour, minute=0, second=0)
            FoodItem.objects.create(
                product_name=f'Food at {hour}',
                calories=Decimal('100'),
                consumed_at=food_time
            )

        response = self.client.get(self.url)
        self.assertEqual(response.context['streak'], 1)

    def test_streak_spans_month_boundary(self):
        """Test that streak correctly spans across month boundaries."""
        # To test month boundary crossing, we need to construct a scenario where
        # a streak exists from today, going back into the previous month.
        # This is tricky with real time if today is the 30th.
        # But for logic testing, we just need a sequence of days.
        
        # Let's create a streak of 40 days ending today. 
        # This guarantees crossing a month boundary regardless of current date.
        for i in range(40):
            day = self.now - timedelta(days=i)
            FoodItem.objects.create(
                product_name=f'Streak Food {i}',
                calories=Decimal('100'),
                consumed_at=day
            )

        response = self.client.get(self.url)
        self.assertEqual(response.context['streak'], 40)

    def test_streak_does_not_count_future_dates(self):
        """Test that streak doesn't count food items in the future."""
        # Create food for today
        FoodItem.objects.create(
            product_name='Today Food',
            calories=Decimal('100'),
            consumed_at=self.now
        )

        # Create food for tomorrow (should be ignored)
        tomorrow = self.now + timedelta(days=1)
        FoodItem.objects.create(
            product_name='Future Food',
            calories=Decimal('100'),
            consumed_at=tomorrow
        )

        response = self.client.get(self.url)
        self.assertEqual(response.context['streak'], 1)


class DateRangeParsingTestCase(TestCase):
    """Test cases for date range parsing in various views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()

    def test_nutrition_data_with_days_parameter(self):
        """Test nutrition data API with days parameter."""
        # Create food items
        for i in range(10):
            day = self.now - timedelta(days=i)
            FoodItem.objects.create(
                product_name=f'Food {i}',
                calories=Decimal('100'),
                protein=Decimal('10'),
                carbohydrates=Decimal('15'),
                fat=Decimal('5'),
                consumed_at=day
            )

        # Test 7 days
        url = reverse('nutrition_data')
        response = self.client.get(url, {'days': '7'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('labels', data)
        self.assertIn('data', data)

        # Should have data from 7 days
        total_protein = data['data'][0]
        self.assertGreater(total_protein, 0)

    def test_nutrition_data_with_specific_date(self):
        """Test nutrition data API with specific date."""
        specific_date = self.now.date()
        FoodItem.objects.create(
            product_name='Test Food',
            calories=Decimal('100'),
            protein=Decimal('20'),
            carbohydrates=Decimal('30'),
            fat=Decimal('10'),
            consumed_at=self.now
        )

        url = reverse('nutrition_data')
        response = self.client.get(url, {'date': specific_date.strftime('%Y-%m-%d')})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should have the macros from today's food (in calories using 4-4-9 rule)
        self.assertEqual(data['data'][0], 80.0)  # protein: 20g * 4 cal/g
        self.assertEqual(data['data'][1], 120.0)  # carbs: 30g * 4 cal/g
        self.assertEqual(data['data'][2], 90.0)  # fat: 10g * 9 cal/g
        # Also check grams are available
        self.assertEqual(data['grams'][0], 20.0)  # protein grams
        self.assertEqual(data['grams'][1], 30.0)  # carbs grams
        self.assertEqual(data['grams'][2], 10.0)  # fat grams

    def test_nutrition_data_with_invalid_days(self):
        """Test nutrition data API with invalid days parameter."""
        url = reverse('nutrition_data')
        response = self.client.get(url, {'days': 'invalid'})
        self.assertEqual(response.status_code, 200)
        # Should fallback to default behavior
        data = json.loads(response.content)
        self.assertIn('labels', data)
        self.assertIn('data', data)

    def test_nutrition_data_with_date_range(self):
        """Test nutrition data API with start and end dates."""
        # Create food items across a range
        for i in range(5):
            day = self.now - timedelta(days=i)
            FoodItem.objects.create(
                product_name=f'Food {i}',
                calories=Decimal('100'),
                protein=Decimal('10'),
                consumed_at=day
            )

        start_date = (self.now - timedelta(days=3)).date()
        end_date = self.now.date()

        url = reverse('nutrition_data')
        response = self.client.get(url, {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should have protein from 4 days (inclusive), in calories (4 cal/g)
        total_protein_cal = data['data'][0]
        self.assertEqual(total_protein_cal, 160.0)  # 4 days * 10g * 4 cal/g

    def test_nutrition_data_all_time_period(self):
        """Test nutrition data API with 'all' time period."""
        # Create food items
        FoodItem.objects.create(
            product_name='Food 1',
            calories=Decimal('100'),
            protein=Decimal('25'),
            consumed_at=self.now - timedelta(days=100)
        )
        FoodItem.objects.create(
            product_name='Food 2',
            calories=Decimal('100'),
            protein=Decimal('25'),
            consumed_at=self.now
        )

        url = reverse('nutrition_data')
        response = self.client.get(url, {'days': 'all'})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should include all food items (protein in calories: 50g * 4 cal/g)
        total_protein_cal = data['data'][0]
        self.assertEqual(total_protein_cal, 200.0)  # 50g * 4 cal/g


class WeightChangeCalculationTestCase(TestCase):
    """Test cases for weight change calculations in home view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('home')
        self.now = timezone.now()

    def test_weight_change_calculation(self):
        """Test that weight change is correctly calculated."""
        # Create weight 7 days ago
        week_ago = self.now - timedelta(days=7)
        Weight.objects.create(
            weight=Decimal('80.0'),
            recorded_at=week_ago
        )

        # Create current weight
        Weight.objects.create(
            weight=Decimal('78.5'),
            recorded_at=self.now
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Weight change should be -1.5 kg
        weight_change = response.context.get('weight_change')
        self.assertIsNotNone(weight_change)
        self.assertAlmostEqual(weight_change, -1.5, places=1)

    def test_no_weight_change_with_single_measurement(self):
        """Test that weight change is None with only one measurement."""
        Weight.objects.create(
            weight=Decimal('80.0'),
            recorded_at=self.now
        )

        response = self.client.get(self.url)
        weight_change = response.context.get('weight_change')
        self.assertIsNone(weight_change)

    def test_no_weight_change_with_no_measurements(self):
        """Test that weight change is None with no measurements."""
        response = self.client.get(self.url)
        weight_change = response.context.get('weight_change')
        self.assertIsNone(weight_change)

    def test_weight_change_positive(self):
        """Test weight gain is correctly calculated."""
        week_ago = self.now - timedelta(days=7)
        Weight.objects.create(
            weight=Decimal('75.0'),
            recorded_at=week_ago
        )

        Weight.objects.create(
            weight=Decimal('77.0'),
            recorded_at=self.now
        )

        response = self.client.get(self.url)
        weight_change = response.context.get('weight_change')
        self.assertIsNotNone(weight_change)
        self.assertAlmostEqual(weight_change, 2.0, places=1)


class StatisticsAggregationTestCase(TestCase):
    """Test cases for statistics aggregation in home view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('home')
        self.now = timezone.now()

        # Set up time boundaries
        self.today_start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        self.today_end = self.now.replace(hour=23, minute=59, second=59, microsecond=999999)

        self.week_start = self.now - timedelta(days=self.now.weekday())
        self.week_start = self.week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    def test_today_stats_aggregation(self):
        """Test that today's stats are correctly aggregated."""
        # Create food items for today
        FoodItem.objects.create(
            product_name='Breakfast',
            calories=Decimal('300'),
            protein=Decimal('20'),
            carbohydrates=Decimal('40'),
            fat=Decimal('10'),
            consumed_at=self.today_start + timedelta(hours=8)
        )
        FoodItem.objects.create(
            product_name='Lunch',
            calories=Decimal('500'),
            protein=Decimal('30'),
            carbohydrates=Decimal('60'),
            fat=Decimal('15'),
            consumed_at=self.today_start + timedelta(hours=12)
        )

        response = self.client.get(self.url)
        today_stats = response.context['today_stats']

        self.assertEqual(float(today_stats['calories']), 800.0)
        self.assertEqual(float(today_stats['protein']), 50.0)
        self.assertEqual(float(today_stats['carbs']), 100.0)
        self.assertEqual(float(today_stats['fat']), 25.0)
        self.assertEqual(today_stats['count'], 2)

    def test_today_stats_empty(self):
        """Test that today's stats show zeros when no food logged."""
        response = self.client.get(self.url)
        today_stats = response.context['today_stats']

        self.assertEqual(today_stats['calories'], 0)
        self.assertEqual(today_stats['protein'], 0)
        self.assertEqual(today_stats['carbs'], 0)
        self.assertEqual(today_stats['fat'], 0)
        self.assertEqual(today_stats['count'], 0)

    def test_week_stats_aggregation(self):
        """Test that week's stats are correctly aggregated."""
        # Create food items for this week (only up to today)
        # We start from today and go backwards to ensure we stay in "past/present" relative to now
        # and also stay within the current week.
        
        current_weekday = self.now.weekday() # 0=Mon, 6=Sun
        # We can go back at most 'current_weekday' days to stay in this week
        days_to_create = min(3, current_weekday + 1)
        
        for i in range(days_to_create):
            day = self.now - timedelta(days=i)
            FoodItem.objects.create(
                product_name=f'Food Day {i}',
                calories=Decimal('1000'),
                protein=Decimal('50'),
                carbohydrates=Decimal('100'),
                fat=Decimal('30'),
                consumed_at=day
            )

        response = self.client.get(self.url)
        week_stats = response.context['week_stats']

        expected_cals = 1000.0 * days_to_create
        self.assertEqual(float(week_stats['calories']), expected_cals)
        self.assertEqual(week_stats['count'], days_to_create)

    def test_today_stats_excludes_yesterday(self):
        """Test that today's stats don't include yesterday's food."""
        # Create food for yesterday
        yesterday = self.today_start - timedelta(days=1)
        FoodItem.objects.create(
            product_name='Yesterday Food',
            calories=Decimal('500'),
            consumed_at=yesterday
        )

        # Create food for today
        FoodItem.objects.create(
            product_name='Today Food',
            calories=Decimal('200'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        today_stats = response.context['today_stats']

        # Should only include today's 200 calories
        self.assertEqual(float(today_stats['calories']), 200.0)
        self.assertEqual(today_stats['count'], 1)


class RunningStatsCalculationTestCase(TestCase):
    """Test cases for running statistics calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('home')
        self.now = timezone.now()
        self.week_start = (self.now - timedelta(days=self.now.weekday())).date()

    def test_week_running_stats_aggregation(self):
        """Test that week's running stats are correctly aggregated."""
        # Create running sessions for this week
        RunningSession.objects.create(
            date=self.now,
            distance=Decimal('5.0'),
            duration=timedelta(minutes=30)
        )
        
        # Check if 2 days ago is still in this week
        two_days_ago = self.now - timedelta(days=2)
        days_since_monday = self.now.weekday()
        
        expected_distance = 5.0
        expected_count = 1
        expected_minutes = 30.0

        if days_since_monday >= 2:
            RunningSession.objects.create(
                date=two_days_ago,
                distance=Decimal('10.0'),
                duration=timedelta(minutes=60)
            )
            expected_distance = 15.0
            expected_count = 2
            expected_minutes = 90.0

        response = self.client.get(self.url)
        week_run_stats = response.context['week_run_stats']

        self.assertEqual(float(week_run_stats['distance']), expected_distance)
        self.assertEqual(week_run_stats['count'], expected_count)

        # Total duration should be correct
        total_minutes = week_run_stats['duration'].total_seconds() / 60
        self.assertEqual(total_minutes, expected_minutes)

    def test_week_running_stats_empty(self):
        """Test week running stats when no runs logged."""
        response = self.client.get(self.url)
        week_run_stats = response.context['week_run_stats']

        self.assertEqual(week_run_stats['distance'], 0)
        self.assertEqual(week_run_stats['duration'], 0)
        self.assertEqual(week_run_stats['count'], 0)

    def test_week_running_excludes_last_week(self):
        """Test that week stats don't include last week's runs."""
        # Create run from last week
        last_week = self.now - timedelta(days=7)
        RunningSession.objects.create(
            date=last_week,
            distance=Decimal('5.0'),
            duration=timedelta(minutes=30)
        )

        # Create run from this week
        RunningSession.objects.create(
            date=self.now,
            distance=Decimal('3.0'),
            duration=timedelta(minutes=20)
        )

        response = self.client.get(self.url)
        week_run_stats = response.context['week_run_stats']

        # Should only include this week's run
        self.assertEqual(float(week_run_stats['distance']), 3.0)
        self.assertEqual(week_run_stats['count'], 1)


class WorkoutStatsCalculationTestCase(TestCase):
    """Test cases for workout statistics calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('home')
        self.now = timezone.now()
        self.week_start = (self.now - timedelta(days=self.now.weekday())).date()

    def test_week_workout_count(self):
        """Test that week's workout count is correct."""
        # Create workouts for this week
        WorkoutSession.objects.create(
            date=self.now,
            name='Workout 1'
        )
        
        # Check if 2 days ago is still in this week
        two_days_ago = self.now - timedelta(days=2)
        days_since_monday = self.now.weekday()
        
        expected_count = 1
        if days_since_monday >= 2:
            # If today is Wed (2) or later, 2 days ago is Mon (0) or later -> same week
            WorkoutSession.objects.create(
                date=two_days_ago,
                name='Workout 2'
            )
            expected_count = 2

        response = self.client.get(self.url)
        week_workouts = response.context['week_workouts']

        self.assertEqual(week_workouts, expected_count)

    def test_week_workout_count_zero(self):
        """Test workout count is zero when no workouts logged."""
        response = self.client.get(self.url)
        week_workouts = response.context['week_workouts']

        self.assertEqual(week_workouts, 0)

    def test_week_workout_excludes_last_week(self):
        """Test that week stats don't include last week's workouts."""
        # Create workout from last week
        last_week = self.now - timedelta(days=7)
        WorkoutSession.objects.create(
            date=last_week,
            name='Last Week Workout'
        )

        # Create workout from this week
        WorkoutSession.objects.create(
            date=self.now,
            name='This Week Workout'
        )

        response = self.client.get(self.url)
        week_workouts = response.context['week_workouts']

        # Should only count this week's workout
        self.assertEqual(week_workouts, 1)


class DecimalPrecisionTestCase(TestCase):
    """Test cases for decimal precision in calculations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

    def test_food_item_decimal_precision(self):
        """Test that food items maintain correct decimal precision."""
        food = FoodItem.objects.create(
            product_name='Test Food',
            calories=Decimal('123.45'),
            protein=Decimal('12.34'),
            carbohydrates=Decimal('23.45'),
            fat=Decimal('6.78'),
            consumed_at=timezone.now()
        )

        # Verify decimals are stored correctly
        self.assertEqual(food.calories, Decimal('123.45'))
        self.assertEqual(food.protein, Decimal('12.34'))
        self.assertEqual(food.carbohydrates, Decimal('23.45'))
        self.assertEqual(food.fat, Decimal('6.78'))

    def test_weight_decimal_precision(self):
        """Test that weight maintains correct decimal precision."""
        weight = Weight.objects.create(
            weight=Decimal('75.25'),
            recorded_at=timezone.now()
        )

        self.assertEqual(weight.weight, Decimal('75.25'))

    def test_running_distance_precision(self):
        """Test that running distance maintains correct precision."""
        run = RunningSession.objects.create(
            date=timezone.now(),
            distance=Decimal('10.75'),
            duration=timedelta(minutes=45)
        )

        self.assertEqual(run.distance, Decimal('10.75'))

    def test_body_measurement_precision(self):
        """Test that body measurements maintain correct precision."""
        measurement = BodyMeasurement.objects.create(
            date=timezone.now(),
            chest=Decimal('102.50'),
            belly=Decimal('85.75')
        )

        self.assertEqual(measurement.chest, Decimal('102.50'))
        self.assertEqual(measurement.belly, Decimal('85.75'))


class EdgeCaseDataValidationTestCase(TestCase):
    """Test cases for edge cases in data validation."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.now = timezone.now()

    def test_food_with_zero_calories(self):
        """Test that food items can have zero calories."""
        food = FoodItem.objects.create(
            product_name='Zero Calorie Food',
            calories=Decimal('0'),
            consumed_at=self.now
        )

        self.assertEqual(food.calories, Decimal('0'))

    def test_food_with_very_large_calories(self):
        """Test that food items can handle large calorie values."""
        # Max is 7 digits with 2 decimal places (99999.99)
        food = FoodItem.objects.create(
            product_name='High Calorie Food',
            calories=Decimal('99999.99'),
            consumed_at=self.now
        )

        self.assertEqual(food.calories, Decimal('99999.99'))

    def test_running_with_very_short_duration(self):
        """Test running session with very short duration."""
        run = RunningSession.objects.create(
            date=self.now,
            distance=Decimal('0.10'),
            duration=timedelta(seconds=30)
        )

        self.assertEqual(run.duration.total_seconds(), 30)

    def test_running_with_very_long_duration(self):
        """Test running session with very long duration."""
        run = RunningSession.objects.create(
            date=self.now,
            distance=Decimal('50.00'),
            duration=timedelta(hours=5, minutes=30)
        )

        expected_seconds = 5 * 3600 + 30 * 60
        self.assertEqual(run.duration.total_seconds(), expected_seconds)

    def test_workout_exercise_with_zero_weight(self):
        """Test workout exercise with no weight (bodyweight)."""
        exercise = Exercise.objects.create(name='Push-ups')
        workout = WorkoutSession.objects.create(date=self.now)

        workout_exercise = WorkoutExercise.objects.create(
            workout=workout,
            exercise=exercise,
            sets=3,
            reps=15,
            weight=None  # Bodyweight exercise
        )

        self.assertIsNone(workout_exercise.weight)

    def test_body_measurement_with_asymmetric_values(self):
        """Test body measurements with different left/right values."""
        measurement = BodyMeasurement.objects.create(
            date=self.now,
            left_biceps=Decimal('35.0'),
            right_biceps=Decimal('36.0'),  # Right arm larger
            left_thigh=Decimal('55.0'),
            right_thigh=Decimal('54.5')
        )

        # Verify asymmetry is allowed and stored correctly
        self.assertNotEqual(measurement.left_biceps, measurement.right_biceps)
        self.assertNotEqual(measurement.left_thigh, measurement.right_thigh)


class RecentItemsDisplayTestCase(TestCase):
    """Test cases for recent items display on home page."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.url = reverse('home')
        self.now = timezone.now()

    def test_recent_foods_limited_to_five(self):
        """Test that recent foods are limited to 5 items."""
        # Create 10 food items
        for i in range(10):
            FoodItem.objects.create(
                product_name=f'Food {i}',
                calories=Decimal('100'),
                consumed_at=self.now - timedelta(hours=i)
            )

        response = self.client.get(self.url)
        recent_foods = response.context['recent_foods']

        # Should only return 5 most recent
        self.assertEqual(len(recent_foods), 5)

    def test_recent_foods_ordered_newest_first(self):
        """Test that recent foods are ordered by newest first."""
        # Create food items with different timestamps
        food1 = FoodItem.objects.create(
            product_name='Old Food',
            calories=Decimal('100'),
            consumed_at=self.now - timedelta(hours=5)
        )
        food2 = FoodItem.objects.create(
            product_name='Newer Food',
            calories=Decimal('100'),
            consumed_at=self.now - timedelta(hours=2)
        )
        food3 = FoodItem.objects.create(
            product_name='Newest Food',
            calories=Decimal('100'),
            consumed_at=self.now
        )

        response = self.client.get(self.url)
        recent_foods = list(response.context['recent_foods'])

        # Should be ordered newest first
        self.assertEqual(recent_foods[0].id, food3.id)
        self.assertEqual(recent_foods[1].id, food2.id)
        self.assertEqual(recent_foods[2].id, food1.id)

    def test_recent_foods_empty_when_no_items(self):
        """Test that recent foods is empty when no food logged."""
        response = self.client.get(self.url)
        recent_foods = response.context['recent_foods']

        self.assertEqual(len(recent_foods), 0)
