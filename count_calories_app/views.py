# F:\Python GitHub ZygimantasB\Calories_Counter_Project\count_calories_app\views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg, Max, Min # Import additional aggregation functions
from django.http import JsonResponse
from django.contrib import messages
from .models import FoodItem, Weight, Exercise, WorkoutSession, WorkoutExercise, RunningSession, WorkoutTable, BodyMeasurement
from .forms import FoodItemForm, WeightForm, ExerciseForm, WorkoutSessionForm, WorkoutExerciseForm, RunningSessionForm, BodyMeasurementForm
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
    selected_date_str = request.GET.get('date')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    now = timezone.now()
    start_date = now
    end_date = None

    # Check if a specific date was selected
    if selected_date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            # Set start_date to the beginning of the selected date
            start_date = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            # Set end_date to the end of the selected date
            end_date = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
        except (ValueError, TypeError):
            # If date parsing fails, fall back to default behavior
            selected_date_str = None

    # Check if a date range was selected
    elif start_date_str and end_date_str:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            # Set start_date to the beginning of the selected start date
            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            # Set end_date to the end of the selected end date
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        except (ValueError, TypeError):
            # If date parsing fails, fall back to default behavior
            start_date_str = None
            end_date_str = None

    # If no specific date or date range was selected, determine the date range based on time_range
    else:
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Filter food items based on the selected time range, specific date, or date range
    if end_date:
        # For a specific date or date range, filter between start and end dates
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        # For a time range, filter from start_date onwards
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
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    now = timezone.now()
    start_date = now
    end_date = None
    selected_date = None
    date_range_selected = False
    show_averages = False

    # Check if a date range was selected
    if start_date_str and end_date_str:
        try:
            # Parse the date strings into date objects
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            # Set start_date to the beginning of the selected start date
            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            # Set end_date to the end of the selected end date
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

            # Override time_range to indicate we're viewing a date range
            time_range = 'date_range'
            date_range_selected = True
            show_averages = True
        except (ValueError, TypeError):
            # If date parsing fails, fall back to default behavior
            start_date_str = None
            end_date_str = None

    # Check if a specific date was selected (if no date range was selected)
    elif selected_date_str:
        try:
            # Parse the date string into a date object
            from datetime import datetime
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

            # Check if the selected date is today
            today_date = now.date()
            if selected_date == today_date:
                # Use the same date range as 'today' to ensure consistency
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                # Keep track that we're viewing today but with a specific date parameter
                time_range = 'today_specific'
            else:
                # Set start_date to the beginning of the selected date
                start_date = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
                # Set end_date to the end of the selected date
                end_date = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
                # Override time_range to indicate we're viewing a specific date
                time_range = 'specific_date'
        except (ValueError, TypeError):
            # If date parsing fails, fall back to default behavior
            selected_date = None

    # If no specific date or date range was selected, determine the date range based on time_range
    if not selected_date and not date_range_selected:
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            # Set end_date to the end of the current day to only show today's items
            end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif time_range == 'week':
            # Start from the beginning of the current week (assuming Monday is the first day)
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            # Set end_date to the end of the current day to only show items up to now
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            # Show averages for weekly view
            show_averages = True
        elif time_range == 'month':
            # Start from the beginning of the current month
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Set end_date to the end of the current day to only show items up to now
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            # Show averages for monthly view
            show_averages = True

    # Import TruncDate for date-based filtering
    from django.db.models.functions import TruncDate

    # Filter food items based on the selected time range, specific date, or date range
    if end_date:
        if time_range == 'specific_date' or time_range == 'today_specific' or time_range == 'today':
            # For a specific date (including today), filter by the date part only
            if selected_date:
                # If we have a selected date, use that
                # Check if selected_date is already a date object or a datetime object
                if hasattr(selected_date, 'date'):
                    # It's a datetime object, so call .date()
                    date_to_filter = selected_date.date()
                else:
                    # It's already a date object
                    date_to_filter = selected_date
            else:
                # For 'today' without a selected date, use today's date
                date_to_filter = now.date()

            food_items = FoodItem.objects.annotate(
                consumed_date=TruncDate('consumed_at')
            ).filter(consumed_date=date_to_filter)
        else:
            # For a date range, filter between start and end dates
            food_items = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        # For a time range, filter from start_date onwards
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date)

    # Get top 30 recently entered food items
    # Using a more SQLite-compatible approach
    from django.db.models import Max
    product_names = FoodItem.objects.filter(
        hide_from_quick_list=False
    ).values('product_name').annotate(
        latest=Max('consumed_at')
    ).order_by('-latest')[:30]

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

    # Calculate macronutrient percentages
    total_macros = totals['total_fat'] + totals['total_carbohydrates'] + totals['total_protein']
    if total_macros > 0:
        totals['fat_percentage'] = round((totals['total_fat'] / total_macros) * 100, 1)
        totals['carbs_percentage'] = round((totals['total_carbohydrates'] / total_macros) * 100, 1)
        totals['protein_percentage'] = round((totals['total_protein'] / total_macros) * 100, 1)
    else:
        totals['fat_percentage'] = 0
        totals['carbs_percentage'] = 0
        totals['protein_percentage'] = 0

    # Calculate averages if a date range is selected
    averages = {}
    if show_averages and food_items.exists():
        # Count the number of days in the range
        from datetime import datetime
        # Get date objects from end_date and start_date
        end_date_obj = end_date.date() if hasattr(end_date, 'date') else end_date
        start_date_obj = start_date.date() if hasattr(start_date, 'date') else start_date
        days_in_range = (end_date_obj - start_date_obj).days + 1

        if days_in_range > 0:
            averages = {
                'avg_calories': round(totals['total_calories'] / days_in_range, 1),
                'avg_fat': round(totals['total_fat'] / days_in_range, 1),
                'avg_carbohydrates': round(totals['total_carbohydrates'] / days_in_range, 1),
                'avg_protein': round(totals['total_protein'] / days_in_range, 1),
                'days_in_range': days_in_range
            }

            # Calculate average macronutrient percentages (same as totals)
            averages['fat_percentage'] = totals['fat_percentage']
            averages['carbs_percentage'] = totals['carbs_percentage']
            averages['protein_percentage'] = totals['protein_percentage']

    if request.method == 'POST':
        # Handle form submission
        logger.info(f"Processing food item form submission: {request.POST}")

        # Create a copy of POST data that we can modify
        post_data = request.POST.copy()

        # Always set consumed_at to the selected date if available, regardless of whether it's in POST data
        if selected_date:
            # Create a datetime at the beginning of the selected date
            initial_datetime = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            post_data['consumed_at'] = initial_datetime
            logger.info(f"Setting consumed_at to selected date: {initial_datetime}")
        # If selected_date is not set but selected_date_str is available, use that
        elif selected_date_str:
            try:
                # Parse the date string into a date object
                selected_date_from_str = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                # Create a datetime at the beginning of the selected date
                initial_datetime = timezone.make_aware(datetime.combine(selected_date_from_str, datetime.min.time()))
                post_data['consumed_at'] = initial_datetime
                logger.info(f"Setting consumed_at to date from URL parameter: {initial_datetime}")
            except (ValueError, TypeError):
                logger.warning(f"Could not parse date string: {selected_date_str}")

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
                elif selected_date_str:
                    # If we have a date string from the URL, redirect back to that date
                    return redirect(f"/food_tracker/?date={selected_date_str}")
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
        # If selected_date is not set but selected_date_str is available, use that
        elif selected_date_str:
            try:
                # Parse the date string into a date object
                selected_date_from_str = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                # Create a datetime at the beginning of the selected date
                initial_datetime = timezone.make_aware(datetime.combine(selected_date_from_str, datetime.min.time()))
                form = FoodItemForm(initial={'consumed_at': initial_datetime})
            except (ValueError, TypeError):
                logger.warning(f"Could not parse date string: {selected_date_str}")
                form = FoodItemForm() # Create an empty form if date parsing fails
        else:
            form = FoodItemForm() # Create an empty form

    context = {
        'form': form,
        'food_items': food_items,
        'recent_items': recent_items,
        'totals': totals,
        'selected_range': time_range, # Pass the selected range to the template
        'selected_date': selected_date, # Pass the selected date to the template
        'show_averages': show_averages, # Whether to show averages section
        'averages': averages if show_averages else {}, # Pass the averages to the template
        'start_date_str': start_date_str, # Pass the start date string to the template
        'end_date_str': end_date_str, # Pass the end date string to the template
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

        # Calculate BMI (assuming height of 175cm - this could be made configurable in user settings)
        height_in_meters = 1.75  # Default height
        latest_weight_value = float(latest_weight.weight) if latest_weight else 0
        if latest_weight_value > 0:
            bmi = latest_weight_value / (height_in_meters * height_in_meters)
            weight_data['stats']['bmi'] = round(bmi, 1)
        else:
            weight_data['stats']['bmi'] = 0

        # Calculate weight consistency (standard deviation)
        if len(weights) >= 3:
            import numpy as np
            weight_values = [float(w.weight) for w in weights]
            weight_data['stats']['consistency'] = round(float(np.std(weight_values)), 2)
        else:
            weight_data['stats']['consistency'] = 0

        # Calculate projected weight in 4 weeks based on current trend
        if weight_data['stats']['change_rate'] != 0:
            projected_weight = latest_weight_value + (weight_data['stats']['change_rate'] * 4)
            weight_data['stats']['projected_weight'] = round(projected_weight, 1)
        else:
            weight_data['stats']['projected_weight'] = latest_weight_value

        # Calculate weight goal metrics (assuming goal is to lose weight to 70kg)
        weight_goal = 70.0  # Default goal weight
        if latest_weight_value > weight_goal and weight_data['stats']['change_rate'] < 0:
            # If losing weight and current weight is above goal
            weeks_to_goal = (latest_weight_value - weight_goal) / abs(weight_data['stats']['change_rate'])
            weight_data['stats']['weeks_to_goal'] = round(weeks_to_goal, 1)

            # Calculate goal date
            import datetime
            goal_date = latest_weight.recorded_at + datetime.timedelta(weeks=weeks_to_goal)
            weight_data['stats']['goal_date'] = goal_date.strftime('%Y-%m-%d')
        else:
            weight_data['stats']['weeks_to_goal'] = 0
            weight_data['stats']['goal_date'] = 'N/A'
    else:
        weight_data['stats'] = {
            'avg': 0,
            'max': 0,
            'min': 0,
            'latest': 0,
            'change_rate': 0,
            'bmi': 0,
            'consistency': 0,
            'projected_weight': 0,
            'weeks_to_goal': 0,
            'goal_date': 'N/A'
        }

    return JsonResponse(weight_data)

def get_weight_calories_correlation(request):
    """
    API endpoint to get correlation data between weight changes and calorie intake
    """
    # Get all weight measurements, ordered by date (oldest first)
    weights = Weight.objects.all().order_by('recorded_at')

    correlation_data = []

    # We need at least 2 weight measurements to calculate changes
    if len(weights) >= 2:
        for i in range(1, len(weights)):
            current_weight = weights[i]
            previous_weight = weights[i-1]

            # Calculate weight change
            weight_change = float(current_weight.weight) - float(previous_weight.weight)

            # Get total calories consumed between these two weight measurements
            # Use the date part of the weight measurements to include all food items for those days
            from datetime import datetime, time

            # Get the date part of the previous weight measurement and set time to 00:00:00
            prev_date = previous_weight.recorded_at.date()
            prev_datetime = timezone.make_aware(datetime.combine(prev_date, time.min))

            # Get the date part of the current weight measurement and set time to 23:59:59
            curr_date = current_weight.recorded_at.date()
            curr_datetime = timezone.make_aware(datetime.combine(curr_date, time.max))

            # Filter food items between the two dates (inclusive of both days)
            food_items = FoodItem.objects.filter(
                consumed_at__gte=prev_datetime,
                consumed_at__lte=curr_datetime
            )

            # Use Django's ORM aggregation to calculate total calories, consistent with food_tracker
            total_calories_result = food_items.aggregate(Sum('calories'))['calories__sum'] or 0
            total_calories = float(total_calories_result)

            # Calculate days between measurements
            days_between = (current_weight.recorded_at - previous_weight.recorded_at).days
            if days_between == 0:  # Avoid division by zero
                days_between = 1

            # Calculate daily average calories (we'll still calculate it even though we won't display it)
            daily_avg_calories = float(total_calories) / days_between

            # Add data to the result
            correlation_data.append({
                'start_date': previous_weight.recorded_at.strftime('%Y-%m-%d'),
                'end_date': current_weight.recorded_at.strftime('%Y-%m-%d'),
                'start_weight': float(previous_weight.weight),
                'end_weight': float(current_weight.weight),
                'weight_change': round(weight_change, 2),
                'days_between': days_between,
                'total_calories': float(total_calories),
                'daily_avg_calories': round(daily_avg_calories, 1),
            })

    # Reverse the order of the data (newest first)
    correlation_data.reverse()

    # Implement pagination
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1

    # Define items per page
    items_per_page = 10

    # Calculate start and end indices for the current page
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page

    # Get the data for the current page
    page_data = correlation_data[start_idx:end_idx]

    # Calculate total pages
    total_pages = (len(correlation_data) + items_per_page - 1) // items_per_page

    return JsonResponse({
        'correlation_data': page_data,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    })

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

    # Calculate speed for each running session
    running_sessions_with_speed = []
    for session in running_sessions:
        session_data = {
            'session': session,
            'speed': 0  # Default value
        }

        # Calculate speed in km/h
        duration_seconds = session.duration.total_seconds()
        if duration_seconds > 0:  # Avoid division by zero
            hours = duration_seconds / 3600  # Convert seconds to hours
            speed = float(session.distance) / hours
            session_data['speed'] = round(speed, 1)  # Round to 1 decimal place

        running_sessions_with_speed.append(session_data)

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
        'running_sessions': running_sessions_with_speed,
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
        'avg_speed': 0,  # Average speed in km/h
        'avg_pace': 0,   # Average pace in min/km
        'total_calories': 0,  # Estimated total calories burned
        'weekly_distance': 0,  # Average weekly distance
        'monthly_distance': 0,  # Average monthly distance
        'pace_improvement': 0,  # Pace improvement over time (%)
        'longest_run': 0,  # Longest run distance
        'fastest_pace': 0,  # Fastest pace (min/km)
    }

    # Prepare data for chart
    labels = []
    distances = []
    durations = []
    paces = []  # Pace in min/km
    speeds = []  # Speed in km/h
    calories = []  # Estimated calories burned

    # For weekly and monthly aggregation
    weekly_distances = {}
    monthly_distances = {}

    # For pace improvement calculation
    first_pace = None
    last_pace = None

    # For fastest pace and longest run
    fastest_pace_value = float('inf')
    longest_run_distance = 0

    for session in running_sessions:
        labels.append(session.date.strftime('%Y-%m-%d'))
        distances.append(float(session.distance))

        # Convert duration to minutes for the chart
        duration_minutes = session.duration.total_seconds() / 60
        durations.append(duration_minutes)

        # Calculate pace (minutes per km)
        if float(session.distance) > 0:
            pace = duration_minutes / float(session.distance)
            paces.append(pace)

            # Track first and last pace for improvement calculation
            if first_pace is None:
                first_pace = pace
            last_pace = pace

            # Track fastest pace
            if pace < fastest_pace_value:
                fastest_pace_value = pace
        else:
            paces.append(0)

        # Calculate speed (km/h)
        if duration_minutes > 0:
            speed = float(session.distance) / (duration_minutes / 60)
            speeds.append(speed)
        else:
            speeds.append(0)

        # Estimate calories burned (rough estimate: ~60 calories per km)
        calorie_estimate = float(session.distance) * 60
        calories.append(calorie_estimate)

        # Track longest run
        if float(session.distance) > longest_run_distance:
            longest_run_distance = float(session.distance)

        # Aggregate by week
        week_key = session.date.strftime('%Y-%W')
        if week_key not in weekly_distances:
            weekly_distances[week_key] = 0
        weekly_distances[week_key] += float(session.distance)

        # Aggregate by month
        month_key = session.date.strftime('%Y-%m')
        if month_key not in monthly_distances:
            monthly_distances[month_key] = 0
        monthly_distances[month_key] += float(session.distance)

    # Calculate stats if we have data
    if running_sessions:
        stats['total_distance'] = sum(distances)
        stats['total_sessions'] = len(running_sessions)
        stats['avg_distance'] = stats['total_distance'] / stats['total_sessions']
        total_duration_minutes = sum(durations)
        stats['avg_duration'] = total_duration_minutes / stats['total_sessions']

        # Calculate average speed in km/h
        # Convert duration from minutes to hours for speed calculation
        total_duration_hours = total_duration_minutes / 60
        if total_duration_hours > 0:  # Avoid division by zero
            stats['avg_speed'] = stats['total_distance'] / total_duration_hours

        # Calculate average pace in min/km
        if stats['total_distance'] > 0:
            stats['avg_pace'] = total_duration_minutes / stats['total_distance']

        # Calculate total calories burned
        stats['total_calories'] = sum(calories)

        # Calculate weekly and monthly averages
        if weekly_distances:
            stats['weekly_distance'] = sum(weekly_distances.values()) / len(weekly_distances)

        if monthly_distances:
            stats['monthly_distance'] = sum(monthly_distances.values()) / len(monthly_distances)

        # Calculate pace improvement (if we have at least 2 sessions)
        if first_pace is not None and last_pace is not None and first_pace > 0:
            # Negative value means improvement (less time per km)
            improvement_percentage = ((last_pace - first_pace) / first_pace) * 100
            stats['pace_improvement'] = -improvement_percentage  # Invert so positive means improvement

        # Set longest run and fastest pace
        stats['longest_run'] = longest_run_distance
        stats['fastest_pace'] = fastest_pace_value if fastest_pace_value != float('inf') else 0

    running_data = {
        'labels': labels,
        'distances': distances,
        'durations': durations,
        'paces': paces,
        'speeds': speeds,
        'calories': calories,
        'stats': stats
    }

    return JsonResponse(running_data)

def body_measurements_tracker(request):
    """
    View for the body measurements tracker page.
    """
    try:
        # Get all body measurements ordered by date (newest first)
        measurements = BodyMeasurement.objects.all().order_by('-date')

        # Handle form submission for adding new measurements
        if request.method == 'POST':
            form = BodyMeasurementForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Body measurements added successfully!')
                return redirect('body_measurements_tracker')
        else:
            # Pre-populate the date field with the current date and time
            form = BodyMeasurementForm(initial={'date': timezone.now()})

        # Get all weight measurements
        weights = Weight.objects.all()

        # Calculate comparison data for arrows
        measurements_with_arrows = []
        for i, measurement in enumerate(measurements):
            measurement_data = {
                'measurement': measurement,
                'arrows': {},
                'weight': None
            }

            # Find weight for the same date
            # Get just the date part, handling both datetime and date objects
            measurement_date = measurement.date.date() if hasattr(measurement.date, 'date') else measurement.date
            matching_weight = weights.filter(recorded_at__date=measurement_date).first()
            if matching_weight:
                measurement_data['weight'] = matching_weight.weight

            # If there's a next measurement (chronologically previous), compare values
            if i < len(measurements) - 1:
                next_measurement = measurements[i + 1]

                # Compare each field
                for field in ['neck', 'chest', 'belly', 'left_biceps', 'right_biceps', 
                             'left_triceps', 'right_triceps', 'left_forearm', 'right_forearm',
                             'left_thigh', 'right_thigh', 'left_lower_leg', 'right_lower_leg', 'butt']:
                    current_value = getattr(measurement, field)
                    next_value = getattr(next_measurement, field)

                    if current_value is not None and next_value is not None:
                        if current_value > next_value:
                            measurement_data['arrows'][field] = 'up'
                        elif current_value < next_value:
                            measurement_data['arrows'][field] = 'down'

            # Compare weight if available
            if i < len(measurements) - 1 and measurement_data['weight'] is not None:
                # Get just the date part, handling both datetime and date objects
                next_measurement_date = measurements[i + 1].date.date() if hasattr(measurements[i + 1].date, 'date') else measurements[i + 1].date
                next_matching_weight = weights.filter(recorded_at__date=next_measurement_date).first()
                if next_matching_weight:
                    if measurement_data['weight'] > next_matching_weight.weight:
                        measurement_data['arrows']['weight'] = 'up'
                    elif measurement_data['weight'] < next_matching_weight.weight:
                        measurement_data['arrows']['weight'] = 'down'

            measurements_with_arrows.append(measurement_data)

        # Render the template with the form and measurements
        return render(request, 'count_calories_app/body_measurements_tracker.html', {
            'form': form,
            'measurements_with_arrows': measurements_with_arrows,
            'page_title': 'Body Measurements Tracker',
        })
    except Exception as e:
        logger.error(f"Error in body_measurements_tracker: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('home')

def edit_body_measurement(request, measurement_id):
    """
    View for editing an existing body measurement.
    """
    try:
        # Get the measurement to edit
        measurement = get_object_or_404(BodyMeasurement, id=measurement_id)

        # Handle form submission
        if request.method == 'POST':
            form = BodyMeasurementForm(request.POST, instance=measurement)
            if form.is_valid():
                form.save()
                messages.success(request, 'Body measurements updated successfully!')
                return redirect('body_measurements_tracker')
        else:
            form = BodyMeasurementForm(instance=measurement)

        # Render the template with the form
        return render(request, 'count_calories_app/edit_body_measurement.html', {
            'form': form,
            'measurement': measurement,
            'page_title': 'Edit Body Measurements',
        })
    except Exception as e:
        logger.error(f"Error in edit_body_measurement: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('body_measurements_tracker')

def delete_body_measurement(request, measurement_id):
    """
    View for deleting a body measurement.
    """
    try:
        # Get the measurement to delete
        measurement = get_object_or_404(BodyMeasurement, id=measurement_id)

        # Handle form submission
        if request.method == 'POST':
            measurement.delete()
            messages.success(request, 'Body measurements deleted successfully!')
            return redirect('body_measurements_tracker')

        # Render the confirmation template
        return render(request, 'count_calories_app/delete_body_measurement.html', {
            'measurement': measurement,
            'page_title': 'Delete Body Measurements',
        })
    except Exception as e:
        logger.error(f"Error in delete_body_measurement: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('body_measurements_tracker')

def get_body_measurements_data(request):
    """
    API endpoint to get body measurements data for charts.
    """
    try:
        # Get all body measurements ordered by date
        measurements = BodyMeasurement.objects.all().order_by('date')

        # Get all weight measurements
        weights = Weight.objects.all()

        # Prepare data for charts
        dates = [m.date.strftime('%Y-%m-%d') for m in measurements]
        neck_data = [float(m.neck) if m.neck else None for m in measurements]
        chest_data = [float(m.chest) if m.chest else None for m in measurements]
        belly_data = [float(m.belly) if m.belly else None for m in measurements]
        left_biceps_data = [float(m.left_biceps) if m.left_biceps else None for m in measurements]
        right_biceps_data = [float(m.right_biceps) if m.right_biceps else None for m in measurements]
        left_triceps_data = [float(m.left_triceps) if m.left_triceps else None for m in measurements]
        right_triceps_data = [float(m.right_triceps) if m.right_triceps else None for m in measurements]
        left_forearm_data = [float(m.left_forearm) if m.left_forearm else None for m in measurements]
        right_forearm_data = [float(m.right_forearm) if m.right_forearm else None for m in measurements]
        left_thigh_data = [float(m.left_thigh) if m.left_thigh else None for m in measurements]
        right_thigh_data = [float(m.right_thigh) if m.right_thigh else None for m in measurements]
        left_lower_leg_data = [float(m.left_lower_leg) if m.left_lower_leg else None for m in measurements]
        right_lower_leg_data = [float(m.right_lower_leg) if m.right_lower_leg else None for m in measurements]
        butt_data = [float(m.butt) if m.butt else None for m in measurements]

        # Get weight data for each measurement date
        weight_data = []
        for m in measurements:
            # Get just the date part, handling both datetime and date objects
            measurement_date = m.date.date() if hasattr(m.date, 'date') else m.date
            matching_weight = weights.filter(recorded_at__date=measurement_date).first()
            if matching_weight:
                weight_data.append(float(matching_weight.weight))
            else:
                weight_data.append(None)

        # Return the data as JSON
        return JsonResponse({
            'dates': dates,
            'weight': weight_data,
            'neck': neck_data,
            'chest': chest_data,
            'belly': belly_data,
            'left_biceps': left_biceps_data,
            'right_biceps': right_biceps_data,
            'left_triceps': left_triceps_data,
            'right_triceps': right_triceps_data,
            'left_forearm': left_forearm_data,
            'right_forearm': right_forearm_data,
            'left_thigh': left_thigh_data,
            'right_thigh': right_thigh_data,
            'left_lower_leg': left_lower_leg_data,
            'right_lower_leg': right_lower_leg_data,
            'butt': butt_data,
        })
    except Exception as e:
        logger.error(f"Error in get_body_measurements_data: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)
