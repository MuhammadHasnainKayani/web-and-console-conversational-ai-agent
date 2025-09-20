import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from voiceai_app.routing import websocket_urlpatterns  # Import WebSocket URLs

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "voiceai.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Handles HTTP requests
    "websocket": AuthMiddlewareStack(  # WebSocket requests with authentication
        URLRouter(websocket_urlpatterns)
    ),
})
