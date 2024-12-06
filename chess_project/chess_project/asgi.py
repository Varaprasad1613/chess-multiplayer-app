import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chess_project.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
import game.routing

from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

application = ProtocolTypeRouter({
    "http": ASGIStaticFilesHandler(get_asgi_application()),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            game.routing.websocket_urlpatterns
        )
    ),
})
