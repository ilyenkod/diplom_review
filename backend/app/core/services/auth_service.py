"""
Сервис аутентификации.

Предоставляет функции для регистрации, аутентификации и работы с токенами.
"""

from dataclasses import dataclass

from app.config import get_settings
from app.core.const import UserRole
from app.core.domain import User
from app.core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    ValidationError,
)
from app.core.interfaces.database import UserRepository
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_access_token as security_validate_access_token,
    validate_password_strength,
    validate_refresh_token as security_validate_refresh_token,
    verify_password,
)


@dataclass
class TokenPair:
    """Пара access и refresh токенов."""

    access_token: str
    refresh_token: str


@dataclass
class TokenPayload:
    """Данные из JWT токена."""

    user_id: str
    role: str


class AuthService:
    """Сервис для работы с аутентификацией."""

    def __init__(self, user_repo: UserRepository) -> None:
        """Инициализирует сервис аутентификации.

        Args:
            user_repo: Репозиторий пользователей.
        """
        self._user_repo = user_repo

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
    ) -> User:
        """Регистрирует нового пользователя.

        Args:
            email: Email пользователя.
            password: Пароль.
            full_name: Полное имя пользователя.

        Returns:
            Созданный пользователь.

        Raises:
            UserAlreadyExistsError: Если пользователь с таким email уже существует.
            ValidationError: Если пароль не соответствует требованиям.
        """
        # Проверяем, что пользователь с таким email не существует
        existing_user = await self._user_repo.get_by_email(email)
        if existing_user is not None:
            raise UserAlreadyExistsError(email)

        # Валидируем сложность пароля
        if not validate_password_strength(password):
            raise ValidationError(
                f"Password is too short. Minimum length: {get_settings().security.password_min_length}"
            )

        # Создаем нового пользователя
        hashed_password = hash_password(password)
        user = User(
            id=self._generate_user_id(),
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            role=UserRole.STUDENT,
        )

        return await self._user_repo.create(user)

    async def login(
        self,
        email: str,
        password: str,
    ) -> TokenPair:
        """Аутентифицирует пользователя и возвращает токены.

        Args:
            email: Email пользователя.
            password: Пароль.

        Returns:
            Пара токенов (access, refresh).

        Raises:
            InvalidCredentialsError: Если неверный email или пароль.
            InactiveUserError: Если пользователь неактивен.
        """
        # Получаем пользователя по email
        user = await self._user_repo.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError()

        # Проверяем пароль
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        # Проверяем активность
        if not user.is_active:
            raise InactiveUserError()

        # Создаем токены
        payload = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
        }
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def validate_access_token(self, token: str) -> TokenPayload | None:
        """Валидирует access токен.

        Args:
            token: JWT access токен.

        Returns:
            Payload с данными пользователя или None если токен невалиден.
        """
        payload = security_validate_access_token(token)
        if payload is None:
            return None

        user_id = payload.get("sub")
        if user_id is None:
            return None

        return TokenPayload(
            user_id=user_id,
            role=payload.get("role", UserRole.STUDENT),
        )

    async def validate_refresh_token(self, token: str) -> TokenPayload | None:
        """Валидирует refresh токен.

        Args:
            token: JWT refresh токен.

        Returns:
            Payload с данными пользователя или None если токен невалиден.
        """
        payload = security_validate_refresh_token(token)
        if payload is None:
            return None

        user_id = payload.get("sub")
        if user_id is None:
            return None

        return TokenPayload(
            user_id=user_id,
            role=payload.get("role", UserRole.STUDENT),
        )

    async def refresh_tokens(self, refresh_token: str) -> TokenPair:
        """Обновляет токены используя refresh токен.

        Args:
            refresh_token: JWT refresh токен.

        Returns:
            Новая пара токенов (access, refresh).

        Raises:
            InvalidCredentialsError: Если refresh токен невалиден.
        """
        # Валидируем refresh токен
        payload = await self.validate_refresh_token(refresh_token)
        if payload is None:
            raise InvalidCredentialsError()

        # Получаем пользователя
        user = await self._user_repo.get_by_id(payload.user_id)
        if user is None:
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError()

        # Создаем новые токены
        new_payload = {
            "sub": user.id,
            "email": user.email,
            "role": user.role,
        }
        access_token = create_access_token(new_payload)
        new_refresh_token = create_refresh_token(new_payload)

        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    def _generate_user_id(self) -> str:
        """Генерирует уникальный ID пользователя.

        Returns:
            Уникальный ID пользователя.
        """
        import uuid

        return str(uuid.uuid4())
