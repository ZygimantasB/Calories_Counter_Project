# F:\Python GitHub ZygimantasB\Calories_Counter_Project\count_calories_app\views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg, Max, Min # Import additional aggregation functions
from django.http import JsonResponse
from .models import FoodItem, Weight, Exercise, WorkoutSession, WorkoutExercise
from .forms import FoodItemForm, WeightForm, ExerciseForm, WorkoutSessionForm, WorkoutExerciseForm

def get_nutrition_data(request):
    """
    API endpoint to get nutrition data for charts
    """
    time_range = request.GET.get('range', 'today')
    now = timezone.now()
    start_date = now

    # Determine the date range for filtering
    if time_range == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'week':
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Filter food items based on the selected time range
    food_items = FoodItem.objects.filter(consumed_at__gte=start_date)

    # Get data for charts
    nutrition_data = {
        'labels': ['Protein', 'Carbs', 'Fat'],
        'data': [
            float(food_items.aggregate(Sum('protein'))['protein__sum'] or 0),
            float(food_items.aggregate(Sum('carbohydrates'))['carbohydrates__sum'] or 0),
            float(food_items.aggregate(Sum('fat'))['fat__sum'] or 0)
        ]
    }

    return JsonResponse(nutrition_data)

def home(request):
    """
    View for the main calorie counting page.
    Handles displaying the form, list of items, and totals,
    as well as processing form submissions.
    """
    time_range = request.GET.get('range', 'today') # Default to 'today'
    now = timezone.now()
    start_date = now

    # Determine the date range for filtering
    if time_range == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'week':
        # Start from the beginning of the current week (assuming Monday is the first day)
        start_date = now - timedelta(days=now.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == 'month':
        # Start from the beginning of the current month
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Filter food items based on the selected time range
    food_items = FoodItem.objects.filter(consumed_at__gte=start_date)

    # Get top 15 recently entered food items
    # Using a more SQLite-compatible approach
    from django.db.models import Max
    product_names = FoodItem.objects.values('product_name').annotate(
        latest=Max('consumed_at')
    ).order_by('-latest')[:15]

    recent_items = []
    for item in product_names:
        # Get the most recent entry for each product name
        food = FoodItem.objects.filter(
            product_name=item['product_name'],
            consumed_at=item['latest']
        ).first()
        if food:
            recent_items.append(food)

    # Calculate totals for the selected range
    # Use aggregate and Sum, handling None if no items exist
    totals = food_items.aggregate(
        total_calories=Sum('calories'),
        total_fat=Sum('fat'),
        total_carbohydrates=Sum('carbohydrates'),
        total_protein=Sum('protein')
    )

    # Replace None with 0 if the aggregation result is None
    for key, value in totals.items():
        if value is None:
            totals[key] = 0

    if request.method == 'POST':
        # Handle form submission
        form = FoodItemForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to the same page (using GET) to prevent form resubmission
            # Keep the current time range selection
            return redirect(f"{request.path}?range={time_range}")
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        form = FoodItemForm() # Create an empty form

    context = {
        'form': form,
        'food_items': food_items,
        'recent_items': recent_items,
        'totals': totals,
        'selected_range': time_range, # Pass the selected range to the template
    }
    return render(request, 'count_calories_app/home.html', context)

def get_calories_trend_data(request):
    """
    API endpoint to get calorie intake trend data for charts
    """
    # Get the last 30 days of data
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    # Get all food items in the date range
    food_items = FoodItem.objects.filter(
        consumed_at__gte=start_date,
        consumed_at__lte=end_date
    ).order_by('consumed_at')

    # Group by day and sum calories
    from django.db.models.functions import TruncDate
    daily_calories = food_items.annotate(
        day=TruncDate('consumed_at')
    ).values('day').annotate(
        total_calories=Sum('calories')
    ).order_by('day')

    # Prepare data for chart
    calories_data = {
        'labels': [item['day'].strftime('%Y-%m-%d') for item in daily_calories],
        'data': [float(item['total_calories']) for item in daily_calories]
    }

    return JsonResponse(calories_data)

def get_macros_trend_data(request):
    """
    API endpoint to get macronutrient trend data for charts
    """
    # Get the last 30 days of data
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)

    # Get all food items in the date range
    food_items = FoodItem.objects.filter(
        consumed_at__gte=start_date,
        consumed_at__lte=end_date
    ).order_by('consumed_at')

    # Group by day and sum macros
    from django.db.models.functions import TruncDate
    daily_macros = food_items.annotate(
        day=TruncDate('consumed_at')
    ).values('day').annotate(
        total_protein=Sum('protein'),
        total_carbs=Sum('carbohydrates'),
        total_fat=Sum('fat')
    ).order_by('day')

    # Prepare data for chart
    macros_data = {
        'labels': [item['day'].strftime('%Y-%m-%d') for item in daily_macros],
        'protein': [float(item['total_protein']) for item in daily_macros],
        'carbs': [float(item['total_carbs']) for item in daily_macros],
        'fat': [float(item['total_fat']) for item in daily_macros]
    }

    return JsonResponse(macros_data)

def get_weight_data(request):
    """
    API endpoint to get weight data for charts
    """
    # Get all weight measurements, ordered by date
    weights = Weight.objects.all().order_by('recorded_at')

    # Prepare data for chart
    weight_data = {
        'labels': [w.recorded_at.strftime('%Y-%m-%d') for w in weights],
        'data': [float(w.weight) for w in weights]
    }

    # Add statistics
    if weights.exists():
        stats = weights.aggregate(
            avg_weight=Avg('weight'),
            max_weight=Max('weight'),
            min_weight=Min('weight'),
            latest_weight=Max('recorded_at')
        )

        # Get the latest weight measurement
        latest_weight = weights.filter(recorded_at=stats['latest_weight']).first()

        weight_data['stats'] = {
            'avg': float(stats['avg_weight']),
            'max': float(stats['max_weight']),
            'min': float(stats['min_weight']),
            'latest': float(latest_weight.weight) if latest_weight else 0
        }

        # Calculate weight change rate (kg per week)
        if len(weights) >= 2:
            # Get oldest and newest weights
            oldest_weight = weights.first()
            newest_weight = weights.last()

            # Calculate time difference in weeks
            time_diff = (newest_weight.recorded_at - oldest_weight.recorded_at).total_seconds() / (60 * 60 * 24 * 7)

            # Avoid division by zero
            if time_diff > 0:
                weight_change = newest_weight.weight - oldest_weight.weight
                weight_change_rate = weight_change / time_diff
                weight_data['stats']['change_rate'] = float(weight_change_rate)
            else:
                weight_data['stats']['change_rate'] = 0
        else:
            weight_data['stats']['change_rate'] = 0

        # Calculate BMI if height is available (for future implementation)
        # For now, we'll just add a placeholder
        weight_data['stats']['bmi'] = 0
    else:
        weight_data['stats'] = {
            'avg': 0,
            'max': 0,
            'min': 0,
            'latest': 0,
            'change_rate': 0,
            'bmi': 0
        }

    return JsonResponse(weight_data)

def weight_tracker(request):
    """
    View for the weight tracking page.
    Handles displaying the form, list of weight measurements, and chart,
    as well as processing form submissions.
    """
    # Get all weight measurements, ordered by date (newest first)
    weights = Weight.objects.all().order_by('-recorded_at')

    if request.method == 'POST':
        # Handle form submission
        form = WeightForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to the same page (using GET) to prevent form resubmission
            return redirect('weight_tracker')
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        form = WeightForm(initial={'recorded_at': timezone.now()})  # Create an empty form with current date/time

    context = {
        'form': form,
        'weights': weights,
    }
    return render(request, 'count_calories_app/weight_tracker.html', context)

def workout_tracker(request):
    """
    View for the workout tracking page.
    Displays a list of workout sessions and a form to create a new session.
    """
    # Get all workout sessions, ordered by date (newest first)
    workouts = WorkoutSession.objects.all().order_by('-date')

    if request.method == 'POST':
        # Handle form submission
        form = WorkoutSessionForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to the same page (using GET) to prevent form resubmission
            return redirect('workout_tracker')
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        form = WorkoutSessionForm(initial={'date': timezone.now()})  # Create an empty form with current date/time

    context = {
        'form': form,
        'workouts': workouts,
    }
    return render(request, 'count_calories_app/workout_tracker.html', context)

def exercise_list(request):
    """
    View for managing exercises.
    Displays a list of exercises and a form to create a new exercise.
    """
    # Get all exercises, ordered by name
    exercises = Exercise.objects.all().order_by('name')

    if request.method == 'POST':
        # Handle form submission
        form = ExerciseForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to the same page (using GET) to prevent form resubmission
            return redirect('exercise_list')
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        form = ExerciseForm()  # Create an empty form

    context = {
        'form': form,
        'exercises': exercises,
    }
    return render(request, 'count_calories_app/exercise_list.html', context)

def get_workout_frequency_data(request):
    """
    API endpoint to get workout frequency data for charts
    """
    # Get the last 90 days of data
    end_date = timezone.now()
    start_date = end_date - timedelta(days=90)

    # Get all workouts in the date range
    workouts = WorkoutSession.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')

    # Group by day and count workouts
    from django.db.models.functions import TruncDate
    daily_workouts = workouts.annotate(
        day=TruncDate('date')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')

    # Prepare data for chart
    workout_data = {
        'labels': [item['day'].strftime('%Y-%m-%d') for item in daily_workouts],
        'data': [item['count'] for item in daily_workouts]
    }

    return JsonResponse(workout_data)

def get_exercise_progress_data(request, exercise_id=None):
    """
    API endpoint to get progress data for a specific exercise
    """
    if exercise_id is None:
        exercise_id = request.GET.get('exercise_id')

    if not exercise_id:
        return JsonResponse({'error': 'No exercise ID provided'}, status=400)

    # Get the exercise or return 404
    exercise = get_object_or_404(Exercise, id=exercise_id)

    # Get all workout exercises for this exercise
    workout_exercises = WorkoutExercise.objects.filter(
        exercise_id=exercise_id
    ).order_by('workout__date')

    # Prepare data for chart
    progress_data = {
        'exercise_name': exercise.name,
        'labels': [we.workout.date.strftime('%Y-%m-%d') for we in workout_exercises],
        'weight': [float(we.weight) if we.weight else 0 for we in workout_exercises],
        'sets': [we.sets for we in workout_exercises],
        'reps': [we.reps for we in workout_exercises],
        # Calculate volume (weight * sets * reps)
        'volume': [float(we.weight) * we.sets * we.reps if we.weight else 0 for we in workout_exercises]
    }

    return JsonResponse(progress_data)

def workout_detail(request, workout_id):
    """
    View for a specific workout session.
    Displays details of the workout and a form to add exercises to it.
    """
    # Get the workout session or return 404 if not found
    workout = get_object_or_404(WorkoutSession, id=workout_id)

    # Get all exercises in this workout
    workout_exercises = WorkoutExercise.objects.filter(workout=workout).order_by('id')

    if request.method == 'POST':
        # Handle form submission
        form = WorkoutExerciseForm(request.POST)
        if form.is_valid():
            # Save the form but don't commit to database yet
            workout_exercise = form.save(commit=False)
            # Set the workout field to the current workout
            workout_exercise.workout = workout
            # Now save to database
            workout_exercise.save()
            # Redirect to the same page (using GET) to prevent form resubmission
            return redirect('workout_detail', workout_id=workout_id)
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        form = WorkoutExerciseForm()  # Create an empty form

    context = {
        'workout': workout,
        'workout_exercises': workout_exercises,
        'form': form,
    }
    return render(request, 'count_calories_app/workout_detail.html', context)
