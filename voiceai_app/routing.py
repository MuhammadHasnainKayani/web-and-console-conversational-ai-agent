# chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # This URL will be used by your frontend WebSocket connection.
    re_path(r'^ws/voiceagent/$', consumers.VoiceAgentConsumer.as_asgi()),
]
