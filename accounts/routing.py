from django.urls import re_path
from accounts import consumers

websocket_urlpatterns = [
    re_path(r'ws/livestream/$', consumers.LiveStreamConsumer.as_asgi()),
]
