"""
Композит для сборки компонентов базы данных.

Создает async engine, session factory и инициализирует репозитории.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.config import settings
from app.infrastructure.database.session import DatabaseSessionManager
from app.infrastructure.logging import AppLogger
from composites.base import BaseComposite


class DatabaseComposite(BaseComposite):
    """Композит для управления базой данных."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует композит базы данных.

        Args:
            logger: Логгер приложения.
        """
        super().__init__()
        self._logger = logger
        self._session_manager: DatabaseSessionManager | None = None

    async def initialize(self) -> None:
        """Инициализирует компоненты базы данных."""
        if self._initialized:
            return

        self._logger.info("Initializing database composite")

        # Создание менеджера сессий
        self._session_manager = DatabaseSessionManager(
            database_url=settings.database.url,
            echo=settings.database.echo,
        )

        # Создание заглушек для репозиториев (полная реализация в фазе 3)
        self._initialize_repositories()

        # Сохраняем зависимости
        self.set_dependency("engine", self._session_manager.engine)
        self.set_dependency("session_factory", self._session_manager.session_factory)
        self.set_dependency("session_manager", self._session_manager)

        self._initialized = True
        self._logger.info("Database composite initialized")

    def _initialize_repositories(self) -> None:
        """Инициализирует репозитории с пустыми реализациями.

        Полная реализация репозиториев будет в фазе 3.
        """
        # Здесь будут создаваться экземпляры репозиториев
        # Сейчас используем заглушки (пустые классы)
        pass

    async def start(self) -> None:
        """Запускает компоненты базы данных."""
        await self._ensure_initialized()

        if self._started:
            return

        self._logger.info("Starting database composite")
        # Проверка соединения с базой данных
        # Будет реализовано в фазе 3
        self._started = True
        self._logger.info("Database composite started")

    async def shutdown(self) -> None:
        """Останавливает компоненты базы данных."""
        await self._ensure_started()

        self._logger.info("Shutting down database composite")

        if self._session_manager:
            await self._session_manager.close()

        self._started = False
        self._logger.info("Database composite shut down")

    @property
    def engine(self) -> AsyncEngine:
        """Возвращает engine базы данных.

        Returns:
            AsyncEngine.

        Raises:
            RuntimeError: Если композит не инициализирован.
        """
        if not self._initialized:
            msg = "Database composite is not initialized"
            raise RuntimeError(msg)
        return self.get_dependency("engine")

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Возвращает factory для создания сессий.

        Returns:
            async_sessionmaker.

        Raises:
            RuntimeError: Если композит не инициализирован.
        """
        if not self._initialized:
            msg = "Database composite is not initialized"
            raise RuntimeError(msg)
        return self.get_dependency("session_factory")

    @property
    def session_manager(self) -> DatabaseSessionManager:
        """Возвращает менеджер сессий.

        Returns:
            DatabaseSessionManager.

        Raises:
            RuntimeError: Если композит не инициализирован.
        """
        if not self._initialized:
            msg = "Database composite is not initialized"
            raise RuntimeError(msg)
        return self.get_dependency("session_manager")
