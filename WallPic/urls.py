from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('', include('wallpapers.urls')),
    path('admin/', admin.site.urls),
    
]

