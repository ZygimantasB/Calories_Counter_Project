"""
Unit tests for all models in count_calories_app.

Tests cover:
- FoodItem model (validation, string representation, ordering)
- Weight model (validation, string representation, ordering)
- RunningSession model (validation, string representation, ordering)
- Exercise model (validation, string representation, ordering)
- WorkoutSession model (validation, string representation, ordering)
- WorkoutExercise model (validation, string representation, relationships)
- WorkoutTable model (JSON field, validation, ordering)
- BodyMeasurement model (validation, optional fields, ordering)
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from count_calories_app.models import (
    FoodItem, Weight, RunningSession, Exercise,
    WorkoutSession, WorkoutExercise, WorkoutTable, BodyMeasurement
)


class FoodItemModelTestCase(TestCase):
    """Test cases for the FoodItem model."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()

    def test_create_food_item_with_all_fields(self):
        """Test creating a food item with all required fields."""
        food = FoodItem.objects.create(
            product_name='Apple',
            calories=Decimal('95.00'),
            fat=Decimal('0.30'),
            carbohydrates=Decimal('25.00'),
            protein=Decimal('0.50'),
            consumed_at=self.now
        )

        self.assertEqual(food.product_name, 'Apple')
        self.assertEqual(food.calories, Decimal('95.00'))
        self.assertEqual(food.fat, Decimal('0.30'))
        self.assertEqual(food.carbohydrates, Decimal('25.00'))
        self.assertEqual(food.protein, Decimal('0.50'))
        self.assertFalse(food.hide_from_quick_list)

    def test_food_item_default_values(self):
        """Test that food item has correct default values."""
        food = FoodItem.objects.create(
            product_name='Test Food',
            consumed_at=self.now
        )

        self.assertEqual(food.calories, Decimal('0.00'))
        self.assertEqual(food.fat, Decimal('0.00'))
        self.assertEqual(food.carbohydrates, Decimal('0.00'))
        self.assertEqual(food.protein, Decimal('0.00'))
        self.assertFalse(food.hide_from_quick_list)

    def test_food_item_str_representation(self):
        """Test the string representation of a food item."""
        food = FoodItem.objects.create(
            product_name='Banana',
            calories=Decimal('105.00'),
            consumed_at=self.now
        )

        expected = f"Banana (105.00 kcal) consumed at {self.now.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(food), expected)

    def test_food_item_ordering(self):
        """Test that food items are ordered by consumed_at descending."""
        food1 = FoodItem.objects.create(
            product_name='Food 1',
            calories=Decimal('100'),
            consumed_at=self.now - timedelta(days=2)
        )
        food2 = FoodItem.objects.create(
            product_name='Food 2',
            calories=Decimal('200'),
            consumed_at=self.now - timedelta(days=1)
        )
        food3 = FoodItem.objects.create(
            product_name='Food 3',
            calories=Decimal('300'),
            consumed_at=self.now
        )

        foods = list(FoodItem.objects.all())
        self.assertEqual(foods[0], food3)  # Most recent first
        self.assertEqual(foods[1], food2)
        self.assertEqual(foods[2], food1)

    def test_food_item_hide_from_quick_list(self):
        """Test the hide_from_quick_list functionality."""
        food = FoodItem.objects.create(
            product_name='Hidden Food',
            calories=Decimal('500'),
            consumed_at=self.now,
            hide_from_quick_list=True
        )

        self.assertTrue(food.hide_from_quick_list)

    def test_food_item_max_digits_validation(self):
        """Test that decimal fields respect max_digits constraints."""
        # calories max_digits=7, decimal_places=2 means max value is 99999.99
        food = FoodItem.objects.create(
            product_name='High Calorie Food',
            calories=Decimal('99999.99'),
            consumed_at=self.now
        )
        self.assertEqual(food.calories, Decimal('99999.99'))

    def test_food_item_decimal_precision(self):
        """Test that decimal fields maintain correct precision."""
        food = FoodItem.objects.create(
            product_name='Precise Food',
            calories=Decimal('123.45'),
            fat=Decimal('12.34'),
            carbohydrates=Decimal('56.78'),
            protein=Decimal('9.01'),
            consumed_at=self.now
        )

        self.assertEqual(food.calories, Decimal('123.45'))
        self.assertEqual(food.fat, Decimal('12.34'))
        self.assertEqual(food.carbohydrates, Decimal('56.78'))
        self.assertEqual(food.protein, Decimal('9.01'))


class WeightModelTestCase(TestCase):
    """Test cases for the Weight model."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()

    def test_create_weight_measurement(self):
        """Test creating a weight measurement."""
        weight = Weight.objects.create(
            weight=Decimal('75.50'),
            recorded_at=self.now
        )

        self.assertEqual(weight.weight, Decimal('75.50'))
        self.assertEqual(weight.recorded_at, self.now)
        self.assertIsNone(weight.notes)

    def test_weight_with_notes(self):
        """Test creating a weight measurement with notes."""
        weight = Weight.objects.create(
            weight=Decimal('80.00'),
            recorded_at=self.now,
            notes='Morning weight after breakfast'
        )

        self.assertEqual(weight.notes, 'Morning weight after breakfast')

    def test_weight_str_representation(self):
        """Test the string representation of a weight measurement."""
        weight = Weight.objects.create(
            weight=Decimal('72.30'),
            recorded_at=self.now
        )

        expected = f"72.30 kg on {self.now.strftime('%Y-%m-%d')}"
        self.assertEqual(str(weight), expected)

    def test_weight_ordering(self):
        """Test that weights are ordered by recorded_at descending."""
        weight1 = Weight.objects.create(
            weight=Decimal('80.00'),
            recorded_at=self.now - timedelta(days=2)
        )
        weight2 = Weight.objects.create(
            weight=Decimal('79.50'),
            recorded_at=self.now - timedelta(days=1)
        )
        weight3 = Weight.objects.create(
            weight=Decimal('79.00'),
            recorded_at=self.now
        )

        weights = list(Weight.objects.all())
        self.assertEqual(weights[0], weight3)
        self.assertEqual(weights[1], weight2)
        self.assertEqual(weights[2], weight1)

    def test_weight_decimal_precision(self):
        """Test that weight maintains correct decimal precision."""
        weight = Weight.objects.create(
            weight=Decimal('68.75'),
            recorded_at=self.now
        )

        self.assertEqual(weight.weight, Decimal('68.75'))

    def test_weight_default_recorded_at(self):
        """Test that recorded_at defaults to now if not specified."""
        before_creation = timezone.now()
        weight = Weight.objects.create(weight=Decimal('70.00'))
        after_creation = timezone.now()

        self.assertGreaterEqual(weight.recorded_at, before_creation)
        self.assertLessEqual(weight.recorded_at, after_creation)


class RunningSessionModelTestCase(TestCase):
    """Test cases for the RunningSession model."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()

    def test_create_running_session(self):
        """Test creating a running session."""
        session = RunningSession.objects.create(
            date=self.now,
            distance=Decimal('5.50'),
            duration=timedelta(minutes=30, seconds=45)
        )

        self.assertEqual(session.distance, Decimal('5.50'))
        self.assertEqual(session.duration, timedelta(minutes=30, seconds=45))
        self.assertIsNone(session.notes)

    def test_running_session_with_notes(self):
        """Test creating a running session with notes."""
        session = RunningSession.objects.create(
            date=self.now,
            distance=Decimal('10.00'),
            duration=timedelta(hours=1, minutes=15),
            notes='Great run in the park'
        )

        self.assertEqual(session.notes, 'Great run in the park')

    def test_running_session_str_representation(self):
        """Test the string representation of a running session."""
        session = RunningSession.objects.create(
            date=self.now,
            distance=Decimal('8.25'),
            duration=timedelta(minutes=45)
        )

        expected = f"8.25 km on {self.now.strftime('%Y-%m-%d')}"
        self.assertEqual(str(session), expected)

    def test_running_session_ordering(self):
        """Test that running sessions are ordered by date descending."""
        session1 = RunningSession.objects.create(
            date=self.now - timedelta(days=2),
            distance=Decimal('5.00'),
            duration=timedelta(minutes=30)
        )
        session2 = RunningSession.objects.create(
            date=self.now - timedelta(days=1),
            distance=Decimal('6.00'),
            duration=timedelta(minutes=35)
        )
        session3 = RunningSession.objects.create(
            date=self.now,
            distance=Decimal('7.00'),
            duration=timedelta(minutes=40)
        )

        sessions = list(RunningSession.objects.all())
        self.assertEqual(sessions[0], session3)
        self.assertEqual(sessions[1], session2)
        self.assertEqual(sessions[2], session1)

    def test_running_session_duration_format(self):
        """Test that duration is stored correctly as timedelta."""
        session = RunningSession.objects.create(
            date=self.now,
            distance=Decimal('12.50'),
            duration=timedelta(hours=1, minutes=30, seconds=45)
        )

        self.assertEqual(session.duration.total_seconds(), 5445)  # 1:30:45 in seconds


class ExerciseModelTestCase(TestCase):
    """Test cases for the Exercise model."""

    def test_create_exercise_minimal(self):
        """Test creating an exercise with only required fields."""
        exercise = Exercise.objects.create(name='Push-ups')

        self.assertEqual(exercise.name, 'Push-ups')
        self.assertIsNone(exercise.description)
        self.assertIsNone(exercise.muscle_group)

    def test_create_exercise_complete(self):
        """Test creating an exercise with all fields."""
        exercise = Exercise.objects.create(
            name='Bench Press',
            description='Lie on bench, lower bar to chest, press up',
            muscle_group='Chest'
        )

        self.assertEqual(exercise.name, 'Bench Press')
        self.assertEqual(exercise.description, 'Lie on bench, lower bar to chest, press up')
        self.assertEqual(exercise.muscle_group, 'Chest')

    def test_exercise_str_representation(self):
        """Test the string representation of an exercise."""
        exercise = Exercise.objects.create(name='Squats')
        self.assertEqual(str(exercise), 'Squats')

    def test_exercise_ordering(self):
        """Test that exercises are ordered alphabetically by name."""
        exercise_c = Exercise.objects.create(name='Curls')
        exercise_a = Exercise.objects.create(name='Ab Crunches')
        exercise_b = Exercise.objects.create(name='Bench Press')

        exercises = list(Exercise.objects.all())
        self.assertEqual(exercises[0], exercise_a)
        self.assertEqual(exercises[1], exercise_b)
        self.assertEqual(exercises[2], exercise_c)

    def test_exercise_long_name(self):
        """Test that exercise name can be up to 200 characters."""
        long_name = 'A' * 200
        exercise = Exercise.objects.create(name=long_name)
        self.assertEqual(len(exercise.name), 200)


class WorkoutSessionModelTestCase(TestCase):
    """Test cases for the WorkoutSession model."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()

    def test_create_workout_session_minimal(self):
        """Test creating a workout session with minimal fields."""
        workout = WorkoutSession.objects.create(date=self.now)

        self.assertEqual(workout.date, self.now)
        self.assertIsNone(workout.name)
        self.assertIsNone(workout.notes)

    def test_create_workout_session_complete(self):
        """Test creating a workout session with all fields."""
        workout = WorkoutSession.objects.create(
            date=self.now,
            name='Morning Workout',
            notes='Felt great today!'
        )

        self.assertEqual(workout.name, 'Morning Workout')
        self.assertEqual(workout.notes, 'Felt great today!')

    def test_workout_session_str_with_name(self):
        """Test string representation when workout has a name."""
        workout = WorkoutSession.objects.create(
            date=self.now,
            name='Leg Day'
        )

        expected = f"Leg Day on {self.now.strftime('%Y-%m-%d')}"
        self.assertEqual(str(workout), expected)

    def test_workout_session_str_without_name(self):
        """Test string representation when workout has no name."""
        workout = WorkoutSession.objects.create(date=self.now)

        expected = f"Workout on {self.now.strftime('%Y-%m-%d')}"
        self.assertEqual(str(workout), expected)

    def test_workout_session_ordering(self):
        """Test that workout sessions are ordered by date descending."""
        workout1 = WorkoutSession.objects.create(date=self.now - timedelta(days=2))
        workout2 = WorkoutSession.objects.create(date=self.now - timedelta(days=1))
        workout3 = WorkoutSession.objects.create(date=self.now)

        workouts = list(WorkoutSession.objects.all())
        self.assertEqual(workouts[0], workout3)
        self.assertEqual(workouts[1], workout2)
        self.assertEqual(workouts[2], workout1)


class WorkoutExerciseModelTestCase(TestCase):
    """Test cases for the WorkoutExercise model."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()
        self.workout = WorkoutSession.objects.create(date=self.now)
        self.exercise = Exercise.objects.create(name='Squats', muscle_group='Legs')

    def test_create_workout_exercise_minimal(self):
        """Test creating a workout exercise with minimal fields."""
        workout_ex = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10
        )

        self.assertEqual(workout_ex.sets, 3)
        self.assertEqual(workout_ex.reps, 10)
        self.assertIsNone(workout_ex.weight)
        self.assertIsNone(workout_ex.notes)

    def test_create_workout_exercise_with_weight(self):
        """Test creating a workout exercise with weight."""
        workout_ex = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=4,
            reps=8,
            weight=Decimal('100.50')
        )

        self.assertEqual(workout_ex.weight, Decimal('100.50'))

    def test_create_workout_exercise_with_notes(self):
        """Test creating a workout exercise with notes."""
        workout_ex = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=12,
            notes='Felt challenging'
        )

        self.assertEqual(workout_ex.notes, 'Felt challenging')

    def test_workout_exercise_str_without_weight(self):
        """Test string representation without weight."""
        workout_ex = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=15
        )

        expected = "Squats: 3 sets x 15 reps"
        self.assertEqual(str(workout_ex), expected)

    def test_workout_exercise_str_with_weight(self):
        """Test string representation with weight."""
        workout_ex = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=5,
            reps=5,
            weight=Decimal('150.00')
        )

        expected = "Squats: 5 sets x 5 reps with 150.00 kg"
        self.assertEqual(str(workout_ex), expected)

    def test_workout_exercise_relationship_to_workout(self):
        """Test the foreign key relationship to WorkoutSession."""
        workout_ex = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10
        )

        self.assertEqual(workout_ex.workout, self.workout)
        self.assertIn(workout_ex, self.workout.exercises.all())

    def test_workout_exercise_relationship_to_exercise(self):
        """Test the foreign key relationship to Exercise."""
        workout_ex = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10
        )

        self.assertEqual(workout_ex.exercise, self.exercise)

    def test_workout_exercise_cascade_delete_workout(self):
        """Test that deleting a workout deletes its exercises."""
        WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10
        )

        self.assertEqual(WorkoutExercise.objects.count(), 1)
        self.workout.delete()
        self.assertEqual(WorkoutExercise.objects.count(), 0)

    def test_workout_exercise_cascade_delete_exercise(self):
        """Test that deleting an exercise deletes related workout exercises."""
        WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            sets=3,
            reps=10
        )

        self.assertEqual(WorkoutExercise.objects.count(), 1)
        self.exercise.delete()
        self.assertEqual(WorkoutExercise.objects.count(), 0)

    def test_workout_exercise_default_values(self):
        """Test default values for sets and reps."""
        workout_ex = WorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise
        )

        self.assertEqual(workout_ex.sets, 1)
        self.assertEqual(workout_ex.reps, 1)


class WorkoutTableModelTestCase(TestCase):
    """Test cases for the WorkoutTable model."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()
        self.table_data = {
            'exercises': ['Bench Press', 'Squats', 'Deadlift'],
            'weeks': [
                {'week': 1, 'sets': [3, 3, 3], 'reps': [10, 10, 10]},
                {'week': 2, 'sets': [4, 4, 4], 'reps': [8, 8, 8]}
            ]
        }

    def test_create_workout_table(self):
        """Test creating a workout table with JSON data."""
        table = WorkoutTable.objects.create(
            name='12 Week Program',
            table_data=self.table_data,
            created_at=self.now
        )

        self.assertEqual(table.name, '12 Week Program')
        self.assertEqual(table.table_data, self.table_data)

    def test_workout_table_json_field(self):
        """Test that JSON data is properly stored and retrieved."""
        table = WorkoutTable.objects.create(
            name='Test Program',
            table_data=self.table_data
        )

        retrieved_table = WorkoutTable.objects.get(id=table.id)
        self.assertEqual(retrieved_table.table_data['exercises'], ['Bench Press', 'Squats', 'Deadlift'])
        self.assertEqual(len(retrieved_table.table_data['weeks']), 2)

    def test_workout_table_str_representation(self):
        """Test the string representation of a workout table."""
        table = WorkoutTable.objects.create(
            name='Strength Program',
            table_data=self.table_data,
            created_at=self.now
        )

        expected = f"Strength Program (created on {self.now.strftime('%Y-%m-%d')})"
        self.assertEqual(str(table), expected)

    def test_workout_table_ordering(self):
        """Test that workout tables are ordered by created_at descending."""
        table1 = WorkoutTable.objects.create(
            name='Program 1',
            table_data={'data': 'test1'},
            created_at=self.now - timedelta(days=2)
        )
        table2 = WorkoutTable.objects.create(
            name='Program 2',
            table_data={'data': 'test2'},
            created_at=self.now - timedelta(days=1)
        )
        table3 = WorkoutTable.objects.create(
            name='Program 3',
            table_data={'data': 'test3'},
            created_at=self.now
        )

        tables = list(WorkoutTable.objects.all())
        self.assertEqual(tables[0], table3)
        self.assertEqual(tables[1], table2)
        self.assertEqual(tables[2], table1)

    def test_workout_table_empty_json(self):
        """Test creating a workout table with empty JSON data."""
        table = WorkoutTable.objects.create(
            name='Empty Program',
            table_data={}
        )

        self.assertEqual(table.table_data, {})


class BodyMeasurementModelTestCase(TestCase):
    """Test cases for the BodyMeasurement model."""

    def setUp(self):
        """Set up test data."""
        self.now = timezone.now()

    def test_create_body_measurement_minimal(self):
        """Test creating a body measurement with no optional fields."""
        measurement = BodyMeasurement.objects.create(date=self.now)

        self.assertEqual(measurement.date, self.now)
        self.assertIsNone(measurement.neck)
        self.assertIsNone(measurement.chest)
        self.assertIsNone(measurement.belly)
        self.assertIsNone(measurement.notes)

    def test_create_body_measurement_complete(self):
        """Test creating a body measurement with all fields."""
        measurement = BodyMeasurement.objects.create(
            date=self.now,
            neck=Decimal('38.50'),
            chest=Decimal('102.00'),
            belly=Decimal('85.50'),
            left_biceps=Decimal('35.00'),
            right_biceps=Decimal('35.50'),
            left_triceps=Decimal('28.00'),
            right_triceps=Decimal('28.50'),
            left_forearm=Decimal('30.00'),
            right_forearm=Decimal('30.50'),
            left_thigh=Decimal('58.00'),
            right_thigh=Decimal('58.50'),
            left_lower_leg=Decimal('38.00'),
            right_lower_leg=Decimal('38.50'),
            butt=Decimal('95.00'),
            notes='Morning measurements'
        )

        self.assertEqual(measurement.neck, Decimal('38.50'))
        self.assertEqual(measurement.chest, Decimal('102.00'))
        self.assertEqual(measurement.belly, Decimal('85.50'))
        self.assertEqual(measurement.left_biceps, Decimal('35.00'))
        self.assertEqual(measurement.right_biceps, Decimal('35.50'))
        self.assertEqual(measurement.notes, 'Morning measurements')

    def test_body_measurement_str_representation(self):
        """Test the string representation of body measurements."""
        measurement = BodyMeasurement.objects.create(date=self.now)

        expected = f"Body measurements on {self.now.strftime('%Y-%m-%d')}"
        self.assertEqual(str(measurement), expected)

    def test_body_measurement_ordering(self):
        """Test that body measurements are ordered by date descending."""
        m1 = BodyMeasurement.objects.create(date=self.now - timedelta(days=2))
        m2 = BodyMeasurement.objects.create(date=self.now - timedelta(days=1))
        m3 = BodyMeasurement.objects.create(date=self.now)

        measurements = list(BodyMeasurement.objects.all())
        self.assertEqual(measurements[0], m3)
        self.assertEqual(measurements[1], m2)
        self.assertEqual(measurements[2], m1)

    def test_body_measurement_partial_data(self):
        """Test creating measurements with only some fields populated."""
        measurement = BodyMeasurement.objects.create(
            date=self.now,
            neck=Decimal('40.00'),
            chest=Decimal('105.00'),
            belly=Decimal('90.00')
        )

        # Check populated fields
        self.assertEqual(measurement.neck, Decimal('40.00'))
        self.assertEqual(measurement.chest, Decimal('105.00'))
        self.assertEqual(measurement.belly, Decimal('90.00'))

        # Check unpopulated fields are None
        self.assertIsNone(measurement.left_biceps)
        self.assertIsNone(measurement.right_biceps)
        self.assertIsNone(measurement.butt)

    def test_body_measurement_decimal_precision(self):
        """Test that all measurement fields maintain correct precision."""
        measurement = BodyMeasurement.objects.create(
            date=self.now,
            neck=Decimal('38.75'),
            chest=Decimal('101.25'),
            left_thigh=Decimal('59.99')
        )

        self.assertEqual(measurement.neck, Decimal('38.75'))
        self.assertEqual(measurement.chest, Decimal('101.25'))
        self.assertEqual(measurement.left_thigh, Decimal('59.99'))

    def test_body_measurement_symmetric_measurements(self):
        """Test that left and right measurements can be different."""
        measurement = BodyMeasurement.objects.create(
            date=self.now,
            left_biceps=Decimal('34.00'),
            right_biceps=Decimal('35.00'),
            left_thigh=Decimal('57.00'),
            right_thigh=Decimal('58.00')
        )

        # Right side is larger (common in real life)
        self.assertLess(measurement.left_biceps, measurement.right_biceps)
        self.assertLess(measurement.left_thigh, measurement.right_thigh)
