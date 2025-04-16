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
    else:
        weight_data['stats'] = {
            'avg': 0,
            'max': 0,
            'min': 0,
            'latest': 0
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
