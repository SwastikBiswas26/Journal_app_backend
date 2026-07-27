import jwt
from datetime import datetime, timedelta, timezone
from config import Config

def generate_token(user_id):
    """
    Generates a JWT signed token for a given user_id.
    """
    payload = {
        "user_id": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

def decode_token(token):
    """
    Decodes a JWT token using SECRET_KEY.
    Returns (payload, None) on success or (None, error_message) on failure.
    """
    if not token or not isinstance(token, str):
        return None, "Token is missing or invalid type!"

    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired! Please log in again."
    except jwt.InvalidTokenError:
        return None, "Invalid token format!"
    except Exception as e:
        return None, f"Token verification error: {str(e)}"

def extract_token_from_header(auth_header):
    """
    Extracts Bearer token string from Authorization header safely.
    Format: 'Bearer <token>' or '<token>'
    """
    if not auth_header or not isinstance(auth_header, str):
        return None

    parts = auth_header.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    elif len(parts) == 1:
        return parts[0]
    return None
