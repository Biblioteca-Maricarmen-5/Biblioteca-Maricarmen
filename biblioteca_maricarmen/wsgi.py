import os
import sys

# Agrega el directorio base del proyecto
sys.path.append('/var/www/html')

# Setea la variable de entorno del settings de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca_maricarmen.settings')

# Inicializa la aplicación WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
