# # consumers.py
# from channels.generic.websocket import AsyncWebsocketConsumer
# from channels.db import database_sync_to_async
# from rest_framework_simplejwt.tokens import AccessToken
# from django.contrib.auth import get_user_model
# import json

# class InquiryConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.company_id = self.scope['url_route']['kwargs']['company_id']
#         self.group_name = f'company_{self.company_id}_inquiries'
        
#         # Get token from query parameters
#         query_params = self.scope['query_string'].decode()
#         token = None
#         for param in query_params.split('&'):
#             if param.startswith('token='):
#                 token = param.split('=')[1]
#                 break

#         if not token:
#             await self.close(code=4001)
#             return

#         try:
#             # Validate JWT token
#             access_token = AccessToken(token)
#             user_id = access_token['user_id']
#             user = await self.get_user(user_id)
            
#             if not user:
#                 await self.close(code=4002)
#                 return

#             # Join channel group
#             await self.channel_layer.group_add(
#                 self.group_name,
#                 self.channel_name
#             )
#             await self.accept()
            
#         except Exception as e:
#             print(f"Connection error: {str(e)}")
#             await self.close(code=4003)

#     @database_sync_to_async
#     def get_user(self, user_id):
#         return get_user_model().objects.filter(id=user_id).first()

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.group_name,
#             self.channel_name
#         )

#     async def inquiry_update(self, event):
#         await self.send(text_data=json.dumps(event))