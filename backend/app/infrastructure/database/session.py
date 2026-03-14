"""
Управление сессиями базы данных.

Создает async engine и session factory для SQLAlchemy.
"""

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class DatabaseSessionManager:
    """Менеджер сессий базы данных."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """Инициализирует менеджер сессий.

        Args:
            database_url: URL для подключения к базе данных.
            echo: Включить логирование SQL запросов.
        """
        self._engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            future=True,
        )
        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        """Возвращает engine базы данных.

        Returns:
            AsyncEngine.
        """
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Возвращает factory для создания сессий.

        Returns:
            async_sessionmaker.
        """
        return self._session_factory

    async def get_session(self) -> AsyncGenerator[AsyncSession, Any]:
        """Возвращает новую сессию базы данных.

        Yields:
            AsyncSession.

        Example:
            async with session_manager.get_session() as session:
                await session.execute(query)
        """
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def close(self) -> None:
        """Закрывает все соединения с базой данных."""
        await self._engine.dispose()
