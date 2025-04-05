from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .models import Usuari, Centre, Cicle
import csv
import os
import re
from django.conf import settings
from django.core.files.storage import default_storage

def index(response):
    try:
        tpl = get_template("index.html")
        return render(response, "index.html")
    except TemplateDoesNotExist:
        return HttpResponse("Backend OK. Posa en marxa el frontend seguint el README.")


#api para comprovar documento
class DocumentoUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        archivo = request.FILES.get('archivo')
        if not archivo:
            return JsonResponse({"mensaje": "No se proporcionó ningún archivo"}, status=400)

        file_path = default_storage.save(f"temp/{archivo.name}", archivo)
        file_path = os.path.join(settings.MEDIA_ROOT, file_path)

        registros_guardados = []
        registros_descartados = []

        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                headers = next(reader)

                for row in reader:
                    if len(row) < 7:
                        registros_descartados.append({"usuario": row, "motivo": "Datos incompletos"})
                        continue

                    nom, cognom1, cognom2, email, telefon, centre, grup = map(str.strip, row)

                    if not self.validar_texto(nom) or not self.validar_texto(cognom1) or not self.validar_texto(cognom2):
                        registros_descartados.append({"usuario": row, "motivo": "Nombre o apellido inválido"})
                        continue

                    if not self.validar_telefono(telefon):
                        registros_descartados.append({"usuario": row, "motivo": "Teléfono inválido"})
                        continue

                    if Usuari.objects.filter(email=email).exists():
                        registros_descartados.append({"usuario": row, "motivo": "Email duplicado"})
                        continue

                    centro_obj = Centre.objects.filter(nom__iexact=centre).first()
                    if not centro_obj:
                        registros_descartados.append({"usuario": row, "motivo": "Centro no válido"})
                        continue

                    cicle_obj = Cicle.objects.filter(nom__iexact=grup).first()
                    if not cicle_obj:
                        registros_descartados.append({"usuario": row, "motivo": "Grupo no válido"})
                        continue

                    usuario = Usuari.objects.create_user(
                        first_name=nom,
                        last_name=f"{cognom1} {cognom2}",
                        email=email,
                        username=email,
                        password='temporal123',  # Cambia esto en producción
                        centre=centro_obj,
                        cicle=cicle_obj,
                        telefon=telefon
                    )

                    registros_guardados.append(usuario.email)

            return JsonResponse({
                "mensaje": "Archivo procesado",
                "registros_guardados": registros_guardados,
                "registros_descartados": registros_descartados
            }, status=200)

        except Exception as e:
            return JsonResponse({"mensaje": f"Error al procesar el archivo: {str(e)}"}, status=500)

        # finally:
        #     os.remove(file_path)

    def validar_texto(self, texto):
        return bool(re.fullmatch(r"[A-Za-zÀ-ÿ\s]+", texto))

    def validar_telefono(self, telefono):
        return bool(re.fullmatch(r"\d{9,15}", telefono))
