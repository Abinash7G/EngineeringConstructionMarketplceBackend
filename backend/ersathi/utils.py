from itsdangerous import URLSafeTimedSerializer

# Configure a secret key (use a strong, unique key)
SECRET_KEY = "2e14a6352c97c2fe33315af6804d89d474432d4d5835326005d55695fd8a4274"
SALT = "c3d00104b56828f98d4592e81dba0ece"

def generate_verification_token(email):
    """
    Generate a token for email verification.
    """
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=SALT)

def verify_verification_token(token, expiration=3600):
    """
    Verify the token and return the email if valid.
    :param token: The token to verify.
    :param expiration: Expiry time in seconds.
    """
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt=SALT, max_age=expiration)
        return email
    except Exception as e:
        return None  # Token is invalid or expired

# from django.db.models import Q
# from .models import Inquiry, Order, PaymentDistribution, Company, CustomUser

# def can_user_chat_with_company(user, company):
#     """
#     Check if a user can chat with a company based on inquiries or orders.
#     """
#     has_inquiry = Inquiry.objects.filter(user=user, company=company).exists()
#     has_order = PaymentDistribution.objects.filter(order__user=user, company=company).exists()
#     return has_inquiry or has_order

# def can_user_chat_with_admin(user):
#     """
#     Check if a user can chat with platform admin (must have inquiry or order).
#     """
#     has_inquiry = Inquiry.objects.filter(user=user).exists()
#     has_order = Order.objects.filter(user=user).exists()
#     return has_inquiry or has_order

# def can_company_chat_with_admin(company):
#     """
#     Companies can always chat with platform admins.
#     """
#     return True

# def can_admin_chat_with_user(admin, user):
#     """
#     Admins can chat with any user who has an inquiry or order.
#     """
#     return can_user_chat_with_admin(user)

# def can_admin_chat_with_company(admin, company):
#     """
#     Admins can chat with any company.
#     """
#     return True