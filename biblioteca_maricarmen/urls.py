from django.contrib import admin

from biblioteca import views

from ninja import NinjaAPI
from biblioteca.api import api
from django.conf import settings
from django.conf.urls.static import static

from django.urls import path, include



urlpatterns = [
    path('', views.index),
    path('admin/', admin.site.urls),
    #path('api/', include(router.urls)), 
  

    path("api/", api.urls),
  
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

