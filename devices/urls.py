from django.urls import path
from django.shortcuts import redirect
from .views import create_pairing_token, claim_device, list_devices, device_heartbeat

urlpatterns = [
    path('', lambda request: redirect('devices/')),  # <-- redirect root API
    path('pairing-token/', create_pairing_token),
    path('devices/claim/', claim_device),
    path('devices/', list_devices),
    path('devices/heartbeat/', device_heartbeat),
]
