"""Эндпоинты аутентификации.

Предоставляет API для регистрации, входа и обновления токенов.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.domain import User
from app.core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.core.services.auth_service import AuthService
from app.infrastructure.api.deps import get_db
from app.infrastructure.api.schemas.user import (
    LoginRequest,
    RegisterRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.infrastructure.logging import get_logger

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("api.v1.auth")


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Возвращает сервис аутентификации.

    Args:
        db: Сессия базы данных.

    Returns:
        Экземпляр AuthService.
    """
    from app.infrastructure.database.repositories.user_repo import UserRepository

    user_repo = UserRepository(db)
    return AuthService(user_repo)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
    description="Создает нового пользователя в системе.",
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Регистрирует нового пользователя.

    Args:
        request: Данные для регистрации.
        auth_service: Сервис аутентификации.

    Returns:
        Созданный пользователь.

    Raises:
        HTTPException: Если пользователь с таким email уже существует
                      или пароль не соответствует требованиям.
    """
    try:
        user = await auth_service.register(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )
        logger.info(
            "User registered successfully",
            extra={"user_id": user.id, "email": user.email},
        )
        return user
    except UserAlreadyExistsError as e:
        logger.warning(
            "Registration failed: user already exists",
            extra={"email": request.email},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход в систему",
    description="Аутентифицирует пользователя и возвращает токены.",
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Аутентифицирует пользователя и возвращает токены.

    Args:
        request: Данные для входа.
        auth_service: Сервис аутентификации.

    Returns:
        Пара токенов (access, refresh) и время их жизни.

    Raises:
        HTTPException: Если неверный email или пароль,
                      или пользователь неактивен.
    """
    try:
        token_pair = await auth_service.login(
            email=request.email,
            password=request.password,
        )
        logger.info(
            "User logged in successfully",
            extra={"email": request.email},
        )

        settings = get_settings()
        return TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type="bearer",
            expires_in=settings.security.access_token_expire_minutes * 60,
        )
    except InvalidCredentialsError as e:
        logger.warning(
            "Login failed: invalid credentials",
            extra={"email": request.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except InactiveUserError as e:
        logger.warning(
            "Login failed: user inactive",
            extra={"email": request.email},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновление токена",
    description="Обновляет access токен используя refresh токен.",
)
async def refresh_token(
    request: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Обновляет токены используя refresh токен.

    Args:
        request: Refresh токен.
        auth_service: Сервис аутентификации.

    Returns:
        Новая пара токенов (access, refresh) и время их жизни.

    Raises:
        HTTPException: Если refresh токен невалиден или пользователь неактивен.
    """
    try:
        token_pair = await auth_service.refresh_tokens(request.refresh_token)
        logger.info(
            "Token refreshed successfully",
        )

        settings = get_settings()
        return TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            token_type="bearer",
            expires_in=settings.security.access_token_expire_minutes * 60,
        )
    except InvalidCredentialsError as e:
        logger.warning(
            "Token refresh failed: invalid refresh token",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except InactiveUserError as e:
        logger.warning(
            "Token refresh failed: user inactive",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        ) from e
