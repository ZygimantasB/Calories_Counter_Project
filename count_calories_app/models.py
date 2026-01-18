from django.db import models
from django.utils import timezone
import json

class FoodItem(models.Model):
    """
    Represents a single food item consumed by the user.
    """
    product_name = models.CharField(max_length=200, help_text="Name of the food or drink")
    calories = models.DecimalField(max_digits=7, decimal_places=2, default=0.0, help_text="Calories per serving")
    fat = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Fat content in grams")
    carbohydrates = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Carbohydrate content in grams")
    protein = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Protein content in grams")
    consumed_at = models.DateTimeField(default=timezone.now, help_text="Date and time the item was consumed")
    hide_from_quick_list = models.BooleanField(default=False, help_text="Hide this item from the quick add list")

    def __str__(self):
        """String representation of the food item."""
        return f"{self.product_name} ({self.calories} kcal) consumed at {self.consumed_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-consumed_at'] # Show newest items first

class RunningSession(models.Model):
    """
    Represents a running session recorded by the user.
    """
    date = models.DateTimeField(default=timezone.now, help_text="Date and time of the run")
    distance = models.DecimalField(max_digits=5, decimal_places=2, help_text="Distance in kilometers")
    duration = models.DurationField(help_text="Duration of the run (HH:MM:SS)")
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this run")

    def __str__(self):
        """String representation of the running session."""
        return f"{self.distance} km on {self.date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-date'] # Show newest runs first

class Weight(models.Model):
    """
    Represents a weight measurement recorded by the user.
    """
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kilograms")
    recorded_at = models.DateTimeField(default=timezone.now, help_text="Date and time the weight was recorded")
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this weight measurement")

    def __str__(self):
        """String representation of the weight measurement."""
        return f"{self.weight} kg on {self.recorded_at.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-recorded_at'] # Show newest measurements first

class Exercise(models.Model):
    """
    Represents a type of exercise that can be performed in a workout.
    """
    name = models.CharField(max_length=200, help_text="Name of the exercise")
    description = models.TextField(blank=True, null=True, help_text="Description of how to perform the exercise")
    muscle_group = models.CharField(max_length=100, blank=True, null=True, help_text="Primary muscle group targeted")

    def __str__(self):
        """String representation of the exercise."""
        return self.name

    class Meta:
        ordering = ['name'] # Order alphabetically by name

class WorkoutSession(models.Model):
    """
    Represents a workout session performed by the user.
    """
    date = models.DateTimeField(default=timezone.now, help_text="Date and time of the workout")
    name = models.CharField(max_length=200, blank=True, null=True, help_text="Optional name for this workout session")
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this workout session")

    def __str__(self):
        """String representation of the workout session."""
        if self.name:
            return f"{self.name} on {self.date.strftime('%Y-%m-%d')}"
        return f"Workout on {self.date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-date'] # Show newest workouts first

class WorkoutExercise(models.Model):
    """
    Represents an exercise performed during a workout session, including sets and reps.
    """
    workout = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.PositiveIntegerField(default=1, help_text="Number of sets performed")
    reps = models.PositiveIntegerField(default=1, help_text="Number of repetitions per set")
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Weight used (if applicable)")
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about this exercise performance")

    def __str__(self):
        """String representation of the exercise in a workout."""
        weight_str = f" with {self.weight} kg" if self.weight else ""
        return f"{self.exercise.name}: {self.sets} sets x {self.reps} reps{weight_str}"

    class Meta:
        ordering = ['id'] # Preserve the order exercises were added

class WorkoutTable(models.Model):
    """
    Represents a workout table with exercises and workout data.
    """
    name = models.CharField(max_length=200, help_text="Name of the workout table")
    created_at = models.DateTimeField(default=timezone.now, help_text="Date and time the table was created")
    table_data = models.JSONField(help_text="JSON representation of the table data")

    def __str__(self):
        """String representation of the workout table."""
        return f"{self.name} (created on {self.created_at.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ['-created_at'] # Show newest tables first

class BodyMeasurement(models.Model):
    """
    Represents body measurements recorded by the user.
    """
    date = models.DateTimeField(default=timezone.now, help_text="Date and time the measurements were recorded")
    neck = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Neck circumference in cm")
    chest = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Chest circumference in cm")
    belly = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Belly/waist circumference in cm")
    left_biceps = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Left biceps circumference in cm")
    right_biceps = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Right biceps circumference in cm")
    left_triceps = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Left triceps circumference in cm")
    right_triceps = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Right triceps circumference in cm")
    left_forearm = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Left forearm circumference in cm")
    right_forearm = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Right forearm circumference in cm")
    left_thigh = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Left thigh circumference in cm")
    right_thigh = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Right thigh circumference in cm")
    left_lower_leg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Left lower leg/calf circumference in cm")
    right_lower_leg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Right lower leg/calf circumference in cm")
    butt = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Butt/glutes circumference in cm")
    notes = models.TextField(blank=True, null=True, help_text="Optional notes about these measurements")

    def __str__(self):
        """String representation of the body measurements."""
        return f"Body measurements on {self.date.strftime('%Y-%m-%d')}"

    class Meta:
        ordering = ['-date'] # Show newest measurements first


class UserSettings(models.Model):
    """
    Stores user settings for the application.
    Only one instance should exist (singleton pattern for single-user app).
    """
    # Profile & Goals
    name = models.CharField(max_length=100, blank=True, default='', help_text="User's name")
    age = models.PositiveIntegerField(blank=True, null=True, help_text="User's age in years")
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Height in cm")
    current_weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Current weight in kg")

    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary (little or no exercise)'),
        ('light', 'Light (exercise 1-3 days/week)'),
        ('moderate', 'Moderate (exercise 3-5 days/week)'),
        ('active', 'Active (exercise 6-7 days/week)'),
        ('very_active', 'Very Active (hard exercise daily)'),
    ]
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='moderate', help_text="Activity level for BMR calculation")

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male', help_text="Gender for BMR calculation")

    FITNESS_GOAL_CHOICES = [
        ('maintain', 'Maintain Weight'),
        ('bulk', 'Bulk (Gain Muscle)'),
        ('cut', 'Cut (Lose Fat)'),
    ]
    fitness_goal = models.CharField(max_length=10, choices=FITNESS_GOAL_CHOICES, default='maintain', help_text="Your fitness goal")

    # Whether to use auto-calculated macros based on fitness goal
    use_auto_macros = models.BooleanField(default=True, help_text="Auto-calculate macros based on fitness goal")

    daily_calorie_target = models.PositiveIntegerField(default=2000, help_text="Daily calorie goal")
    target_weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Target weight in kg")
    weekly_workout_goal = models.PositiveIntegerField(default=3, help_text="Number of workouts per week goal")

    # Macro targets
    protein_target = models.PositiveIntegerField(default=150, help_text="Daily protein target in grams")
    carbs_target = models.PositiveIntegerField(default=200, help_text="Daily carbohydrates target in grams")
    fat_target = models.PositiveIntegerField(default=65, help_text="Daily fat target in grams")

    # Appearance
    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'System Default'),
    ]
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='dark', help_text="Color theme preference")

    CHART_COLOR_CHOICES = [
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('purple', 'Purple'),
        ('orange', 'Orange'),
        ('pink', 'Pink'),
    ]
    chart_color = models.CharField(max_length=10, choices=CHART_COLOR_CHOICES, default='blue', help_text="Primary chart color")

    DATE_RANGE_CHOICES = [
        (7, 'Last 7 days'),
        (14, 'Last 14 days'),
        (30, 'Last 30 days'),
        (90, 'Last 90 days'),
    ]
    default_date_range = models.PositiveIntegerField(choices=DATE_RANGE_CHOICES, default=30, help_text="Default date range for analytics")

    # Notification preferences (for future mobile app)
    meal_reminder_enabled = models.BooleanField(default=False, help_text="Enable meal logging reminders")
    meal_reminder_times = models.JSONField(default=list, blank=True, help_text="Times for meal reminders (e.g., ['08:00', '12:00', '18:00'])")

    workout_reminder_enabled = models.BooleanField(default=False, help_text="Enable workout reminders")
    workout_reminder_time = models.TimeField(blank=True, null=True, help_text="Time for workout reminder")
    workout_reminder_days = models.JSONField(default=list, blank=True, help_text="Days for workout reminders (e.g., ['monday', 'wednesday', 'friday'])")

    weight_reminder_enabled = models.BooleanField(default=False, help_text="Enable weight logging reminders")
    weight_reminder_time = models.TimeField(blank=True, null=True, help_text="Time for weight reminder")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_bmr(self):
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation."""
        if not all([self.age, self.height, self.current_weight]):
            return None

        weight = float(self.current_weight)
        height = float(self.height)
        age = self.age

        if self.gender == 'male':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

        # Apply activity multiplier
        multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9,
        }
        return round(bmr * multipliers.get(self.activity_level, 1.55))

    def get_recommended_macros(self):
        """
        Calculate recommended macros based on fitness goal and body weight.

        Research-based recommendations:
        - Bulk: Protein 2.0g/kg, Carbs 5g/kg, Fat 1.0g/kg, Calories TDEE+15%
        - Maintain: Protein 1.8g/kg, Carbs 4g/kg, Fat 0.9g/kg, Calories TDEE
        - Cut: Protein 2.4g/kg, Carbs 2.5g/kg, Fat 0.7g/kg, Calories TDEE-20%

        Sources: Helms et al. (2014), Ribeiro et al. (2019), ISSN Position Stand
        """
        if not self.current_weight:
            return None

        weight_kg = float(self.current_weight)
        tdee = self.calculate_bmr()

        if not tdee:
            return None

        # Macro multipliers per kg bodyweight based on fitness goal
        macro_configs = {
            'bulk': {
                'protein_per_kg': 2.0,
                'carbs_per_kg': 5.0,
                'fat_per_kg': 1.0,
                'calorie_multiplier': 1.15,  # +15% surplus
                'description': 'High carbs for energy and muscle growth',
            },
            'maintain': {
                'protein_per_kg': 1.8,
                'carbs_per_kg': 4.0,
                'fat_per_kg': 0.9,
                'calorie_multiplier': 1.0,  # maintenance
                'description': 'Balanced macros for weight maintenance',
            },
            'cut': {
                'protein_per_kg': 2.4,  # Higher protein to preserve muscle
                'carbs_per_kg': 2.5,
                'fat_per_kg': 0.7,
                'calorie_multiplier': 0.80,  # -20% deficit
                'description': 'High protein to preserve muscle while losing fat',
            },
        }

        config = macro_configs.get(self.fitness_goal, macro_configs['maintain'])

        return {
            'protein': round(weight_kg * config['protein_per_kg']),
            'carbs': round(weight_kg * config['carbs_per_kg']),
            'fat': round(weight_kg * config['fat_per_kg']),
            'calories': round(tdee * config['calorie_multiplier']),
            'description': config['description'],
            'goal': self.fitness_goal,
        }

    def get_effective_targets(self):
        """
        Returns the effective macro targets - either auto-calculated or manual.
        """
        if self.use_auto_macros and self.current_weight:
            recommended = self.get_recommended_macros()
            if recommended:
                return {
                    'calories': recommended['calories'],
                    'protein': recommended['protein'],
                    'carbs': recommended['carbs'],
                    'fat': recommended['fat'],
                    'is_auto': True,
                }

        return {
            'calories': self.daily_calorie_target,
            'protein': self.protein_target,
            'carbs': self.carbs_target,
            'fat': self.fat_target,
            'is_auto': False,
        }

    def __str__(self):
        return f"User Settings (updated {self.updated_at.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        verbose_name = "User Settings"
        verbose_name_plural = "User Settings"

    @classmethod
    def get_settings(cls):
        """Get or create the singleton settings instance."""
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
