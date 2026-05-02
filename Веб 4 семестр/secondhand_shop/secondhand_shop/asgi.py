"""ASGI-конфигурация для асинхронного запуска проекта."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'secondhand_shop.settings')

application = get_asgi_application()
