from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
import os


def serve_react_app(request):
    """Serve the React app's index.html"""
    react_index_path = os.path.join(settings.BASE_DIR, 'static', 'react', 'index.html')
    try:
        with open(react_index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    except FileNotFoundError:
        return HttpResponse(
            '<h1>React app not built</h1><p>Run "npm run build" in the frontend folder.</p>',
            content_type='text/html',
            status=404
        )


urlpatterns = [
    path('admin/', admin.site.urls),
    # React app routes - these will be handled by React Router
    path('app/', serve_react_app, name='react_app'),
    re_path(r'^app/.*$', serve_react_app),  # Catch-all for React routes
    # Django app routes
    path('', include('count_calories_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
