# backend/firebase.py
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase Admin SDK
cred = credentials.Certificate("backend/credentials/ersathi-fb5vc-firebase-adminsdk-xxx.json")
firebase_admin.initialize_app(cred)

def send_push_notification(device_tokens, title, body, data=None):
    """
    Send a push notification to multiple device tokens.
    :param device_tokens: List of device tokens to send the notification to
    :param title: Notification title
    :param body: Notification body
    :param data: Optional custom data payload
    """
    if not device_tokens:
        print("No device tokens provided.")
        return False

    try:
        # Create a multicast message to send to multiple devices
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            tokens=device_tokens,
            data=data,
        )
        response = messaging.send_multicast(message)
        print(f"Successfully sent notification: {response}")
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False