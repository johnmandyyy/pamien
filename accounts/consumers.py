import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LiveStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'stream_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data and not bytes_data:
            raise ValueError("You must pass one of bytes_data or text_data")

        if text_data:
            text_data_json = json.loads(text_data)
            message = text_data_json['message']
            message_type = text_data_json.get('type', 'chat')

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'livestream_message',
                    'message': message,
                    'message_type': message_type,
                }
            )
        elif bytes_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'livestream_message',
                    'bytes': bytes_data
                }
            )

    async def livestream_message(self, event):
        if 'message' in event:
            message = event['message']
            message_type = event.get('message_type', 'chat')

            await self.send(text_data=json.dumps({
                'message': message,
                'type': message_type,
            }))
        elif 'bytes' in event:
            bytes_data = event['bytes']
            await self.send(bytes_data=bytes_data)
