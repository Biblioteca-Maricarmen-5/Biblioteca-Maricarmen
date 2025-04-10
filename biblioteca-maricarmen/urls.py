from django.contrib import admin
from django.urls import path
from biblioteca import views

from ninja import NinjaAPI
from biblioteca.api import api
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', views.index),
    path('admin/', admin.site.urls),
    path("api/", api.urls),
  
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

