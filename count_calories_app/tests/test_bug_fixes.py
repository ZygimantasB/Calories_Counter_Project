"""
Unit tests for bug fixes discovered via Playwright MCP investigation.

Tests cover:
- CSV download link for ?days=N views (Bug #1)
- API ?range=today handling (Bug #2)
- Running stats API date filtering (Bug #3)
- Weight goal from UserSettings (Bug #4)
- Consumed Items heading for days views (Bug #5)
- Date inputs not rendering "None" (Bug #6)
- Dashboard API week values as floats (Bug #9)
- Settings API includes tdee field (Bug #12)
- Off-by-one in daily averages day count (Bug #14)
"""

import json
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from count_calories_app.models import (
    FoodItem, Weight, RunningSession, UserSettings
)


class CSVDownloadLinkTestCase(TestCase):
    """Bug #1: CSV download link broken for ?days=N views."""

    def setUp(self):
        self.client = Client()
        self.now = timezone.now()
        FoodItem.objects.create(
            product_name='Test Food',
            calories=Decimal('500'),
            consumed_at=self.now
        )

    def test_csv_link_contains_days_param(self):
        """CSV download link should use days= param when viewing ?days=7."""
        response = self.client.get(reverse('food_tracker'), {'days': '7'})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('days=7&export=csv', content)
        # CSV link should NOT use the invalid range=days_range
        self.assertNotIn('range=days_range&export=csv', content)

    def test_csv_link_contains_days_30(self):
        """CSV download link should use days=30 when viewing ?days=30."""
        response = self.client.get(reverse('food_tracker'), {'days': '30'})
        content = response.content.decode()
        self.assertIn('days=30&export=csv', content)

    def test_csv_link_contains_days_all(self):
        """CSV download link should use days=all when viewing ?days=all."""
        response = self.client.get(reverse('food_tracker'), {'days': 'all'})
        content = response.content.decode()
        self.assertIn('days=all&export=csv', content)

    def test_csv_link_for_date_range(self):
        """CSV download link should use start_date/end_date for custom range."""
        response = self.client.get(reverse('food_tracker'), {
            'start_date': '2026-01-01',
            'end_date': '2026-01-31',
        })
        content = response.content.decode()
        self.assertIn('start_date=2026-01-01', content)
        self.assertIn('end_date=2026-01-31', content)

    def test_csv_link_for_today(self):
        """CSV download link should use range=today for today view."""
        response = self.client.get(reverse('food_tracker'), {'range': 'today'})
        content = response.content.decode()
        self.assertIn('range=today', content)
        self.assertIn('export=csv', content)


class CaloriesTrendAPITestCase(TestCase):
    """Bug #2: API ?range=today should return only today's data."""

    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        # Create food for today
        FoodItem.objects.create(
            product_name='Today Food',
            calories=Decimal('500'),
            consumed_at=self.now
        )
        # Create food for 5 days ago
        FoodItem.objects.create(
            product_name='Old Food',
            calories=Decimal('300'),
            consumed_at=self.now - timedelta(days=5)
        )

    def test_range_today_returns_single_day(self):
        """?range=today should return only today's data, not 30 days."""
        response = self.client.get(reverse('calories_trend_data'), {'range': 'today'})
        data = json.loads(response.content)
        self.assertEqual(len(data['labels']), 1)
        self.assertEqual(data['data'][0], 500.0)

    def test_range_week_returns_week_data(self):
        """?range=week should return about a week of data."""
        response = self.client.get(reverse('calories_trend_data'), {'range': 'week'})
        data = json.loads(response.content)
        # Should have both today and 5-days-ago food
        self.assertEqual(len(data['labels']), 2)

    def test_days_param_works(self):
        """?days=7 should return data within 7 days."""
        response = self.client.get(reverse('calories_trend_data'), {'days': '7'})
        data = json.loads(response.content)
        self.assertEqual(len(data['labels']), 2)

    def test_end_of_day_included(self):
        """Items logged today should always be included in trend data."""
        response = self.client.get(reverse('calories_trend_data'), {'days': '30'})
        data = json.loads(response.content)
        today_str = self.now.strftime('%Y-%m-%d')
        self.assertIn(today_str, data['labels'])


class MacrosTrendAPITestCase(TestCase):
    """Bug #2: Same range=today fix for macros trend API."""

    def setUp(self):
        self.client = Client()
        self.now = timezone.now()
        FoodItem.objects.create(
            product_name='Today Food',
            calories=Decimal('500'),
            protein=Decimal('30'),
            carbohydrates=Decimal('50'),
            fat=Decimal('20'),
            consumed_at=self.now
        )
        FoodItem.objects.create(
            product_name='Old Food',
            calories=Decimal('300'),
            protein=Decimal('15'),
            carbohydrates=Decimal('40'),
            fat=Decimal('10'),
            consumed_at=self.now - timedelta(days=5)
        )

    def test_range_today_returns_single_day(self):
        """Macros trend ?range=today should return only today's data."""
        response = self.client.get(reverse('macros_trend_data'), {'range': 'today'})
        data = json.loads(response.content)
        self.assertEqual(len(data['labels']), 1)
        self.assertEqual(data['protein'][0], 30.0)


class RunningDataAPITestCase(TestCase):
    """Bug #3: Running stats showing zeros due to 90-day hard filter."""

    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        # Create a session from 6 months ago
        RunningSession.objects.create(
            date=self.now - timedelta(days=180),
            distance=Decimal('5.0'),
            duration=timedelta(minutes=30),
        )
        # Create a recent session
        RunningSession.objects.create(
            date=self.now - timedelta(days=5),
            distance=Decimal('8.0'),
            duration=timedelta(minutes=45),
        )

    def test_default_90_days_shows_recent(self):
        """Default 90-day filter should show recent sessions."""
        response = self.client.get(reverse('running_data'))
        data = json.loads(response.content)
        self.assertEqual(data['stats']['total_sessions'], 1)
        self.assertGreater(data['stats']['total_distance'], 0)

    def test_all_days_shows_all_sessions(self):
        """?days=all should show all sessions including old ones."""
        response = self.client.get(reverse('running_data'), {'days': 'all'})
        data = json.loads(response.content)
        self.assertEqual(data['stats']['total_sessions'], 2)

    def test_custom_days_param(self):
        """?days=365 should show sessions within a year."""
        response = self.client.get(reverse('running_data'), {'days': '365'})
        data = json.loads(response.content)
        self.assertEqual(data['stats']['total_sessions'], 2)


class WeightGoalTestCase(TestCase):
    """Bug #4: Hardcoded 70kg goal weight should use UserSettings."""

    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        # Create weight entries showing a downward trend
        for i in range(10):
            Weight.objects.create(
                weight=Decimal(str(100 - i * 0.5)),
                recorded_at=self.now - timedelta(days=9 - i)
            )

    def test_no_target_weight_shows_no_goal(self):
        """When target_weight is not set, weeks_to_goal should be 0."""
        settings = UserSettings.get_settings()
        settings.target_weight = None
        settings.save()

        response = self.client.get(reverse('weight_data'))
        data = json.loads(response.content)
        self.assertEqual(data['stats']['weeks_to_goal'], 0)
        self.assertEqual(data['stats']['goal_date'], 'N/A')

    def test_with_target_weight_uses_settings(self):
        """When target_weight is set, it should be used for projections."""
        settings = UserSettings.get_settings()
        settings.target_weight = Decimal('90.0')
        settings.save()

        response = self.client.get(reverse('weight_data'))
        data = json.loads(response.content)
        self.assertEqual(data['stats'].get('weight_goal'), 90.0)


class ConsumedItemsHeadingTestCase(TestCase):
    """Bug #5: Heading shows 'Days_Range' instead of human-readable label."""

    def setUp(self):
        self.client = Client()
        self.now = timezone.now()
        FoodItem.objects.create(
            product_name='Test Food',
            calories=Decimal('500'),
            consumed_at=self.now
        )

    def test_days_7_shows_last_7_days(self):
        """?days=7 should show 'Last 7 Days' in heading."""
        response = self.client.get(reverse('food_tracker'), {'days': '7'})
        content = response.content.decode()
        self.assertIn('Last 7 Days', content)
        self.assertNotIn('Days_Range', content)

    def test_days_30_shows_last_30_days(self):
        """?days=30 should show 'Last 30 Days' in heading."""
        response = self.client.get(reverse('food_tracker'), {'days': '30'})
        content = response.content.decode()
        self.assertIn('Last 30 Days', content)
        self.assertNotIn('Days_Range', content)

    def test_today_shows_today(self):
        """?range=today should show 'Today' in heading."""
        response = self.client.get(reverse('food_tracker'), {'range': 'today'})
        content = response.content.decode()
        self.assertIn('Consumed Items (Today)', content)

    def test_date_range_shows_dates(self):
        """Custom date range should show date range in heading."""
        response = self.client.get(reverse('food_tracker'), {
            'start_date': '2026-01-01',
            'end_date': '2026-01-31',
        })
        content = response.content.decode()
        self.assertIn('2026-01-01 to 2026-01-31', content)


class DateInputNoneTestCase(TestCase):
    """Bug #6: Date inputs rendering value='None'."""

    def setUp(self):
        self.client = Client()

    def test_food_tracker_no_none_in_date_inputs(self):
        """Food tracker should not render 'None' in date input values."""
        response = self.client.get(reverse('food_tracker'))
        content = response.content.decode()
        # Check that value="None" does not appear in date inputs
        self.assertNotIn('value="None"', content)

    def test_food_tracker_with_days_no_none(self):
        """Food tracker with days param should not render 'None'."""
        response = self.client.get(reverse('food_tracker'), {'days': '7'})
        content = response.content.decode()
        self.assertNotIn('value="None"', content)

    def test_top_foods_no_none_in_date_inputs(self):
        """Top foods should not render 'None' in date input values."""
        response = self.client.get(reverse('top_foods'))
        content = response.content.decode()
        self.assertNotIn('value="None"', content)


class DashboardAPITypesTestCase(TestCase):
    """Bug #9: Dashboard API week values returned as strings."""

    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        # Create food items for this week
        FoodItem.objects.create(
            product_name='Test Food',
            calories=Decimal('500.50'),
            protein=Decimal('30.5'),
            carbohydrates=Decimal('50.5'),
            fat=Decimal('20.5'),
            consumed_at=self.now
        )

    def test_week_calories_is_float(self):
        """Week calories should be a float, not a string."""
        response = self.client.get(reverse('api_dashboard'))
        data = json.loads(response.content)
        self.assertIsInstance(data['week']['calories'], float)

    def test_week_protein_is_float(self):
        """Week protein should be a float, not a string."""
        response = self.client.get(reverse('api_dashboard'))
        data = json.loads(response.content)
        self.assertIsInstance(data['week']['protein'], float)

    def test_week_carbs_is_float(self):
        """Week carbs should be a float, not a string."""
        response = self.client.get(reverse('api_dashboard'))
        data = json.loads(response.content)
        self.assertIsInstance(data['week']['carbs'], float)

    def test_week_fat_is_float(self):
        """Week fat should be a float, not a string."""
        response = self.client.get(reverse('api_dashboard'))
        data = json.loads(response.content)
        self.assertIsInstance(data['week']['fat'], float)

    def test_today_calories_is_float(self):
        """Today calories should also be a float."""
        response = self.client.get(reverse('api_dashboard'))
        data = json.loads(response.content)
        self.assertIsInstance(data['today']['calories'], float)


class SettingsAPITDEEFieldTestCase(TestCase):
    """Bug #12: Settings API bmr field actually returns TDEE."""

    def setUp(self):
        self.client = Client()
        settings = UserSettings.get_settings()
        settings.age = 30
        settings.height = Decimal('180')
        settings.current_weight = Decimal('80')
        settings.gender = 'male'
        settings.activity_level = 'moderate'
        settings.save()

    def test_settings_api_includes_tdee_field(self):
        """Settings API should include a 'tdee' field alongside 'bmr'."""
        response = self.client.get(reverse('api_settings'))
        data = json.loads(response.content)
        self.assertIn('tdee', data['profile'])
        self.assertIn('bmr', data['profile'])  # Keep backward compat
        self.assertEqual(data['profile']['tdee'], data['profile']['bmr'])


class DailyAveragesDayCountTestCase(TestCase):
    """Bug #14: Off-by-one error in daily averages day count."""

    def setUp(self):
        self.client = Client()
        self.now = timezone.now()

        # Create food items across several days
        for i in range(7):
            FoodItem.objects.create(
                product_name=f'Food Day {i}',
                calories=Decimal('500'),
                protein=Decimal('30'),
                carbohydrates=Decimal('50'),
                fat=Decimal('20'),
                consumed_at=self.now - timedelta(days=i)
            )

    def test_days_7_shows_7_days_average(self):
        """?days=7 should show 'Daily Averages (7 days)', not 8."""
        response = self.client.get(reverse('food_tracker'), {'days': '7'})
        content = response.content.decode()
        self.assertIn('7 days', content)
        self.assertNotIn('8 days', content)

    def test_days_30_shows_30_days_average(self):
        """?days=30 should show 'Daily Averages (30 days)', not 31."""
        response = self.client.get(reverse('food_tracker'), {'days': '30'})
        content = response.content.decode()
        self.assertIn('30 days', content)
        self.assertNotIn('31 days', content)


class SettingsPageAutoMacrosDisplayTestCase(TestCase):
    """Bug #8: Settings page shows stale defaults when auto-macros enabled."""

    def setUp(self):
        self.client = Client()
        settings = UserSettings.get_settings()
        settings.age = 30
        settings.height = Decimal('180')
        settings.current_weight = Decimal('80')
        settings.gender = 'male'
        settings.activity_level = 'moderate'
        settings.use_auto_macros = True
        settings.daily_calorie_target = 2000  # stale default
        settings.protein_target = 150  # stale default
        settings.save()
        # Create weight entry so auto-calc works
        Weight.objects.create(
            weight=Decimal('80'),
            recorded_at=timezone.now()
        )

    def test_auto_macros_shows_effective_values(self):
        """When auto-macros is on, disabled fields should show effective values."""
        response = self.client.get(reverse('settings'))
        content = response.content.decode()
        settings = UserSettings.get_settings()
        effective = settings.get_effective_targets()
        # The effective calorie target should appear in the form
        self.assertIn(str(effective['calories']), content)
        # The stale 2000 default should NOT appear as a form input value
        # (it may appear elsewhere on the page, so we check specifically in input context)
        self.assertNotIn(f'value="2000"', content)
