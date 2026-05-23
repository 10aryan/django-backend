# Import re_path for regex-based URL routing
from django.urls import re_path

# Import the WebRTC consumer
from .consumers import CallConsumer


# List of WebSocket routes
websocket_urlpatterns = [

    # Route for WebRTC signaling
    # Example connection URL:
    # ws://server/ws/call/12/
    # where 12 is the device ID
    re_path(
        r'ws/call/(?P<device_id>\d+)/$',  # capture device_id from URL
        CallConsumer.as_asgi()            # attach WebSocket consumer
    ),
]