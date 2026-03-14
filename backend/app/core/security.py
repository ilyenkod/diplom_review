"""
Модуль безопасности приложения.

Предоставляет функции для хеширования паролей, работы с JWT токенами и валидации.
"""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from jose import JWTError, jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext

from app.config import settings

if TYPE_CHECKING:
    from passlib.context import CryptContext as CryptContextType

# Настройка хеширования паролей
pwd_context: CryptContextType = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хеширует пароль.

    Args:
        password: Пароль в открытом виде.

    Returns:
        Хешированный пароль.
    """
    return pwd_context.hash(password)  # type: ignore[no-any-return]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль.

    Args:
        plain_password: Пароль в открытом виде.
        hashed_password: Хешированный пароль.

    Returns:
        True если пароли совпадают, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)  # type: ignore[no-any-return]


def create_access_token(
    payload: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Создает JWT access токен.

    Args:
        payload: Данные для кодирования в токен.
        expires_delta: Время жизни токена.

    Returns:
        Закодированный JWT токен.
    """
    to_encode = payload.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.security.access_token_expire_minutes,
        )

    to_encode.update({"exp": expire, "type": "access"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.secret_key,
        algorithm=settings.security.algorithm,
    )
    return encoded_jwt  # type: ignore[no-any-return]


def create_refresh_token(
    payload: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Создает JWT refresh токен.

    Args:
        payload: Данные для кодирования в токен.
        expires_delta: Время жизни токена.

    Returns:
        Закодированный JWT токен.
    """
    to_encode = payload.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            days=settings.security.refresh_token_expire_days,
        )

    to_encode.update({"exp": expire, "type": "refresh"})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.secret_key,
        algorithm=settings.security.algorithm,
    )
    return encoded_jwt  # type: ignore[no-any-return]


def decode_token(token: str) -> dict[str, Any] | None:
    """Декодирует JWT токен.

    Args:
        token: JWT токен.

    Returns:
        Декодированные данные токена или None при ошибке.
    """
    try:
        payload = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm],
        )
        return payload  # type: ignore[no-any-return]
    except JWTError:
        return None


def validate_access_token(token: str) -> dict[str, Any] | None:
    """Валидирует access токен.

    Args:
        token: JWT токен.

    Returns:
        Декодированные данные токена или None при ошибке.
    """
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.get("type") != "access":
        return None

    return payload


def validate_refresh_token(token: str) -> dict[str, Any] | None:
    """Валидирует refresh токен.

    Args:
        token: JWT токен.

    Returns:
        Декодированные данные токена или None при ошибке.
    """
    payload = decode_token(token)

    if payload is None:
        return None

    if payload.get("type") != "refresh":
        return None

    return payload


def extract_user_id_from_token(token: str) -> str | None:
    """Извлекает ID пользователя из токена.

    Args:
        token: JWT токен.

    Returns:
        ID пользователя или None при ошибке.
    """
    payload = decode_token(token)
    if payload is None:
        return None
    return payload.get("sub")


def extract_role_from_token(token: str) -> str | None:
    """Извлекает роль пользователя из токена.

    Args:
        token: JWT токен.

    Returns:
        Роль пользователя или None при ошибке.
    """
    payload = decode_token(token)
    if payload is None:
        return None
    return payload.get("role")


def is_token_expired(token: str) -> bool:
    """Проверяет, истек ли токен.

    Args:
        token: JWT токен.

    Returns:
        True если токен истек, иначе False.
    """
    payload = decode_token(token)
    if payload is None:
        return True

    exp = payload.get("exp")
    if exp is None:
        return True

    now = datetime.now(UTC).timestamp()
    return now > (exp or 0)


def validate_password_strength(password: str) -> bool:
    """Валидирует сложность пароля.

    Args:
        password: Пароль для проверки.

    Returns:
        True если пароль достаточно сложный, иначе False.
    """
    min_length = settings.security.password_min_length

    return len(password) >= min_length
