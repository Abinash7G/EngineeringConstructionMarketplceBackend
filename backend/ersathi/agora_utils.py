# # # # import time
# # # # from agora_token_builder import RtmTokenBuilder

# # # # AGORA_APP_ID = '8238e00c51e248bebdab0d0083cb9161'
# # # # AGORA_APP_CERTIFICATE = '52c49d030d30475996d565b282b1e409'


# # # # def generate_agora_rtm_token(user_id):
# # # #     """
# # # #     Generate an Agora RTM token for a user.
# # # #     """
# # # #     expiration_time_in_seconds = 3600  # 1 hour
# # # #     current_timestamp = int(time.time())
# # # #     privilege_expired_ts = current_timestamp + expiration_time_in_seconds

# # # #     try:
# # # #         token = RtmTokenBuilder.buildToken(
# # # #             AGORA_APP_ID,
# # # #             AGORA_APP_CERTIFICATE,
# # # #             user_id,
# # # #             privilege_expired_ts
# # # #         )
# # # #         return token
# # # #     except Exception as e:
# # # #         raise Exception(f"Failed to generate Agora RTM token: {str(e)}")



# # # import time
# # # from AgoraDynamicKey.src.RtmTokenBuilder import RtmTokenBuilder, Role

# # # AGORA_APP_ID = '8238e00c51e248bebdab0d0083cb9161'
# # # AGORA_APP_CERTIFICATE = '52c49d030d30475996d565b282b1e409'


# # # def generate_agora_rtm_token(user_id):
# # #     """
# # #     Generate an Agora RTM token for a user using AgoraDynamicKey.
# # #     """
# # #     expiration_time_in_seconds = 3600  # 1 hour
# # #     current_timestamp = int(time.time())
# # #     privilege_expired_ts = current_timestamp + expiration_time_in_seconds

# # #     try:
# # #         token = RtmTokenBuilder.buildToken(
# # #             AGORA_APP_ID,
# # #             AGORA_APP_CERTIFICATE,
# # #             user_id,
# # #             Role.Rtm_User,
# # #             privilege_expired_ts
# # #         )
# # #         return token
# # #     except Exception as e:
# # #         raise Exception(f"Failed to generate Agora RTM token: {str(e)}")
# # import time
# # import sys
# # import os

# # # Add the AgoraDynamicKey directory to the Python path
# # sys.path.append(os.path.abspath(os.path.join(os.path.dirname('backend\Tools\DynamicKey\AgoraDynamicKey\python'), 'AgoraDynamicKey')))
# # from src.RtmTokenBuilder import RtmTokenBuilder, Role

# # AGORA_APP_ID = '8238e00c51e248bebdab0d0083cb9161'
# # AGORA_APP_CERTIFICATE = '52c49d030d30475996d565b282b1e409'


# # def generate_agora_rtm_token(user_id):
# #     """
# #     Generate an Agora RTM token for a user using AgoraDynamicKey.
# #     """
# #     expiration_time_in_seconds = 3600  # 1 hour
# #     current_timestamp = int(time.time())
# #     privilege_expired_ts = current_timestamp + expiration_time_in_seconds

# #     try:
# #         token = RtmTokenBuilder.buildToken(
# #             AGORA_APP_ID,
# #             AGORA_APP_CERTIFICATE,
# #             user_id,
# #             Role.Rtm_User,
# #             privilege_expired_ts
# #         )
# #         return token
# #     except Exception as e:
# #         raise Exception(f"Failed to generate Agora RTM token: {str(e)}")



# import time
# import sys
# import os

# # Add the AgoraDynamicKey directory to the Python path
# # agora_utils.py is in backend/ersathi/, so go up one directory to backend/, then into Tools/DynamicKey/AgoraDynamicKey/python3
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Tools', 'DynamicKey', 'AgoraDynamicKey', 'python3')))
# from src.RtmTokenBuilder import RtmTokenBuilder

# AGORA_APP_ID = '8238e00c51e248bebdab0d0083cb9161'
# AGORA_APP_CERTIFICATE = '52c49d030d30475996d565b282b1e409'


# def generate_agora_rtm_token(user_id):
#     """
#     Generate an Agora RTM token for a user using AgoraDynamicKey.
#     """
#     expiration_time_in_seconds = 3600  # 1 hour
#     current_timestamp = int(time.time())
#     privilege_expired_ts = current_timestamp + expiration_time_in_seconds

#     try:
#         token = RtmTokenBuilder.buildToken(
#             AGORA_APP_ID,
#             AGORA_APP_CERTIFICATE,
#             user_id,
#             privilege_expired_ts
#         )
#         return token
#     except Exception as e:
#         raise Exception(f"Failed to generate Agora RTM token: {str(e)}")

