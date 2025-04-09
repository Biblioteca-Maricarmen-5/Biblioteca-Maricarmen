import os
import random
from datetime import datetime, timedelta
from django.core.files import File
from django.utils.timezone import make_aware
from django.contrib.auth.hashers import make_password
from faker import Faker
from faker.providers import lorem, person, address, company, date_time, misc

# Configuración inicial de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca-maricarmen.settings')
import django
django.setup()

from biblioteca.models import (
    Categoria, Pais, Llengua, Llibre, Exemplar, Usuari, Prestec, Reserva,
    Centre, Cicle, Revista, CD, DVD, BR, Dispositiu, Imatge
)

# Configuramos Faker para que use español de España
fake = Faker('es_ES')
fake.add_provider(lorem)
fake.add_provider(person)
fake.add_provider(address)
fake.add_provider(company)
fake.add_provider(date_time)
fake.add_provider(misc)

def limpiar_db():
    """Opcional: Limpiar la base de datos existente (solo para desarrollo)"""
    print("Limpiando base de datos...")
    # Desactivar constraints temporalmente para PostgreSQL
    from django.db import connection
    cursor = connection.cursor()
    try:
        cursor.execute('SET CONSTRAINTS ALL IMMEDIATE;')
        cursor.execute('SET CONSTRAINTS ALL DEFERRED;')
    except:
        pass
    
    # Eliminar todos los datos
    models = [Categoria, Pais, Llengua, Llibre, Exemplar, Usuari, 
              Prestec, Reserva, Centre, Cicle, Revista, CD, DVD, BR, Dispositiu]
    
    for model in models:
        model.objects.all().delete()
    print("Base de datos limpiada")

def crear_categorias():
    print("Creando categorías...")
    categorias_principales = [
        "Literatura", "Ciencia", "Historia", "Arte", "Tecnología",
        "Filosofía", "Economía", "Salud", "Deportes", "Infantil"
    ]
    
    for cat in categorias_principales:
        categoria = Categoria.objects.create(nom=cat)
        
        # Subcategorías nivel 1
        for _ in range(random.randint(2, 5)):
            subcat = Categoria.objects.create(
                nom=f"{cat} - {fake.word().capitalize()}",
                parent=categoria
            )
            
            # Subcategorías nivel 2 (30% de probabilidad)
            if random.random() < 0.3:
                for __ in range(random.randint(1, 3)):
                    Categoria.objects.create(
                        nom=f"{subcat.nom} - {fake.word().capitalize()}",
                        parent=subcat
                    )

def crear_paises_y_lenguas():
    print("Creando países y lenguas...")
    paises_comunes = [
        "España", "Francia", "Italia", "Reino Unido", "Alemania",
        "Estados Unidos", "México", "Argentina", "China", "Japón"
    ]
    
    for pais in paises_comunes:
        Pais.objects.create(nom=pais)
    
    lenguas_comunes = [
        "Catalán", "Español", "Inglés", "Francés", "Alemán",
        "Italiano", "Portugués", "Chino", "Japonés", "Ruso", "Árabe"
    ]
    
    for lengua in lenguas_comunes:
        Llengua.objects.create(nom=lengua)

def crear_autores_y_libros():
    print("Creando autores y libros...")
    
    # Crear exactamente 100 autores con nombres en español
    autores = [fake.name() for _ in range(100)]
    
    paises = list(Pais.objects.all())
    lenguas = list(Llengua.objects.all())
    categorias = list(Categoria.objects.all())
    
    # Contadores para seguimiento
    libros_creados = 0
    ejemplares_creados = 0
    ejemplares_objetivo = 5000
    
    # Conjunto para almacenar ISBNs ya utilizados y garantizar unicidad
    used_isbns = set()
    
    # Función para obtener un ISBN único
    def get_unique_isbn():
        while True:
            isbn = fake.isbn13()
            if isbn not in used_isbns:
                used_isbns.add(isbn)
                return isbn
    
    # Primera pasada: asignar entre 1 y 10 libros a cada autor
    for autor in autores:
        # Determinar cuántos libros tendrá este autor (entre 1 y 10)
        num_libros = random.randint(1, 10)
        
        # Crear los libros para este autor
        for _ in range(num_libros):
            # Si ya alcanzamos 1000 libros, salimos del bucle
            if libros_creados >= 1000:
                break
                
            titulo = fake.sentence(nb_words=3).replace('.', '').title()
            
            libro = Llibre.objects.create(
                titol=titulo,
                titol_original=titulo if random.random() < 0.3 else fake.sentence(nb_words=3).replace('.', '').title(),
                autor=autor,
                CDU=fake.numerify("###.##"),
                signatura=f"LB-{fake.bothify('??###')}",
                data_edicio=fake.date_between(start_date='-50y', end_date='today'),
                resum=fake.paragraph(nb_sentences=5),
                anotacions=fake.paragraph(nb_sentences=2) if random.random() < 0.7 else None,
                mides=f"{random.randint(15, 30)}x{random.randint(20, 40)} cm",
                ISBN=get_unique_isbn(),  # Siempre generamos un ISBN único
                editorial=fake.company(),
                colleccio=fake.word().title() if random.random() < 0.5 else None,
                lloc=fake.city(),
                pais=random.choice(paises),
                llengua=random.choice(lenguas),
                numero=random.randint(1, 10) if random.random() < 0.3 else None,
                volums=random.randint(1, 5) if random.random() < 0.2 else None,
                pagines=random.randint(50, 800) if random.random() < 0.9 else None,
                info_url=fake.url() if random.random() < 0.5 else None,
                preview_url=fake.url() if random.random() < 0.3 else None,
                thumbnail_url=fake.image_url(width=200, height=300) if random.random() < 0.4 else None
            )
            
            # Añadir 1-4 categorías aleatorias
            cats = random.sample(categorias, random.randint(1, 4))
            libro.tags.set(cats)
            
            libros_creados += 1
            
            # Para controlar los ejemplares y llegar exactamente a 5000
            ejemplares_por_libro = 5
            # Ajustamos el último libro para llegar exactamente a 5000 ejemplares
            if ejemplares_creados + ejemplares_por_libro > ejemplares_objetivo:
                ejemplares_por_libro = ejemplares_objetivo - ejemplares_creados
            
            # Crear ejemplares para este libro
            for _ in range(ejemplares_por_libro):
                Exemplar.objects.create(
                    cataleg=libro,
                    registre=f"REG-{fake.bothify('####-####')}",
                    exclos_prestec=random.random() < 0.1,
                    baixa=random.random() < 0.05
                )
                ejemplares_creados += 1
                
                # Si ya alcanzamos los 5000 ejemplares, detenemos la creación
                if ejemplares_creados >= ejemplares_objetivo:
                    break
            
            if libros_creados % 100 == 0:
                print(f"Creados {libros_creados} libros y {ejemplares_creados} ejemplares...")
                
            # Si ya alcanzamos los 5000 ejemplares, salimos del bucle
            if ejemplares_creados >= ejemplares_objetivo:
                break
                
        # Si ya alcanzamos los objetivos, salimos del bucle principal
        if libros_creados >= 1000 or ejemplares_creados >= ejemplares_objetivo:
            break
    
    # Si no hemos llegado a 1000 libros, añadimos más a autores aleatorios
    while libros_creados < 1000:
        autor = random.choice(autores)
        titulo = fake.sentence(nb_words=3).replace('.', '').title()
        
        libro = Llibre.objects.create(
            titol=titulo,
            titol_original=titulo if random.random() < 0.3 else fake.sentence(nb_words=3).replace('.', '').title(),
            autor=autor,
            CDU=fake.numerify("###.##"),
            signatura=f"LB-{fake.bothify('??###')}",
            data_edicio=fake.date_between(start_date='-50y', end_date='today'),
            resum=fake.paragraph(nb_sentences=5),
            anotacions=fake.paragraph(nb_sentences=2) if random.random() < 0.7 else None,
            mides=f"{random.randint(15, 30)}x{random.randint(20, 40)} cm",
            ISBN=get_unique_isbn(),  # Siempre generamos un ISBN único
            editorial=fake.company(),
            colleccio=fake.word().title() if random.random() < 0.5 else None,
            lloc=fake.city(),
            pais=random.choice(paises),
            llengua=random.choice(lenguas),
            numero=random.randint(1, 10) if random.random() < 0.3 else None,
            volums=random.randint(1, 5) if random.random() < 0.2 else None,
            pagines=random.randint(50, 800) if random.random() < 0.9 else None,
            info_url=fake.url() if random.random() < 0.5 else None,
            preview_url=fake.url() if random.random() < 0.3 else None,
            thumbnail_url=fake.image_url(width=200, height=300) if random.random() < 0.4 else None
        )
        
        cats = random.sample(categorias, random.randint(1, 4))
        libro.tags.set(cats)
        
        libros_creados += 1
        
        if libros_creados % 100 == 0:
            print(f"Creados {libros_creados} libros...")
    
    # Si no hemos llegado a 5000 ejemplares, añadimos más a libros existentes
    if ejemplares_creados < ejemplares_objetivo:
        libros = list(Llibre.objects.all())
        while ejemplares_creados < ejemplares_objetivo:
            libro = random.choice(libros)
            Exemplar.objects.create(
                cataleg=libro,
                registre=f"REG-{fake.bothify('####-####')}",
                exclos_prestec=random.random() < 0.1,
                baixa=random.random() < 0.05
            )
            ejemplares_creados += 1
            
            if ejemplares_creados % 100 == 0:
                print(f"Creados {ejemplares_creados} ejemplares...")
    
    print(f"Final: {libros_creados} libros y {ejemplares_creados} ejemplares")

def crear_otros_materiales():
    print("Creando otros materiales...")
    categorias = list(Categoria.objects.all())
    paises = list(Pais.objects.all())
    lenguas = list(Llengua.objects.all())
    
    # Revistas (50 unidades)
    for i in range(50):
        revista = Revista.objects.create(
            titol=f"Revista {fake.word().capitalize()} {fake.word().capitalize()}",
            data_edicio=fake.date_between(start_date='-20y', end_date='today'),
            resum=fake.paragraph(nb_sentences=3),
            ISSN=fake.bothify("####-####"),
            editorial=fake.company(),
            lloc=fake.city(),
            pais=random.choice(paises),
            llengua=random.choice(lenguas),
            numero=random.randint(1, 100),
            pagines=random.randint(20, 200)
        )
        
        # 1-3 categorías por revista
        cats = random.sample(categorias, random.randint(1, 3))
        revista.tags.set(cats)
        
        # 1-3 ejemplares por revista
        for _ in range(random.randint(1, 3)):
            Exemplar.objects.create(
                cataleg=revista,
                registre=f"REV-{fake.bothify('####-####')}",
                exclos_prestec=True,
                baixa=random.random() < 0.05
            )
    
    # CDs (30 unidades)
    estilos_musicales = ["Pop", "Rock", "Clásica", "Jazz", "Electrónica", "Hip-Hop", "Flamenco", "Salsa"]
    for i in range(30):
        cd = CD.objects.create(
            titol=f"{fake.word().capitalize()} {fake.word().capitalize()}",
            autor=fake.name(),
            data_edicio=fake.date_between(start_date='-30y', end_date='today'),
            discografica=fake.company(),
            estil=random.choice(estilos_musicales),
            duracio=make_aware(datetime.now() + timedelta(minutes=random.randint(30, 120)))
        )
        
        # 1-2 categorías por CD
        cats = random.sample(categorias, random.randint(1, 2))
        cd.tags.set(cats)
        
        # 1-3 ejemplares por CD
        for _ in range(random.randint(1, 3)):
            Exemplar.objects.create(
                cataleg=cd,
                registre=f"CD-{fake.bothify('####-####')}",
                exclos_prestec=random.random() < 0.2,
                baixa=random.random() < 0.05
            )

def crear_centros_y_ciclos():
    print("Creando centros y ciclos formativos...")
    # Centros educativos
    centros = []
    for i in range(5):
        centro = Centre.objects.create(
            nom=f"Instituto {fake.word().capitalize()}"
        )
        centros.append(centro)
    
    # Ciclos formativos
    ciclos = []
    areas = ["Informática", "Administración", "Comercio", "Sanidad", "Diseño"]
    for area in areas:
        for nivel in ["GS", "GM"]:
            cicle = Cicle.objects.create(
                nom=f"{nivel} en {area} {fake.word().capitalize()}"
            )
            ciclos.append(cicle)
    
    return centros, ciclos

def crear_usuarios_y_prestamos():
    print("Creando usuarios y préstamos...")
    centros, ciclos = crear_centros_y_ciclos()
    
    # Crear 50 usuarios
    usuarios = []
    for i in range(50):
        username = fake.user_name()
        usuario = Usuari.objects.create_user(
            username=username,
            email=fake.email(),
            password=make_password(username),  # Contraseña igual al username
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            centre=random.choice(centros),
            cicle=random.choice(ciclos),
            auth_token=fake.md5()
        )
        usuarios.append(usuario)
    
    # Crear préstamos (500 unidades)
    ejemplares = list(Exemplar.objects.filter(baixa=False, exclos_prestec=False))
    
    # Fecha actual para referencia
    current_date = datetime.now().date()
    
    # Crear préstamos
    for i in range(500):
        ejemplar = random.choice(ejemplares)
        usuario = random.choice(usuarios)
        
        # CORRECCIÓN: Generar fecha de préstamo de forma segura (hasta hace 60 días)
        max_days_ago = min(365, (current_date - datetime(2023, 1, 1).date()).days)
        days_ago = random.randint(7, max_days_ago)
        fecha_prestamo = current_date - timedelta(days=days_ago)
        
        # CORRECCIÓN: Asegurar que la fecha de devolución es POSTERIOR a la fecha de préstamo
        # Rango: desde 1 día después hasta la fecha actual
        min_return_date = fecha_prestamo + timedelta(days=1)  # Mínimo 1 día después del préstamo
        
        # Calcular los días entre la fecha mínima de devolución y hoy
        days_range = (current_date - min_return_date).days
        if days_range > 0:
            # Si hay al menos un día de diferencia, elegir una fecha aleatoria en ese rango
            days_after = random.randint(0, days_range)
            fecha_devolucion = min_return_date + timedelta(days=days_after)
        else:
            # Si la fecha mínima ya es hoy o después, usar esa fecha
            fecha_devolucion = min_return_date
        
        # Verificación final para garantizar que fecha_devolucion > fecha_prestamo
        assert fecha_devolucion > fecha_prestamo, f"Error: fecha_devolucion ({fecha_devolucion}) <= fecha_prestamo ({fecha_prestamo})"
        
        # Crear el préstamo
        Prestec.objects.create(
            usuari=usuario,
            exemplar=ejemplar,
            data_prestec=fecha_prestamo,
            data_retorn=fecha_devolucion,
            anotacions=fake.sentence() if random.random() < 0.3 else None
        )
        
        if i % 50 == 0:
            print(f"Creados {i} préstamos...")
    
    # Crear reservas (100 unidades)
    for i in range(100):
        Reserva.objects.create(
            usuari=random.choice(usuarios),
            exemplar=random.choice(ejemplares),
            data=fake.date_between(start_date='-6m', end_date='today')
        )

def main():
    print("=== INICIANDO GENERACIÓN DE DATOS DE PRUEBA ===")
    print("Este proceso puede tardar varios minutos...")
    
    # Limpiar base de datos
    # limpiar_db()
    
    crear_categorias()
    crear_paises_y_lenguas()
    crear_autores_y_libros()
    # crear_otros_materiales()
    crear_usuarios_y_prestamos()
    
    print("=== GENERACIÓN DE DATOS COMPLETADA ===")
    print(f"Total libros creados: {Llibre.objects.count()}")
    print(f"Total ejemplares creados: {Exemplar.objects.count()}")
    print(f"Total usuarios creados: {Usuari.objects.count()}")
    print(f"Total préstamos creados: {Prestec.objects.count()}")

if __name__ == "__main__":
    main()