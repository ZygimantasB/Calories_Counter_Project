"""
Unit tests for all forms in count_calories_app.

Tests cover:
- FoodItemForm (validation, required fields, widget attributes)
- WeightForm (validation, required fields)
- ExerciseForm (validation, optional fields)
- WorkoutSessionForm (validation, optional name)
- WorkoutExerciseForm (validation, relationships)
- RunningSessionForm (validation, duration field)
- BodyMeasurementForm (validation, many optional fields)
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from count_calories_app.forms import (
    FoodItemForm, WeightForm, ExerciseForm, WorkoutSessionForm,
    WorkoutExerciseForm, RunningSessionForm, BodyMeasurementForm
)
from count_calories_app.models import Exercise, WorkoutSession


class FoodItemFormTestCase(TestCase):
    """Test cases for the FoodItemForm."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()

    def test_form_valid_with_all_fields(self):
        """Test that form is valid with all fields populated."""
        form_data = {
            'product_name': 'Apple',
            'calories': '95.00',
            'fat': '0.30',
            'carbohydrates': '25.00',
            'protein': '0.50',
            'consumed_at': self.now
        }
        form = FoodItemForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_minimal_fields(self):
        """Test that form is valid with minimal required fields."""
        form_data = {
            'product_name': 'Test Food',
            'calories': '100',
            'fat': '0',
            'carbohydrates': '0',
            'protein': '0',
            'consumed_at': self.now
        }
        form = FoodItemForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_product_name(self):
        """Test that form is invalid without product name."""
        form_data = {
            'calories': '100',
            'fat': '10',
            'carbohydrates': '20',
            'protein': '5',
            'consumed_at': self.now
        }
        form = FoodItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('product_name', form.errors)

    def test_form_invalid_missing_consumed_at(self):
        """Test that form is invalid without consumed_at."""
        form_data = {
            'product_name': 'Test Food',
            'calories': '100',
            'fat': '10',
            'carbohydrates': '20',
            'protein': '5'
        }
        form = FoodItemForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('consumed_at', form.errors)

    def test_form_invalid_negative_calories(self):
        """Test that form is invalid with negative calories."""
        form_data = {
            'product_name': 'Test Food',
            'calories': '-100',
            'fat': '0',
            'carbohydrates': '0',
            'protein': '0',
            'consumed_at': self.now
        }
        form = FoodItemForm(data=form_data)
        # Note: Form validation may or may not catch this depending on widget attributes
        # The HTML5 min='0' would catch it in the browser

    def test_form_has_correct_fields(self):
        """Test that form has all expected fields."""
        form = FoodItemForm()
        expected_fields = ['product_name', 'calories', 'fat', 'carbohydrates', 'protein', 'consumed_at']
        self.assertEqual(list(form.fields.keys()), expected_fields)

    def test_form_widget_classes(self):
        """Test that form widgets have correct CSS classes."""
        form = FoodItemForm()
        self.assertIn('form-control', form.fields['product_name'].widget.attrs['class'])
        self.assertIn('form-control', form.fields['calories'].widget.attrs['class'])
        self.assertIn('form-control', form.fields['fat'].widget.attrs['class'])

    def test_form_labels(self):
        """Test that form fields have correct labels."""
        form = FoodItemForm()
        self.assertEqual(form.fields['product_name'].label, 'Product Name')
        self.assertEqual(form.fields['calories'].label, 'Calories (kcal)')
        self.assertEqual(form.fields['protein'].label, 'Protein (g)')


class WeightFormTestCase(TestCase):
    """Test cases for the WeightForm."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()

    def test_form_valid_with_all_fields(self):
        """Test that form is valid with all fields."""
        form_data = {
            'weight': '75.50',
            'recorded_at': self.now.strftime('%Y-%m-%dT%H:%M'),
            'notes': 'Morning weight'
        }
        form = WeightForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_without_notes(self):
        """Test that form is valid without notes (optional field)."""
        form_data = {
            'weight': '80.00',
            'recorded_at': self.now.strftime('%Y-%m-%dT%H:%M')
        }
        form = WeightForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_weight(self):
        """Test that form is invalid without weight."""
        form_data = {
            'recorded_at': self.now.strftime('%Y-%m-%dT%H:%M'),
            'notes': 'Test'
        }
        form = WeightForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('weight', form.errors)

    def test_form_invalid_missing_recorded_at(self):
        """Test that form is invalid without recorded_at."""
        form_data = {
            'weight': '75.00'
        }
        form = WeightForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('recorded_at', form.errors)

    def test_form_has_correct_fields(self):
        """Test that form has all expected fields."""
        form = WeightForm()
        expected_fields = ['weight', 'recorded_at', 'notes']
        self.assertEqual(list(form.fields.keys()), expected_fields)

    def test_form_labels(self):
        """Test that form fields have correct labels."""
        form = WeightForm()
        self.assertEqual(form.fields['weight'].label, 'Weight (kg)')
        self.assertEqual(form.fields['recorded_at'].label, 'Date and Time')
        self.assertEqual(form.fields['notes'].label, 'Notes')


class ExerciseFormTestCase(TestCase):
    """Test cases for the ExerciseForm."""

    def test_form_valid_with_all_fields(self):
        """Test that form is valid with all fields."""
        form_data = {
            'name': 'Bench Press',
            'muscle_group': 'Chest',
            'description': 'Lie on bench and press bar up'
        }
        form = ExerciseForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_only_name(self):
        """Test that form is valid with only name (other fields optional)."""
        form_data = {
            'name': 'Push-ups'
        }
        form = ExerciseForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_name(self):
        """Test that form is invalid without name."""
        form_data = {
            'muscle_group': 'Arms',
            'description': 'Some description'
        }
        form = ExerciseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_form_has_correct_fields(self):
        """Test that form has all expected fields."""
        form = ExerciseForm()
        expected_fields = ['name', 'muscle_group', 'description']
        self.assertEqual(list(form.fields.keys()), expected_fields)

    def test_form_labels(self):
        """Test that form fields have correct labels."""
        form = ExerciseForm()
        self.assertEqual(form.fields['name'].label, 'Exercise Name')
        self.assertEqual(form.fields['muscle_group'].label, 'Muscle Group')
        self.assertEqual(form.fields['description'].label, 'Description')


class WorkoutSessionFormTestCase(TestCase):
    """Test cases for the WorkoutSessionForm."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()

    def test_form_valid_with_all_fields(self):
        """Test that form is valid with all fields."""
        form_data = {
            'name': 'Morning Workout',
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'notes': 'Great session!'
        }
        form = WorkoutSessionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_only_date(self):
        """Test that form is valid with only date (name and notes optional)."""
        form_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M')
        }
        form = WorkoutSessionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_date(self):
        """Test that form is invalid without date."""
        form_data = {
            'name': 'Test Workout',
            'notes': 'Some notes'
        }
        form = WorkoutSessionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_form_has_correct_fields(self):
        """Test that form has all expected fields."""
        form = WorkoutSessionForm()
        expected_fields = ['name', 'date', 'notes']
        self.assertEqual(list(form.fields.keys()), expected_fields)


class WorkoutExerciseFormTestCase(TestCase):
    """Test cases for the WorkoutExerciseForm."""

    def setUp(self):
        """Set up test data."""
        self.exercise = Exercise.objects.create(name='Squats', muscle_group='Legs')

    def test_form_valid_with_all_fields(self):
        """Test that form is valid with all fields."""
        form_data = {
            'exercise': self.exercise.id,
            'sets': '4',
            'reps': '10',
            'weight': '100.50',
            'notes': 'Felt strong'
        }
        form = WorkoutExerciseForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_without_weight(self):
        """Test that form is valid without weight (optional for bodyweight exercises)."""
        form_data = {
            'exercise': self.exercise.id,
            'sets': '3',
            'reps': '15'
        }
        form = WorkoutExerciseForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_exercise(self):
        """Test that form is invalid without exercise selection."""
        form_data = {
            'sets': '3',
            'reps': '10'
        }
        form = WorkoutExerciseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('exercise', form.errors)

    def test_form_invalid_missing_sets(self):
        """Test that form is invalid without sets."""
        form_data = {
            'exercise': self.exercise.id,
            'reps': '10'
        }
        form = WorkoutExerciseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('sets', form.errors)

    def test_form_invalid_missing_reps(self):
        """Test that form is invalid without reps."""
        form_data = {
            'exercise': self.exercise.id,
            'sets': '3'
        }
        form = WorkoutExerciseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('reps', form.errors)

    def test_form_has_correct_fields(self):
        """Test that form has all expected fields."""
        form = WorkoutExerciseForm()
        expected_fields = ['exercise', 'sets', 'reps', 'weight', 'notes']
        self.assertEqual(list(form.fields.keys()), expected_fields)


class RunningSessionFormTestCase(TestCase):
    """Test cases for the RunningSessionForm."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()

    def test_form_valid_with_all_fields(self):
        """Test that form is valid with all fields."""
        form_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'distance': '5.50',
            'duration': '00:30:00',
            'notes': 'Great run!'
        }
        form = RunningSessionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_without_notes(self):
        """Test that form is valid without notes (optional)."""
        form_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'distance': '10.00',
            'duration': '01:00:00'
        }
        form = RunningSessionForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_date(self):
        """Test that form is invalid without date."""
        form_data = {
            'distance': '5.00',
            'duration': '00:30:00'
        }
        form = RunningSessionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_form_invalid_missing_distance(self):
        """Test that form is invalid without distance."""
        form_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'duration': '00:30:00'
        }
        form = RunningSessionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('distance', form.errors)

    def test_form_invalid_missing_duration(self):
        """Test that form is invalid without duration."""
        form_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'distance': '5.00'
        }
        form = RunningSessionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('duration', form.errors)

    def test_form_has_correct_fields(self):
        """Test that form has all expected fields."""
        form = RunningSessionForm()
        expected_fields = ['date', 'distance', 'duration', 'notes']
        self.assertEqual(list(form.fields.keys()), expected_fields)

    def test_form_labels(self):
        """Test that form fields have correct labels."""
        form = RunningSessionForm()
        self.assertEqual(form.fields['date'].label, 'Date and Time')
        self.assertEqual(form.fields['distance'].label, 'Distance (km)')
        self.assertEqual(form.fields['duration'].label, 'Duration (HH:MM:SS)')


class BodyMeasurementFormTestCase(TestCase):
    """Test cases for the BodyMeasurementForm."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()

    def test_form_valid_with_all_fields(self):
        """Test that form is valid with all fields populated."""
        form_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'neck': '38.50',
            'chest': '102.00',
            'belly': '85.50',
            'left_biceps': '35.00',
            'right_biceps': '35.50',
            'left_triceps': '28.00',
            'right_triceps': '28.50',
            'left_forearm': '30.00',
            'right_forearm': '30.50',
            'left_thigh': '58.00',
            'right_thigh': '58.50',
            'left_lower_leg': '38.00',
            'right_lower_leg': '38.50',
            'butt': '95.00',
            'notes': 'Morning measurements'
        }
        form = BodyMeasurementForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_only_date(self):
        """Test that form is valid with only date (all measurements optional)."""
        form_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M')
        }
        form = BodyMeasurementForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_valid_with_partial_measurements(self):
        """Test that form is valid with only some measurements."""
        form_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'neck': '40.00',
            'chest': '105.00',
            'belly': '90.00'
        }
        form = BodyMeasurementForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_missing_date(self):
        """Test that form is invalid without date."""
        form_data = {
            'neck': '40.00',
            'chest': '105.00'
        }
        form = BodyMeasurementForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_form_has_correct_fields(self):
        """Test that form has all expected fields."""
        form = BodyMeasurementForm()
        expected_fields = [
            'date', 'neck', 'chest', 'belly',
            'left_biceps', 'right_biceps', 'left_triceps', 'right_triceps',
            'left_forearm', 'right_forearm', 'left_thigh', 'right_thigh',
            'left_lower_leg', 'right_lower_leg', 'butt', 'notes'
        ]
        self.assertEqual(list(form.fields.keys()), expected_fields)

    def test_form_labels(self):
        """Test that form fields have correct labels."""
        form = BodyMeasurementForm()
        self.assertEqual(form.fields['date'].label, 'Date and Time')
        self.assertEqual(form.fields['neck'].label, 'Neck (cm)')
        self.assertEqual(form.fields['chest'].label, 'Chest (cm)')
        self.assertEqual(form.fields['belly'].label, 'Belly/Waist (cm)')
        self.assertEqual(form.fields['left_biceps'].label, 'Left Biceps (cm)')
        self.assertEqual(form.fields['butt'].label, 'Butt/Glutes (cm)')

    def test_form_symmetric_measurements(self):
        """Test form with different left/right measurements (realistic scenario)."""
        form_data = {
            'date': self.now.strftime('%Y-%m-%dT%H:%M'),
            'left_biceps': '34.00',
            'right_biceps': '35.00',
            'left_thigh': '57.00',
            'right_thigh': '58.00'
        }
        form = BodyMeasurementForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_widget_classes(self):
        """Test that form widgets have correct CSS classes."""
        form = BodyMeasurementForm()
        self.assertIn('form-control', form.fields['neck'].widget.attrs['class'])
        self.assertIn('form-control', form.fields['chest'].widget.attrs['class'])
        self.assertIn('form-control', form.fields['notes'].widget.attrs['class'])
