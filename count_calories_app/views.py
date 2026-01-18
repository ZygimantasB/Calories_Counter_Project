from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count, Avg, Max, Min
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import FoodItem, Weight, Exercise, WorkoutSession, WorkoutExercise, RunningSession, WorkoutTable, BodyMeasurement, UserSettings
from .forms import FoodItemForm, WeightForm, ExerciseForm, WorkoutSessionForm, WorkoutExerciseForm, RunningSessionForm, BodyMeasurementForm
from .services import GeminiService
import logging
import json
import google.generativeai as genai
import os
import csv
from django.conf import settings
from google.api_core.exceptions import GoogleAPICallError, PermissionDenied, Unauthenticated, InvalidArgument, FailedPrecondition

logger = logging.getLogger('count_calories_app')

def home(request):
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Week start (Monday)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Month start
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Today's food stats
    today_food = FoodItem.objects.filter(consumed_at__gte=today_start, consumed_at__lte=today_end)
    today_stats = today_food.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        carbs=Sum('carbohydrates'),
        fat=Sum('fat'),
        count=Count('id')
    )

    # This week's food stats
    week_food = FoodItem.objects.filter(consumed_at__gte=week_start, consumed_at__lte=today_end)
    week_stats = week_food.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        carbs=Sum('carbohydrates'),
        fat=Sum('fat'),
        count=Count('id')
    )

    # Latest weight
    latest_weight = Weight.objects.order_by('-recorded_at').first()

    # Weight change (last 7 days)
    week_ago = now - timedelta(days=7)
    weight_week_ago = Weight.objects.filter(recorded_at__lte=week_ago).order_by('-recorded_at').first()
    weight_change = None
    if latest_weight and weight_week_ago:
        weight_change = float(latest_weight.weight) - float(weight_week_ago.weight)

    # This week's workouts
    week_workouts = WorkoutSession.objects.filter(date__gte=week_start.date()).count()

    # This week's runs
    week_runs = RunningSession.objects.filter(date__gte=week_start.date())
    week_run_stats = week_runs.aggregate(
        total_distance=Sum('distance'),
        total_duration=Sum('duration'),
        count=Count('id')
    )

    # Recent food items (last 5)
    recent_foods = FoodItem.objects.order_by('-consumed_at')[:5]

    # Streak calculation (consecutive days with food logged)
    streak = 0
    check_date = now.date()
    while True:
        day_start = timezone.make_aware(timezone.datetime.combine(check_date, timezone.datetime.min.time()))
        day_end = timezone.make_aware(timezone.datetime.combine(check_date, timezone.datetime.max.time()))
        if FoodItem.objects.filter(consumed_at__gte=day_start, consumed_at__lte=day_end).exists():
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    context = {
        'today_stats': {
            'calories': today_stats['calories'] or 0,
            'protein': today_stats['protein'] or 0,
            'carbs': today_stats['carbs'] or 0,
            'fat': today_stats['fat'] or 0,
            'count': today_stats['count'] or 0,
        },
        'week_stats': {
            'calories': week_stats['calories'] or 0,
            'protein': week_stats['protein'] or 0,
            'carbs': week_stats['carbs'] or 0,
            'fat': week_stats['fat'] or 0,
            'count': week_stats['count'] or 0,
        },
        'latest_weight': latest_weight,
        'weight_change': weight_change,
        'week_workouts': week_workouts,
        'week_run_stats': {
            'distance': week_run_stats['total_distance'] or 0,
            'duration': week_run_stats['total_duration'] or 0,
            'count': week_run_stats['count'] or 0,
        },
        'recent_foods': recent_foods,
        'streak': streak,
        'current_date': now,
    }

    return render(request, 'count_calories_app/home.html', context)

def get_nutrition_data(request):
    time_range = request.GET.get('range', 'today')
    selected_date_str = request.GET.get('date')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    days_param = request.GET.get('days')
    now = timezone.now()
    start_date = now
    end_date = None

    # Handle days parameter (7, 30, 90, 180, 365, or 'all')
    if days_param:
        from datetime import datetime
        if days_param == 'all':
            start_date = None
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            try:
                days = int(days_param)
                start_date = now - timedelta(days=days)
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                pass

    elif selected_date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            start_date = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
        except (ValueError, TypeError):
            selected_date_str = None

    elif start_date_str and end_date_str:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        except (ValueError, TypeError):
            start_date_str = None
            end_date_str = None

    else:
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_range == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Build query based on start_date and end_date
    if start_date is None and end_date:
        # "All" option - no start date filter
        food_items = FoodItem.objects.filter(consumed_at__lte=end_date)
    elif end_date:
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date)

    # Get grams
    protein_g = float(food_items.aggregate(Sum('protein'))['protein__sum'] or 0)
    carbs_g = float(food_items.aggregate(Sum('carbohydrates'))['carbohydrates__sum'] or 0)
    fat_g = float(food_items.aggregate(Sum('fat'))['fat__sum'] or 0)

    # Convert to calories using 4-4-9 rule
    protein_cal = protein_g * 4
    carbs_cal = carbs_g * 4
    fat_cal = fat_g * 9

    nutrition_data = {
        'labels': ['Protein', 'Carbs', 'Fat'],
        'data': [protein_cal, carbs_cal, fat_cal],  # Calorie-based for chart
        'grams': [protein_g, carbs_g, fat_g]  # Also include grams if needed
    }

    return JsonResponse(nutrition_data)

def get_gemini_nutrition(request):
    """
    API endpoint to get nutritional information from Gemini AI
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    try:
        data = json.loads(request.body)
        food_name = data.get('food_name', '').strip()

        result = GeminiService.get_nutrition_info(food_name)

        if result['success']:
            return JsonResponse(result)
        else:
            response_data = {'error': result.get('error')}
            if 'code' in result:
                response_data['code'] = result['code']
            return JsonResponse(response_data, status=result.get('status', 500))

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in get_gemini_nutrition: {e}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

    except Exception as e:
        logger.error(f"Error getting nutrition from Gemini: {e}")
        return JsonResponse({
            'error': 'Failed to get nutritional information'
        }, status=500)

def food_tracker(request):
    time_range = request.GET.get('range')
    selected_date_str = request.GET.get('date')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    days_param = request.GET.get('days')
    now = timezone.now()
    start_date = now
    end_date = None
    selected_date = None
    date_range_selected = False
    show_averages = False

    # Default to 90 days if no parameters specified
    if not time_range and not selected_date_str and not start_date_str and not days_param:
        days_param = '90'

    current_days = days_param if days_param else None

    # Handle days parameter (7, 30, 90, 180, 365, or 'all')
    if days_param:
        from datetime import datetime
        if days_param == 'all':
            # Get all food items
            start_date = None
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            try:
                days = int(days_param)
                start_date = now - timedelta(days=days)
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                current_days = None
        if days_param != 'all' or start_date is None:
            time_range = 'days_range'
            date_range_selected = True
            show_averages = True

    elif start_date_str and end_date_str:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

            time_range = 'date_range'
            date_range_selected = True
            show_averages = True
        except (ValueError, TypeError):
            start_date_str = None
            end_date_str = None

    elif selected_date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

            today_date = now.date()
            if selected_date == today_date:
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_range = 'today_specific'
            else:
                start_date = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
                end_date = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
                time_range = 'specific_date'
        except (ValueError, TypeError):
            selected_date = None

    if not selected_date and not date_range_selected:
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif time_range == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            show_averages = True
        elif time_range == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            show_averages = True

    from django.db.models.functions import TruncDate

    if end_date:
        if time_range == 'specific_date' or time_range == 'today_specific' or time_range == 'today':
            if selected_date:
                if hasattr(selected_date, 'date'):
                    date_to_filter = selected_date.date()
                else:
                    date_to_filter = selected_date
            else:
                date_to_filter = now.date()

            food_items = FoodItem.objects.annotate(
                consumed_date=TruncDate('consumed_at')
            ).filter(consumed_date=date_to_filter)
        elif start_date is None:
            # "All" option - no start date filter
            food_items = FoodItem.objects.filter(consumed_at__lte=end_date)
        else:
            food_items = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date)

    # CSV export for Food Tracker (respects current filters)
    export = request.GET.get('export')
    if export == 'csv':
        # Build filename based on selected filters
        def _date_label():
            try:
                if start_date_str and end_date_str:
                    return f"{start_date_str}_to_{end_date_str}"
                if selected_date_str:
                    return str(selected_date_str)
                return time_range
            except Exception:
                return time_range
        filename = f"food_items_{_date_label()}.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['Consumed At', 'Product Name', 'Calories', 'Fat (g)', 'Carbs (g)', 'Protein (g)'])
        for fi in food_items.order_by('consumed_at').iterator():
            writer.writerow([
                fi.consumed_at.strftime('%Y-%m-%d %H:%M:%S') if fi.consumed_at else '',
                fi.product_name,
                float(fi.calories or 0),
                float(fi.fat or 0),
                float(fi.carbohydrates or 0),
                float(fi.protein or 0),
            ])
        return response

    from django.db.models import Max
    product_names = FoodItem.objects.filter(
        hide_from_quick_list=False
    ).values('product_name').annotate(
        latest=Max('consumed_at')
    ).order_by('-latest')

    quick_add_items = []
    for item in product_names:
        food = FoodItem.objects.filter(
            product_name=item['product_name'],
            consumed_at=item['latest'],
            hide_from_quick_list=False
        ).first()
        if food:
            quick_add_items.append(food)

    totals = food_items.aggregate(
        total_calories=Sum('calories'),
        total_fat=Sum('fat'),
        total_carbohydrates=Sum('carbohydrates'),
        total_protein=Sum('protein')
    )

    for key, value in totals.items():
        if value is None:
            totals[key] = 0

    # Gram-based percentages (by weight)
    total_macros = totals['total_fat'] + totals['total_carbohydrates'] + totals['total_protein']
    if total_macros > 0:
        totals['fat_percentage'] = round((totals['total_fat'] / total_macros) * 100, 1)
        totals['carbs_percentage'] = round((totals['total_carbohydrates'] / total_macros) * 100, 1)
        totals['protein_percentage'] = round((totals['total_protein'] / total_macros) * 100, 1)
    else:
        totals['fat_percentage'] = 0
        totals['carbs_percentage'] = 0
        totals['protein_percentage'] = 0

    # Calorie-based percentages (4-4-9 rule: protein=4, carbs=4, fat=9 cal/g)
    fat_calories = float(totals['total_fat']) * 9
    carbs_calories = float(totals['total_carbohydrates']) * 4
    protein_calories = float(totals['total_protein']) * 4
    total_macro_calories = fat_calories + carbs_calories + protein_calories

    if total_macro_calories > 0:
        totals['fat_cal_percentage'] = round((fat_calories / total_macro_calories) * 100, 1)
        totals['carbs_cal_percentage'] = round((carbs_calories / total_macro_calories) * 100, 1)
        totals['protein_cal_percentage'] = round((protein_calories / total_macro_calories) * 100, 1)
    else:
        totals['fat_cal_percentage'] = 0
        totals['carbs_cal_percentage'] = 0
        totals['protein_cal_percentage'] = 0

    averages = {}
    if show_averages and food_items.exists():
        from datetime import datetime
        end_date_obj = end_date.date() if hasattr(end_date, 'date') else end_date

        # Handle "all" case where start_date is None
        if start_date is None:
            # Get the earliest food item date
            earliest_food = food_items.order_by('consumed_at').first()
            if earliest_food and earliest_food.consumed_at:
                start_date_obj = earliest_food.consumed_at.date()
            else:
                start_date_obj = end_date_obj
        else:
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

            # Gram-based percentages (by weight)
            avg_total_macros = averages['avg_fat'] + averages['avg_carbohydrates'] + averages['avg_protein']
            if avg_total_macros > 0:
                averages['fat_percentage'] = round((averages['avg_fat'] / avg_total_macros) * 100, 1)
                averages['carbs_percentage'] = round((averages['avg_carbohydrates'] / avg_total_macros) * 100, 1)
                averages['protein_percentage'] = round((averages['avg_protein'] / avg_total_macros) * 100, 1)
            else:
                averages['fat_percentage'] = 0
                averages['carbs_percentage'] = 0
                averages['protein_percentage'] = 0

            # Calorie-based percentages (4-4-9 rule: protein=4, carbs=4, fat=9 cal/g)
            avg_fat_cal = averages['avg_fat'] * 9
            avg_carbs_cal = averages['avg_carbohydrates'] * 4
            avg_protein_cal = averages['avg_protein'] * 4
            avg_total_macro_cal = avg_fat_cal + avg_carbs_cal + avg_protein_cal

            if avg_total_macro_cal > 0:
                averages['fat_cal_percentage'] = round((avg_fat_cal / avg_total_macro_cal) * 100, 1)
                averages['carbs_cal_percentage'] = round((avg_carbs_cal / avg_total_macro_cal) * 100, 1)
                averages['protein_cal_percentage'] = round((avg_protein_cal / avg_total_macro_cal) * 100, 1)
            else:
                averages['fat_cal_percentage'] = 0
                averages['carbs_cal_percentage'] = 0
                averages['protein_cal_percentage'] = 0

    if request.method == 'POST':
        logger.info(f"Processing food item form submission: {request.POST}")

        post_data = request.POST.copy()

        if selected_date:
            initial_datetime = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            post_data['consumed_at'] = initial_datetime
            logger.info(f"Setting consumed_at to selected date: {initial_datetime}")
        elif selected_date_str:
            try:
                selected_date_from_str = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
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
                if selected_date:
                    return redirect(f"/food_tracker/?date={selected_date.strftime('%Y-%m-%d')}")
                elif selected_date_str:
                    return redirect(f"/food_tracker/?date={selected_date_str}")
                else:
                    return redirect(f"/food_tracker/?range={time_range}")
            except Exception as e:
                logger.error(f"Error saving food item: {str(e)}")
                messages.error(request, f"Error saving food item: {str(e)}")
        else:
            logger.warning(f"Invalid food item form: {form.errors}")
            messages.warning(request, "Please correct the errors in the form.")
    else:
        if selected_date:
            initial_datetime = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
            form = FoodItemForm(initial={'consumed_at': initial_datetime})
        elif selected_date_str:
            try:
                selected_date_from_str = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
                initial_datetime = timezone.make_aware(datetime.combine(selected_date_from_str, datetime.min.time()))
                form = FoodItemForm(initial={'consumed_at': initial_datetime})
            except (ValueError, TypeError):
                logger.warning(f"Could not parse date string: {selected_date_str}")
                form = FoodItemForm() # Create an empty form if date parsing fails
        else:
            form = FoodItemForm() # Create an empty form

    page_number = request.GET.get('page', 1)
    sort_by = request.GET.get('sort', 'count')  # Default sort by count
    sort_order = request.GET.get('order', 'desc')  # Default descending order

    if end_date:
        if time_range == 'specific_date' or time_range == 'today_specific' or time_range == 'today':
            if selected_date:
                if hasattr(selected_date, 'date'):
                    date_to_filter = selected_date.date()
                else:
                    date_to_filter = selected_date
            else:
                date_to_filter = now.date()

            top_foods_queryset = FoodItem.objects.annotate(
                consumed_date=TruncDate('consumed_at')
            ).filter(consumed_date=date_to_filter)
        elif start_date is None:
            # "All" option - no start date filter
            top_foods_queryset = FoodItem.objects.filter(consumed_at__lte=end_date)
        else:
            top_foods_queryset = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        top_foods_queryset = FoodItem.objects.filter(consumed_at__gte=start_date)

    top_foods_data = top_foods_queryset.values('product_name').annotate(
        count=Count('id'),
        total_calories=Sum('calories'),
        avg_calories=Avg('calories'),
        total_fat=Sum('fat'),
        total_carbs=Sum('carbohydrates'),
        total_protein=Sum('protein'),
        latest_consumed=Max('consumed_at')
    )

    if sort_by == 'count':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-count', '-latest_consumed')
        else:
            top_foods_data = top_foods_data.order_by('count', '-latest_consumed')
    elif sort_by == 'name':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-product_name')
        else:
            top_foods_data = top_foods_data.order_by('product_name')
    elif sort_by == 'calories':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-total_calories', '-count')
        else:
            top_foods_data = top_foods_data.order_by('total_calories', '-count')
    elif sort_by == 'latest':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-latest_consumed')
        else:
            top_foods_data = top_foods_data.order_by('latest_consumed')
    else:
        top_foods_data = top_foods_data.order_by('-count', '-latest_consumed')

    paginator = Paginator(top_foods_data, 10)  # Show 10 items per page
    try:
        top_foods_page = paginator.page(page_number)
    except:
        top_foods_page = paginator.page(1)

    # Paginate food_items (Consumed Items list)
    food_items_ordered = food_items.order_by('-consumed_at')
    food_items_page_number = request.GET.get('items_page', 1)
    food_items_paginator = Paginator(food_items_ordered, 15)  # Show 15 items per page
    try:
        food_items_paginated = food_items_paginator.page(food_items_page_number)
    except:
        food_items_paginated = food_items_paginator.page(1)

    context = {
        'form': form,
        'food_items': food_items_paginated,
        'recent_items': quick_add_items,  # Using quick_add_items but keeping the template variable name for compatibility
        'totals': totals,
        'selected_range': time_range, # Pass the selected range to the template
        'selected_date': selected_date, # Pass the selected date to the template
        'show_averages': show_averages, # Whether to show averages section
        'averages': averages if show_averages else {}, # Pass the averages to the template
        'start_date_str': start_date_str, # Pass the start date string to the template
        'end_date_str': end_date_str, # Pass the end date string to the template
        'top_foods_page': top_foods_page,  # Paginated top foods data
        'current_sort': sort_by,  # Current sort field
        'current_order': sort_order,  # Current sort order
        'current_days': current_days,  # Current days filter for button highlighting
    }
    return render(request, 'count_calories_app/food_tracker.html', context)

def top_foods(request):
    """
    View for displaying top foods eaten with pagination, date filtering, sorting, and search.
    """
    time_range = request.GET.get('range', 'today')
    selected_date_str = request.GET.get('date')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    days_param = request.GET.get('days')
    search_query = request.GET.get('q', '').strip()
    # Multi-food search: comma-separated food names for exact matching
    foods_param = request.GET.get('foods', '').strip()
    selected_foods = [f.strip() for f in foods_param.split(',') if f.strip()] if foods_param else []
    page_number = request.GET.get('page', 1)
    sort_by = request.GET.get('sort', 'count')  # Default sort by count
    sort_order = request.GET.get('order', 'desc')  # Default descending order
    export = request.GET.get('export')  # If 'csv', return CSV

    now = timezone.now()
    start_date = now
    end_date = None
    selected_date = None
    date_range_selected = False
    current_days = days_param if days_param else None

    # Handle days parameter (7, 30, 90, 180, 365, or 'all')
    if days_param:
        if days_param == 'all':
            start_date = None
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            try:
                days = int(days_param)
                start_date = now - timedelta(days=days)
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                current_days = None
        if days_param == 'all' or current_days:
            time_range = 'days_range'
            date_range_selected = True

    elif start_date_str and end_date_str:
        try:
            from datetime import datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

            time_range = 'date_range'
            date_range_selected = True
        except (ValueError, TypeError):
            start_date_str = None
            end_date_str = None

    elif selected_date_str:
        try:
            from datetime import datetime
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()

            today_date = now.date()
            if selected_date == today_date:
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                time_range = 'today_specific'
            else:
                start_date = timezone.make_aware(datetime.combine(selected_date, datetime.min.time()))
                end_date = timezone.make_aware(datetime.combine(selected_date, datetime.max.time()))
                time_range = 'specific_date'
        except (ValueError, TypeError):
            selected_date = None

    if not selected_date and not date_range_selected:
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif time_range == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif time_range == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    from django.db.models.functions import TruncDate

    if end_date:
        if time_range == 'specific_date' or time_range == 'today_specific' or time_range == 'today':
            if selected_date:
                if hasattr(selected_date, 'date'):
                    date_to_filter = selected_date.date()
                else:
                    date_to_filter = selected_date
            else:
                date_to_filter = now.date()

            top_foods_queryset = FoodItem.objects.annotate(
                consumed_date=TruncDate('consumed_at')
            ).filter(consumed_date=date_to_filter)
        elif start_date is None:
            # "All" option - no start date filter
            top_foods_queryset = FoodItem.objects.filter(consumed_at__lte=end_date)
        else:
            top_foods_queryset = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=end_date)
    else:
        top_foods_queryset = FoodItem.objects.filter(consumed_at__gte=start_date)

    # Apply search filter if provided
    if selected_foods:
        # Multi-food exact match (case-insensitive)
        from django.db.models import Q
        food_filter = Q()
        for food_name in selected_foods:
            food_filter |= Q(product_name__iexact=food_name)
        top_foods_queryset = top_foods_queryset.filter(food_filter)
    elif search_query:
        top_foods_queryset = top_foods_queryset.filter(product_name__icontains=search_query)

    top_foods_data = top_foods_queryset.values('product_name').annotate(
        count=Count('id'),
        total_calories=Sum('calories'),
        avg_calories=Avg('calories'),
        total_fat=Sum('fat'),
        total_carbs=Sum('carbohydrates'),
        total_protein=Sum('protein'),
        latest_consumed=Max('consumed_at')
    )

    if sort_by == 'count':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-count', '-latest_consumed')
        else:
            top_foods_data = top_foods_data.order_by('count', '-latest_consumed')
    elif sort_by == 'name':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-product_name')
        else:
            top_foods_data = top_foods_data.order_by('product_name')
    elif sort_by == 'calories':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-total_calories', '-count')
        else:
            top_foods_data = top_foods_data.order_by('total_calories', '-count')
    elif sort_by == 'latest':
        if sort_order == 'desc':
            top_foods_data = top_foods_data.order_by('-latest_consumed')
        else:
            top_foods_data = top_foods_data.order_by('latest_consumed')
    else:
        top_foods_data = top_foods_data.order_by('-count', '-latest_consumed')

    # CSV export (fast, respects current filters and sorting)
    if export == 'csv':
        # Build filename based on selected filters
        def _date_label():
            try:
                if start_date_str and end_date_str:
                    return f"{start_date_str}_to_{end_date_str}"
                if selected_date_str:
                    return str(selected_date_str)
                return time_range
            except Exception:
                return time_range
        filename = f"top_foods_{_date_label()}.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['Product Name', 'Times Eaten', 'Total Calories', 'Average Calories', 'Total Fat (g)', 'Total Carbs (g)', 'Total Protein (g)', 'Latest Consumed'])
        for item in top_foods_data.iterator():
            writer.writerow([
                item['product_name'],
                item['count'],
                float(item['total_calories'] or 0),
                float(item['avg_calories'] or 0),
                float(item['total_fat'] or 0),
                float(item['total_carbs'] or 0),
                float(item['total_protein'] or 0),
                item['latest_consumed'].strftime('%Y-%m-%d %H:%M:%S') if item['latest_consumed'] else ''
            ])
        return response

    paginator = Paginator(top_foods_data, 10)  # Show 10 items per page
    try:
        top_foods_page = paginator.page(page_number)
    except:
        top_foods_page = paginator.page(1)

    # Calculate summary statistics from the base queryset (not the aggregated one)
    summary_data = top_foods_queryset.aggregate(
        total_count=Count('id'),
        total_calories=Sum('calories'),
        total_fat=Sum('fat'),
        total_carbs=Sum('carbohydrates'),
        total_protein=Sum('protein')
    )

    # Count unique foods
    unique_foods_count = top_foods_queryset.values('product_name').distinct().count()

    summary = {
        'total_count': summary_data['total_count'] or 0,
        'total_calories': summary_data['total_calories'] or 0,
        'total_fat': summary_data['total_fat'] or 0,
        'total_carbs': summary_data['total_carbs'] or 0,
        'total_protein': summary_data['total_protein'] or 0,
        'unique_foods': unique_foods_count,
    }

    # Calculate averages
    if summary['unique_foods'] and summary['unique_foods'] > 0:
        summary['avg_calories_per_food'] = summary['total_calories'] / summary['unique_foods']
        summary['avg_count_per_food'] = summary['total_count'] / summary['unique_foods']
    else:
        summary['avg_calories_per_food'] = 0
        summary['avg_count_per_food'] = 0

    context = {
        'top_foods_page': top_foods_page,
        'selected_range': time_range,
        'selected_date': selected_date,
        'start_date_str': start_date_str,
        'end_date_str': end_date_str,
        'current_sort': sort_by,
        'current_order': sort_order,
        'current_days': current_days,
        'search_query': search_query,
        'selected_foods': selected_foods,
        'foods_param': foods_param,
        'summary': summary,
    }

    return render(request, 'count_calories_app/top_foods.html', context)


def food_autocomplete(request):
    """
    API endpoint for food name autocomplete suggestions.
    Returns unique food names matching the query, ordered by frequency.
    """
    query = request.GET.get('q', '').strip()
    if len(query) < 1:
        return JsonResponse({'suggestions': []})

    # Get distinct food names matching the query, ordered by how often they appear
    food_names = FoodItem.objects.filter(
        product_name__icontains=query
    ).values('product_name').annotate(
        count=Count('id')
    ).order_by('-count')[:15]

    suggestions = [item['product_name'] for item in food_names]

    return JsonResponse({'suggestions': suggestions})


def get_calories_trend_data(request):
    days_param = request.GET.get('days')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_date_str = request.GET.get('date')
    time_range = request.GET.get('range', 'today')

    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)  # Default 30 days

    # Handle days parameter
    if days_param:
        from datetime import datetime
        if days_param == 'all':
            start_date = None
        else:
            try:
                days = int(days_param)
                start_date = end_date - timedelta(days=days)
            except ValueError:
                pass
    elif selected_date_str:
        # Single date - show last 30 days for context
        start_date = end_date - timedelta(days=30)
    elif start_date_str and end_date_str:
        try:
            from datetime import datetime
            start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59))
        except ValueError:
            pass
    elif time_range == 'week':
        start_date = end_date - timedelta(days=7)
    elif time_range == 'month':
        start_date = end_date - timedelta(days=30)

    # Build query
    if start_date is None:
        food_items = FoodItem.objects.filter(consumed_at__lte=end_date).order_by('consumed_at')
    else:
        food_items = FoodItem.objects.filter(
            consumed_at__gte=start_date,
            consumed_at__lte=end_date
        ).order_by('consumed_at')

    from django.db.models.functions import TruncDate
    daily_calories = food_items.annotate(
        day=TruncDate('consumed_at')
    ).values('day').annotate(
        total_calories=Sum('calories')
    ).order_by('day')

    calories_data = {
        'labels': [item['day'].strftime('%Y-%m-%d') for item in daily_calories],
        'data': [float(item['total_calories']) for item in daily_calories]
    }

    return JsonResponse(calories_data)

def get_macros_trend_data(request):
    days_param = request.GET.get('days')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    selected_date_str = request.GET.get('date')
    time_range = request.GET.get('range', 'today')

    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)  # Default 30 days

    # Handle days parameter
    if days_param:
        from datetime import datetime
        if days_param == 'all':
            start_date = None
        else:
            try:
                days = int(days_param)
                start_date = end_date - timedelta(days=days)
            except ValueError:
                pass
    elif selected_date_str:
        # Single date - show last 30 days for context
        start_date = end_date - timedelta(days=30)
    elif start_date_str and end_date_str:
        try:
            from datetime import datetime
            start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59))
        except ValueError:
            pass
    elif time_range == 'week':
        start_date = end_date - timedelta(days=7)
    elif time_range == 'month':
        start_date = end_date - timedelta(days=30)

    # Build query
    if start_date is None:
        food_items = FoodItem.objects.filter(consumed_at__lte=end_date).order_by('consumed_at')
    else:
        food_items = FoodItem.objects.filter(
            consumed_at__gte=start_date,
            consumed_at__lte=end_date
        ).order_by('consumed_at')

    from django.db.models.functions import TruncDate
    daily_macros = food_items.annotate(
        day=TruncDate('consumed_at')
    ).values('day').annotate(
        total_protein=Sum('protein'),
        total_carbs=Sum('carbohydrates'),
        total_fat=Sum('fat')
    ).order_by('day')

    macros_data = {
        'labels': [item['day'].strftime('%Y-%m-%d') for item in daily_macros],
        'protein': [float(item['total_protein']) for item in daily_macros],
        'carbs': [float(item['total_carbs']) for item in daily_macros],
        'fat': [float(item['total_fat']) for item in daily_macros]
    }

    return JsonResponse(macros_data)

def get_weight_data(request):
    # Get date range from request parameters
    days_param = request.GET.get('days')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    range_param = request.GET.get('range')

    end_date = timezone.now()

    if range_param == 'week':
        # This week (from Monday to now)
        start_date = end_date - timedelta(days=end_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif range_param == 'month':
        # This month (from 1st to now)
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    elif start_date_str and end_date_str:
        # Custom date range
        try:
            from datetime import datetime
            start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
            end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59))
        except ValueError:
            start_date = end_date - timedelta(days=90)
    elif days_param:
        # Preset days (90, 180, 365, or 'all')
        if days_param == 'all':
            start_date = None  # No start date filter
        else:
            try:
                days = int(days_param)
                start_date = end_date - timedelta(days=days)
            except ValueError:
                start_date = end_date - timedelta(days=90)
    else:
        # Default: last 90 days
        start_date = end_date - timedelta(days=90)

    # Build query
    if start_date:
        weights = Weight.objects.filter(recorded_at__gte=start_date, recorded_at__lte=end_date).order_by('recorded_at')
    else:
        weights = Weight.objects.filter(recorded_at__lte=end_date).order_by('recorded_at')

    weight_data = {
        'labels': [w.recorded_at.strftime('%Y-%m-%d') for w in weights],
        'data': [float(w.weight) for w in weights]
    }
    if weights.exists():
        stats = weights.aggregate(
            avg_weight=Avg('weight'),
            max_weight=Max('weight'),
            min_weight=Min('weight'),
            latest_weight=Max('recorded_at')
        )
        latest_weight = weights.filter(recorded_at=stats['latest_weight']).first()

        weight_data['stats'] = {
            'avg': float(stats['avg_weight']),
            'max': float(stats['max_weight']),
            'min': float(stats['min_weight']),
            'latest': float(latest_weight.weight) if latest_weight else 0
        }
        if len(weights) >= 2:
            oldest_weight = weights.first()
            newest_weight = weights.last()
            time_diff = (newest_weight.recorded_at - oldest_weight.recorded_at).total_seconds() / (60 * 60 * 24 * 7)
            if time_diff > 0:
                weight_change = newest_weight.weight - oldest_weight.weight
                weight_change_rate = float(weight_change) / time_diff
                weight_data['stats']['change_rate'] = float(weight_change_rate)
            else:
                weight_data['stats']['change_rate'] = 0
        else:
            weight_data['stats']['change_rate'] = 0

        height_in_meters = 1.75  # Default height
        latest_weight_value = float(latest_weight.weight) if latest_weight else 0
        if latest_weight_value > 0:
            bmi = latest_weight_value / (height_in_meters * height_in_meters)
            weight_data['stats']['bmi'] = round(bmi, 1)
        else:
            weight_data['stats']['bmi'] = 0

        if len(weights) >= 3:
            import numpy as np
            weight_values = [float(w.weight) for w in weights]
            weight_data['stats']['consistency'] = round(float(np.std(weight_values)), 2)
        else:
            weight_data['stats']['consistency'] = 0

        if weight_data['stats']['change_rate'] != 0:
            projected_weight = latest_weight_value + (weight_data['stats']['change_rate'] * 4)
            weight_data['stats']['projected_weight'] = round(projected_weight, 1)
        else:
            weight_data['stats']['projected_weight'] = latest_weight_value

        weight_goal = 70.0  # Default goal weight
        if latest_weight_value > weight_goal and weight_data['stats']['change_rate'] < 0:
            weeks_to_goal = (latest_weight_value - weight_goal) / abs(weight_data['stats']['change_rate'])
            weight_data['stats']['weeks_to_goal'] = round(weeks_to_goal, 1)

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
    weights = Weight.objects.all().order_by('recorded_at')

    correlation_data = []
    if len(weights) >= 2:
        for i in range(1, len(weights)):
            current_weight = weights[i]
            previous_weight = weights[i-1]
            weight_change = float(current_weight.weight) - float(previous_weight.weight)
            from datetime import datetime, time
            prev_date = previous_weight.recorded_at.date()
            prev_datetime = timezone.make_aware(datetime.combine(prev_date, time.min))
            curr_date = current_weight.recorded_at.date()
            curr_datetime = timezone.make_aware(datetime.combine(curr_date, time.max))
            food_items = FoodItem.objects.filter(
                consumed_at__gte=prev_datetime,
                consumed_at__lte=curr_datetime
            )
            total_calories_result = food_items.aggregate(Sum('calories'))['calories__sum'] or 0
            total_calories = float(total_calories_result)
            days_between = (current_weight.recorded_at - previous_weight.recorded_at).days
            if days_between == 0:
                days_between = 1
            daily_avg_calories = float(total_calories) / days_between
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

    correlation_data.reverse()
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1
    items_per_page = 10
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_data = correlation_data[start_idx:end_idx]
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
    export = request.GET.get('export')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    days_param = request.GET.get('days')
    range_param = request.GET.get('range')

    # Default to the last 90 days
    end_date = timezone.now()
    current_days = days_param if days_param else None
    current_range = range_param if range_param else None

    # Calculate start_date based on range or days parameter
    if range_param == 'week':
        # This week (from Monday to now)
        start_date = end_date - timedelta(days=end_date.weekday())
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_param == 'month':
        # This month (from 1st to now)
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif days_param == 'all':
        start_date = None
    elif days_param:
        try:
            days = int(days_param)
            start_date = end_date - timedelta(days=days)
        except ValueError:
            start_date = end_date - timedelta(days=90)
            current_days = '90'
    else:
        start_date = end_date - timedelta(days=90)
        current_days = '90'

    # Base queryset for the page and default CSV export
    if start_date:
        weights_query = Weight.objects.filter(recorded_at__gte=start_date).order_by('-recorded_at')
    else:
        weights_query = Weight.objects.all().order_by('-recorded_at')

    # Handle CSV export
    if export == 'csv':
        # If a date range is provided for the export, use it
        if start_date_str and end_date_str:
            try:
                from datetime import datetime, time
                from django.utils.timezone import make_aware

                start_date_csv = make_aware(datetime.combine(datetime.strptime(start_date_str, '%Y-%m-%d').date(), time.min))
                end_date_csv = make_aware(datetime.combine(datetime.strptime(end_date_str, '%Y-%m-%d').date(), time.max))
                # Use a different queryset for the ranged export
                export_query = Weight.objects.filter(recorded_at__gte=start_date_csv, recorded_at__lte=end_date_csv).order_by('recorded_at')
                filename_label = f"{start_date_str}_to_{end_date_str}"
            except (ValueError, TypeError):
                # Fallback to the default 90-day export if dates are invalid
                export_query = weights_query.order_by('recorded_at')
                filename_label = 'last_90_days'
        else:
            # Default CSV export is the last 90 days
            export_query = weights_query.order_by('recorded_at')
            filename_label = 'last_90_days'

        filename = f"weights_{filename_label}.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['Recorded At', 'Weight (kg)', 'Notes'])
        for recorded_at, weight, notes in export_query.values_list('recorded_at', 'weight', 'notes').iterator():
            writer.writerow([
                recorded_at.strftime('%Y-%m-%d %H:%M:%S') if recorded_at else '',
                float(weight) if weight is not None else '',
                notes or ''
            ])
        return response

    # Pagination for the main page view (last 90 days)
    paginator = Paginator(weights_query, 10)
    page_number = request.GET.get('page')
    weights = paginator.get_page(page_number)

    if request.method == 'POST':
        logger.info(f"Processing weight form submission: {request.POST}")
        form = WeightForm(request.POST)
        if form.is_valid():
            try:
                weight = form.save()
                logger.info(f"Weight measurement saved successfully: {weight.id} - {weight.weight} kg")
                messages.success(request, f"Weight measurement of {weight.weight} kg added successfully!")
                return redirect('weight_tracker')
            except Exception as e:
                logger.error(f"Error saving weight measurement: {str(e)}")
                messages.error(request, f"Error saving weight measurement: {str(e)}")
        else:
            logger.warning(f"Invalid weight form: {form.errors}")
            messages.warning(request, "Please correct the errors in the form.")
    else:
        form = WeightForm(initial={'recorded_at': timezone.now()})

    context = {
        'form': form,
        'weights': weights,
        'current_days': current_days,
        'current_range': current_range,
    }
    return render(request, 'count_calories_app/weight_tracker.html', context)

def workout_tracker(request):
    workouts = WorkoutSession.objects.all().order_by('-date')

    if request.method == 'POST':
        form = WorkoutSessionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('workout_tracker')
    else:
        form = WorkoutSessionForm(initial={'date': timezone.now()})

    context = {
        'form': form,
        'workouts': workouts,
    }
    return render(request, 'count_calories_app/workout_tracker.html', context)

def exercise_list(request):
    exercises = Exercise.objects.all().order_by('name')

    if request.method == 'POST':
        form = ExerciseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('exercise_list')
    else:
        form = ExerciseForm()

    context = {
        'form': form,
        'exercises': exercises,
    }
    return render(request, 'count_calories_app/exercise_list.html', context)

def get_workout_frequency_data(request):
    end_date = timezone.now()
    start_date = end_date - timedelta(days=90)

    workouts = WorkoutSession.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')

    from django.db.models.functions import TruncDate
    daily_workouts = workouts.annotate(
        day=TruncDate('date')
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')

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

    exercise = get_object_or_404(Exercise, id=exercise_id)

    workout_exercises = WorkoutExercise.objects.filter(
        exercise_id=exercise_id
    ).order_by('workout__date')

    progress_data = {
        'exercise_name': exercise.name,
        'labels': [we.workout.date.strftime('%Y-%m-%d') for we in workout_exercises],
        'weight': [float(we.weight) if we.weight else 0 for we in workout_exercises],
        'sets': [we.sets for we in workout_exercises],
        'reps': [we.reps for we in workout_exercises],
        'volume': [float(we.weight) * we.sets * we.reps if we.weight else 0 for we in workout_exercises]
    }

    return JsonResponse(progress_data)

def edit_food_item(request, food_item_id):
    """
    View for editing a food item.
    """
    food_item = get_object_or_404(FoodItem, id=food_item_id)

    if request.method == 'POST':
        form = FoodItemForm(request.POST, instance=food_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Food item updated successfully!')
            return redirect('food_tracker')
    else:
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
    food_item = get_object_or_404(FoodItem, id=food_item_id)

    if request.method == 'POST':
        food_item.delete()
        messages.success(request, 'Food item deleted successfully!')
        return redirect('food_tracker')

    context = {
        'food_item': food_item,
    }
    return render(request, 'count_calories_app/delete_food_item.html', context)

def edit_weight(request, weight_id):
    """
    View for editing a weight measurement.
    """
    weight = get_object_or_404(Weight, id=weight_id)

    if request.method == 'POST':
        form = WeightForm(request.POST, instance=weight)
        if form.is_valid():
            form.save()
            messages.success(request, 'Weight measurement updated successfully!')
            return redirect('weight_tracker')
    else:
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
    weight = get_object_or_404(Weight, id=weight_id)

    if request.method == 'POST':
        weight.delete()
        messages.success(request, 'Weight measurement deleted successfully!')
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
            logger.info(f"Raw table_data for table {table.id}: {table.table_data}")

            table_data = table.table_data

            if isinstance(table_data, str):
                try:
                    table_data = json.loads(table_data)
                    logger.info(f"Successfully parsed table_data as JSON for table {table.id}")
                except json.JSONDecodeError:
                    logger.error(f"Error parsing table_data as JSON for table {table.id}")
                    pass

            if isinstance(table_data, dict) and 'workouts' in table_data and 'exercises' in table_data:
                logger.info(f"Table {table.id} has proper structure with workouts and exercises")
            else:
                logger.warning(f"Table {table.id} data structure might be incorrect: {table_data}")
                if isinstance(table_data, str):
                    try:
                        table_data = json.loads(table_data)
                        logger.info(f"Fixed double-encoded JSON for table {table.id}")
                    except json.JSONDecodeError:
                        logger.error(f"Failed to fix double-encoded JSON for table {table.id}")

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
    workout = get_object_or_404(WorkoutSession, id=workout_id)

    workout_exercises = WorkoutExercise.objects.filter(workout=workout).order_by('id')

    if request.method == 'POST':
        form = WorkoutExerciseForm(request.POST)
        if form.is_valid():
            workout_exercise = form.save(commit=False)
            workout_exercise.workout = workout
            workout_exercise.save()
            return redirect('workout_detail', workout_id=workout_id)
    else:
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
    min_distance = request.GET.get('min_distance', 3)
    try:
        min_distance = float(min_distance)
    except ValueError:
        min_distance = 3

    running_sessions = RunningSession.objects.filter(distance__gte=min_distance).order_by('-date')

    running_sessions_with_speed = []
    highest_speed_session = None
    lowest_speed_session = None
    highest_speed = 0
    lowest_speed = float('inf')

    for session in running_sessions:
        session_data = {
            'session': session,
            'speed': 0  # Default value
        }

        duration_seconds = session.duration.total_seconds()
        if duration_seconds > 0:  # Avoid division by zero
            hours = duration_seconds / 3600  # Convert seconds to hours
            speed = float(session.distance) / hours
            session_data['speed'] = round(speed, 1)  # Round to 1 decimal place

            if speed > highest_speed:
                highest_speed = speed
                highest_speed_session = session_data
            if speed < lowest_speed:
                lowest_speed = speed
                lowest_speed_session = session_data

        running_sessions_with_speed.append(session_data)

    if request.method == 'POST':
        logger.info(f"Processing running session form submission: {request.POST}")
        form = RunningSessionForm(request.POST)
        if form.is_valid():
            try:
                running_session = form.save()
                logger.info(f"Running session saved successfully: {running_session.id} - {running_session.distance} km")
                messages.success(request, f"Running session of {running_session.distance} km added successfully!")
                return redirect('running_tracker')
            except Exception as e:
                logger.error(f"Error saving running session: {str(e)}")
                messages.error(request, f"Error saving running session: {str(e)}")
        else:
            logger.warning(f"Invalid running session form: {form.errors}")
            messages.warning(request, "Please correct the errors in the form.")
    else:
        form = RunningSessionForm(initial={'date': timezone.now()})  # Create an empty form with current date/time

    context = {
        'form': form,
        'running_sessions': running_sessions_with_speed,
        'highest_speed_session': highest_speed_session,
        'lowest_speed_session': lowest_speed_session,
        'min_distance': min_distance,
    }
    return render(request, 'count_calories_app/running_tracker.html', context)

def edit_running_session(request, running_session_id):
    """
    View for editing a running session.
    """
    running_session = get_object_or_404(RunningSession, id=running_session_id)

    if request.method == 'POST':
        form = RunningSessionForm(request.POST, instance=running_session)
        if form.is_valid():
            form.save()
            messages.success(request, 'Running session updated successfully!')
            return redirect('running_tracker')
    else:
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
    running_session = get_object_or_404(RunningSession, id=running_session_id)

    if request.method == 'POST':
        running_session.delete()
        messages.success(request, 'Running session deleted successfully!')
        return redirect('running_tracker')

    context = {
        'running_session': running_session,
    }
    return render(request, 'count_calories_app/delete_running_session.html', context)

def hide_from_quick_list(request, food_item_id):
    """
    View for hiding a food item from the quick list.
    """
    food_item = get_object_or_404(FoodItem, id=food_item_id)

    food_item.hide_from_quick_list = True
    food_item.save()

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        return JsonResponse({
            'success': True,
            'message': f"'{food_item.product_name}' has been hidden from the quick list."
        })
    else:
        messages.success(request, f"'{food_item.product_name}' has been hidden from the quick list.")

        return redirect('food_tracker')

def get_running_data(request):
    """
    API endpoint to get running data for charts
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=90)

    min_distance = request.GET.get('min_distance', 3)
    try:
        min_distance = float(min_distance)
    except ValueError:
        min_distance = 3

    running_sessions = RunningSession.objects.filter(
        date__gte=start_date,
        date__lte=end_date,
        distance__gte=min_distance
    ).order_by('date')

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

    labels = []
    distances = []
    durations = []
    paces = []  # Pace in min/km
    speeds = []  # Speed in km/h
    calories = []  # Estimated calories burned

    weekly_distances = {}
    monthly_distances = {}

    first_pace = None
    last_pace = None

    fastest_pace_value = float('inf')
    longest_run_distance = 0

    for session in running_sessions:
        labels.append(session.date.strftime('%Y-%m-%d'))
        distances.append(float(session.distance))

        duration_minutes = session.duration.total_seconds() / 60
        durations.append(duration_minutes)

        if float(session.distance) > 0:
            pace = duration_minutes / float(session.distance)
            paces.append(pace)

            if first_pace is None:
                first_pace = pace
            last_pace = pace

            if pace < fastest_pace_value:
                fastest_pace_value = pace
        else:
            paces.append(0)

        if duration_minutes > 0:
            speed = float(session.distance) / (duration_minutes / 60)
            speeds.append(speed)
        else:
            speeds.append(0)

        calorie_estimate = float(session.distance) * 60
        calories.append(calorie_estimate)

        if float(session.distance) > longest_run_distance:
            longest_run_distance = float(session.distance)

        week_key = session.date.strftime('%Y-%W')
        if week_key not in weekly_distances:
            weekly_distances[week_key] = 0
        weekly_distances[week_key] += float(session.distance)

        month_key = session.date.strftime('%Y-%m')
        if month_key not in monthly_distances:
            monthly_distances[month_key] = 0
        monthly_distances[month_key] += float(session.distance)

    if running_sessions:
        stats['total_distance'] = sum(distances)
        stats['total_sessions'] = len(running_sessions)
        stats['avg_distance'] = stats['total_distance'] / stats['total_sessions']
        total_duration_minutes = sum(durations)
        stats['avg_duration'] = total_duration_minutes / stats['total_sessions']

        total_duration_hours = total_duration_minutes / 60
        if total_duration_hours > 0:  # Avoid division by zero
            stats['avg_speed'] = stats['total_distance'] / total_duration_hours

        if stats['total_distance'] > 0:
            stats['avg_pace'] = total_duration_minutes / stats['total_distance']

        stats['total_calories'] = sum(calories)

        if weekly_distances:
            stats['weekly_distance'] = sum(weekly_distances.values()) / len(weekly_distances)

        if monthly_distances:
            stats['monthly_distance'] = sum(monthly_distances.values()) / len(monthly_distances)

        if first_pace is not None and last_pace is not None and first_pace > 0:
            improvement_percentage = ((last_pace - first_pace) / first_pace) * 100
            stats['pace_improvement'] = -improvement_percentage  # Invert so positive means improvement

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
        measurements = BodyMeasurement.objects.all().order_by('-date')

        if request.method == 'POST':
            form = BodyMeasurementForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Body measurements added successfully!')
                return redirect('body_measurements_tracker')
        else:
            form = BodyMeasurementForm(initial={'date': timezone.now()})

        weights = Weight.objects.all()

        measurements_with_arrows = []
        for i, measurement in enumerate(measurements):
            measurement_data = {
                'measurement': measurement,
                'arrows': {},
                'weight': None
            }

            measurement_date = measurement.date.date() if hasattr(measurement.date, 'date') else measurement.date
            matching_weight = weights.filter(recorded_at__date=measurement_date).first()
            if matching_weight:
                measurement_data['weight'] = matching_weight.weight

            if i < len(measurements) - 1:
                next_measurement = measurements[i + 1]

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
                        else:
                            measurement_data['arrows'][field] = 'equal'

            if i < len(measurements) - 1 and measurement_data['weight'] is not None:
                next_measurement_date = measurements[i + 1].date.date() if hasattr(measurements[i + 1].date, 'date') else measurements[i + 1].date
                next_matching_weight = weights.filter(recorded_at__date=next_measurement_date).first()
                if next_matching_weight:
                    if measurement_data['weight'] > next_matching_weight.weight:
                        measurement_data['arrows']['weight'] = 'up'
                    elif measurement_data['weight'] < next_matching_weight.weight:
                        measurement_data['arrows']['weight'] = 'down'
                    else:
                        measurement_data['arrows']['weight'] = 'equal'

            measurements_with_arrows.append(measurement_data)

        from django.core.paginator import Paginator
        paginator = Paginator(measurements_with_arrows, 10)  # Show 10 measurements per page

        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        table_view = request.GET.get('table_view', 'false')

        return render(request, 'count_calories_app/body_measurements_tracker.html', {
            'form': form,
            'measurements_with_arrows': measurements_with_arrows,  # Keep the full list for charts
            'page_obj': page_obj,  # Add paginated measurements
            'page_title': 'Body Measurements Tracker',
            'table_view': table_view,  # Pass table view state to template
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
        measurement = get_object_or_404(BodyMeasurement, id=measurement_id)

        if request.method == 'POST':
            form = BodyMeasurementForm(request.POST, instance=measurement)
            if form.is_valid():
                form.save()
                messages.success(request, 'Body measurements updated successfully!')
                return redirect('body_measurements_tracker')
        else:
            form = BodyMeasurementForm(instance=measurement)

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
        measurement = get_object_or_404(BodyMeasurement, id=measurement_id)

        if request.method == 'POST':
            measurement.delete()
            messages.success(request, 'Body measurements deleted successfully!')
            return redirect('body_measurements_tracker')

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
        measurements = BodyMeasurement.objects.all().order_by('date')

        if not measurements.exists():
            return JsonResponse({
                'dates': [],
                'weight': [],
                'neck': [],
                'chest': [],
                'belly': [],
                'left_biceps': [],
                'right_biceps': [],
                'left_triceps': [],
                'right_triceps': [],
                'left_forearm': [],
                'right_forearm': [],
                'left_thigh': [],
                'right_thigh': [],
                'left_lower_leg': [],
                'right_lower_leg': [],
                'butt': [],
            })

        weights = Weight.objects.all()

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

        weight_data = []
        for m in measurements:
            measurement_date = m.date.date() if hasattr(m.date, 'date') else m.date
            matching_weight = weights.filter(recorded_at__date=measurement_date).first()
            if matching_weight:
                weight_data.append(float(matching_weight.weight))
            else:
                weight_data.append(None)

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



def export_body_measurements_csv(request):
    """
    Export all body measurements as CSV with a matched weight column by date.
    """
    try:
        measurements = BodyMeasurement.objects.all().order_by('-date')
        weights = Weight.objects.all()

        response = HttpResponse(content_type='text/csv')
        filename = timezone.now().strftime('body_measurements_%Y-%m-%d.csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        header = [
            'Date', 'Weight (kg)', 'Neck (cm)', 'Chest (cm)', 'Belly/Waist (cm)',
            'Left Biceps (cm)', 'Right Biceps (cm)', 'Left Triceps (cm)', 'Right Triceps (cm)',
            'Left Forearm (cm)', 'Right Forearm (cm)', 'Left Thigh (cm)', 'Right Thigh (cm)',
            'Left Lower Leg (cm)', 'Right Lower Leg (cm)', 'Butt/Glutes (cm)', 'Notes'
        ]
        writer.writerow(header)

        for m in measurements:
            measurement_date = m.date.date() if hasattr(m.date, 'date') else m.date
            matching_weight = weights.filter(recorded_at__date=measurement_date).first()
            weight_value = float(matching_weight.weight) if (matching_weight and matching_weight.weight is not None) else ''

            row = [
                m.date.strftime('%Y-%m-%d'),
                weight_value,
                float(m.neck) if m.neck is not None else '',
                float(m.chest) if m.chest is not None else '',
                float(m.belly) if m.belly is not None else '',
                float(m.left_biceps) if m.left_biceps is not None else '',
                float(m.right_biceps) if m.right_biceps is not None else '',
                float(m.left_triceps) if m.left_triceps is not None else '',
                float(m.right_triceps) if m.right_triceps is not None else '',
                float(m.left_forearm) if m.left_forearm is not None else '',
                float(m.right_forearm) if m.right_forearm is not None else '',
                float(m.left_thigh) if m.left_thigh is not None else '',
                float(m.right_thigh) if m.right_thigh is not None else '',
                float(m.left_lower_leg) if m.left_lower_leg is not None else '',
                float(m.right_lower_leg) if m.right_lower_leg is not None else '',
                float(m.butt) if m.butt is not None else '',
                (m.notes or '').replace('\r', ' ').replace('\n', ' ').strip()
            ]
            writer.writerow(row)

        return response
    except Exception as e:
        logger.error(f"Error exporting body measurements CSV: {str(e)}")
        messages.error(request, f"An error occurred while exporting CSV: {str(e)}")
        return redirect('body_measurements_tracker')


def analytics(request):
    """
    Analytics page with weekly/monthly reports and correlation insights.
    """
    from datetime import datetime, timedelta
    from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
    from django.db.models import F
    import statistics

    now = timezone.now()

    # Get period from request (default: last 90 days)
    period = request.GET.get('period', '90')

    if period == 'all':
        start_date = None
    else:
        try:
            days = int(period)
            start_date = now - timedelta(days=days)
        except ValueError:
            start_date = now - timedelta(days=90)

    # Fetch data
    if start_date:
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date, consumed_at__lte=now)
        weights = Weight.objects.filter(recorded_at__gte=start_date, recorded_at__lte=now).order_by('recorded_at')
    else:
        food_items = FoodItem.objects.filter(consumed_at__lte=now)
        weights = Weight.objects.filter(recorded_at__lte=now).order_by('recorded_at')

    # === DAILY STATS ===
    daily_stats = food_items.annotate(
        day=TruncDate('consumed_at')
    ).values('day').annotate(
        total_calories=Sum('calories'),
        total_protein=Sum('protein'),
        total_carbs=Sum('carbohydrates'),
        total_fat=Sum('fat')
    ).order_by('day')

    daily_stats_list = list(daily_stats)

    # === THIS WEEK SUMMARY (for dashboard) ===
    this_week_start = now - timedelta(days=now.weekday())  # Monday of this week
    this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start

    # This week's data
    this_week_food = FoodItem.objects.filter(consumed_at__gte=this_week_start, consumed_at__lte=now)
    this_week_weights = Weight.objects.filter(recorded_at__gte=this_week_start, recorded_at__lte=now).order_by('recorded_at')
    this_week_workouts = WorkoutSession.objects.filter(date__gte=this_week_start, date__lte=now)
    this_week_runs = RunningSession.objects.filter(date__gte=this_week_start, date__lte=now)

    # Last week's data (for comparison)
    last_week_food = FoodItem.objects.filter(consumed_at__gte=last_week_start, consumed_at__lt=last_week_end)
    last_week_weights = Weight.objects.filter(recorded_at__gte=last_week_start, recorded_at__lt=last_week_end).order_by('recorded_at')
    last_week_workouts = WorkoutSession.objects.filter(date__gte=last_week_start, date__lt=last_week_end)

    # Calculate this week stats
    this_week_daily = this_week_food.annotate(day=TruncDate('consumed_at')).values('day').annotate(
        total_cal=Sum('calories'), total_prot=Sum('protein')
    )
    this_week_days_logged = this_week_daily.count()
    this_week_total_cal = sum([d['total_cal'] or 0 for d in this_week_daily])
    this_week_total_prot = sum([d['total_prot'] or 0 for d in this_week_daily])
    this_week_avg_cal = round(this_week_total_cal / this_week_days_logged, 0) if this_week_days_logged else 0
    this_week_avg_prot = round(this_week_total_prot / this_week_days_logged, 1) if this_week_days_logged else 0

    # Calculate last week stats
    last_week_daily = last_week_food.annotate(day=TruncDate('consumed_at')).values('day').annotate(
        total_cal=Sum('calories'), total_prot=Sum('protein')
    )
    last_week_days_logged = last_week_daily.count()
    last_week_total_cal = sum([d['total_cal'] or 0 for d in last_week_daily])
    last_week_total_prot = sum([d['total_prot'] or 0 for d in last_week_daily])
    last_week_avg_cal = round(last_week_total_cal / last_week_days_logged, 0) if last_week_days_logged else 0
    last_week_avg_prot = round(last_week_total_prot / last_week_days_logged, 1) if last_week_days_logged else 0

    # Weight change this week
    this_week_weight_change = None
    if this_week_weights.exists() and this_week_weights.count() >= 2:
        first_w = float(this_week_weights.first().weight)
        last_w = float(this_week_weights.last().weight)
        this_week_weight_change = round(last_w - first_w, 1)

    # Build weekly summary
    weekly_summary = {
        'this_week': {
            'days_logged': this_week_days_logged,
            'total_calories': this_week_total_cal,
            'avg_calories': this_week_avg_cal,
            'total_protein': round(this_week_total_prot, 0),
            'avg_protein': this_week_avg_prot,
            'workouts': this_week_workouts.count(),
            'runs': this_week_runs.count(),
            'run_distance': round(sum([float(r.distance) for r in this_week_runs]), 1),
            'weight_change': this_week_weight_change,
            'current_weight': float(this_week_weights.last().weight) if this_week_weights.exists() else None,
        },
        'last_week': {
            'days_logged': last_week_days_logged,
            'avg_calories': last_week_avg_cal,
            'avg_protein': last_week_avg_prot,
            'workouts': last_week_workouts.count(),
        },
        'comparison': {
            'calories_diff': round(this_week_avg_cal - last_week_avg_cal, 0) if last_week_avg_cal else None,
            'protein_diff': round(this_week_avg_prot - last_week_avg_prot, 1) if last_week_avg_prot else None,
            'workouts_diff': this_week_workouts.count() - last_week_workouts.count(),
            'logging_diff': this_week_days_logged - last_week_days_logged,
        }
    }

    # === GOAL TRACKING ===
    # Default goals (could be user-configurable in future)
    goals = {
        'daily_calories': 2500,
        'daily_protein': 150,
        'weekly_workouts': 4,
        'weekly_runs': 2,
        'target_weight': 80,  # kg
    }

    # Calculate goal progress
    goal_progress = {}

    # Calories goal (based on this week average)
    if this_week_avg_cal > 0:
        cal_progress = min(100, round((this_week_avg_cal / goals['daily_calories']) * 100, 0))
        cal_status = 'on_track' if 90 <= cal_progress <= 110 else 'under' if cal_progress < 90 else 'over'
        goal_progress['calories'] = {
            'current': this_week_avg_cal,
            'target': goals['daily_calories'],
            'progress': cal_progress,
            'status': cal_status,
        }

    # Protein goal
    if this_week_avg_prot > 0:
        prot_progress = min(100, round((this_week_avg_prot / goals['daily_protein']) * 100, 0))
        goal_progress['protein'] = {
            'current': this_week_avg_prot,
            'target': goals['daily_protein'],
            'progress': prot_progress,
            'status': 'achieved' if prot_progress >= 100 else 'in_progress',
        }

    # Workouts goal
    workout_progress = min(100, round((this_week_workouts.count() / goals['weekly_workouts']) * 100, 0))
    goal_progress['workouts'] = {
        'current': this_week_workouts.count(),
        'target': goals['weekly_workouts'],
        'progress': workout_progress,
        'status': 'achieved' if workout_progress >= 100 else 'in_progress',
    }

    # Running goal
    run_progress = min(100, round((this_week_runs.count() / goals['weekly_runs']) * 100, 0))
    goal_progress['runs'] = {
        'current': this_week_runs.count(),
        'target': goals['weekly_runs'],
        'progress': run_progress,
        'status': 'achieved' if run_progress >= 100 else 'in_progress',
    }

    # === WEEKLY REPORTS ===
    weekly_stats = food_items.annotate(
        week=TruncWeek('consumed_at')
    ).values('week').annotate(
        total_calories=Sum('calories'),
        total_protein=Sum('protein'),
        total_carbs=Sum('carbohydrates'),
        total_fat=Sum('fat'),
        days_logged=Count('consumed_at__date', distinct=True)
    ).order_by('-week')

    weekly_reports = []
    for week in weekly_stats:
        days = week['days_logged'] or 1
        weekly_reports.append({
            'week_start': week['week'],
            'total_calories': week['total_calories'] or 0,
            'avg_calories': round((week['total_calories'] or 0) / days, 0),
            'total_protein': week['total_protein'] or 0,
            'avg_protein': round((week['total_protein'] or 0) / days, 1),
            'total_carbs': week['total_carbs'] or 0,
            'avg_carbs': round((week['total_carbs'] or 0) / days, 1),
            'total_fat': week['total_fat'] or 0,
            'avg_fat': round((week['total_fat'] or 0) / days, 1),
            'days_logged': days
        })

    # === MONTHLY REPORTS ===
    monthly_stats = food_items.annotate(
        month=TruncMonth('consumed_at')
    ).values('month').annotate(
        total_calories=Sum('calories'),
        total_protein=Sum('protein'),
        total_carbs=Sum('carbohydrates'),
        total_fat=Sum('fat'),
        days_logged=Count('consumed_at__date', distinct=True)
    ).order_by('-month')

    monthly_reports = []
    for month in monthly_stats:
        days = month['days_logged'] or 1
        monthly_reports.append({
            'month': month['month'],
            'total_calories': month['total_calories'] or 0,
            'avg_calories': round((month['total_calories'] or 0) / days, 0),
            'total_protein': month['total_protein'] or 0,
            'avg_protein': round((month['total_protein'] or 0) / days, 1),
            'total_carbs': month['total_carbs'] or 0,
            'avg_carbs': round((month['total_carbs'] or 0) / days, 1),
            'total_fat': month['total_fat'] or 0,
            'avg_fat': round((month['total_fat'] or 0) / days, 1),
            'days_logged': days
        })

    # === BEST/WORST DAYS ===
    best_worst_days = {}
    if daily_stats_list:
        # Best day (lowest calories with reasonable amount - at least 500)
        valid_days = [d for d in daily_stats_list if d['total_calories'] and d['total_calories'] >= 500]
        if valid_days:
            best_worst_days['lowest_calorie_day'] = min(valid_days, key=lambda x: x['total_calories'])
            best_worst_days['highest_calorie_day'] = max(valid_days, key=lambda x: x['total_calories'])
            best_worst_days['highest_protein_day'] = max(valid_days, key=lambda x: x['total_protein'] or 0)
            best_worst_days['lowest_protein_day'] = min(valid_days, key=lambda x: x['total_protein'] or 0)

    # === WEIGHT ANALYSIS ===
    weight_analysis = {}
    weights_list = list(weights)
    if len(weights_list) >= 2:
        first_weight = float(weights_list[0].weight)
        last_weight = float(weights_list[-1].weight)
        weight_analysis['start_weight'] = first_weight
        weight_analysis['end_weight'] = last_weight
        weight_analysis['total_change'] = round(last_weight - first_weight, 1)

        # Calculate weekly weight changes
        weight_values = [float(w.weight) for w in weights_list]
        weight_analysis['min_weight'] = min(weight_values)
        weight_analysis['max_weight'] = max(weight_values)
        weight_analysis['avg_weight'] = round(statistics.mean(weight_values), 1)

        if len(weight_values) >= 3:
            weight_analysis['std_dev'] = round(statistics.stdev(weight_values), 2)

    # === CORRELATION INSIGHTS ===
    insights = []

    if len(weights_list) >= 3 and len(daily_stats_list) >= 7:
        # Create a dict of daily food stats by date
        daily_food_by_date = {d['day']: d for d in daily_stats_list}

        # Analyze weight changes vs nutrition
        weight_changes_with_nutrition = []

        for i in range(1, len(weights_list)):
            current_weight = weights_list[i]
            prev_weight = weights_list[i-1]

            weight_change = float(current_weight.weight) - float(prev_weight.weight)

            # Get food data between these weight measurements
            start_dt = prev_weight.recorded_at
            end_dt = current_weight.recorded_at

            period_food = [d for d in daily_stats_list
                          if d['day'] and start_dt.date() <= d['day'] <= end_dt.date()]

            if period_food:
                avg_calories = float(statistics.mean([float(d['total_calories']) for d in period_food if d['total_calories']]))
                avg_protein = float(statistics.mean([float(d['total_protein'] or 0) for d in period_food]))
                avg_carbs = float(statistics.mean([float(d['total_carbs'] or 0) for d in period_food]))
                avg_fat = float(statistics.mean([float(d['total_fat'] or 0) for d in period_food]))

                weight_changes_with_nutrition.append({
                    'weight_change': weight_change,
                    'avg_calories': avg_calories,
                    'avg_protein': avg_protein,
                    'avg_carbs': avg_carbs,
                    'avg_fat': avg_fat
                })

        if len(weight_changes_with_nutrition) >= 3:
            # Analyze patterns
            weight_loss_periods = [p for p in weight_changes_with_nutrition if p['weight_change'] < -0.1]
            weight_gain_periods = [p for p in weight_changes_with_nutrition if p['weight_change'] > 0.1]

            # Calorie insights
            if weight_loss_periods and weight_gain_periods:
                avg_cal_loss = statistics.mean([p['avg_calories'] for p in weight_loss_periods])
                avg_cal_gain = statistics.mean([p['avg_calories'] for p in weight_gain_periods])

                if avg_cal_loss < avg_cal_gain:
                    insights.append({
                        'type': 'calories',
                        'icon': '🔥',
                        'title': 'Calorie Impact',
                        'description': f'You tend to lose weight when averaging {avg_cal_loss:.0f} kcal/day and gain when averaging {avg_cal_gain:.0f} kcal/day.',
                        'recommendation': f'Try to stay around {avg_cal_loss:.0f} kcal/day for weight loss.'
                    })

            # Protein insights
            if weight_loss_periods:
                avg_protein_loss = statistics.mean([p['avg_protein'] for p in weight_loss_periods])
                all_avg_protein = statistics.mean([p['avg_protein'] for p in weight_changes_with_nutrition])

                if avg_protein_loss > all_avg_protein * 1.1:  # 10% higher
                    insights.append({
                        'type': 'protein',
                        'icon': '💪',
                        'title': 'Protein Correlation',
                        'description': f'Weight loss periods correlate with higher protein intake (~{avg_protein_loss:.0f}g/day vs average {all_avg_protein:.0f}g/day).',
                        'recommendation': f'Aim for at least {avg_protein_loss:.0f}g protein daily.'
                    })

            # Carb insights
            if weight_loss_periods and weight_gain_periods:
                avg_carbs_loss = statistics.mean([p['avg_carbs'] for p in weight_loss_periods])
                avg_carbs_gain = statistics.mean([p['avg_carbs'] for p in weight_gain_periods])

                if avg_carbs_loss < avg_carbs_gain * 0.9:  # 10% lower
                    insights.append({
                        'type': 'carbs',
                        'icon': '🍞',
                        'title': 'Carbohydrate Pattern',
                        'description': f'Lower carb intake (~{avg_carbs_loss:.0f}g/day) correlates with weight loss vs (~{avg_carbs_gain:.0f}g/day) with weight gain.',
                        'recommendation': f'Consider keeping carbs around {avg_carbs_loss:.0f}g/day.'
                    })

            # Fat insights
            if weight_loss_periods and weight_gain_periods:
                avg_fat_loss = statistics.mean([p['avg_fat'] for p in weight_loss_periods])
                avg_fat_gain = statistics.mean([p['avg_fat'] for p in weight_gain_periods])

                if abs(avg_fat_loss - avg_fat_gain) > 10:
                    insights.append({
                        'type': 'fat',
                        'icon': '🥑',
                        'title': 'Fat Intake Pattern',
                        'description': f'During weight loss: ~{avg_fat_loss:.0f}g fat/day. During weight gain: ~{avg_fat_gain:.0f}g fat/day.',
                        'recommendation': f'Optimal fat intake appears to be around {avg_fat_loss:.0f}g/day.'
                    })

    # Overall stats
    overall_stats = {}
    calories_list = []
    if daily_stats_list:
        calories_list = [float(d['total_calories']) for d in daily_stats_list if d['total_calories']]
        if calories_list:
            overall_stats['avg_daily_calories'] = round(statistics.mean(calories_list), 0)
            overall_stats['total_days_logged'] = len(daily_stats_list)
            overall_stats['total_calories'] = round(sum(calories_list), 0)

            protein_list = [float(d['total_protein']) for d in daily_stats_list if d['total_protein']]
            carbs_list = [float(d['total_carbs']) for d in daily_stats_list if d['total_carbs']]
            fat_list = [float(d['total_fat']) for d in daily_stats_list if d['total_fat']]

            if protein_list:
                overall_stats['avg_daily_protein'] = round(statistics.mean(protein_list), 1)
                overall_stats['total_protein'] = round(sum(protein_list), 0)
            if carbs_list:
                overall_stats['avg_daily_carbs'] = round(statistics.mean(carbs_list), 1)
                overall_stats['total_carbs'] = round(sum(carbs_list), 0)
            if fat_list:
                overall_stats['avg_daily_fat'] = round(statistics.mean(fat_list), 1)
                overall_stats['total_fat'] = round(sum(fat_list), 0)

            # Calorie variability
            if len(calories_list) >= 3:
                overall_stats['calorie_std_dev'] = round(statistics.stdev(calories_list), 0)
                overall_stats['calorie_min'] = round(min(calories_list), 0)
                overall_stats['calorie_max'] = round(max(calories_list), 0)

    # === DAY OF WEEK ANALYSIS ===
    day_of_week_stats = {}
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    if daily_stats_list:
        for day_num in range(7):
            day_data = [d for d in daily_stats_list if d['day'] and d['day'].weekday() == day_num]
            if day_data:
                day_calories = [float(d['total_calories']) for d in day_data if d['total_calories']]
                if day_calories:
                    day_of_week_stats[day_names[day_num]] = {
                        'avg_calories': round(statistics.mean(day_calories), 0),
                        'count': len(day_calories),
                        'total_calories': round(sum(day_calories), 0)
                    }

    # Find best and worst days of week
    weekday_insights = {}
    if day_of_week_stats:
        sorted_days = sorted(day_of_week_stats.items(), key=lambda x: x[1]['avg_calories'])
        if sorted_days:
            weekday_insights['lowest_day'] = {'name': sorted_days[0][0], 'calories': sorted_days[0][1]['avg_calories']}
            weekday_insights['highest_day'] = {'name': sorted_days[-1][0], 'calories': sorted_days[-1][1]['avg_calories']}

            # Weekend vs Weekday comparison
            weekday_cals = [v['avg_calories'] for k, v in day_of_week_stats.items() if k in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']]
            weekend_cals = [v['avg_calories'] for k, v in day_of_week_stats.items() if k in ['Saturday', 'Sunday']]

            if weekday_cals and weekend_cals:
                weekday_insights['weekday_avg'] = round(statistics.mean(weekday_cals), 0)
                weekday_insights['weekend_avg'] = round(statistics.mean(weekend_cals), 0)
                weekday_insights['weekend_difference'] = round(weekday_insights['weekend_avg'] - weekday_insights['weekday_avg'], 0)

    # === LOGGING STREAKS ===
    streaks = {}
    if daily_stats_list:
        # Sort by date
        sorted_days = sorted([d['day'] for d in daily_stats_list if d['day']])

        if sorted_days:
            # Current streak
            current_streak = 0
            check_date = now.date()
            for i in range(len(sorted_days)):
                if check_date in sorted_days or (check_date - timedelta(days=1)) in sorted_days:
                    # Allow for today or yesterday
                    pass

            # Calculate current streak (consecutive days ending at most recent log)
            current_streak = 1
            for i in range(len(sorted_days) - 1, 0, -1):
                if (sorted_days[i] - sorted_days[i-1]).days == 1:
                    current_streak += 1
                else:
                    break

            # Calculate longest streak
            longest_streak = 1
            temp_streak = 1
            for i in range(1, len(sorted_days)):
                if (sorted_days[i] - sorted_days[i-1]).days == 1:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 1

            streaks['current_streak'] = current_streak
            streaks['longest_streak'] = longest_streak
            streaks['total_days'] = len(sorted_days)

            # Days since first log
            if sorted_days:
                days_since_start = (now.date() - sorted_days[0]).days + 1
                streaks['consistency_rate'] = round((len(sorted_days) / days_since_start) * 100, 1) if days_since_start > 0 else 0

    # === MACRO RATIO ANALYSIS ===
    macro_analysis = {}
    if overall_stats.get('avg_daily_protein') and overall_stats.get('avg_daily_carbs') and overall_stats.get('avg_daily_fat'):
        protein_g = overall_stats['avg_daily_protein']
        carbs_g = overall_stats['avg_daily_carbs']
        fat_g = overall_stats['avg_daily_fat']

        # Calculate calories from each macro
        protein_cal = protein_g * 4
        carbs_cal = carbs_g * 4
        fat_cal = fat_g * 9

        total_macro_cal = protein_cal + carbs_cal + fat_cal

        if total_macro_cal > 0:
            macro_analysis['protein_percent'] = round((protein_cal / total_macro_cal) * 100, 1)
            macro_analysis['carbs_percent'] = round((carbs_cal / total_macro_cal) * 100, 1)
            macro_analysis['fat_percent'] = round((fat_cal / total_macro_cal) * 100, 1)

            # Protein per kg body weight (if we have weight data)
            if weights_list:
                latest_weight = float(weights_list[-1].weight)
                macro_analysis['protein_per_kg'] = round(protein_g / latest_weight, 2)

            # Macro balance assessment
            # Recommended ranges: Protein 10-35%, Carbs 45-65%, Fat 20-35%
            macro_analysis['balance_notes'] = []
            if macro_analysis['protein_percent'] < 15:
                macro_analysis['balance_notes'].append('Protein intake is low (below 15%)')
            elif macro_analysis['protein_percent'] > 35:
                macro_analysis['balance_notes'].append('Protein intake is high (above 35%)')

            if macro_analysis['carbs_percent'] < 40:
                macro_analysis['balance_notes'].append('Carb intake is low (below 40%)')
            elif macro_analysis['carbs_percent'] > 65:
                macro_analysis['balance_notes'].append('Carb intake is high (above 65%)')

            if macro_analysis['fat_percent'] < 20:
                macro_analysis['balance_notes'].append('Fat intake is low (below 20%)')
            elif macro_analysis['fat_percent'] > 40:
                macro_analysis['balance_notes'].append('Fat intake is high (above 40%)')

    # === WEIGHT PACE ANALYSIS ===
    weight_pace = {}
    if len(weights_list) >= 2:
        first_weight = float(weights_list[0].weight)
        last_weight = float(weights_list[-1].weight)
        first_date = weights_list[0].recorded_at
        last_date = weights_list[-1].recorded_at

        days_diff = (last_date - first_date).days
        if days_diff > 0:
            total_change = last_weight - first_weight
            weight_pace['total_change'] = round(total_change, 1)
            weight_pace['days'] = days_diff
            weight_pace['weekly_rate'] = round((total_change / days_diff) * 7, 2)
            weight_pace['monthly_rate'] = round((total_change / days_diff) * 30, 1)

            # Healthy weight loss/gain is typically 0.5-1 kg per week
            if total_change < 0:
                weight_pace['status'] = 'losing'
                if abs(weight_pace['weekly_rate']) > 1:
                    weight_pace['pace_assessment'] = 'Rapid weight loss (>1 kg/week) - may be too fast'
                elif abs(weight_pace['weekly_rate']) >= 0.5:
                    weight_pace['pace_assessment'] = 'Healthy weight loss pace (0.5-1 kg/week)'
                else:
                    weight_pace['pace_assessment'] = 'Slow but steady weight loss (<0.5 kg/week)'
            elif total_change > 0:
                weight_pace['status'] = 'gaining'
                if weight_pace['weekly_rate'] > 0.5:
                    weight_pace['pace_assessment'] = 'Rapid weight gain (>0.5 kg/week)'
                else:
                    weight_pace['pace_assessment'] = 'Gradual weight gain (<0.5 kg/week)'
            else:
                weight_pace['status'] = 'maintaining'
                weight_pace['pace_assessment'] = 'Weight is stable'

            # Estimated calorie deficit/surplus
            # 1 kg of body weight ≈ 7700 calories
            if days_diff >= 7:
                daily_cal_change = (total_change * 7700) / days_diff
                weight_pace['estimated_daily_deficit'] = round(daily_cal_change, 0)

    # === GOAL PROJECTIONS ===
    projections = {}
    if weight_pace.get('weekly_rate') and weights_list:
        current_weight = float(weights_list[-1].weight)
        weekly_rate = weight_pace['weekly_rate']

        # Project weight in 4 weeks, 8 weeks, 12 weeks
        if weekly_rate != 0:
            projections['4_weeks'] = round(current_weight + (weekly_rate * 4), 1)
            projections['8_weeks'] = round(current_weight + (weekly_rate * 8), 1)
            projections['12_weeks'] = round(current_weight + (weekly_rate * 12), 1)

            # Time to reach common goals (if losing weight)
            if weekly_rate < 0:
                goal_weights = [70, 75, 80, 85, 90, 95]
                projections['goals'] = []
                for goal in goal_weights:
                    if goal < current_weight:
                        weeks_to_goal = (current_weight - goal) / abs(weekly_rate)
                        if weeks_to_goal <= 52:  # Only show if achievable within a year
                            target_date = now + timedelta(weeks=weeks_to_goal)
                            projections['goals'].append({
                                'weight': goal,
                                'weeks': round(weeks_to_goal, 0),
                                'date': target_date.strftime('%B %d, %Y')
                            })

    # === CALORIE CONSISTENCY SCORE ===
    consistency_score = {}
    if calories_list and len(calories_list) >= 7:
        avg_cal = statistics.mean(calories_list)
        std_dev = statistics.stdev(calories_list) if len(calories_list) > 1 else 0

        # Coefficient of variation (lower is more consistent)
        cv = (std_dev / avg_cal) * 100 if avg_cal > 0 else 0

        if cv < 10:
            consistency_score['rating'] = 'Excellent'
            consistency_score['description'] = 'Very consistent calorie intake'
            consistency_score['score'] = 95
        elif cv < 15:
            consistency_score['rating'] = 'Good'
            consistency_score['description'] = 'Fairly consistent calorie intake'
            consistency_score['score'] = 80
        elif cv < 25:
            consistency_score['rating'] = 'Moderate'
            consistency_score['description'] = 'Some variation in daily calories'
            consistency_score['score'] = 60
        else:
            consistency_score['rating'] = 'Variable'
            consistency_score['description'] = 'High variation in daily calories'
            consistency_score['score'] = 40

        consistency_score['cv'] = round(cv, 1)

    # === ADDITIONAL INSIGHTS ===
    # Add more insights based on data patterns

    # Weekend overeating insight
    if weekday_insights.get('weekend_difference') and weekday_insights['weekend_difference'] > 200:
        insights.append({
            'type': 'weekend',
            'icon': '📅',
            'title': 'Weekend Pattern',
            'description': f'You eat ~{weekday_insights["weekend_difference"]:.0f} more calories on weekends ({weekday_insights["weekend_avg"]:.0f}) vs weekdays ({weekday_insights["weekday_avg"]:.0f}).',
            'recommendation': 'Plan weekend meals in advance to stay on track.'
        })

    # Consistency insight
    if consistency_score.get('rating') == 'Variable':
        insights.append({
            'type': 'consistency',
            'icon': '📊',
            'title': 'Calorie Variability',
            'description': f'Your daily calories vary significantly (CV: {consistency_score["cv"]:.1f}%). Range: {overall_stats.get("calorie_min", 0):.0f} - {overall_stats.get("calorie_max", 0):.0f} kcal.',
            'recommendation': 'Try meal prepping to maintain more consistent intake.'
        })

    # Protein adequacy insight
    if macro_analysis.get('protein_per_kg'):
        if macro_analysis['protein_per_kg'] < 1.2:
            insights.append({
                'type': 'protein',
                'icon': '🥩',
                'title': 'Protein Intake',
                'description': f'You\'re getting {macro_analysis["protein_per_kg"]:.2f}g protein per kg body weight. For muscle maintenance, aim for 1.2-1.6g/kg.',
                'recommendation': f'Consider increasing protein to {round(float(weights_list[-1].weight) * 1.4, 0):.0f}g daily.'
            })
        elif macro_analysis['protein_per_kg'] >= 1.6:
            insights.append({
                'type': 'protein',
                'icon': '💪',
                'title': 'Strong Protein Intake',
                'description': f'Excellent! You\'re getting {macro_analysis["protein_per_kg"]:.2f}g protein per kg body weight.',
                'recommendation': 'Keep up the good protein intake for muscle health.'
            })

    # Streak insight
    if streaks.get('current_streak', 0) >= 7:
        insights.append({
            'type': 'streak',
            'icon': '🔥',
            'title': 'Logging Streak',
            'description': f'Great job! You\'ve logged {streaks["current_streak"]} days in a row. Your longest streak is {streaks["longest_streak"]} days.',
            'recommendation': 'Keep the momentum going!'
        })

    # Weight milestone insight
    if weight_pace.get('total_change') and weight_pace['total_change'] < -5:
        insights.append({
            'type': 'milestone',
            'icon': '🏆',
            'title': 'Weight Loss Milestone',
            'description': f'Amazing! You\'ve lost {abs(weight_pace["total_change"]):.1f} kg in {weight_pace["days"]} days.',
            'recommendation': 'Celebrate your progress and keep going!'
        })

    # === MEAL TIMING ANALYSIS ===
    meal_timing = {}
    if food_items.exists():
        # Group by hour of day
        hour_data = {}
        for item in food_items:
            hour = item.consumed_at.hour
            if hour not in hour_data:
                hour_data[hour] = {'calories': 0, 'count': 0}
            hour_data[hour]['calories'] += float(item.calories or 0)
            hour_data[hour]['count'] += 1

        if hour_data:
            # Define meal periods
            morning = sum(hour_data.get(h, {}).get('calories', 0) for h in range(5, 11))  # 5-10
            midday = sum(hour_data.get(h, {}).get('calories', 0) for h in range(11, 15))  # 11-14
            afternoon = sum(hour_data.get(h, {}).get('calories', 0) for h in range(15, 18))  # 15-17
            evening = sum(hour_data.get(h, {}).get('calories', 0) for h in range(18, 22))  # 18-21
            night = sum(hour_data.get(h, {}).get('calories', 0) for h in list(range(22, 24)) + list(range(0, 5)))

            total_cal = morning + midday + afternoon + evening + night
            if total_cal > 0:
                meal_timing['morning'] = {'calories': round(morning, 0), 'percent': round((morning/total_cal)*100, 1)}
                meal_timing['midday'] = {'calories': round(midday, 0), 'percent': round((midday/total_cal)*100, 1)}
                meal_timing['afternoon'] = {'calories': round(afternoon, 0), 'percent': round((afternoon/total_cal)*100, 1)}
                meal_timing['evening'] = {'calories': round(evening, 0), 'percent': round((evening/total_cal)*100, 1)}
                meal_timing['night'] = {'calories': round(night, 0), 'percent': round((night/total_cal)*100, 1)}

                # Find peak eating time
                periods = [('Morning (5-10)', morning), ('Midday (11-14)', midday),
                          ('Afternoon (15-17)', afternoon), ('Evening (18-21)', evening), ('Night (22-4)', night)]
                peak_period = max(periods, key=lambda x: x[1])
                meal_timing['peak_period'] = peak_period[0]

    # === TOP FOODS ANALYSIS ===
    top_foods = {}
    if food_items.exists():
        from django.db.models import Count as DjangoCount

        # Most frequent foods
        frequent_foods = food_items.values('product_name').annotate(
            count=DjangoCount('id'),
            total_calories=Sum('calories'),
            total_protein=Sum('protein')
        ).order_by('-count')[:10]

        top_foods['most_frequent'] = list(frequent_foods)

        # Highest calorie foods (single items)
        high_cal_foods = food_items.order_by('-calories')[:5]
        top_foods['highest_calorie'] = [
            {'name': f.product_name, 'calories': float(f.calories), 'date': f.consumed_at}
            for f in high_cal_foods
        ]

        # Highest protein foods
        high_protein_foods = food_items.filter(protein__isnull=False).order_by('-protein')[:5]
        top_foods['highest_protein'] = [
            {'name': f.product_name, 'protein': float(f.protein), 'date': f.consumed_at}
            for f in high_protein_foods
        ]

    # === CALORIE BUDGET ANALYSIS ===
    calorie_budget = {}
    target_calories = 2500  # Default target, could be user-configurable

    if calories_list:
        days_under = sum(1 for c in calories_list if c <= target_calories)
        days_over = len(calories_list) - days_under

        calorie_budget['target'] = target_calories
        calorie_budget['days_under'] = days_under
        calorie_budget['days_over'] = days_over
        calorie_budget['under_percent'] = round((days_under / len(calories_list)) * 100, 1)
        calorie_budget['avg_over_amount'] = round(
            statistics.mean([c - target_calories for c in calories_list if c > target_calories]), 0
        ) if days_over > 0 else 0
        calorie_budget['avg_under_amount'] = round(
            statistics.mean([target_calories - c for c in calories_list if c <= target_calories]), 0
        ) if days_under > 0 else 0

    # === WEIGHT VOLATILITY ANALYSIS ===
    weight_volatility = {}
    if len(weights_list) >= 5:
        weight_values = [float(w.weight) for w in weights_list]

        # Calculate daily fluctuations
        fluctuations = [abs(weight_values[i] - weight_values[i-1]) for i in range(1, len(weight_values))]

        weight_volatility['avg_fluctuation'] = round(statistics.mean(fluctuations), 2)
        weight_volatility['max_fluctuation'] = round(max(fluctuations), 2)

        # Count significant fluctuations (>0.5 kg)
        significant_fluct = sum(1 for f in fluctuations if f > 0.5)
        weight_volatility['significant_fluctuations'] = significant_fluct
        weight_volatility['stability_score'] = round(100 - (significant_fluct / len(fluctuations) * 100), 0) if fluctuations else 100

        # Trend analysis - compare first half to second half
        mid = len(weight_values) // 2
        first_half_avg = statistics.mean(weight_values[:mid])
        second_half_avg = statistics.mean(weight_values[mid:])
        weight_volatility['trend_direction'] = 'decreasing' if second_half_avg < first_half_avg else 'increasing' if second_half_avg > first_half_avg else 'stable'
        weight_volatility['trend_change'] = round(second_half_avg - first_half_avg, 2)

    # === NUTRITION SCORE ===
    nutrition_score = {}
    if macro_analysis and overall_stats.get('avg_daily_calories'):
        score = 0
        max_score = 100
        breakdown = []

        # Protein score (max 25 points)
        protein_per_kg = macro_analysis.get('protein_per_kg', 0)
        if protein_per_kg >= 1.6:
            protein_score = 25
            breakdown.append({'name': 'Protein', 'score': 25, 'status': 'Excellent'})
        elif protein_per_kg >= 1.2:
            protein_score = 20
            breakdown.append({'name': 'Protein', 'score': 20, 'status': 'Good'})
        elif protein_per_kg >= 0.8:
            protein_score = 15
            breakdown.append({'name': 'Protein', 'score': 15, 'status': 'Adequate'})
        else:
            protein_score = 5
            breakdown.append({'name': 'Protein', 'score': 5, 'status': 'Low'})
        score += protein_score

        # Macro balance score (max 25 points)
        protein_pct = macro_analysis.get('protein_percent', 0)
        carbs_pct = macro_analysis.get('carbs_percent', 0)
        fat_pct = macro_analysis.get('fat_percent', 0)

        balance_score = 25
        if protein_pct < 15 or protein_pct > 35:
            balance_score -= 8
        if carbs_pct < 40 or carbs_pct > 65:
            balance_score -= 8
        if fat_pct < 20 or fat_pct > 40:
            balance_score -= 8
        balance_score = max(0, balance_score)
        breakdown.append({'name': 'Macro Balance', 'score': balance_score, 'status': 'Good' if balance_score >= 20 else 'Needs Work'})
        score += balance_score

        # Consistency score (max 25 points)
        if consistency_score.get('score'):
            cons_points = round(consistency_score['score'] * 0.25)
            breakdown.append({'name': 'Consistency', 'score': cons_points, 'status': consistency_score.get('rating', 'N/A')})
            score += cons_points

        # Logging dedication (max 25 points)
        if streaks.get('consistency_rate'):
            log_score = min(25, round(streaks['consistency_rate'] * 0.25))
            breakdown.append({'name': 'Logging', 'score': log_score, 'status': 'Dedicated' if log_score >= 20 else 'Regular' if log_score >= 10 else 'Sporadic'})
            score += log_score

        nutrition_score['total'] = min(100, score)
        nutrition_score['breakdown'] = breakdown
        nutrition_score['grade'] = 'A' if score >= 85 else 'B' if score >= 70 else 'C' if score >= 55 else 'D' if score >= 40 else 'F'

    # === PERIOD COMPARISON ===
    period_comparison = {}
    if start_date and daily_stats_list:
        # Calculate previous period of same length
        period_days = int(period) if period != 'all' else 90
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date

        prev_food_items = FoodItem.objects.filter(consumed_at__gte=prev_start, consumed_at__lt=prev_end)
        prev_weights = Weight.objects.filter(recorded_at__gte=prev_start, recorded_at__lt=prev_end).order_by('recorded_at')

        if prev_food_items.exists():
            # Previous period stats
            prev_daily = prev_food_items.annotate(day=TruncDate('consumed_at')).values('day').annotate(
                total_calories=Sum('calories'),
                total_protein=Sum('protein')
            )
            prev_daily_list = list(prev_daily)

            if prev_daily_list:
                prev_cal_list = [float(d['total_calories']) for d in prev_daily_list if d['total_calories']]
                if prev_cal_list and calories_list:
                    prev_avg_cal = statistics.mean(prev_cal_list)
                    curr_avg_cal = statistics.mean(calories_list)

                    period_comparison['prev_avg_calories'] = round(prev_avg_cal, 0)
                    period_comparison['curr_avg_calories'] = round(curr_avg_cal, 0)
                    period_comparison['calorie_change'] = round(curr_avg_cal - prev_avg_cal, 0)
                    period_comparison['calorie_change_percent'] = round(((curr_avg_cal - prev_avg_cal) / prev_avg_cal) * 100, 1) if prev_avg_cal > 0 else 0

                    prev_protein_list = [float(d['total_protein']) for d in prev_daily_list if d['total_protein']]
                    if prev_protein_list:
                        curr_protein_list = [float(d['total_protein']) for d in daily_stats_list if d['total_protein']]
                        if curr_protein_list:
                            prev_avg_protein = statistics.mean(prev_protein_list)
                            curr_avg_protein = statistics.mean(curr_protein_list)
                            period_comparison['prev_avg_protein'] = round(prev_avg_protein, 1)
                            period_comparison['curr_avg_protein'] = round(curr_avg_protein, 1)
                            period_comparison['protein_change'] = round(curr_avg_protein - prev_avg_protein, 1)

        # Weight comparison
        if prev_weights.exists() and weights_list:
            prev_weight_list = list(prev_weights)
            if prev_weight_list:
                prev_avg_weight = statistics.mean([float(w.weight) for w in prev_weight_list])
                curr_avg_weight = statistics.mean([float(w.weight) for w in weights_list])
                period_comparison['prev_avg_weight'] = round(prev_avg_weight, 1)
                period_comparison['curr_avg_weight'] = round(curr_avg_weight, 1)
                period_comparison['weight_change'] = round(curr_avg_weight - prev_avg_weight, 1)

    # === ACHIEVEMENTS ===
    achievements = []

    # Streak achievements
    if streaks.get('current_streak', 0) >= 30:
        achievements.append({'icon': '🔥', 'title': 'Monthly Warrior', 'desc': '30+ day logging streak'})
    elif streaks.get('current_streak', 0) >= 14:
        achievements.append({'icon': '🔥', 'title': 'Two Week Champion', 'desc': '14+ day logging streak'})
    elif streaks.get('current_streak', 0) >= 7:
        achievements.append({'icon': '🔥', 'title': 'Week Warrior', 'desc': '7+ day logging streak'})

    # Weight achievements
    if weight_pace.get('total_change', 0) <= -10:
        achievements.append({'icon': '🏆', 'title': 'Major Milestone', 'desc': 'Lost 10+ kg'})
    elif weight_pace.get('total_change', 0) <= -5:
        achievements.append({'icon': '🥇', 'title': 'Great Progress', 'desc': 'Lost 5+ kg'})
    elif weight_pace.get('total_change', 0) <= -2:
        achievements.append({'icon': '🥈', 'title': 'Good Start', 'desc': 'Lost 2+ kg'})

    # Consistency achievements
    if consistency_score.get('score', 0) >= 90:
        achievements.append({'icon': '🎯', 'title': 'Precision Eater', 'desc': 'Excellent calorie consistency'})

    # Protein achievements
    if macro_analysis.get('protein_per_kg', 0) >= 2.0:
        achievements.append({'icon': '💪', 'title': 'Protein Champion', 'desc': '2+ g protein per kg body weight'})
    elif macro_analysis.get('protein_per_kg', 0) >= 1.6:
        achievements.append({'icon': '🥩', 'title': 'Protein Pro', 'desc': '1.6+ g protein per kg body weight'})

    # Logging achievements
    if streaks.get('total_days', 0) >= 100:
        achievements.append({'icon': '📊', 'title': 'Century Logger', 'desc': '100+ days logged'})
    elif streaks.get('total_days', 0) >= 50:
        achievements.append({'icon': '📈', 'title': 'Dedicated Tracker', 'desc': '50+ days logged'})

    # Consistency rate achievements
    if streaks.get('consistency_rate', 0) >= 90:
        achievements.append({'icon': '⭐', 'title': 'Super Consistent', 'desc': '90%+ logging consistency'})

    # Balance achievement
    if nutrition_score.get('total', 0) >= 80:
        achievements.append({'icon': '🌟', 'title': 'Nutrition Master', 'desc': 'Excellent overall nutrition score'})

    # === CALORIE DISTRIBUTION ANALYSIS ===
    calorie_distribution = {}
    if calories_list and len(calories_list) >= 10:
        # Categorize days
        very_low = sum(1 for c in calories_list if c < 1500)
        low = sum(1 for c in calories_list if 1500 <= c < 2000)
        moderate = sum(1 for c in calories_list if 2000 <= c < 2500)
        high = sum(1 for c in calories_list if 2500 <= c < 3000)
        very_high = sum(1 for c in calories_list if c >= 3000)

        total = len(calories_list)
        calorie_distribution['very_low'] = {'count': very_low, 'percent': round((very_low/total)*100, 1), 'label': '<1500'}
        calorie_distribution['low'] = {'count': low, 'percent': round((low/total)*100, 1), 'label': '1500-2000'}
        calorie_distribution['moderate'] = {'count': moderate, 'percent': round((moderate/total)*100, 1), 'label': '2000-2500'}
        calorie_distribution['high'] = {'count': high, 'percent': round((high/total)*100, 1), 'label': '2500-3000'}
        calorie_distribution['very_high'] = {'count': very_high, 'percent': round((very_high/total)*100, 1), 'label': '3000+'}

    # Add insight for late night eating
    if meal_timing.get('night', {}).get('percent', 0) > 15:
        insights.append({
            'type': 'timing',
            'icon': '🌙',
            'title': 'Late Night Eating',
            'description': f'{meal_timing["night"]["percent"]:.0f}% of your calories are consumed late at night (after 10 PM).',
            'recommendation': 'Try to finish eating earlier for better digestion and sleep quality.'
        })

    # Add insight for calorie distribution
    if calorie_distribution.get('very_high', {}).get('percent', 0) > 20:
        insights.append({
            'type': 'distribution',
            'icon': '📊',
            'title': 'High Calorie Days',
            'description': f'{calorie_distribution["very_high"]["percent"]:.0f}% of your days exceed 3000 calories.',
            'recommendation': 'Identify triggers for high-calorie days and plan alternatives.'
        })

    context = {
        'period': period,
        'weekly_summary': weekly_summary,  # This week dashboard
        'goal_progress': goal_progress,  # Goal tracking with progress bars
        'goals': goals,  # Goal targets
        'weekly_reports': weekly_reports[:12],  # Last 12 weeks
        'monthly_reports': monthly_reports[:12],  # Last 12 months
        'best_worst_days': best_worst_days,
        'weight_analysis': weight_analysis,
        'insights': insights,
        'overall_stats': overall_stats,
        'day_of_week_stats': day_of_week_stats,
        'weekday_insights': weekday_insights,
        'streaks': streaks,
        'macro_analysis': macro_analysis,
        'weight_pace': weight_pace,
        'projections': projections,
        'consistency_score': consistency_score,
        'meal_timing': meal_timing,
        'top_foods': top_foods,
        'calorie_budget': calorie_budget,
        'weight_volatility': weight_volatility,
        'nutrition_score': nutrition_score,
        'period_comparison': period_comparison,
        'achievements': achievements,
        'calorie_distribution': calorie_distribution,
    }

    return render(request, 'count_calories_app/analytics.html', context)


# ============================================
# REACT FRONTEND JSON API ENDPOINTS
# ============================================

@require_http_methods(["GET"])
def api_dashboard(request):
    """Dashboard data for React frontend"""
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # Today's food stats
    today_food = FoodItem.objects.filter(consumed_at__gte=today_start, consumed_at__lte=today_end)
    today_stats = today_food.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        carbs=Sum('carbohydrates'),
        fat=Sum('fat'),
        count=Count('id')
    )

    # This week's food stats
    week_food = FoodItem.objects.filter(consumed_at__gte=week_start, consumed_at__lte=today_end)
    week_stats = week_food.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        carbs=Sum('carbohydrates'),
        fat=Sum('fat'),
        count=Count('id')
    )

    # Latest weight
    latest_weight = Weight.objects.order_by('-recorded_at').first()
    weight_week_ago = Weight.objects.filter(recorded_at__lte=now - timedelta(days=7)).order_by('-recorded_at').first()
    weight_change = None
    if latest_weight and weight_week_ago:
        weight_change = float(latest_weight.weight) - float(weight_week_ago.weight)

    # This week's workouts and runs
    week_workouts = WorkoutSession.objects.filter(date__gte=week_start.date()).count()
    week_runs = RunningSession.objects.filter(date__gte=week_start.date())
    week_run_stats = week_runs.aggregate(
        total_distance=Sum('distance'),
        count=Count('id')
    )

    # Recent food items
    recent_foods = list(FoodItem.objects.order_by('-consumed_at')[:5].values(
        'id', 'product_name', 'calories', 'protein', 'carbohydrates', 'fat', 'consumed_at'
    ))
    for food in recent_foods:
        food['consumed_at'] = food['consumed_at'].isoformat() if food['consumed_at'] else None

    # Streak calculation
    streak = 0
    check_date = now.date()
    while True:
        day_start = timezone.make_aware(timezone.datetime.combine(check_date, timezone.datetime.min.time()))
        day_end = timezone.make_aware(timezone.datetime.combine(check_date, timezone.datetime.max.time()))
        if FoodItem.objects.filter(consumed_at__gte=day_start, consumed_at__lte=day_end).exists():
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    # Get user settings for targets
    settings = UserSettings.get_settings()
    effective_targets = settings.get_effective_targets()

    # Calculate macro warnings (when exceeded by more than 10%)
    today_calories = today_stats['calories'] or 0
    today_protein = today_stats['protein'] or 0
    today_carbs = today_stats['carbs'] or 0
    today_fat = today_stats['fat'] or 0

    warnings = []
    if today_calories > effective_targets['calories'] * 1.1:
        excess = today_calories - effective_targets['calories']
        warnings.append({
            'type': 'calories',
            'message': f'You have exceeded your daily calorie target by {int(excess)} kcal',
            'severity': 'warning' if today_calories <= effective_targets['calories'] * 1.25 else 'error',
            'current': today_calories,
            'target': effective_targets['calories'],
        })
    if today_protein > effective_targets['protein'] * 1.1:
        excess = today_protein - effective_targets['protein']
        warnings.append({
            'type': 'protein',
            'message': f'You have exceeded your daily protein target by {int(excess)}g',
            'severity': 'info',  # Exceeding protein is often okay
            'current': round(today_protein, 1),
            'target': effective_targets['protein'],
        })
    if today_carbs > effective_targets['carbs'] * 1.1:
        excess = today_carbs - effective_targets['carbs']
        warnings.append({
            'type': 'carbs',
            'message': f'You have exceeded your daily carbs target by {int(excess)}g',
            'severity': 'warning',
            'current': round(today_carbs, 1),
            'target': effective_targets['carbs'],
        })
    if today_fat > effective_targets['fat'] * 1.1:
        excess = today_fat - effective_targets['fat']
        warnings.append({
            'type': 'fat',
            'message': f'You have exceeded your daily fat target by {int(excess)}g',
            'severity': 'warning' if today_fat <= effective_targets['fat'] * 1.25 else 'error',
            'current': round(today_fat, 1),
            'target': effective_targets['fat'],
        })

    return JsonResponse({
        'today': {
            'calories': today_calories,
            'protein': round(today_protein, 1),
            'carbs': round(today_carbs, 1),
            'fat': round(today_fat, 1),
            'count': today_stats['count'] or 0,
        },
        'week': {
            'calories': week_stats['calories'] or 0,
            'protein': round(week_stats['protein'] or 0, 1),
            'carbs': round(week_stats['carbs'] or 0, 1),
            'fat': round(week_stats['fat'] or 0, 1),
            'count': week_stats['count'] or 0,
            'workouts': week_workouts,
            'runs': week_run_stats['count'] or 0,
            'run_distance': float(week_run_stats['total_distance'] or 0),
        },
        'weight': {
            'current': float(latest_weight.weight) if latest_weight else None,
            'change': round(weight_change, 2) if weight_change else None,
        },
        'recent_foods': recent_foods,
        'streak': streak,
        'goals': {
            'daily_calories': effective_targets['calories'],
            'daily_protein': effective_targets['protein'],
            'daily_carbs': effective_targets['carbs'],
            'daily_fat': effective_targets['fat'],
            'weekly_workouts': settings.weekly_workout_goal,
            'weekly_runs': 2,  # Could add to settings if needed
            'is_auto': effective_targets['is_auto'],
            'fitness_goal': settings.fitness_goal,
        },
        'warnings': warnings,
    })


@require_http_methods(["GET"])
def api_food_items(request):
    """Get food items with filtering for React frontend"""
    days = request.GET.get('days', '90')
    date_param = request.GET.get('date')  # Single day filter (YYYY-MM-DD)
    now = timezone.now()

    # Single day filter takes priority
    if date_param:
        try:
            from datetime import datetime
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            day_start = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
            day_end = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))
            food_items = FoodItem.objects.filter(consumed_at__gte=day_start, consumed_at__lte=day_end)
        except ValueError:
            food_items = FoodItem.objects.filter(consumed_at__gte=now - timedelta(days=1))
    elif days == 'all':
        food_items = FoodItem.objects.all()
    else:
        try:
            days_int = int(days)
            start_date = now - timedelta(days=days_int)
            food_items = FoodItem.objects.filter(consumed_at__gte=start_date)
        except ValueError:
            food_items = FoodItem.objects.filter(consumed_at__gte=now - timedelta(days=90))

    food_items = food_items.order_by('-consumed_at')

    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = int(request.GET.get('per_page', 50))
    paginator = Paginator(food_items, per_page)
    page_obj = paginator.get_page(page)

    items = []
    for item in page_obj:
        items.append({
            'id': item.id,
            'name': item.product_name,
            'calories': float(item.calories) if item.calories else 0,
            'protein': float(item.protein) if item.protein else 0,
            'carbs': float(item.carbohydrates) if item.carbohydrates else 0,
            'fat': float(item.fat) if item.fat else 0,
            'consumed_at': item.consumed_at.isoformat() if item.consumed_at else None,
            'hidden': item.hide_from_quick_list,
        })

    # Totals
    totals = food_items.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        carbs=Sum('carbohydrates'),
        fat=Sum('fat'),
        count=Count('id')
    )

    return JsonResponse({
        'items': items,
        'totals': {
            'calories': float(totals['calories']) if totals['calories'] else 0,
            'protein': round(float(totals['protein']) if totals['protein'] else 0, 1),
            'carbs': round(float(totals['carbs']) if totals['carbs'] else 0, 1),
            'fat': round(float(totals['fat']) if totals['fat'] else 0, 1),
            'count': totals['count'] or 0,
        },
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
        }
    })


@require_http_methods(["POST"])
@csrf_exempt
def api_add_food(request):
    """Add a new food item via API"""
    try:
        from datetime import datetime
        data = json.loads(request.body)

        # Handle date parameter (YYYY-MM-DD format from frontend)
        consumed_at = timezone.now()
        if data.get('date'):
            try:
                date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
                consumed_at = timezone.make_aware(datetime.combine(date_obj, datetime.now().time()))
            except ValueError:
                pass
        elif data.get('consumed_at'):
            consumed_at = data['consumed_at']

        food_item = FoodItem.objects.create(
            product_name=data.get('name', ''),
            calories=data.get('calories', 0),
            protein=data.get('protein', 0),
            carbohydrates=data.get('carbs', 0),
            fat=data.get('fat', 0),
            consumed_at=consumed_at,
        )
        return JsonResponse({
            'success': True,
            'id': food_item.id,
            'message': 'Food item added successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["PUT", "PATCH"])
@csrf_exempt
def api_update_food(request, food_id):
    """Update a food item via API"""
    try:
        food_item = get_object_or_404(FoodItem, id=food_id)
        data = json.loads(request.body)

        if 'name' in data:
            food_item.product_name = data['name']
        if 'calories' in data:
            food_item.calories = data['calories']
        if 'protein' in data:
            food_item.protein = data['protein']
        if 'carbs' in data:
            food_item.carbohydrates = data['carbs']
        if 'fat' in data:
            food_item.fat = data['fat']

        food_item.save()
        return JsonResponse({'success': True, 'message': 'Food item updated'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["DELETE"])
@csrf_exempt
def api_delete_food(request, food_id):
    """Delete a food item via API"""
    try:
        food_item = get_object_or_404(FoodItem, id=food_id)
        food_item.delete()
        return JsonResponse({'success': True, 'message': 'Food item deleted'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
def api_quick_add_foods(request):
    """Get recent foods for quick-add feature"""
    recent_foods = FoodItem.objects.filter(
        hide_from_quick_list=False
    ).values('product_name').annotate(
        count=Count('id'),
        avg_calories=Avg('calories'),
        avg_protein=Avg('protein'),
        avg_carbs=Avg('carbohydrates'),
        avg_fat=Avg('fat'),
    ).order_by('-count')[:15]

    # Transform to frontend-expected format
    foods = []
    for i, food in enumerate(recent_foods):
        foods.append({
            'id': i + 1,  # Generate an ID for display purposes
            'name': food['product_name'],
            'calories': round(food['avg_calories'] or 0),
            'protein': round(food['avg_protein'] or 0, 1),
            'carbs': round(food['avg_carbs'] or 0, 1),
            'fat': round(food['avg_fat'] or 0, 1),
        })

    return JsonResponse({
        'foods': foods
    })


@require_http_methods(["GET"])
def api_search_all_foods(request):
    """Search all foods in database by name for React frontend"""
    query = request.GET.get('q', '').strip()
    limit = int(request.GET.get('limit', 20))

    if not query:
        # Return most frequently logged foods if no query
        foods = FoodItem.objects.values('product_name').annotate(
            count=Count('id'),
            avg_calories=Avg('calories'),
            avg_protein=Avg('protein'),
            avg_carbs=Avg('carbohydrates'),
            avg_fat=Avg('fat'),
            last_used=Max('consumed_at'),
        ).order_by('-count')[:limit]
    else:
        # Search by name (case-insensitive)
        foods = FoodItem.objects.filter(
            product_name__icontains=query
        ).values('product_name').annotate(
            count=Count('id'),
            avg_calories=Avg('calories'),
            avg_protein=Avg('protein'),
            avg_carbs=Avg('carbohydrates'),
            avg_fat=Avg('fat'),
            last_used=Max('consumed_at'),
        ).order_by('-count')[:limit]

    # Transform to frontend-expected format
    results = []
    for food in foods:
        results.append({
            'name': food['product_name'],
            'calories': round(food['avg_calories'] or 0),
            'protein': round(food['avg_protein'] or 0, 1),
            'carbs': round(food['avg_carbs'] or 0, 1),
            'fat': round(food['avg_fat'] or 0, 1),
            'count': food['count'],
            'last_used': food['last_used'].isoformat() if food['last_used'] else None,
        })

    return JsonResponse({
        'results': results,
        'query': query,
        'total': len(results),
    })


@require_http_methods(["GET"])
def api_weight_items(request):
    """Get weight entries for React frontend"""
    days = request.GET.get('days', '365')
    now = timezone.now()

    if days == 'all':
        weights = Weight.objects.all()
    else:
        try:
            days_int = int(days)
            start_date = now - timedelta(days=days_int)
            weights = Weight.objects.filter(recorded_at__gte=start_date)
        except ValueError:
            weights = Weight.objects.filter(recorded_at__gte=now - timedelta(days=365))

    weights = weights.order_by('-recorded_at')

    items = []
    for w in weights:
        items.append({
            'id': w.id,
            'weight': float(w.weight),
            'recorded_at': w.recorded_at.isoformat(),
            'notes': w.notes,
        })

    # Stats
    weight_values = [float(w.weight) for w in weights]
    stats = {}
    if weight_values:
        stats = {
            'current': weight_values[0] if weight_values else None,
            'avg': round(sum(weight_values) / len(weight_values), 1),
            'min': min(weight_values),
            'max': max(weight_values),
            'change': round(weight_values[0] - weight_values[-1], 1) if len(weight_values) > 1 else 0,
        }

    return JsonResponse({
        'items': items,
        'stats': stats,
    })


@require_http_methods(["POST"])
@csrf_exempt
def api_add_weight(request):
    """Add a weight entry via API"""
    try:
        data = json.loads(request.body)
        weight = Weight.objects.create(
            weight=data.get('weight'),
            notes=data.get('notes', ''),
            recorded_at=timezone.now() if not data.get('recorded_at') else data.get('recorded_at'),
        )
        return JsonResponse({'success': True, 'id': weight.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["DELETE"])
@csrf_exempt
def api_delete_weight(request, weight_id):
    """Delete a weight entry via API"""
    try:
        weight = get_object_or_404(Weight, id=weight_id)
        weight.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
def api_running_items(request):
    """Get running sessions for React frontend"""
    days = request.GET.get('days', '365')
    now = timezone.now()

    if days == 'all':
        runs = RunningSession.objects.all()
    else:
        try:
            days_int = int(days)
            start_date = now - timedelta(days=days_int)
            runs = RunningSession.objects.filter(date__gte=start_date.date())
        except ValueError:
            runs = RunningSession.objects.filter(date__gte=(now - timedelta(days=365)).date())

    runs = runs.order_by('-date')

    items = []
    for r in runs:
        duration_seconds = r.duration.total_seconds() if r.duration else 0
        distance = float(r.distance) if r.distance else 0
        speed = (distance / (duration_seconds / 3600)) if duration_seconds > 0 else 0
        pace_seconds = (duration_seconds / distance) if distance > 0 else 0

        items.append({
            'id': r.id,
            'date': r.date.isoformat() if r.date else None,
            'distance': distance,
            'duration': str(r.duration) if r.duration else None,
            'duration_minutes': round(duration_seconds / 60, 1),
            'speed': round(speed, 2),
            'pace': f"{int(pace_seconds // 60)}:{int(pace_seconds % 60):02d}" if pace_seconds else None,
            'notes': r.notes,
        })

    # Stats
    total_distance = sum(item['distance'] for item in items)
    total_duration = sum(item['duration_minutes'] for item in items)
    stats = {
        'total_runs': len(items),
        'total_distance': round(total_distance, 1),
        'total_duration': round(total_duration, 1),
        'avg_distance': round(total_distance / len(items), 1) if items else 0,
        'avg_duration': round(total_duration / len(items), 1) if items else 0,
        'avg_speed': round(sum(item['speed'] for item in items) / len(items), 2) if items else 0,
    }

    return JsonResponse({
        'items': items,
        'stats': stats,
    })


@require_http_methods(["POST"])
@csrf_exempt
def api_add_running(request):
    """Add a running session via API"""
    try:
        data = json.loads(request.body)
        from datetime import datetime

        # Parse duration
        duration_str = data.get('duration', '00:30:00')
        parts = duration_str.split(':')
        if len(parts) == 3:
            duration = timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))
        elif len(parts) == 2:
            duration = timedelta(minutes=int(parts[0]), seconds=int(parts[1]))
        else:
            duration = timedelta(minutes=30)

        run = RunningSession.objects.create(
            date=data.get('date', timezone.now().date()),
            distance=data.get('distance'),
            duration=duration,
            notes=data.get('notes', ''),
        )
        return JsonResponse({'success': True, 'id': run.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["GET"])
def api_workouts(request):
    """Get workout sessions for React frontend"""
    days = request.GET.get('days', '90')
    now = timezone.now()

    if days == 'all':
        workouts = WorkoutSession.objects.all()
    else:
        try:
            days_int = int(days)
            start_date = now - timedelta(days=days_int)
            workouts = WorkoutSession.objects.filter(date__gte=start_date.date())
        except ValueError:
            workouts = WorkoutSession.objects.filter(date__gte=(now - timedelta(days=90)).date())

    workouts = workouts.order_by('-date')

    items = []
    for w in workouts:
        exercises = WorkoutExercise.objects.filter(workout_session=w)
        exercise_list = []
        total_volume = 0

        for ex in exercises:
            volume = (ex.sets or 0) * (ex.reps or 0) * (float(ex.weight) if ex.weight else 0)
            total_volume += volume
            exercise_list.append({
                'id': ex.id,
                'exercise': ex.exercise.name if ex.exercise else 'Unknown',
                'sets': ex.sets,
                'reps': ex.reps,
                'weight': float(ex.weight) if ex.weight else None,
                'volume': round(volume, 1),
            })

        items.append({
            'id': w.id,
            'name': w.name,
            'date': w.date.isoformat() if w.date else None,
            'notes': w.notes,
            'exercises': exercise_list,
            'exercise_count': len(exercise_list),
            'total_volume': round(total_volume, 1),
        })

    # Stats
    stats = {
        'total_workouts': len(items),
        'total_exercises': sum(item['exercise_count'] for item in items),
        'total_volume': round(sum(item['total_volume'] for item in items), 1),
    }

    return JsonResponse({
        'items': items,
        'stats': stats,
    })


@require_http_methods(["GET"])
def api_exercises(request):
    """Get exercise library"""
    exercises = Exercise.objects.all().order_by('name')
    items = []
    for ex in exercises:
        items.append({
            'id': ex.id,
            'name': ex.name,
            'muscle_group': ex.muscle_group,
            'description': ex.description,
        })

    return JsonResponse({'exercises': items})


@require_http_methods(["GET"])
def api_body_measurements(request):
    """Get body measurements for React frontend"""
    measurements = BodyMeasurement.objects.all().order_by('-date')[:50]

    items = []
    prev_measurement = None

    for m in reversed(list(measurements)):
        item = {
            'id': m.id,
            'date': m.date.isoformat() if m.date else None,
            'neck': float(m.neck) if m.neck else None,
            'chest': float(m.chest) if m.chest else None,
            'belly': float(m.belly) if m.belly else None,
            'left_biceps': float(m.left_biceps) if m.left_biceps else None,
            'right_biceps': float(m.right_biceps) if m.right_biceps else None,
            'left_triceps': float(m.left_triceps) if m.left_triceps else None,
            'right_triceps': float(m.right_triceps) if m.right_triceps else None,
            'left_forearm': float(m.left_forearm) if m.left_forearm else None,
            'right_forearm': float(m.right_forearm) if m.right_forearm else None,
            'butt': float(m.butt) if m.butt else None,
            'left_thigh': float(m.left_thigh) if m.left_thigh else None,
            'right_thigh': float(m.right_thigh) if m.right_thigh else None,
            'left_lower_leg': float(m.left_lower_leg) if m.left_lower_leg else None,
            'right_lower_leg': float(m.right_lower_leg) if m.right_lower_leg else None,
            'notes': m.notes,
            'changes': {},
        }

        # Calculate changes from previous measurement
        if prev_measurement:
            for field in ['neck', 'chest', 'belly', 'left_biceps', 'right_biceps', 'butt']:
                current = getattr(m, field)
                previous = getattr(prev_measurement, field)
                if current and previous:
                    item['changes'][field] = round(float(current) - float(previous), 1)

        items.append(item)
        prev_measurement = m

    items.reverse()  # Most recent first

    return JsonResponse({'items': items})


@require_http_methods(["GET"])
def api_analytics(request):
    """Get analytics data for React frontend"""
    period = request.GET.get('period', '90')
    now = timezone.now()

    if period == 'all':
        start_date = None
    else:
        try:
            days = int(period)
            start_date = now - timedelta(days=days)
        except ValueError:
            start_date = now - timedelta(days=90)

    # Get food items
    if start_date:
        food_items = FoodItem.objects.filter(consumed_at__gte=start_date)
    else:
        food_items = FoodItem.objects.all()

    # Daily stats
    from django.db.models.functions import TruncDate
    daily_stats = food_items.annotate(
        day=TruncDate('consumed_at')
    ).values('day').annotate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        carbs=Sum('carbohydrates'),
        fat=Sum('fat'),
    ).order_by('day')

    daily_data = []
    for stat in daily_stats:
        if stat['day']:
            daily_data.append({
                'date': stat['day'].isoformat(),
                'calories': stat['calories'] or 0,
                'protein': round(float(stat['protein'] or 0), 1),
                'carbs': round(float(stat['carbs'] or 0), 1),
                'fat': round(float(stat['fat'] or 0), 1),
            })

    # Weekly summary
    this_week_start = now - timedelta(days=now.weekday())
    this_week_start = this_week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    last_week_start = this_week_start - timedelta(days=7)

    this_week_food = FoodItem.objects.filter(consumed_at__gte=this_week_start)
    last_week_food = FoodItem.objects.filter(consumed_at__gte=last_week_start, consumed_at__lt=this_week_start)

    this_week_stats = this_week_food.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        days=Count('consumed_at__date', distinct=True)
    )
    last_week_stats = last_week_food.aggregate(
        calories=Sum('calories'),
        protein=Sum('protein'),
        days=Count('consumed_at__date', distinct=True)
    )

    this_week_workouts = WorkoutSession.objects.filter(date__gte=this_week_start.date()).count()
    last_week_workouts = WorkoutSession.objects.filter(
        date__gte=last_week_start.date(),
        date__lt=this_week_start.date()
    ).count()

    this_week_runs = RunningSession.objects.filter(date__gte=this_week_start.date()).count()

    weekly_summary = {
        'this_week': {
            'days_logged': this_week_stats['days'] or 0,
            'total_calories': this_week_stats['calories'] or 0,
            'avg_calories': round((this_week_stats['calories'] or 0) / max(this_week_stats['days'] or 1, 1), 0),
            'total_protein': round(float(this_week_stats['protein'] or 0), 0),
            'workouts': this_week_workouts,
            'runs': this_week_runs,
        },
        'last_week': {
            'days_logged': last_week_stats['days'] or 0,
            'avg_calories': round((last_week_stats['calories'] or 0) / max(last_week_stats['days'] or 1, 1), 0),
            'workouts': last_week_workouts,
        },
    }

    # Goals
    goals = {
        'daily_calories': {'current': weekly_summary['this_week']['avg_calories'], 'target': 2500},
        'daily_protein': {'current': round(float(this_week_stats['protein'] or 0) / max(this_week_stats['days'] or 1, 1), 0), 'target': 150},
        'weekly_workouts': {'current': this_week_workouts, 'target': 4},
        'weekly_runs': {'current': this_week_runs, 'target': 2},
    }

    # Streak
    streak = 0
    check_date = now.date()
    while True:
        day_start = timezone.make_aware(timezone.datetime.combine(check_date, timezone.datetime.min.time()))
        day_end = timezone.make_aware(timezone.datetime.combine(check_date, timezone.datetime.max.time()))
        if FoodItem.objects.filter(consumed_at__gte=day_start, consumed_at__lte=day_end).exists():
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return JsonResponse({
        'daily_data': daily_data,
        'weekly_summary': weekly_summary,
        'goals': goals,
        'streak': streak,
    })


@require_http_methods(["GET"])
def api_top_foods(request):
    """Get top foods for React frontend"""
    days = request.GET.get('days', '90')
    sort_by = request.GET.get('sort', 'count')
    now = timezone.now()

    if days == 'all':
        food_items = FoodItem.objects.all()
    else:
        try:
            days_int = int(days)
            start_date = now - timedelta(days=days_int)
            food_items = FoodItem.objects.filter(consumed_at__gte=start_date)
        except ValueError:
            food_items = FoodItem.objects.filter(consumed_at__gte=now - timedelta(days=90))

    # Aggregate by product name
    top_foods = food_items.values('product_name').annotate(
        count=Count('id'),
        total_calories=Sum('calories'),
        avg_calories=Avg('calories'),
        total_protein=Sum('protein'),
        total_carbs=Sum('carbohydrates'),
        total_fat=Sum('fat'),
        latest=Max('consumed_at'),
    )

    if sort_by == 'calories':
        top_foods = top_foods.order_by('-total_calories')
    elif sort_by == 'protein':
        top_foods = top_foods.order_by('-total_protein')
    else:
        top_foods = top_foods.order_by('-count')

    items = []
    for food in top_foods[:50]:
        items.append({
            'name': food['product_name'],
            'count': food['count'],
            'total_calories': food['total_calories'] or 0,
            'avg_calories': round(food['avg_calories'] or 0, 0),
            'total_protein': round(float(food['total_protein'] or 0), 1),
            'total_carbs': round(float(food['total_carbs'] or 0), 1),
            'total_fat': round(float(food['total_fat'] or 0), 1),
            'latest': food['latest'].isoformat() if food['latest'] else None,
        })

    return JsonResponse({'items': items})


# ==================== Settings Views ====================

def settings_view(request):
    """Main settings page with sidebar navigation"""
    user_settings = UserSettings.get_settings()
    section = request.GET.get('section', 'profile')

    if request.method == 'POST':
        section = request.POST.get('section', 'profile')

        if section == 'profile':
            user_settings.name = request.POST.get('name', '')
            user_settings.age = request.POST.get('age') or None
            user_settings.height = request.POST.get('height') or None
            user_settings.current_weight = request.POST.get('current_weight') or None
            user_settings.gender = request.POST.get('gender', 'male')
            user_settings.activity_level = request.POST.get('activity_level', 'moderate')
            user_settings.fitness_goal = request.POST.get('fitness_goal', 'maintain')
            user_settings.use_auto_macros = request.POST.get('use_auto_macros') == 'on'
            user_settings.daily_calorie_target = request.POST.get('daily_calorie_target') or 2000
            user_settings.target_weight = request.POST.get('target_weight') or None
            user_settings.weekly_workout_goal = request.POST.get('weekly_workout_goal') or 3
            user_settings.protein_target = request.POST.get('protein_target') or 150
            user_settings.carbs_target = request.POST.get('carbs_target') or 200
            user_settings.fat_target = request.POST.get('fat_target') or 65
            user_settings.save()
            messages.success(request, 'Profile settings saved successfully!')

        elif section == 'appearance':
            user_settings.theme = request.POST.get('theme', 'dark')
            user_settings.chart_color = request.POST.get('chart_color', 'blue')
            user_settings.default_date_range = request.POST.get('default_date_range') or 30
            user_settings.save()
            messages.success(request, 'Appearance settings saved successfully!')

        elif section == 'notifications':
            user_settings.meal_reminder_enabled = request.POST.get('meal_reminder_enabled') == 'on'
            meal_times = request.POST.getlist('meal_reminder_times')
            user_settings.meal_reminder_times = [t for t in meal_times if t]
            user_settings.workout_reminder_enabled = request.POST.get('workout_reminder_enabled') == 'on'
            workout_time = request.POST.get('workout_reminder_time')
            user_settings.workout_reminder_time = workout_time if workout_time else None
            workout_days = request.POST.getlist('workout_reminder_days')
            user_settings.workout_reminder_days = workout_days
            user_settings.weight_reminder_enabled = request.POST.get('weight_reminder_enabled') == 'on'
            weight_time = request.POST.get('weight_reminder_time')
            user_settings.weight_reminder_time = weight_time if weight_time else None
            user_settings.save()
            messages.success(request, 'Notification preferences saved successfully!')

        return redirect(f'/settings/?section={section}')

    bmr = user_settings.calculate_bmr()
    recommended_macros = user_settings.get_recommended_macros()
    effective_targets = user_settings.get_effective_targets()

    context = {
        'settings': user_settings,
        'section': section,
        'bmr': bmr,
        'recommended_macros': recommended_macros,
        'effective_targets': effective_targets,
        'activity_choices': UserSettings.ACTIVITY_CHOICES,
        'gender_choices': UserSettings.GENDER_CHOICES,
        'fitness_goal_choices': UserSettings.FITNESS_GOAL_CHOICES,
        'theme_choices': UserSettings.THEME_CHOICES,
        'chart_color_choices': UserSettings.CHART_COLOR_CHOICES,
        'date_range_choices': UserSettings.DATE_RANGE_CHOICES,
        'weekdays': [
            ('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'),
            ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'), ('sunday', 'Sunday'),
        ],
    }
    return render(request, 'count_calories_app/settings.html', context)


def export_data(request):
    """Handle data export requests"""
    export_type = request.GET.get('type', 'all')
    export_format = request.GET.get('format', 'csv')

    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv')

        if export_type == 'food':
            response['Content-Disposition'] = 'attachment; filename="food_data.csv"'
            writer = csv.writer(response)
            writer.writerow(['Date', 'Product Name', 'Calories', 'Protein (g)', 'Carbs (g)', 'Fat (g)'])
            for item in FoodItem.objects.all().order_by('-consumed_at'):
                writer.writerow([item.consumed_at.strftime('%Y-%m-%d %H:%M'), item.product_name,
                    float(item.calories), float(item.protein), float(item.carbohydrates), float(item.fat)])

        elif export_type == 'weight':
            response['Content-Disposition'] = 'attachment; filename="weight_data.csv"'
            writer = csv.writer(response)
            writer.writerow(['Date', 'Weight (kg)', 'Notes'])
            for item in Weight.objects.all().order_by('-recorded_at'):
                writer.writerow([item.recorded_at.strftime('%Y-%m-%d %H:%M'), float(item.weight), item.notes or ''])

        elif export_type == 'workout':
            response['Content-Disposition'] = 'attachment; filename="workout_data.csv"'
            writer = csv.writer(response)
            writer.writerow(['Date', 'Workout Name', 'Exercise', 'Sets', 'Reps', 'Weight (kg)', 'Notes'])
            for workout in WorkoutSession.objects.all().order_by('-date'):
                for exercise in workout.exercises.all():
                    writer.writerow([workout.date.strftime('%Y-%m-%d'), workout.name or 'Unnamed',
                        exercise.exercise.name, exercise.sets, exercise.reps,
                        float(exercise.weight) if exercise.weight else '', exercise.notes or ''])

        elif export_type == 'running':
            response['Content-Disposition'] = 'attachment; filename="running_data.csv"'
            writer = csv.writer(response)
            writer.writerow(['Date', 'Distance (km)', 'Duration', 'Notes'])
            for item in RunningSession.objects.all().order_by('-date'):
                writer.writerow([item.date.strftime('%Y-%m-%d'), float(item.distance), str(item.duration), item.notes or ''])

        elif export_type == 'body':
            response['Content-Disposition'] = 'attachment; filename="body_measurements.csv"'
            writer = csv.writer(response)
            writer.writerow(['Date', 'Neck', 'Chest', 'Belly', 'Left Biceps', 'Right Biceps',
                'Left Triceps', 'Right Triceps', 'Left Forearm', 'Right Forearm',
                'Left Thigh', 'Right Thigh', 'Left Lower Leg', 'Right Lower Leg', 'Butt', 'Notes'])
            for item in BodyMeasurement.objects.all().order_by('-date'):
                writer.writerow([item.date.strftime('%Y-%m-%d'),
                    float(item.neck) if item.neck else '', float(item.chest) if item.chest else '',
                    float(item.belly) if item.belly else '', float(item.left_biceps) if item.left_biceps else '',
                    float(item.right_biceps) if item.right_biceps else '', float(item.left_triceps) if item.left_triceps else '',
                    float(item.right_triceps) if item.right_triceps else '', float(item.left_forearm) if item.left_forearm else '',
                    float(item.right_forearm) if item.right_forearm else '', float(item.left_thigh) if item.left_thigh else '',
                    float(item.right_thigh) if item.right_thigh else '', float(item.left_lower_leg) if item.left_lower_leg else '',
                    float(item.right_lower_leg) if item.right_lower_leg else '', float(item.butt) if item.butt else '',
                    item.notes or ''])

        elif export_type == 'all':
            import json as json_module
            response = HttpResponse(content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="all_data.json"'
            data = {'food_items': [], 'weight': [], 'workouts': [], 'running': [], 'body_measurements': []}
            for item in FoodItem.objects.all():
                data['food_items'].append({
                    'consumed_at': item.consumed_at.isoformat(), 'product_name': item.product_name,
                    'calories': float(item.calories), 'protein': float(item.protein),
                    'carbohydrates': float(item.carbohydrates), 'fat': float(item.fat)
                })
            for item in Weight.objects.all():
                data['weight'].append({'recorded_at': item.recorded_at.isoformat(), 'weight': float(item.weight), 'notes': item.notes})
            for item in RunningSession.objects.all():
                data['running'].append({'date': item.date.isoformat(), 'distance': float(item.distance), 'duration': str(item.duration), 'notes': item.notes})
            for item in BodyMeasurement.objects.all():
                data['body_measurements'].append({
                    'date': item.date.isoformat(), 'neck': float(item.neck) if item.neck else None,
                    'chest': float(item.chest) if item.chest else None, 'belly': float(item.belly) if item.belly else None, 'notes': item.notes
                })
            for workout in WorkoutSession.objects.all():
                workout_data = {'date': workout.date.isoformat(), 'name': workout.name, 'notes': workout.notes, 'exercises': []}
                for ex in workout.exercises.all():
                    workout_data['exercises'].append({'exercise_name': ex.exercise.name, 'sets': ex.sets, 'reps': ex.reps,
                        'weight': float(ex.weight) if ex.weight else None, 'notes': ex.notes})
                data['workouts'].append(workout_data)
            response.write(json_module.dumps(data, indent=2))

        return response
    return redirect('/settings/?section=data')


# ==================== React API for Settings ====================

@require_http_methods(["GET"])
def api_settings(request):
    """Get user settings for React frontend"""
    user_settings = UserSettings.get_settings()
    recommended_macros = user_settings.get_recommended_macros()
    effective_targets = user_settings.get_effective_targets()

    return JsonResponse({
        'profile': {
            'name': user_settings.name, 'age': user_settings.age,
            'height': float(user_settings.height) if user_settings.height else None,
            'current_weight': float(user_settings.current_weight) if user_settings.current_weight else None,
            'gender': user_settings.gender, 'activity_level': user_settings.activity_level,
            'fitness_goal': user_settings.fitness_goal,
            'use_auto_macros': user_settings.use_auto_macros,
            'daily_calorie_target': user_settings.daily_calorie_target,
            'target_weight': float(user_settings.target_weight) if user_settings.target_weight else None,
            'weekly_workout_goal': user_settings.weekly_workout_goal,
            'protein_target': user_settings.protein_target, 'carbs_target': user_settings.carbs_target,
            'fat_target': user_settings.fat_target, 'bmr': user_settings.calculate_bmr(),
        },
        'recommended_macros': recommended_macros,
        'effective_targets': effective_targets,
        'appearance': {
            'theme': user_settings.theme, 'chart_color': user_settings.chart_color,
            'default_date_range': user_settings.default_date_range,
        },
        'notifications': {
            'meal_reminder_enabled': user_settings.meal_reminder_enabled,
            'meal_reminder_times': user_settings.meal_reminder_times,
            'workout_reminder_enabled': user_settings.workout_reminder_enabled,
            'workout_reminder_time': str(user_settings.workout_reminder_time) if user_settings.workout_reminder_time else None,
            'workout_reminder_days': user_settings.workout_reminder_days,
            'weight_reminder_enabled': user_settings.weight_reminder_enabled,
            'weight_reminder_time': str(user_settings.weight_reminder_time) if user_settings.weight_reminder_time else None,
        },
        'choices': {
            'activity_levels': [{'value': c[0], 'label': c[1]} for c in UserSettings.ACTIVITY_CHOICES],
            'genders': [{'value': c[0], 'label': c[1]} for c in UserSettings.GENDER_CHOICES],
            'fitness_goals': [{'value': c[0], 'label': c[1]} for c in UserSettings.FITNESS_GOAL_CHOICES],
            'themes': [{'value': c[0], 'label': c[1]} for c in UserSettings.THEME_CHOICES],
            'chart_colors': [{'value': c[0], 'label': c[1]} for c in UserSettings.CHART_COLOR_CHOICES],
            'date_ranges': [{'value': c[0], 'label': c[1]} for c in UserSettings.DATE_RANGE_CHOICES],
        }
    })


@require_http_methods(["PUT", "PATCH"])
@csrf_exempt
def api_update_settings(request):
    """Update user settings from React frontend"""
    try:
        data = json.loads(request.body)
        user_settings = UserSettings.get_settings()

        if 'profile' in data:
            profile = data['profile']
            for field in ['name', 'age', 'height', 'current_weight', 'gender', 'activity_level',
                         'fitness_goal', 'use_auto_macros', 'daily_calorie_target', 'target_weight',
                         'weekly_workout_goal', 'protein_target', 'carbs_target', 'fat_target']:
                if field in profile:
                    setattr(user_settings, field, profile[field])

        if 'appearance' in data:
            appearance = data['appearance']
            for field in ['theme', 'chart_color', 'default_date_range']:
                if field in appearance:
                    setattr(user_settings, field, appearance[field])

        if 'notifications' in data:
            notifications = data['notifications']
            for field in ['meal_reminder_enabled', 'meal_reminder_times', 'workout_reminder_enabled',
                         'workout_reminder_time', 'workout_reminder_days', 'weight_reminder_enabled',
                         'weight_reminder_time']:
                if field in notifications:
                    setattr(user_settings, field, notifications[field])

        user_settings.save()
        return JsonResponse({
            'success': True,
            'message': 'Settings updated successfully',
            'bmr': user_settings.calculate_bmr(),
            'recommended_macros': user_settings.get_recommended_macros(),
            'effective_targets': user_settings.get_effective_targets(),
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)