from django.urls import path
from .views import create_pairing_token, claim_device, list_devices

urlpatterns = [
    path('pairing-token/', create_pairing_token, name='pairing_token'),
    path('devices/claim/', claim_device, name='claim_device'),
    path('devices/', list_devices, name='list_devices'),
]
