from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import Device, PairingToken
from .serializers import DeviceSerializer
import secrets


# -------------------------------------------------
# POST API
# Used by Viewer app to create a temporary pairing code
# Viewer must be logged in
# -------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_pairing_token(request):
    # Delete old expired tokens from database
    PairingToken.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()

    # Create 6 character random token, example: A1B2C3
    token = secrets.token_hex(3).upper()

    # Save token in database for current logged-in user
    PairingToken.objects.create(
        user=request.user,
        token=token,
        expires_at=timezone.now() + timedelta(minutes=5),
        used=False
    )

    # Return token to viewer app
    return Response({
        "pairing_token": token,
        "expires_in": 300
    })


# -------------------------------------------------
# POST API
# Used by Camera app to register/connect using token
# Camera sends token and camera name
# -------------------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claim_device(request):
    # Get token sent by camera app
    token = request.data.get("token")

    # Get camera name, if not sent use default name
    name = request.data.get("name", "Unnamed Camera")

    # If token is missing, return error
    if not token:
        return Response(
            {"success": False, "error": "Token required"},
            status=400
        )

    # Check token is valid, not used, and not expired
    pairing = PairingToken.objects.filter(
        token=token,
        used=False,
        expires_at__gte=timezone.now()
    ).first()

    # If token is invalid/expired, reject camera
    if not pairing:
        return Response(
            {"success": False, "error": "Invalid or expired token"},
            status=400
        )

    # Create new camera device under the user who generated token
    device = Device.objects.create(
        user=pairing.user,
        name=name,
        is_online=True,
        last_seen=timezone.now()
    )

    # Mark token as used so it cannot be reused
    pairing.used = True
    pairing.save()

    # Return device_id and secret_key to camera
    # Camera must save both for automatic reconnect
    return Response({
        "success": True,
        "device_id": device.id,
        "secret_key": str(device.secret_key)
    })


# If heartbeat is not received for 15 seconds,
# device will be considered offline
OFFLINE_AFTER = timedelta(seconds=15)


# -------------------------------------------------
# GET API
# Used by Viewer app to get all cameras of logged-in user
# Also updates offline status before returning list
# -------------------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_devices(request):
    # Mark old online devices as offline
    # If last_seen is older than 15 seconds
    Device.objects.filter(
        user=request.user,
        last_seen__lt=timezone.now() - OFFLINE_AFTER,
        is_online=True
    ).update(is_online=False)

    # Get all devices of logged-in user
    devices = Device.objects.filter(user=request.user)

    # Convert device objects into JSON
    serializer = DeviceSerializer(devices, many=True)

    # Return device list to viewer app
    return Response(serializer.data)


# -------------------------------------------------
# POST API
# Used to create/register a new user account
# Anyone can access this API
# -------------------------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    # Get username and password from request
    username = request.data.get("username")
    password = request.data.get("password")

    # Check required fields
    if not username or not password:
        return Response(
            {"error": "Username and password required"},
            status=400
        )

    # Check if user already exists
    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "User exists"},
            status=400
        )

    # Create user with hashed password
    User.objects.create_user(
        username=username,
        password=password
    )

    # Return success message
    return Response(
        {"message": "User created"},
        status=201
    )


# -------------------------------------------------
# POST API
# Used by Camera app again and again
# Camera sends device_id and secret_key every few seconds
# This keeps the camera online
# -------------------------------------------------
@api_view(['POST'])
def device_heartbeat(request):
    # Get device_id and secret_key from camera
    device_id = request.data.get("device_id")
    secret_key = request.data.get("secret_key")

    # Both are required
    if not device_id or not secret_key:
        return Response(
            {"error": "device_id and secret_key required"},
            status=400
        )

    try:
        # Verify device using id and secret_key
        device = Device.objects.get(
            id=device_id,
            secret_key=secret_key
        )

        # Update last_seen time
        device.last_seen = timezone.now()

        # Mark device online
        device.is_online = True

        # Save only changed fields
        device.save(
            update_fields=["last_seen", "is_online"]
        )

        # Tell camera heartbeat received
        return Response({"status": "alive"})

    except Device.DoesNotExist:
        return Response(
            {"error": "Device not found"},
            status=404
        )