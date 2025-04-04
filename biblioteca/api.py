from django.contrib.auth import authenticate, get_user_model
from ninja import NinjaAPI, Schema
from ninja.security import HttpBasicAuth, HttpBearer
from .models import *
from django.shortcuts import get_object_or_404
from typing import List, Optional, Union, Literal, Dict
import secrets

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

@api.post("/login", response=AuthResponse)
def login(request, payload: LoginSchema):
    username = payload.username
    password = payload.password
    user = authenticate(username=username, password=password)
    if user:
        grupos = [group.name for group in user.groups.all()]  # Obtener nombres de los grupos
        return {"exists": True, "grupos": grupos}
    else:
        return {"exists": False, "grupos": []}







# Esquema de respuesta para el perfil del usuario
class UserProfileResponse(Schema):
    username: str
    nombre: str
    email: str
    centre: Optional[str]
    cicle: Optional[str]
    imatge: Optional[str]
    grupos: List[str]
    telefon: Optional[str]

# Endpoint para obtener el perfil del usuario
@api.get("/perfil/{username}", response=UserProfileResponse)
def perfil(request, username: str):
    user = get_object_or_404(User, username=username)
    nombre = user.get_full_name() if user.first_name and user.last_name else None
    centre_name = user.centre.nom if user.centre else None
    cicle_name = user.cicle.nom if user.cicle else None
    imatge_url = user.imatge.url if user.imatge else None
    grupos = [group.name for group in user.groups.all()]
    telefon = user.telefon if user.telefon else None

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
