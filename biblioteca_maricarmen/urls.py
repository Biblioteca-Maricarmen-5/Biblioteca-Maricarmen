from django.contrib import admin

from biblioteca import views

from biblioteca.api import api  # Importa la API de Ninja

# Para ver export documentos (si es necesario en el futuro)
#from biblioteca.views import DocumentoUploadView  
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include



urlpatterns = [
    path('', views.index),
    path('admin/', admin.site.urls),
    #path('api/', include(router.urls)), 
    path("api/", api.urls), 

  
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Para servir archivos estáticos durante el desarrollo
#if settings.DEBUG:
 #   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
