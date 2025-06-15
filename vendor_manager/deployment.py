import os
from .settings import *
from .settings import BASE_DIR

ALLOWED_HOSTS = [os.environ.get("WEBSITE_HOSTNAME")]
CSRF_TRUSTED_ORIGINS = [f"https://{os.environ.get('WEBSITE_HOSTNAME')}"]
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': os.environ.get("DATABASE_ENGINE"),
        'NAME': os.environ.get("DATABASE_NAME"),
        'USER': os.environ.get("DATABASE_USERNAME"),
        'PASSWORD': os.environ.get("DATABASE_PASSWORD"),
        'HOST': os.environ.get("DATABASE_HOST"),
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
    }
}
}