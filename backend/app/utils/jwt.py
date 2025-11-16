import jwt
from datetime import datetime, timedelta
from app.core.config import settings


def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode JWT token and return payload

    Args:
        token: JWT token string

    Returns:
        dict: Token payload

    Raises:
        jwt.PyJWTError: If token is invalid
    """
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=["HS256"]
    )