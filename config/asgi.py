"""ASGI entry point (not used in production; kept for completeness)."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_asgi_application()
