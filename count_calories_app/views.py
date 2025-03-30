from django.shortcuts import render
import os

def home(request):
    return render(request, 'count_calories_app/home.html')
