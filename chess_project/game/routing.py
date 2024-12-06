# routing.py

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/lobby/', consumers.LobbyConsumer.as_asgi()),
    path('ws/game/<int:game_id>/', consumers.GameConsumer.as_asgi()),
]
