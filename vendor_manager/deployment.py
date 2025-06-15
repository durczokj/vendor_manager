import os
from .settings import *
from .settings import BASE_DIR

ALLOWED_HOSTS = [os.environ.get("WEBSITE_HOSTNAME")]
CSRF_TRUSTED_ORIGINS = [f"https://{os.environ.get('WEBSITE_HOSTNAME')}"]
DEBUG = True

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

DATABASES = {
    'default': {
        'ENGINE': "mssql",
        'NAME': "vendor_manager",
        'USER': "jakubdurczok",
        'PASSWORD': 'Wynalazek3D!',
        'HOST': 'serverjd107950.database.windows.net',
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
    }
}
}