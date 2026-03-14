"""
Корневой композит приложения.

Агрегирует все остальные композиты, определяет порядок инициализации
и координирует graceful shutdown.
"""

from typing import Any

from composites.api_composite import APIComposite
from composites.base import BaseComposite
from composites.cache_composite import CacheComposite
from composites.database_composite import DatabaseComposite
from composites.llm_composite import LLMComposite
from composites.logging_composite import LoggingComposite
from composites.storage_composite import StorageComposite


class AppComposite(BaseComposite):
    """Корневой композит для управления всем приложением."""

    def __init__(self) -> None:
        """Инициализирует корневой композит."""
        super().__init__()
        self._logging_composite = LoggingComposite()
        self._database_composite: DatabaseComposite | None = None
        self._cache_composite: CacheComposite | None = None
        self._llm_composite: LLMComposite | None = None
        self._storage_composite: StorageComposite | None = None
        self._api_composite: APIComposite | None = None

    async def initialize(self) -> None:
        """Инициализирует все компоненты приложения в правильном порядке.

        Порядок инициализации:
        1. Logging (первый - все зависят от логгера)
        2. Database, Cache, LLM, Storage (параллельно - независимы друг от друга)
        3. API (последний - зависит от всех остальных)
        """
        if self._initialized:
            return

        # 1. Инициализация логгера (обязательно первой)
        await self._logging_composite.initialize()
        logger = self._logging_composite.logger

        # Сохраняем логгер как зависимость
        self.set_dependency("logger", logger)

        # 2. Инициализация остальных композитов (параллельно)
        self._database_composite = DatabaseComposite(logger)
        self._cache_composite = CacheComposite(logger)
        self._llm_composite = LLMComposite(logger)
        self._storage_composite = StorageComposite(logger)

        await self._database_composite.initialize()
        await self._cache_composite.initialize()
        await self._llm_composite.initialize()
        await self._storage_composite.initialize()

        # Сохраняем зависимости
        self.set_dependency("database_composite", self._database_composite)
        self.set_dependency("cache_composite", self._cache_composite)
        self.set_dependency("llm_composite", self._llm_composite)
        self.set_dependency("storage_composite", self._storage_composite)

        # 3. Инициализация API (после всех остальных)
        self._api_composite = APIComposite(logger)
        await self._api_composite.initialize()

        # Сохраняем зависимость
        self.set_dependency("api_composite", self._api_composite)

        self._initialized = True
        logger.info("All components initialized")

    async def start(self) -> None:
        """Запускает все компоненты приложения в правильном порядке.

        Порядок запуска:
        1. Logging (первый)
        2. Database, Cache, LLM, Storage (параллельно)
        3. API (последний)
        """
        await self._ensure_initialized()

        if self._started:
            return

        logger = self._logging_composite.logger
        logger.info("Starting all components")

        # 1. Запуск логгера
        await self._logging_composite.start()

        # 2. Запуск остальных композитов (параллельно)
        if self._database_composite:
            await self._database_composite.start()
        if self._cache_composite:
            await self._cache_composite.start()
        if self._llm_composite:
            await self._llm_composite.start()
        if self._storage_composite:
            await self._storage_composite.start()

        # 3. Запуск API
        if self._api_composite:
            await self._api_composite.start()

        self._started = True
        logger.info("All components started")

    async def shutdown(self) -> None:
        """Останавливает все компоненты приложения в обратном порядке.

        Порядок остановки:
        1. API (первый - обратный порядок запуска)
        2. Database, Cache, LLM, Storage (параллельно)
        3. Logging (последний)
        """
        await self._ensure_started()

        logger = self._logging_composite.logger
        logger.info("Shutting down all components")

        # 1. Остановка API
        if self._api_composite:
            await self._api_composite.shutdown()

        # 2. Остановка остальных композитов (параллельно)
        if self._database_composite:
            await self._database_composite.shutdown()
        if self._cache_composite:
            await self._cache_composite.shutdown()
        if self._llm_composite:
            await self._llm_composite.shutdown()
        if self._storage_composite:
            await self._storage_composite.shutdown()

        # 3. Остановка логгера
        await self._logging_composite.shutdown()

        self._started = False
        logger.info("All components shut down")

    @property
    def api_app(self) -> APIComposite:
        """Возвращает API композит.

        Returns:
            APIComposite.

        Raises:
            RuntimeError: Если композит не инициализирован.
        """
        if not self._initialized:
            msg = "App composite is not initialized"
            raise RuntimeError(msg)
        if self._api_composite is None:
            msg = "API composite is not initialized"
            raise RuntimeError(msg)
        return self._api_composite

    def get_fastapi_app(self) -> Any:
        """Возвращает FastAPI приложение.

        Returns:
            FastAPI приложение.

        Note:
            Этот метод используется для получения app без async context.
            Убедитесь, что initialize() был вызван перед использованием.
        """
        if not self._initialized:
            msg = "App composite is not initialized"
            raise RuntimeError(msg)
        if self._api_composite is None:
            msg = "API composite is not initialized"
            raise RuntimeError(msg)
        return self._api_composite.get_app()
