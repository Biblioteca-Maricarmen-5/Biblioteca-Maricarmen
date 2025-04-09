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

