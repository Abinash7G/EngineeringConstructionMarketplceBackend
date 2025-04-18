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

