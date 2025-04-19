# F:\Python GitHub ZygimantasB\Calories_Counter_Project\count_calories_app\views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg, Max, Min # Import additional aggregation functions
from django.http import JsonResponse
from django.contrib import messages
from .models import FoodItem, Weight, Exercise, WorkoutSession, WorkoutExercise, RunningSession, WorkoutTable
from .forms import FoodItemForm, WeightForm, ExerciseForm, WorkoutSessionForm, WorkoutExerciseForm, RunningSessionForm
import logging
import json

# Get a logger for this file
logger = logging.getLogger('count_calories_app')

def home(request):
    """
    View for the home page.
    Displays general information about the application.
    """
    return render(request, 'count_calories_app/home.html')

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

def food_tracker(request):
    """
    View for the food tracking page.
    Handles displaying the form, list of items, and totals,
    as well as processing form submissions.
    """
    time_range = request.GET.get('range', 'today') # Default to 'today'
    selected_date_str = request.GET.get('date')
    now = timezone.now()
    start_date = now
    end_date = None
    selected_date = None

    # Check if a specific date was selected
    if selected_date_str:
        try:
            # Parse the date string into a date object
            from datetime import datetime
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            # Set start_date to the beginning of the selected date
            start_date = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            # Set end_date to the end of the selected date
            end_date = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
            # Override time_range to indicate we're viewing a specific date
            time_range = 'specific_date'
        except (ValueError, TypeError):
            # If date parsing fails, fall back to default behavior
            selected_date = None

    # If no specific date was selected, determine the date range based on time_range
    if not selected_date:
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'week':
            # Start from the beginning of the current week (assuming Monday is the first day)
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'month':
            # Start from the beginning of the current month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Filter food items based on the selected time range or specific date
    if end_date:
        # For a specific date, filter between start and end of that day
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        # For a time range, filter from start_date onwards
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date)

    # Get top 15 recently entered food items
    # Using a more SQLite-compatible approach
    from django.db.models import Max
    product_names = FoodItem.objects.filter(
        hide_from_quick_list=False
    ).values('product_name').annotate(
        latest=Max('consumed_at')
    ).order_by('-latest')[:15]

    recent_items = []
    for item in product_names:
        # Get the most recent entry for each product name
        food = FoodItem.objects.filter(
            product_name=item['product_name'],
            consumed_at=item['latest'],
            hide_from_quick_list=False
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
        logger.info(f"Processing food item form submission: {request.POST}")

        # Create a copy of POST data that we can modify
        post_data = request.POST.copy()

        # If a date is selected and consumed_at is not in the POST data, set it
        if selected_date and 'consumed_at' not in post_data:
            # Create a datetime at the beginning of the selected date
            initial_datetime = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            post_data['consumed_at'] = initial_datetime

        form = FoodItemForm(post_data)
        if form.is_valid():
            try:
                food_item = form.save()
                logger.info(f"Food item saved successfully: {food_item.id} - {food_item.product_name}")
                messages.success(request, f"Food item '{food_item.product_name}' added successfully!")
                # Redirect to the same page (using GET) to prevent form resubmission
                # Keep the current date or time range selection
                if selected_date:
                    return redirect(f"/food_tracker/?date={selected_date.strftime('%Y-%m-%d')}")
                else:
                    return redirect(f"/food_tracker/?range={time_range}")
            except Exception as e:
                logger.error(f"Error saving food item: {str(e)}")
                messages.error(request, f"Error saving food item: {str(e)}")
        else:
            logger.warning(f"Invalid food item form: {form.errors}")
            messages.warning(request, "Please correct the errors in the form.")
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        # Initialize form with selected date as consumed_at if a date is selected
        if selected_date:
            # Create a datetime at the beginning of the selected date
            initial_datetime = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            form = FoodItemForm(initial={'consumed_at': initial_datetime})
        else:
            form = FoodItemForm() # Create an empty form

    context = {
        'form': form,
        'food_items': food_items,
        'recent_items': recent_items,
        'totals': totals,
        'selected_range': time_range, # Pass the selected range to the template
        'selected_date': selected_date, # Pass the selected date to the template
    }
    return render(request, 'count_calories_app/food_tracker.html', context)

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
                weight_change_rate = float(weight_change) / time_diff
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
        logger.info(f"Processing weight form submission: {request.POST}")
        form = WeightForm(request.POST)
        if form.is_valid():
            try:
                weight = form.save()
                logger.info(f"Weight measurement saved successfully: {weight.id} - {weight.weight} kg")
                messages.success(request, f"Weight measurement of {weight.weight} kg added successfully!")
                # Redirect to the same page (using GET) to prevent form resubmission
                return redirect('weight_tracker')
            except Exception as e:
                logger.error(f"Error saving weight measurement: {str(e)}")
                messages.error(request, f"Error saving weight measurement: {str(e)}")
        else:
            logger.warning(f"Invalid weight form: {form.errors}")
            messages.warning(request, "Please correct the errors in the form.")
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

def edit_food_item(request, food_item_id):
    """
    View for editing a food item.
    """
    # Get the food item or return 404 if not found
    food_item = get_object_or_404(FoodItem, id=food_item_id)

    if request.method == 'POST':
        # Handle form submission
        form = FoodItemForm(request.POST, instance=food_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Food item updated successfully!')
            # Redirect to the food tracker page
            return redirect('food_tracker')
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        form = FoodItemForm(instance=food_item)

    context = {
        'form': form,
        'food_item': food_item,
        'edit_mode': True,
    }
    return render(request, 'count_calories_app/edit_food_item.html', context)

def delete_food_item(request, food_item_id):
    """
    View for deleting a food item.
    """
    # Get the food item or return 404 if not found
    food_item = get_object_or_404(FoodItem, id=food_item_id)

    if request.method == 'POST':
        # Delete the food item
        food_item.delete()
        messages.success(request, 'Food item deleted successfully!')
        # Redirect to the food tracker page
        return redirect('food_tracker')

    context = {
        'food_item': food_item,
    }
    return render(request, 'count_calories_app/delete_food_item.html', context)

def edit_weight(request, weight_id):
    """
    View for editing a weight measurement.
    """
    # Get the weight measurement or return 404 if not found
    weight = get_object_or_404(Weight, id=weight_id)

    if request.method == 'POST':
        # Handle form submission
        form = WeightForm(request.POST, instance=weight)
        if form.is_valid():
            form.save()
            messages.success(request, 'Weight measurement updated successfully!')
            # Redirect to the weight tracker page
            return redirect('weight_tracker')
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        form = WeightForm(instance=weight)

    context = {
        'form': form,
        'weight': weight,
        'edit_mode': True,
    }
    return render(request, 'count_calories_app/edit_weight.html', context)

def delete_weight(request, weight_id):
    """
    View for deleting a weight measurement.
    """
    # Get the weight measurement or return 404 if not found
    weight = get_object_or_404(Weight, id=weight_id)

    if request.method == 'POST':
        # Delete the weight measurement
        weight.delete()
        messages.success(request, 'Weight measurement deleted successfully!')
        # Redirect to the weight tracker page
        return redirect('weight_tracker')

    context = {
        'weight': weight,
    }
    return render(request, 'count_calories_app/delete_weight.html', context)

def workout_table(request):
    """
    View for the Excel-like workout table interface.
    Allows users to create and manage workout tables with exercises and workout data.
    """
    # Get all workout tables, ordered by date (newest first)
    workout_tables = WorkoutTable.objects.all().order_by('-created_at')

    context = {
        'workout_tables': workout_tables,
    }
    return render(request, 'count_calories_app/workout_table.html', context)

def save_workout_table(request):
    """
    API endpoint to save a workout table.
    """
    if request.method == 'POST':
        try:
            logger.info(f"Processing workout table save request")
            data = json.loads(request.body)

            table_id = data.get('id')
            table_name = data.get('name', 'Workout Table')
            table_data = data.get('data', {})

            if table_id:
                # Update existing table
                try:
                    table = WorkoutTable.objects.get(id=table_id)
                    table.name = table_name
                    table.table_data = table_data
                    table.save()
                    logger.info(f"Workout table updated successfully: {table.id} - {table.name}")
                    return JsonResponse({'success': True, 'message': 'Workout table updated successfully', 'id': table.id})
                except WorkoutTable.DoesNotExist:
                    logger.error(f"Workout table not found: {table_id}")
                    return JsonResponse({'success': False, 'message': 'Workout table not found'}, status=404)
            else:
                # Create new table
                table = WorkoutTable.objects.create(
                    name=table_name,
                    table_data=table_data
                )
                logger.info(f"Workout table created successfully: {table.id} - {table.name}")
                return JsonResponse({'success': True, 'message': 'Workout table created successfully', 'id': table.id})

        except Exception as e:
            logger.error(f"Error saving workout table: {str(e)}")
            return JsonResponse({'success': False, 'message': f"Error saving workout table: {str(e)}"}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

def get_workout_tables(request):
    """
    API endpoint to get all workout tables.
    """
    try:
        workout_tables = WorkoutTable.objects.all().order_by('-created_at')
        tables_data = []

        for table in workout_tables:
            # Log the raw table data for debugging
            logger.info(f"Raw table_data for table {table.id}: {table.table_data}")

            # Ensure table_data is properly parsed as JSON
            table_data = table.table_data

            # If table_data is a string (which might happen if it wasn't properly parsed),
            # try to parse it as JSON
            if isinstance(table_data, str):
                try:
                    table_data = json.loads(table_data)
                    logger.info(f"Successfully parsed table_data as JSON for table {table.id}")
                except json.JSONDecodeError:
                    logger.error(f"Error parsing table_data as JSON for table {table.id}")
                    # If parsing fails, use the original data
                    pass

            # Check if the data might be double-encoded
            if isinstance(table_data, dict) and 'workouts' in table_data and 'exercises' in table_data:
                logger.info(f"Table {table.id} has proper structure with workouts and exercises")
            else:
                logger.warning(f"Table {table.id} data structure might be incorrect: {table_data}")
                # Try to fix the data structure if possible
                if isinstance(table_data, str):
                    try:
                        # Try parsing again in case it's double-encoded
                        table_data = json.loads(table_data)
                        logger.info(f"Fixed double-encoded JSON for table {table.id}")
                    except json.JSONDecodeError:
                        logger.error(f"Failed to fix double-encoded JSON for table {table.id}")

                # If table_data is still not a dict with the expected structure, try to create a valid structure
                if not isinstance(table_data, dict) or 'workouts' not in table_data or 'exercises' not in table_data:
                    logger.warning(f"Creating default structure for table {table.id}")
                    table_data = {
                        'workouts': [],
                        'exercises': []
                    }

            tables_data.append({
                'id': table.id,
                'name': table.name,
                'date': table.created_at.strftime('%m/%d/%Y'),
                'data': table_data
            })

        logger.info(f"Returning {len(tables_data)} tables")
        return JsonResponse({'success': True, 'tables': tables_data})
    except Exception as e:
        logger.error(f"Error getting workout tables: {str(e)}")
        return JsonResponse({'success': False, 'message': f"Error getting workout tables: {str(e)}"}, status=500)

def delete_workout_table(request, table_id):
    """
    API endpoint to delete a workout table.
    """
    if request.method == 'DELETE':
        try:
            table = WorkoutTable.objects.get(id=table_id)
            table.delete()
            logger.info(f"Workout table deleted successfully: {table_id}")
            return JsonResponse({'success': True, 'message': 'Workout table deleted successfully'})
        except WorkoutTable.DoesNotExist:
            logger.error(f"Workout table not found: {table_id}")
            return JsonResponse({'success': False, 'message': 'Workout table not found'}, status=404)
        except Exception as e:
            logger.error(f"Error deleting workout table: {str(e)}")
            return JsonResponse({'success': False, 'message': f"Error deleting workout table: {str(e)}"}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

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

def running_tracker(request):
    """
    View for the running tracking page.
    Handles displaying the form, list of running sessions, and charts,
    as well as processing form submissions.
    """
    # Get all running sessions, ordered by date (newest first)
    running_sessions = RunningSession.objects.all().order_by('-date')

    if request.method == 'POST':
        # Handle form submission
        logger.info(f"Processing running session form submission: {request.POST}")
        form = RunningSessionForm(request.POST)
        if form.is_valid():
            try:
                running_session = form.save()
                logger.info(f"Running session saved successfully: {running_session.id} - {running_session.distance} km")
                messages.success(request, f"Running session of {running_session.distance} km added successfully!")
                # Redirect to the same page (using GET) to prevent form resubmission
                return redirect('running_tracker')
            except Exception as e:
                logger.error(f"Error saving running session: {str(e)}")
                messages.error(request, f"Error saving running session: {str(e)}")
        else:
            logger.warning(f"Invalid running session form: {form.errors}")
            messages.warning(request, "Please correct the errors in the form.")
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        form = RunningSessionForm(initial={'date': timezone.now()})  # Create an empty form with current date/time

    context = {
        'form': form,
        'running_sessions': running_sessions,
    }
    return render(request, 'count_calories_app/running_tracker.html', context)

def edit_running_session(request, running_session_id):
    """
    View for editing a running session.
    """
    # Get the running session or return 404 if not found
    running_session = get_object_or_404(RunningSession, id=running_session_id)

    if request.method == 'POST':
        # Handle form submission
        form = RunningSessionForm(request.POST, instance=running_session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Running session updated successfully!')
            # Redirect to the running tracker page
            return redirect('running_tracker')
        # If form is invalid, it will be re-rendered with errors below
    else:
        # Handle GET request (displaying the page)
        form = RunningSessionForm(instance=running_session)

    context = {
        'form': form,
        'running_session': running_session,
        'edit_mode': True,
    }
    return render(request, 'count_calories_app/edit_running_session.html', context)

def delete_running_session(request, running_session_id):
    """
    View for deleting a running session.
    """
    # Get the running session or return 404 if not found
    running_session = get_object_or_404(RunningSession, id=running_session_id)

    if request.method == 'POST':
        # Delete the running session
        running_session.delete()
        messages.success(request, 'Running session deleted successfully!')
        # Redirect to the running tracker page
        return redirect('running_tracker')

    context = {
        'running_session': running_session,
    }
    return render(request, 'count_calories_app/delete_running_session.html', context)

def hide_from_quick_list(request, food_item_id):
    """
    View for hiding a food item from the quick list.
    """
    # Get the food item or return 404 if not found
    food_item = get_object_or_404(FoodItem, id=food_item_id)

    # Set hide_from_quick_list to True
    food_item.hide_from_quick_list = True
    food_item.save()

    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        # Return a JSON response for AJAX requests
        return JsonResponse({
            'success': True,
            'message': f"'{food_item.product_name}' has been hidden from the quick list."
        })
    else:
        # Return a success message for regular requests
        messages.success(request, f"'{food_item.product_name}' has been hidden from the quick list.")

        # Redirect back to the food tracker page
        return redirect('food_tracker')

def get_running_data(request):
    """
    API endpoint to get running data for charts
    """
    # Get the last 90 days of data
    end_date = timezone.now()
    start_date = end_date - timedelta(days=90)

    # Get all running sessions in the date range
    running_sessions = RunningSession.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')

    # Calculate stats
    stats = {
        'total_distance': 0,
        'total_sessions': 0,
        'avg_distance': 0,
        'avg_duration': 0,
    }

    # Prepare data for chart
    labels = []
    distances = []
    durations = []

    for session in running_sessions:
        labels.append(session.date.strftime('%Y-%m-%d'))
        distances.append(float(session.distance))
        # Convert duration to minutes for the chart
        duration_minutes = session.duration.total_seconds() / 60
        durations.append(duration_minutes)

    # Calculate stats if we have data
    if running_sessions:
        stats['total_distance'] = sum(distances)
        stats['total_sessions'] = len(running_sessions)
        stats['avg_distance'] = stats['total_distance'] / stats['total_sessions']
        total_duration_minutes = sum(durations)
        stats['avg_duration'] = total_duration_minutes / stats['total_sessions']

    running_data = {
        'labels': labels,
        'distances': distances,
        'durations': durations,
        'stats': stats
    }

    return JsonResponse(running_data)
