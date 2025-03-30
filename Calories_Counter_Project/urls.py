from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
                path('admin/', admin.site.urls),
                path('', include('count_calories_app.urls')),  # This should include your app URLs at the root
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)