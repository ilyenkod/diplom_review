"""
Композит для сборки компонентов кэша.

Создает Redis клиент и кэш-репозиторий.
"""

from app.core.interfaces.cache import CacheClient, CacheRepository
from app.infrastructure.cache.redis_client import RedisCacheClient
from app.infrastructure.cache.repository import RedisCacheRepository
from app.infrastructure.logging import AppLogger
from composites.base import BaseComposite


class CacheComposite(BaseComposite):
    """Композит для управления кэшем."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует композит кэша.

        Args:
            logger: Логгер приложения.
        """
        super().__init__()
        self._logger = logger
        self._client: RedisCacheClient | None = None
        self._repository: RedisCacheRepository | None = None

    async def initialize(self) -> None:
        """Инициализирует компоненты кэша."""
        if self._initialized:
            return

        self._logger.info("Initializing cache composite")

        # Создание клиента Redis
        self._client = RedisCacheClient(self._logger)
        await self._client.connect()

        # Создание репозитория кэша
        self._repository = RedisCacheRepository(self._client, self._logger)

        # Сохраняем зависимости
        self.set_dependency("cache_client", self._client)
        self.set_dependency("cache_repository", self._repository)

        self._initialized = True
        self._logger.info("Cache composite initialized")

    async def start(self) -> None:
        """Запускает компоненты кэша."""
        await self._ensure_initialized()

        if self._started:
            return

        self._logger.info("Starting cache composite")

        # Проверка соединения с Redis
        if self._client:
            is_available = await self._client.ping()
            if is_available:
                self._logger.info("Redis connection verified")
            else:
                self._logger.warning("Redis ping failed, cache may be unavailable")

        self._started = True
        self._logger.info("Cache composite started")

    async def shutdown(self) -> None:
        """Останавливает компоненты кэша."""
        await self._ensure_started()

        self._logger.info("Shutting down cache composite")

        if self._client:
            await self._client.disconnect()

        self._started = False
        self._logger.info("Cache composite shut down")

    @property
    def client(self) -> CacheClient:
        """Возвращает клиент кэша.

        Returns:
            CacheClient.

        Raises:
            RuntimeError: Если композит не инициализирован.
        """
        if not self._initialized:
            msg = "Cache composite is not initialized"
            raise RuntimeError(msg)
        return self.get_dependency("cache_client")

    @property
    def repository(self) -> CacheRepository:
        """Возвращает репозиторий кэша.

        Returns:
            CacheRepository.

        Raises:
            RuntimeError: Если композит не инициализирован.
        """
        if not self._initialized:
            msg = "Cache composite is not initialized"
            raise RuntimeError(msg)
        return self.get_dependency("cache_repository")
