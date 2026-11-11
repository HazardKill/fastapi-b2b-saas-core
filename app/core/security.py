from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from database import settings

# Сучасний хешер паролів на базі Argon2
password_hash = PasswordHash.recommended()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевірка відповідності пароля хешу."""
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Генерація безпечного хешу пароля."""
    return password_hash.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Генерація JWT access-токена для авторизації запитів."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=30)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")