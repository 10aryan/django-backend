from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Device, PairingToken
from .serializers import DeviceSerializer
import random

# Generate pairing token (Viewer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_pairing_token(request):
    token = str(random.randint(100000, 999999))
    PairingToken.objects.create(
        user=request.user,
        token=token,
        expires_at=timezone.now() + timedelta(minutes=5)
    )
    return Response({"pairing_token": token, "expires_in": 300})

# Claim device (Camera)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claim_device(request):
    data = request.data
    token = data.get('token')
    name = data.get('name', 'Unnamed Camera')

    if not token:
        return Response({"success": False, "error": "Token required"}, status=400)

    try:
        pairing = PairingToken.objects.get(token=token, expires_at__gte=timezone.now())
        Device.objects.create(user=pairing.user, name=name, is_online=True)
        pairing.delete()  # consume token
        return Response({"success": True})
    except PairingToken.DoesNotExist:
        return Response({"success": False, "error": "Invalid or expired token"}, status=400)

# List devices for logged-in user (Viewer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_devices(request):
    devices = Device.objects.filter(user=request.user)
    serializer = DeviceSerializer(devices, many=True)
    return Response(serializer.data)
