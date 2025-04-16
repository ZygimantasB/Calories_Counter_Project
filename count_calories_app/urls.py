from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/nutrition-data/', views.get_nutrition_data, name='nutrition_data'),
    path('api/calories-trend/', views.get_calories_trend_data, name='calories_trend_data'),
    path('api/macros-trend/', views.get_macros_trend_data, name='macros_trend_data'),

    # Food item edit/delete URLs
    path('food/<int:food_item_id>/edit/', views.edit_food_item, name='edit_food_item'),
    path('food/<int:food_item_id>/delete/', views.delete_food_item, name='delete_food_item'),

    # Weight tracking URLs
    path('weight/', views.weight_tracker, name='weight_tracker'),
    path('weight/<int:weight_id>/edit/', views.edit_weight, name='edit_weight'),
    path('weight/<int:weight_id>/delete/', views.delete_weight, name='delete_weight'),
    path('api/weight-data/', views.get_weight_data, name='weight_data'),

    # Workout tracking URLs
    path('workout/', views.workout_tracker, name='workout_tracker'),
    path('workout/<int:workout_id>/', views.workout_detail, name='workout_detail'),
    path('workout-table/', views.workout_table, name='workout_table'),
    path('exercise/', views.exercise_list, name='exercise_list'),
    path('api/workout-frequency/', views.get_workout_frequency_data, name='workout_frequency_data'),
    path('api/exercise-progress/', views.get_exercise_progress_data, name='exercise_progress_data'),
    path('api/exercise-progress/<int:exercise_id>/', views.get_exercise_progress_data, name='exercise_progress_data_with_id'),

    # Running tracking URLs
    path('running/', views.running_tracker, name='running_tracker'),
    path('api/running-data/', views.get_running_data, name='running_data'),

    # Workout table API endpoints
    path('api/workout-tables/', views.get_workout_tables, name='get_workout_tables'),
    path('api/workout-tables/save/', views.save_workout_table, name='save_workout_table'),
    path('api/workout-tables/<int:table_id>/delete/', views.delete_workout_table, name='delete_workout_table'),
]
