# Import the AsyncWebsocketConsumer class from Django Channels
# This allows us to handle WebSocket connections asynchronously
from channels.generic.websocket import AsyncWebsocketConsumer

# Import json so we can send and receive JSON messages
import json


# Create a WebSocket consumer class for WebRTC signaling
class CallConsumer(AsyncWebsocketConsumer):

    # This function runs when a WebSocket client connects
    async def connect(self):

        # Get the device_id from the WebSocket URL
        # Example URL: ws://server/ws/call/12/
        # Here device_id = 12
        self.device_id = self.scope["url_route"]["kwargs"]["device_id"]

        # Create a unique room name for this device
        # This ensures only camera + viewer for this device communicate
        self.room_group_name = f"call_{self.device_id}"

        # Add this WebSocket connection to the room group
        # This allows messages to be broadcast to everyone in the room
        await self.channel_layer.group_add(
            self.room_group_name,  # group name
            self.channel_name      # unique id for this connection
        )

        # Accept the WebSocket connection
        await self.accept()

        # Notify others in the room that a peer has joined so the camera can send an offer
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "signal_message",
                "message": json.dumps({"type": "peer_joined"}),
                "sender": self.channel_name
            }
        )


    # This function runs when the WebSocket disconnects
    async def disconnect(self, close_code):

        # Remove this WebSocket connection from the room group
        # This prevents sending messages to disconnected clients
        await self.channel_layer.group_discard(
            self.room_group_name,  # group name
            self.channel_name      # connection id
        )


    # This function runs whenever the client sends a WebSocket message
    async def receive(self, text_data):

        # Broadcast the received message to everyone in the same room
        await self.channel_layer.group_send(
            self.room_group_name,  # send to this room
            {
                "type": "signal_message",  # tells Django which method to call
                "message": text_data,      # the actual WebRTC signal
                "sender": self.channel_name # who sent it
            }
        )


    # This function receives messages from group_send
    async def signal_message(self, event):

        # Send the message back to the WebSocket client ONLY if they didn't send it
        # This forwards WebRTC signaling data between peers
        if self.channel_name != event.get("sender"):
            await self.send(
                text_data=event["message"]  # send original message
            )