import json
#from django.contrib.auth.models import User
#from .models import PersonAccount
from channels.generic.websocket import AsyncWebsocketConsumer
#from django.contrib.auth.models import User

class LiveStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'livestream'
        self.room_group_name = 'livestream_group'

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

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        message_type = text_data_json.get('type', 'chat')  # Default to 'chat' if no type is provided
        # user_data = self.scope.get('user').username  # Fetch user data (username)
        user = self.scope.get('user')
        if(user.first_name):
            first_name = user.first_name
        else:
            first_name = 'Anonymous'
        
        # account_type = 'Seller'
        # acc_profile = PersonAccount.objects.filter(user=user).first()
        # if acc_profile:
        #     account_type = acc_profile.usertype

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'livestream_message',
                'message': message,
                'message_type': message_type,
                'user': first_name,
                # 'account_type' : account_type,
            }
        )

    async def livestream_message(self, event):
        message = event['message']
        message_type = event['message_type']
        user_data = event.get('user', 'Anonymous')  # Get user data from the event or default to 'Anonymous'
        # account_type = event['account_type']
        await self.send(text_data=json.dumps({
            'message': message,
            'type': message_type,
            'user': user_data,
            # 'account_type' : account_type,
        }))
