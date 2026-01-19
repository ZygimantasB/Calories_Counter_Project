"""
Unit tests for UserSettings model.

Tests cover:
- UserSettings model fields and defaults
- BMR calculation (Mifflin-St Jeor equation)
- Recommended macros calculation based on fitness goals
- Effective targets (auto vs manual)
- Singleton pattern
"""

from decimal import Decimal
from django.test import TestCase
from count_calories_app.models import UserSettings


class UserSettingsModelTestCase(TestCase):
    """Test cases for the UserSettings model."""

    def setUp(self):
        """Set up test data."""
        # Clear any existing settings
        UserSettings.objects.all().delete()

    def test_create_user_settings_with_defaults(self):
        """Test creating user settings with default values."""
        settings = UserSettings.objects.create()

        self.assertEqual(settings.name, '')
        self.assertIsNone(settings.age)
        self.assertIsNone(settings.height)
        self.assertIsNone(settings.current_weight)
        self.assertEqual(settings.activity_level, 'moderate')
        self.assertEqual(settings.gender, 'male')
        self.assertEqual(settings.fitness_goal, 'maintain')
        self.assertTrue(settings.use_auto_macros)
        self.assertEqual(settings.daily_calorie_target, 2000)
        self.assertEqual(settings.protein_target, 150)
        self.assertEqual(settings.carbs_target, 200)
        self.assertEqual(settings.fat_target, 65)
        self.assertEqual(settings.theme, 'dark')
        self.assertEqual(settings.chart_color, 'blue')
        self.assertEqual(settings.default_date_range, 30)

    def test_create_user_settings_with_complete_profile(self):
        """Test creating user settings with complete profile data."""
        settings = UserSettings.objects.create(
            name='John Doe',
            age=30,
            height=Decimal('180.0'),
            current_weight=Decimal('80.0'),
            activity_level='active',
            gender='male',
            fitness_goal='bulk',
            target_weight=Decimal('85.0'),
            weekly_workout_goal=5
        )

        self.assertEqual(settings.name, 'John Doe')
        self.assertEqual(settings.age, 30)
        self.assertEqual(settings.height, Decimal('180.0'))
        self.assertEqual(settings.current_weight, Decimal('80.0'))
        self.assertEqual(settings.activity_level, 'active')
        self.assertEqual(settings.gender, 'male')
        self.assertEqual(settings.fitness_goal, 'bulk')
        self.assertEqual(settings.target_weight, Decimal('85.0'))
        self.assertEqual(settings.weekly_workout_goal, 5)

    def test_str_representation(self):
        """Test the string representation of user settings."""
        settings = UserSettings.objects.create()
        self.assertIn('User Settings', str(settings))

    def test_singleton_pattern_get_settings(self):
        """Test that get_settings returns singleton instance."""
        settings1 = UserSettings.get_settings()
        settings2 = UserSettings.get_settings()

        self.assertEqual(settings1.pk, settings2.pk)
        self.assertEqual(settings1.id, 1)
        self.assertEqual(UserSettings.objects.count(), 1)


class BMRCalculationTestCase(TestCase):
    """Test cases for BMR (Basal Metabolic Rate) calculation."""

    def setUp(self):
        """Set up test data."""
        UserSettings.objects.all().delete()

    def test_bmr_male_sedentary(self):
        """Test BMR calculation for sedentary male."""
        settings = UserSettings.objects.create(
            age=30,
            height=Decimal('180.0'),
            current_weight=Decimal('80.0'),
            gender='male',
            activity_level='sedentary'
        )

        bmr = settings.calculate_bmr()
        # BMR = (10 * 80) + (6.25 * 180) - (5 * 30) + 5 = 800 + 1125 - 150 + 5 = 1780
        # TDEE = 1780 * 1.2 = 2136
        self.assertEqual(bmr, 2136)

    def test_bmr_male_moderate(self):
        """Test BMR calculation for moderately active male."""
        settings = UserSettings.objects.create(
            age=25,
            height=Decimal('175.0'),
            current_weight=Decimal('75.0'),
            gender='male',
            activity_level='moderate'
        )

        bmr = settings.calculate_bmr()
        # BMR = (10 * 75) + (6.25 * 175) - (5 * 25) + 5 = 750 + 1093.75 - 125 + 5 = 1723.75
        # TDEE = 1723.75 * 1.55 = 2671.8125 -> 2672
        self.assertEqual(bmr, 2672)

    def test_bmr_male_very_active(self):
        """Test BMR calculation for very active male."""
        settings = UserSettings.objects.create(
            age=28,
            height=Decimal('185.0'),
            current_weight=Decimal('90.0'),
            gender='male',
            activity_level='very_active'
        )

        bmr = settings.calculate_bmr()
        # BMR = (10 * 90) + (6.25 * 185) - (5 * 28) + 5 = 900 + 1156.25 - 140 + 5 = 1921.25
        # TDEE = 1921.25 * 1.9 = 3650.375 -> 3650
        self.assertEqual(bmr, 3650)

    def test_bmr_female_sedentary(self):
        """Test BMR calculation for sedentary female."""
        settings = UserSettings.objects.create(
            age=30,
            height=Decimal('165.0'),
            current_weight=Decimal('60.0'),
            gender='female',
            activity_level='sedentary'
        )

        bmr = settings.calculate_bmr()
        # BMR = (10 * 60) + (6.25 * 165) - (5 * 30) - 161 = 600 + 1031.25 - 150 - 161 = 1320.25
        # TDEE = 1320.25 * 1.2 = 1584.3 -> 1584
        self.assertEqual(bmr, 1584)

    def test_bmr_female_moderate(self):
        """Test BMR calculation for moderately active female."""
        settings = UserSettings.objects.create(
            age=27,
            height=Decimal('170.0'),
            current_weight=Decimal('65.0'),
            gender='female',
            activity_level='moderate'
        )

        bmr = settings.calculate_bmr()
        # BMR = (10 * 65) + (6.25 * 170) - (5 * 27) - 161 = 650 + 1062.5 - 135 - 161 = 1416.5
        # TDEE = 1416.5 * 1.55 = 2195.575 -> 2196
        self.assertEqual(bmr, 2196)

    def test_bmr_female_active(self):
        """Test BMR calculation for active female."""
        settings = UserSettings.objects.create(
            age=24,
            height=Decimal('168.0'),
            current_weight=Decimal('58.0'),
            gender='female',
            activity_level='active'
        )

        bmr = settings.calculate_bmr()
        # BMR = (10 * 58) + (6.25 * 168) - (5 * 24) - 161 = 580 + 1050 - 120 - 161 = 1349
        # TDEE = 1349 * 1.725 = 2327.025 -> 2327
        self.assertEqual(bmr, 2327)

    def test_bmr_returns_none_without_age(self):
        """Test BMR calculation returns None without age."""
        settings = UserSettings.objects.create(
            height=Decimal('180.0'),
            current_weight=Decimal('80.0'),
            gender='male',
            activity_level='moderate'
        )

        self.assertIsNone(settings.calculate_bmr())

    def test_bmr_returns_none_without_height(self):
        """Test BMR calculation returns None without height."""
        settings = UserSettings.objects.create(
            age=30,
            current_weight=Decimal('80.0'),
            gender='male',
            activity_level='moderate'
        )

        self.assertIsNone(settings.calculate_bmr())

    def test_bmr_returns_none_without_weight(self):
        """Test BMR calculation returns None without weight."""
        settings = UserSettings.objects.create(
            age=30,
            height=Decimal('180.0'),
            gender='male',
            activity_level='moderate'
        )

        self.assertIsNone(settings.calculate_bmr())


class RecommendedMacrosTestCase(TestCase):
    """Test cases for recommended macros calculation based on fitness goals."""

    def setUp(self):
        """Set up test data."""
        UserSettings.objects.all().delete()

    def test_recommended_macros_bulk(self):
        """Test recommended macros for bulking goal."""
        settings = UserSettings.objects.create(
            age=25,
            height=Decimal('180.0'),
            current_weight=Decimal('80.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='bulk'
        )

        macros = settings.get_recommended_macros()

        # Weight = 80kg
        # Protein: 80 * 2.0 = 160g
        # Carbs: 80 * 5.0 = 400g
        # Fat: 80 * 1.0 = 80g
        self.assertEqual(macros['protein'], 160)
        self.assertEqual(macros['carbs'], 400)
        self.assertEqual(macros['fat'], 80)
        self.assertEqual(macros['goal'], 'bulk')
        self.assertIn('calories', macros)
        self.assertGreater(macros['calories'], 0)

    def test_recommended_macros_maintain(self):
        """Test recommended macros for maintenance goal."""
        settings = UserSettings.objects.create(
            age=30,
            height=Decimal('175.0'),
            current_weight=Decimal('75.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='maintain'
        )

        macros = settings.get_recommended_macros()

        # Weight = 75kg
        # Protein: 75 * 1.8 = 135g
        # Carbs: 75 * 4.0 = 300g
        # Fat: 75 * 0.9 = 67.5 -> 68g (rounded)
        self.assertEqual(macros['protein'], 135)
        self.assertEqual(macros['carbs'], 300)
        self.assertEqual(macros['fat'], 68)
        self.assertEqual(macros['goal'], 'maintain')

    def test_recommended_macros_cut(self):
        """Test recommended macros for cutting goal."""
        settings = UserSettings.objects.create(
            age=28,
            height=Decimal('178.0'),
            current_weight=Decimal('85.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='cut'
        )

        macros = settings.get_recommended_macros()

        # Weight = 85kg
        # Protein: 85 * 2.4 = 204g
        # Carbs: 85 * 2.5 = 212.5 -> 212g (rounded)
        # Fat: 85 * 0.7 = 59.5 -> 59g (rounded)
        self.assertEqual(macros['protein'], 204)
        self.assertEqual(macros['carbs'], 212)
        self.assertEqual(macros['fat'], 59)  # Python's round() uses banker's rounding
        self.assertEqual(macros['goal'], 'cut')

    def test_recommended_macros_female_bulk(self):
        """Test recommended macros for female bulking."""
        settings = UserSettings.objects.create(
            age=26,
            height=Decimal('165.0'),
            current_weight=Decimal('60.0'),
            gender='female',
            activity_level='active',
            fitness_goal='bulk'
        )

        macros = settings.get_recommended_macros()

        # Weight = 60kg
        # Protein: 60 * 2.0 = 120g
        # Carbs: 60 * 5.0 = 300g
        # Fat: 60 * 1.0 = 60g
        self.assertEqual(macros['protein'], 120)
        self.assertEqual(macros['carbs'], 300)
        self.assertEqual(macros['fat'], 60)

    def test_recommended_macros_calories_bulk(self):
        """Test that bulk calories are 15% above TDEE."""
        settings = UserSettings.objects.create(
            age=25,
            height=Decimal('180.0'),
            current_weight=Decimal('80.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='bulk'
        )

        bmr = settings.calculate_bmr()
        macros = settings.get_recommended_macros()

        expected_calories = round(bmr * 1.15)
        self.assertEqual(macros['calories'], expected_calories)

    def test_recommended_macros_calories_maintain(self):
        """Test that maintenance calories equal TDEE."""
        settings = UserSettings.objects.create(
            age=25,
            height=Decimal('180.0'),
            current_weight=Decimal('80.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='maintain'
        )

        bmr = settings.calculate_bmr()
        macros = settings.get_recommended_macros()

        expected_calories = round(bmr * 1.0)
        self.assertEqual(macros['calories'], expected_calories)

    def test_recommended_macros_calories_cut(self):
        """Test that cutting calories are 20% below TDEE."""
        settings = UserSettings.objects.create(
            age=25,
            height=Decimal('180.0'),
            current_weight=Decimal('80.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='cut'
        )

        bmr = settings.calculate_bmr()
        macros = settings.get_recommended_macros()

        expected_calories = round(bmr * 0.80)
        self.assertEqual(macros['calories'], expected_calories)

    def test_recommended_macros_returns_none_without_weight(self):
        """Test that recommended macros returns None without weight."""
        settings = UserSettings.objects.create(
            age=25,
            height=Decimal('180.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='bulk'
        )

        self.assertIsNone(settings.get_recommended_macros())

    def test_recommended_macros_has_description(self):
        """Test that recommended macros include a description."""
        settings = UserSettings.objects.create(
            age=25,
            height=Decimal('180.0'),
            current_weight=Decimal('80.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='bulk'
        )

        macros = settings.get_recommended_macros()

        self.assertIn('description', macros)
        self.assertIsInstance(macros['description'], str)
        self.assertGreater(len(macros['description']), 0)


class EffectiveTargetsTestCase(TestCase):
    """Test cases for effective targets (auto vs manual)."""

    def setUp(self):
        """Set up test data."""
        UserSettings.objects.all().delete()

    def test_effective_targets_auto_enabled_with_weight(self):
        """Test effective targets when auto-macros is enabled and weight is set."""
        settings = UserSettings.objects.create(
            age=25,
            height=Decimal('180.0'),
            current_weight=Decimal('80.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='bulk',
            use_auto_macros=True,
            # Manual targets (should be ignored)
            daily_calorie_target=2500,
            protein_target=150,
            carbs_target=250,
            fat_target=70
        )

        targets = settings.get_effective_targets()
        recommended = settings.get_recommended_macros()

        self.assertTrue(targets['is_auto'])
        self.assertEqual(targets['calories'], recommended['calories'])
        self.assertEqual(targets['protein'], recommended['protein'])
        self.assertEqual(targets['carbs'], recommended['carbs'])
        self.assertEqual(targets['fat'], recommended['fat'])

    def test_effective_targets_auto_disabled(self):
        """Test effective targets when auto-macros is disabled."""
        settings = UserSettings.objects.create(
            age=25,
            height=Decimal('180.0'),
            current_weight=Decimal('80.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='bulk',
            use_auto_macros=False,
            daily_calorie_target=3000,
            protein_target=180,
            carbs_target=350,
            fat_target=90
        )

        targets = settings.get_effective_targets()

        self.assertFalse(targets['is_auto'])
        self.assertEqual(targets['calories'], 3000)
        self.assertEqual(targets['protein'], 180)
        self.assertEqual(targets['carbs'], 350)
        self.assertEqual(targets['fat'], 90)

    def test_effective_targets_auto_enabled_without_weight(self):
        """Test effective targets falls back to manual when auto enabled but no weight."""
        settings = UserSettings.objects.create(
            age=25,
            height=Decimal('180.0'),
            gender='male',
            activity_level='moderate',
            fitness_goal='bulk',
            use_auto_macros=True,
            daily_calorie_target=2800,
            protein_target=170,
            carbs_target=320,
            fat_target=85
        )

        targets = settings.get_effective_targets()

        # Should fall back to manual since weight is not set
        self.assertFalse(targets['is_auto'])
        self.assertEqual(targets['calories'], 2800)
        self.assertEqual(targets['protein'], 170)

    def test_effective_targets_defaults_when_no_data(self):
        """Test effective targets with default values."""
        settings = UserSettings.objects.create(use_auto_macros=False)

        targets = settings.get_effective_targets()

        self.assertFalse(targets['is_auto'])
        self.assertEqual(targets['calories'], 2000)  # Default
        self.assertEqual(targets['protein'], 150)  # Default
        self.assertEqual(targets['carbs'], 200)  # Default
        self.assertEqual(targets['fat'], 65)  # Default


class UserSettingsChoicesTestCase(TestCase):
    """Test cases for UserSettings choice fields."""

    def setUp(self):
        """Set up test data."""
        UserSettings.objects.all().delete()

    def test_activity_level_choices(self):
        """Test all activity level choices are valid."""
        valid_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']

        for level in valid_levels:
            settings = UserSettings.objects.create(activity_level=level)
            self.assertEqual(settings.activity_level, level)
            settings.delete()

    def test_gender_choices(self):
        """Test both gender choices are valid."""
        for gender in ['male', 'female']:
            settings = UserSettings.objects.create(gender=gender)
            self.assertEqual(settings.gender, gender)
            settings.delete()

    def test_fitness_goal_choices(self):
        """Test all fitness goal choices are valid."""
        for goal in ['maintain', 'bulk', 'cut']:
            settings = UserSettings.objects.create(fitness_goal=goal)
            self.assertEqual(settings.fitness_goal, goal)
            settings.delete()

    def test_theme_choices(self):
        """Test all theme choices are valid."""
        for theme in ['light', 'dark', 'auto']:
            settings = UserSettings.objects.create(theme=theme)
            self.assertEqual(settings.theme, theme)
            settings.delete()

    def test_chart_color_choices(self):
        """Test all chart color choices are valid."""
        for color in ['blue', 'green', 'purple', 'orange', 'pink']:
            settings = UserSettings.objects.create(chart_color=color)
            self.assertEqual(settings.chart_color, color)
            settings.delete()

    def test_default_date_range_choices(self):
        """Test all default date range choices are valid."""
        for days in [7, 14, 30, 90]:
            settings = UserSettings.objects.create(default_date_range=days)
            self.assertEqual(settings.default_date_range, days)
            settings.delete()


class UserSettingsNotificationTestCase(TestCase):
    """Test cases for notification preferences."""

    def setUp(self):
        """Set up test data."""
        UserSettings.objects.all().delete()

    def test_notification_defaults(self):
        """Test that notification settings have correct defaults."""
        settings = UserSettings.objects.create()

        self.assertFalse(settings.meal_reminder_enabled)
        self.assertEqual(settings.meal_reminder_times, [])
        self.assertFalse(settings.workout_reminder_enabled)
        self.assertIsNone(settings.workout_reminder_time)
        self.assertEqual(settings.workout_reminder_days, [])
        self.assertFalse(settings.weight_reminder_enabled)
        self.assertIsNone(settings.weight_reminder_time)

    def test_meal_reminder_times_json(self):
        """Test storing meal reminder times as JSON."""
        from datetime import time

        settings = UserSettings.objects.create(
            meal_reminder_enabled=True,
            meal_reminder_times=['08:00', '12:00', '18:00']
        )

        self.assertTrue(settings.meal_reminder_enabled)
        self.assertEqual(len(settings.meal_reminder_times), 3)
        self.assertIn('08:00', settings.meal_reminder_times)

    def test_workout_reminder_days_json(self):
        """Test storing workout reminder days as JSON."""
        settings = UserSettings.objects.create(
            workout_reminder_enabled=True,
            workout_reminder_days=['monday', 'wednesday', 'friday']
        )

        self.assertTrue(settings.workout_reminder_enabled)
        self.assertEqual(len(settings.workout_reminder_days), 3)
        self.assertIn('monday', settings.workout_reminder_days)
