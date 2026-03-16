"""Зависимости для внедрения в FastAPI endpoints."""

from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain.user import User
from app.core.interfaces.cache import CacheClient
from app.core.interfaces.database import SessionManager
from app.core.interfaces.llm import LLMClient
from app.core.security import (
    validate_access_token,
)
from app.infrastructure.logging import get_logger

logger = get_logger("api.deps")

# Singleton instances (будут инициализированы через композиты)
_session_manager: SessionManager | None = None
_cache_client: CacheClient | None = None
_llm_client: LLMClient | None = None
_user_repo_context = None


def set_dependencies(
    session_manager: SessionManager,
    cache_client: CacheClient,
    llm_client: LLMClient,
) -> None:
    """Устанавливает зависимости для внедрения.

    Args:
        session_manager: Менеджер сессий базы данных.
        cache_client: Клиент кэша.
        llm_client: Клиент LLM.
    """
    global _session_manager, _cache_client, _llm_client
    _session_manager = session_manager
    _cache_client = cache_client
    _llm_client = llm_client


def get_session_manager() -> SessionManager:
    """Возвращает менеджер сессий базы данных.

    Returns:
        Менеджер сессий.

    Raises:
        RuntimeError: Если зависимости не инициализированы.
    """
    if _session_manager is None:
        msg = "Session manager not initialized. Call set_dependencies first."
        raise RuntimeError(msg)
    return _session_manager


def get_cache_client() -> CacheClient:
    """Возвращает клиент кэша.

    Returns:
        Клиент кэша.

    Raises:
        RuntimeError: Если зависимости не инициализированы.
    """
    if _cache_client is None:
        msg = "Cache client not initialized. Call set_dependencies first."
        raise RuntimeError(msg)
    return _cache_client


def get_llm_client_dependency() -> LLMClient:
    """Возвращает клиент LLM.

    Returns:
        Клиент LLM.

    Raises:
        RuntimeError: Если зависимости не инициализированы.
    """
    if _llm_client is None:
        msg = "LLM client not initialized. Call set_dependencies first."
        raise RuntimeError(msg)
    return _llm_client


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """Возвращает сессию базы данных.

    Yields:
        Сессия базы данных.

    Example:
        @app.get("/users/{user_id}")
        async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
            user = await db.get(User, user_id)
            return user
    """
    session_manager = get_session_manager()
    async with session_manager.get_session() as session:
        yield session


async def get_cache() -> CacheClient:
    """Возвращает клиент кэша.

    Returns:
        Клиент кэша.

    Example:
        @app.get("/users/{user_id}")
        async def get_user(user_id: str, cache: CacheClient = Depends(get_cache)):
            cached_user = await cache.get(f"user:{user_id}")
            return cached_user
    """
    return get_cache_client()


def get_llm_client() -> LLMClient:
    """Возвращает клиент LLM.

    Returns:
        Клиент LLM.

    Example:
        @app.post("/analyze")
        async def analyze(
            text: str,
            llm: LLMClient = Depends(get_llm_client),
        ):
            result = await llm.completion(text)
            return result
    """
    return get_llm_client_dependency()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Возвращает текущего аутентифицированного пользователя.

    Args:
        credentials: HTTP авторизационные данные.
        db: Сессия базы данных.

    Returns:
        Текущий пользователь.

    Raises:
        HTTPException: Если пользователь не авторизован или неактивен.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Проверяем наличие токена
    if credentials is None:
        logger.warning("No credentials provided")
        raise credentials_exception

    # Валидируем токен
    token = credentials.credentials
    payload = validate_access_token(token)

    if payload is None:
        logger.warning(
            "Invalid token", extra={"token": token[:20] + "..." if len(token) > 20 else token}
        )
        raise credentials_exception

    # Извлекаем ID пользователя
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("No user_id in token payload")
        raise credentials_exception

    # Загружаем пользователя из БД
    from app.core.interfaces.database import UserRepository

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        logger.warning("User not found", extra={"user_id": user_id})
        raise credentials_exception

    if not user.is_active:
        logger.warning("User is inactive", extra={"user_id": user_id})
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Возвращает текущего пользователя или None если не авторизован.

    Args:
        credentials: HTTP авторизационные данные.
        db: Сессия базы данных.

    Returns:
        Текущий пользователь или None.
    """
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_role(*allowed_roles: str) -> Any:
    """Создает зависимость для проверки роли пользователя.

    Args:
        *allowed_roles: Разрешенные роли.

    Returns:
        Зависимость FastAPI.

    Example:
        @app.get("/admin", dependencies=[Depends(require_role("admin", "superadmin"))])
        async def admin_panel():
            return {"message": "Welcome admin"}
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        """Проверяет роль пользователя.

        Args:
            current_user: Текущий пользователь.

        Returns:
            Текущий пользователь.

        Raises:
            HTTPException: Если роль не разрешена.
        """
        if current_user.role not in allowed_roles:
            logger.warning(
                "User role not allowed",
                extra={
                    "user_id": current_user.id,
                    "role": current_user.role,
                    "allowed_roles": allowed_roles,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not allowed. Allowed roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return Depends(role_checker)
