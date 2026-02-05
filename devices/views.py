import random
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Device, PairingToken
from .serializers import DeviceSerializer
from rest_framework.permissions import AllowAny

# Generate pairing token (Viewer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_pairing_token(request):
    token = str(random.randint(100000, 999999))
    PairingToken.objects.create(
        token=token,
        user=request.user,
        expires_at=timezone.now() + timedelta(minutes=5)
    )
    return Response({"pairing_token": token, "expires_in": 300})

# Camera claims device
@api_view(['POST'])
@permission_classes([AllowAny]) 
def claim_device(request):
    token_value = request.data.get("token")
    name = request.data.get("name", "DIY Camera")

    if not token_value:
        return Response({"error": "Token required"}, status=400)

    try:
        pairing = PairingToken.objects.get(token=token_value)
    except PairingToken.DoesNotExist:
        return Response({"error": "Invalid token"}, status=400)

    if not pairing.is_valid():
        return Response({"error": "Token expired or used"}, status=400)

    device = Device.objects.create(
        user=pairing.user,
        name=name,
        is_online=True,
        last_seen=timezone.now()
    )

    pairing.used = True
    pairing.save()

    return Response({
        "device_id": str(device.id),
        "message": "Device paired successfully"
    })

# List devices (Viewer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_devices(request):
    devices = Device.objects.filter(user=request.user)
    serializer = DeviceSerializer(devices, many=True)
    return Response(serializer.data)

# Heartbeat (Camera)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def device_heartbeat(request):
    device_id = request.data.get("device_id")
    try:
        device = Device.objects.get(id=device_id, user=request.user)
    except Device.DoesNotExist:
        return Response({"error": "Unauthorized"}, status=403)

    device.last_seen = timezone.now()
    device.is_online = True
    device.save()
    return Response({"status": "ok"})
