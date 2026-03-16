"""
Репозиторий пользователей.

Реализует интерфейс UserRepository для работы c пользователями в БД.
"""

from typing import Any, cast

from sqlalchemy import update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import User
from app.core.interfaces.database import UserRepository as UserRepositoryInterface
from app.infrastructure.database.repositories.base import BaseRepository


class UserRepository(BaseRepository[User], UserRepositoryInterface):
    """Репозиторий пользователей."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализирует репозиторий пользователей.

        Args:
            session: Сессия базы данных.
        """
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """Возвращает пользователя по email.

        Args:
            email: Email пользователя.

        Returns:
            Пользователь или None если не найден.
        """
        from sqlalchemy import select

        stmt = select(User).where(self._table.c.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_users(self, limit: int = 100, offset: int = 0) -> list[User]:
        """Возвращает список активных пользователей.

        Args:
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список активных пользователей.
        """
        from sqlalchemy import select

        stmt = select(User).where(self._table.c.is_active).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_role(self, role: str, limit: int = 100, offset: int = 0) -> list[User]:
        """Возвращает пользователей c указанной ролью.

        Args:
            role: Роль пользователя.
            limit: Максимальное количество записей.
            offset: Смещение.

        Returns:
            Список пользователей c указанной ролью.
        """
        from sqlalchemy import select

        stmt = select(User).where(self._table.c.role == role).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def set_active_status(self, user_id: str, is_active: bool) -> bool:
        """Устанавливает статус активности пользователя.

        Args:
            user_id: ID пользователя.
            is_active: Статус активности.

        Returns:
            True если обновлено, False если не найдено.
        """
        stmt = update(self._table).where(self._table.c.id == user_id).values(is_active=is_active)
        result = await self._session.execute(stmt)
        await self._session.flush()
        result_cast = cast(CursorResult[Any], result)
        return result_cast.rowcount > 0
