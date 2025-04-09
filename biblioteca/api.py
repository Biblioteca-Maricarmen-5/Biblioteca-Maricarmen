from django.contrib.auth import authenticate
from ninja import NinjaAPI, Schema
from ninja.security import HttpBasicAuth, HttpBearer
from .models import *
from typing import List, Optional, Union, Literal, Dict
import secrets
from ninja import NinjaAPI, Router
from ninja.files import UploadedFile
from .models import Usuari, Centre, Cicle 
import csv
import os
import re
import traceback
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.core.exceptions import ValidationError  # Asegúrate de que esta importación esté aquí



api = NinjaAPI()

# Crear un Router específico para el endpoint de subida de documentos
router = Router()

class UploadResponse(Schema):
    mensaje: str
    registros: Optional[List[dict]] = None
    error: Optional[str] = None


class UsuariCSV(Schema):
    nom: str
    cognom1: str
    cognom2: str
    email: str
    telefon: str
    centre: str
    grup: str


#para errores del documento csv
class FilaError(Schema):
    fila: dict
    error: str



class UploadResponse(Schema):
    mensaje: str
    registros: Optional[List[UsuariCSV]] = None
    error: Optional[str] = None
    errores: Optional[List[FilaError]] = None









# Autenticació bàsica
class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = authenticate(username=username, password=password)
        if user:
            # Genera un token simple
            token = secrets.token_hex(16)
            user.auth_token = token
            user.save()
            return token
        return None

# Autenticació per Token Bearer
class AuthBearer(HttpBearer):
    def authenticate(self, request, token):
        try:
            user = Usuari.objects.get(auth_token=token)
            return user
        except Usuari.DoesNotExist:
            return None

# Endpoint per obtenir un token
@api.get("/token", auth=BasicAuth())
@api.get("/token/", auth=BasicAuth())
def obtenir_token(request):
    return {"token": request.auth}




# Esquema de respuesta
class AuthResponse(Schema):
    exists: bool


# Esquema para recibir las credenciales
class LoginSchema(Schema):
    username: str
    password: str

# Esquema de respuesta
class AuthResponse(Schema):
    exists: bool

@api.post("/login", response=AuthResponse)
def login(request, payload: LoginSchema):
    username = payload.username
    password = payload.password
    user = authenticate(username=username, password=password)
    if user:
        return {"exists": True}
    else:
        return {"exists": False}

class CatalegOut(Schema):
    id: int
    titol: str
    autor: Optional[str]

class LlibreOut(CatalegOut):
    editorial: Optional[str]
    ISBN: Optional[str]

class ExemplarOut(Schema):
    id: int
    registre: str
    exclos_prestec: bool
    baixa: bool
    cataleg: Union[LlibreOut,CatalegOut]
    tipus: str

class LlibreIn(Schema):
    titol: str
    editorial: str





@api.get("/llibres", response=List[LlibreOut])
@api.get("/llibres/", response=List[LlibreOut])
#@api.get("/llibres/", response=List[LlibreOut], auth=AuthBearer())
def get_llibres(request):
    qs = Llibre.objects.all()
    return qs

@api.post("/llibres/")
def post_llibres(request, payload: LlibreIn):
    llibre = Llibre.objects.create(**payload.dict())
    return {
        "id": llibre.id,
        "titol": llibre.titol
    }

@api.get("/exemplars", response=List[ExemplarOut])
@api.get("/exemplars/", response=List[ExemplarOut])
def get_exemplars(request):
    # carreguem objectes amb els proxy models relacionats exactes
    exemplars = Exemplar.objects.select_related(
        "cataleg__llibre",
        "cataleg__revista",
        "cataleg__cd",
        "cataleg__dvd",
        "cataleg__br",
        "cataleg__dispositiu",
    ).all()
    result = []

    for exemplar in exemplars:
        cataleg_instance = exemplar.cataleg

        # Determinar el tipus de l'objecte Cataleg
        if hasattr(cataleg_instance, "llibre"):
            cataleg_schema = LlibreOut.from_orm(cataleg_instance.llibre)
            tipus = "llibre"
        #elif hasattr(cataleg_instance, "dispositiu"):
        #    cataleg_schema = LlibreOut.from_orm(cataleg_instance.dispositiu)
        # TODO: afegir altres esquemes
        else:
            cataleg_schema = CatalegOut.from_orm(cataleg_instance)
            tipus = "indefinit"

        # Afegir l'Exemplar amb el Cataleg serialitzat
        result.append(
            ExemplarOut(
                id=exemplar.id,
                registre=exemplar.registre,
                exclos_prestec=exemplar.exclos_prestec,
                baixa=exemplar.baixa,
                cataleg=cataleg_schema,
                tipus=tipus,
            )
        )

    return result


# Crear un Router específico para el endpoint de subida de documentos
router = Router()

# Función para validar si el nombre contiene solo letras
def validar_nombre(nombre):
    if not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ]+$', nombre):
        raise ValidationError(f"El nombre '{nombre}' contiene caracteres no válidos.")

# Función para validar si el teléfono contiene solo números
def validar_telefono(telefono):
    if not telefono.isdigit():
        raise ValidationError(f"El teléfono '{telefono}' debe contener solo números.")



@router.post("/subir-documento/", response={200: UploadResponse, 500: UploadResponse})
def subir_documento(request, archivo: UploadedFile):
    file_path = default_storage.save(f"temp/{archivo.name}", archivo)
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)

    registros: List[UsuariCSV] = []
    errores: List[Dict] = []
    usuarios_creados = 0

    try:
        with open(full_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                
                cleaned_row = {key.strip(): (value.strip() if value is not None else "") for key, value in row.items()}


                if not any(cleaned_row.values()):
                    continue

                email = (cleaned_row.get("email") or "").strip().replace(' ', '').lower()


                

                if not email or "@" not in email:
                    errores.append({"fila": cleaned_row, "error": "Email vacío o inválido"})
                    continue

                if Usuari.objects.filter(username=email).exists():
                    errores.append({"fila": cleaned_row, "error": f"El email {email} ya existe."})
                    continue

                nom = (cleaned_row.get("nom") or "").strip()
                cognom1 = (cleaned_row.get("cognom1") or "").strip()
                cognom2 = (cleaned_row.get("cognom2") or "").strip()
                telefon = cleaned_row.get("telefon", "")
                centre_nom = cleaned_row.get("centre", "")
                cicle_nom = cleaned_row.get("grup", "")

                if not all([nom, cognom1, cognom2, telefon, centre_nom, cicle_nom]):
                    errores.append({"fila": cleaned_row, "error": "Faltan campos obligatorios."})
                    continue

                try:
                    validar_nombre(nom)
                    validar_nombre(cognom1)
                    if cognom2:
                        validar_nombre(cognom2)
                    validar_telefono(telefon)

                    centre, _ = Centre.objects.get_or_create(nom=centre_nom)
                    cicle, _ = Cicle.objects.get_or_create(nom=cicle_nom)

                    Usuari.objects.create_user(
                        username=email,
                        email=email,
                        first_name=nom,
                        last_name=f"{cognom1} {cognom2}",
                        telefon=telefon,
                        centre=centre,
                        cicle=cicle,
                        password="1234"
                    )
                    usuarios_creados += 1

                    registros.append(UsuariCSV(
                        nom=nom,
                        cognom1=cognom1,
                        cognom2=cognom2,
                        email=email,
                        telefon=telefon,
                        centre=centre_nom,
                        grup=cicle_nom
                    ))

                except ValidationError as e:
                    errores.append({"fila": cleaned_row, "error": str(e)})
                    continue

    except Exception as e:
        print("🔥 Error procesando CSV:", e)
        traceback.print_exc()
        return JsonResponse({"mensaje": "Error interno del servidor."}, status=500)

    finally:
        try:
            os.remove(full_path)
        except:
            pass

    return 200, UploadResponse(
        mensaje=f"✅ Archivo procesado. Usuarios creados: {usuarios_creados}",
        registros=registros,
        errores=errores if errores else None
    )



# Registrar el router con el api
api.add_router("/api/", router)