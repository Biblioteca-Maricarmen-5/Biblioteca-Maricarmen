from django.contrib import admin
from django.urls import path
from biblioteca import views
from ninja import NinjaAPI

from biblioteca.api import api  # Importa la API de Ninja

# Para ver export documentos (si es necesario en el futuro)
#from biblioteca.views import DocumentoUploadView  
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.index),
    path('admin/', admin.site.urls),
    path("api/", api.urls),  # Rutas de la API Ninja
    # Si alguna vez necesitas agregar vistas tradicionales para documentos, puedes descomentar la siguiente línea
    # path("subir-documento/", DocumentoUploadView.as_view(), name="subir-documento"),
]

# Para servir archivos estáticos durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
