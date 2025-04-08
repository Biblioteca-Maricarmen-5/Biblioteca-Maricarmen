from django.contrib.auth import authenticate, get_user_model
from ninja import NinjaAPI, Schema, Field
from ninja.security import HttpBasicAuth, HttpBearer
from .models import *
from django.shortcuts import get_object_or_404
from typing import List, Optional, Union, Literal, Dict
import secrets
from base64 import urlsafe_b64encode, urlsafe_b64decode
import hashlib

api = NinjaAPI()


User = get_user_model()


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
    grupos: List[str] = []
    token: Optional[str] = None  

@api.post("/login", response=AuthResponse)
def login(request, payload: LoginSchema):
    username = payload.username
    password = payload.password
    user = authenticate(username=username, password=password)
    
    if user:
        grupos = [group.name for group in user.groups.all()]  # Obtener nombres de los grupos
        telefon = getattr(user, "telefon", None)

        # Asegurarnos de que el usuario tiene al menos un grupo y un teléfono
        if grupos and telefon:
            primer_grupo = grupos[0]
            # Encriptar el nombre del grupo usando SHA-256 
            grupo_encriptado = hashlib.sha256(primer_grupo.encode()).hexdigest()
            telefon_encriptado = hashlib.sha256(telefon.encode()).hexdigest()
            token = f"{grupo_encriptado}_{telefon_encriptado}"
        else:
            token = None

        return {
            "exists": True,
            "grupos": grupos,
            "token": token  # Aquí devolvemos el token
        }
    else:
        return {"exists": False, "grupos": [], "token": None}




# esquema para ver los grupos y permitir accesos

def desencriptar_grupo(token):
    grupo_encriptado, _ = token.split('_')
    # Desencriptar el grupo usando SHA-256 (esto sería reversible en tu caso, usando el grupo original).
    grupo_original = hashlib.sha256(grupo_encriptado.encode()).hexdigest()
    return grupo_original



# Entrada esperada del POST
class UserProfileRequest(Schema):
    username: str

# Salida del perfil de usuario
class UserProfileResponse(Schema):
    username: str
    nombre: str
    email: str
    centre: str | None = None
    cicle: str | None = None
    imatge: str | None = None
    grupos: list[str]
    telefon: str | None = None

@api.post("/perfil/", response=UserProfileResponse)
def perfil(request, data: UserProfileRequest):
    user = get_object_or_404(User, username=data.username)

    nombre = user.get_full_name() if user.first_name or user.last_name else ""
    centre_name = user.centre.nom if user.centre else None
    cicle_name = user.cicle.nom if user.cicle else None

    # Manejo seguro de imagen
    try:
        imatge_url = user.imatge.url if user.imatge else None
    except ValueError:
        imatge_url = None

    telefon = user.telefon if user.telefon else None
    grupos = [group.name for group in user.groups.all()]

    return {
        "username": user.username,
        "nombre": nombre,
        "email": user.email,
        "centre": centre_name,
        "cicle": cicle_name,
        "imatge": imatge_url,
        "grupos": grupos,
        "telefon": telefon,
    }




class PerfilUpdateSchema(Schema):
    username: str
    nombre: Optional[str]
    email: Optional[str]
    centre: Optional[str]
    cicle: Optional[str]
    telefon: Optional[str]

@api.patch("/perfil/")
def actualizar_perfil(request, data: PerfilUpdateSchema):
    user = get_object_or_404(User, username=data.username)

    # nombre: separar en nombre y apellido si hace falta
    if data.nombre:
        partes = data.nombre.split()
        user.first_name = partes[0]
        user.last_name = " ".join(partes[1:]) if len(partes) > 1 else ""

    if data.email:
        user.email = data.email

    if data.centre:
        user.centre = Centre.objects.filter(nom=data.centre).first()
    else:
        user.centre = None

    if data.cicle:
        user.cicle = Cicle.objects.filter(nom=data.cicle).first()
    else:
        user.cicle = None

    user.telefon = data.telefon
    user.save()

    return {"success": True}


class PerfilCheckSchema(Schema):
    username: str
    nombre: Optional[str]
    email: Optional[str]
    centre: Optional[str]
    cicle: Optional[str]
    telefon: Optional[str]

class PerfilCheckResponse(Schema):
    modified: bool

@api.post("/verificar-cambios/", response=PerfilCheckResponse)
def verificar_cambios(request, data: PerfilCheckSchema):
    user = get_object_or_404(User, username=data.username)

    centre_name = user.centre.nom if user.centre else None
    cicle_name = user.cicle.nom if user.cicle else None

    cambios = (
        (user.get_full_name() != data.nombre) or
        (user.email != data.email) or
        (centre_name != data.centre) or
        (cicle_name != data.cicle) or
        (user.telefon != data.telefon)
    )

    return {"modified": cambios}


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
