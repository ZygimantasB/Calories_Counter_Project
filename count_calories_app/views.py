from django.shortcuts import render
import os

def home(request):
    # Debugging info
    print("Attempting to render home.html")
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'count_calories_app', 'home.html')
    print(f"Template path: {template_path}")
    print(f"Template exists: {os.path.exists(template_path)}")

    return render(request, 'count_calories_app/home.html')
