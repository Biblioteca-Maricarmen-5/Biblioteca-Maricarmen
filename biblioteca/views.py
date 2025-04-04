from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Documento
from .serializers import DocumentoSerializer
import csv
import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse

def index(response):
    try:
        tpl = get_template("index.html")
        return render(response,"index.html")
    except TemplateDoesNotExist:
        return HttpResponse("Backend OK. Posa en marxa el frontend seguint el README.")




class DocumentoUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return JsonResponse({"mensaje": "No se proporcionó ningún archivo"}, status=400)

        # Guardar el archivo en el directorio temporal
        file_path = default_storage.save(f"temp/{archivo.name}", archivo)
        file_path = os.path.join(settings.MEDIA_ROOT, file_path)

        # Verificar si el archivo tiene contenido
        registros = []
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                headers = next(reader)  # Leer las cabeceras del CSV

                # Verificar si el CSV está vacío
                if not any(reader):
                    return JsonResponse({"mensaje": "El archivo CSV está vacío"}, status=400)

                # Leer el contenido y almacenar las filas
                for row in reader:
                    registros.append(row)

            # Si hay registros, devolver los datos
            if registros:
                return JsonResponse({"mensaje": "Archivo procesado", "registros": registros}, status=200)

            else:
                return JsonResponse({"mensaje": "El archivo no contiene registros válidos"}, status=400)

        except Exception as e:
            return JsonResponse({"mensaje": f"Error al procesar el archivo: {str(e)}"}, status=500)

        finally:
            os.remove(file_path)  # Eliminar el archivo después de procesarlo

