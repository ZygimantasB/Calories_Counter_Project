from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('food_tracker/', views.food_tracker, name='food_tracker'),
    path('top_foods/', views.top_foods, name='top_foods'),
    path('api/nutrition-data/', views.get_nutrition_data, name='nutrition_data'),
    path('api/gemini-nutrition/', views.get_gemini_nutrition, name='gemini_nutrition'),
    path('api/calories-trend/', views.get_calories_trend_data, name='calories_trend_data'),
    path('api/macros-trend/', views.get_macros_trend_data, name='macros_trend_data'),

    path('food/<int:food_item_id>/edit/', views.edit_food_item, name='edit_food_item'),
    path('food/<int:food_item_id>/delete/', views.delete_food_item, name='delete_food_item'),
    path('food/<int:food_item_id>/hide-from-quick-list/', views.hide_from_quick_list, name='hide_from_quick_list'),

    path('weight/', views.weight_tracker, name='weight_tracker'),
    path('weight/<int:weight_id>/edit/', views.edit_weight, name='edit_weight'),
    path('weight/<int:weight_id>/delete/', views.delete_weight, name='delete_weight'),
    path('api/weight-data/', views.get_weight_data, name='weight_data'),
    path('api/weight-calories-correlation/', views.get_weight_calories_correlation, name='weight_calories_correlation'),

    path('workout/', views.workout_tracker, name='workout_tracker'),
    path('workout/<int:workout_id>/', views.workout_detail, name='workout_detail'),
    path('workout-table/', views.workout_table, name='workout_table'),
    path('exercise/', views.exercise_list, name='exercise_list'),
    path('api/workout-frequency/', views.get_workout_frequency_data, name='workout_frequency_data'),
    path('api/exercise-progress/', views.get_exercise_progress_data, name='exercise_progress_data'),
    path('api/exercise-progress/<int:exercise_id>/', views.get_exercise_progress_data, name='exercise_progress_data_with_id'),

    path('running/', views.running_tracker, name='running_tracker'),
    path('running/<int:running_session_id>/edit/', views.edit_running_session, name='edit_running_session'),
    path('running/<int:running_session_id>/delete/', views.delete_running_session, name='delete_running_session'),
    path('api/running-data/', views.get_running_data, name='running_data'),

    path('api/workout-tables/', views.get_workout_tables, name='get_workout_tables'),
    path('api/workout-tables/save/', views.save_workout_table, name='save_workout_table'),
    path('api/workout-tables/<int:table_id>/delete/', views.delete_workout_table, name='delete_workout_table'),

    path('body-measurements/', views.body_measurements_tracker, name='body_measurements_tracker'),
    path('body-measurements/<int:measurement_id>/edit/', views.edit_body_measurement, name='edit_body_measurement'),
    path('body-measurements/<int:measurement_id>/delete/', views.delete_body_measurement, name='delete_body_measurement'),
    path('api/body-measurements-data/', views.get_body_measurements_data, name='body_measurements_data'),
]
