import os

import pymysql

pymysql.install_as_MySQLdb()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myapp.settings')

import django
django.setup()

# Force database connection in sync context before entering async ASGI loop.
# Without this, Django's MySQL backend lazy-init (mysql_server_info) may raise
# SynchronousOnlyOperation when called inside an async context by channels.
from django.db import connections
connections['default'].ensure_connection()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

django_asgi_app = get_asgi_application()
static_app = ASGIStaticFilesHandler(django_asgi_app)

import myapp.chat.routing
import myapp.members.routing

application = ProtocolTypeRouter({
    'http': static_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            myapp.chat.routing.websocket_urlpatterns
            + myapp.members.routing.websocket_urlpatterns
        )
    ),
})
