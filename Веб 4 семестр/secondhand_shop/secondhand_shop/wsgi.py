"""WSGI-конфигурация для запуска проекта на сервере."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secondhand_shop.settings')

application = get_wsgi_application()
