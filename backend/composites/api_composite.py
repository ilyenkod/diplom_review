"""
Композит для сборки FastAPI приложения.

Создает FastAPI instance, регистрирует роуты, настраивает middleware и внедряет зависимости.
Запускается последним - зависит от всех остальных композитов.
"""

from typing import Any

from fastapi import FastAPI

from app.config import get_settings
from app.infrastructure.api.deps import set_dependencies
from app.infrastructure.api.deps_composites import set_composite_dependencies
from app.infrastructure.logging import AppLogger
from composites.base import BaseComposite


class APIComposite(BaseComposite):
    """Композит для управления API."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует композит API.

        Args:
            logger: Логгер приложения.
        """
        super().__init__()
        self._logger = logger
        self._app: FastAPI | None = None

    async def initialize(self) -> None:
        """Инициализирует компоненты API."""
        if self._initialized:
            return

        self._logger.info("Initializing API composite")

        # Создание FastAPI приложения
        self._app = FastAPI(
            title="Diplom Review API",
            description="API для автоматизированной проверки дипломных работ с использованием ИИ",
            version="0.1.0",
            docs_url="/docs" if get_settings().app.debug else None,
            redoc_url="/redoc" if get_settings().app.debug else None,
            openapi_url="/openapi.json" if get_settings().app.debug else None,
        )

        # Регистрация роутеров
        self._register_routes()

        # Настройка middleware
        self._setup_middleware()

        # Внедрение зависимостей (делегируется в setup_dependencies из router)
        self._setup_dependencies()

        # Сохраняем зависимость
        self.set_dependency("app", self._app)

        self._initialized = True
        self._logger.info("API composite initialized")

    def _register_routes(self) -> None:
        """Регистрирует роутеры API.

        Полная реализация будет в фазе 5 и последующих.
        """
        self._logger.info("Routes registered (empty for now)")

    def _setup_middleware(self) -> None:
        """Настраивает middleware.

        Полная реализация будет в фазе 5.
        """
        # Middleware будут настроены здесь
        # Например: CORS, Request ID, Logging
        self._logger.info("Middleware setup (empty for now)")

    def _setup_dependencies(self) -> None:
        """Внедряет зависимости в приложение.

        Полная реализация будет в фазе 5.
        """
        # Зависимости будут настроены здесь
        # Например: get_db, get_cache, get_current_user
        self._logger.info("Dependencies setup (empty for now)")

    def setup_dependencies(
        self,
        session_manager: Any,
        cache_client: Any,
        llm_client: Any,
        storage: Any,
        app_composite: Any,
    ) -> None:
        """Настраивает зависимости для внедрения в FastAPI.

        Args:
            session_manager: Менеджер сессий базы данных.
            cache_client: Клиент кэша.
            llm_client: Клиент LLM.
            storage: Хранилище файлов.
            app_composite: Основной композит приложения.
        """
        set_dependencies(session_manager, cache_client, llm_client)
        set_composite_dependencies(app_composite, self._logger, storage)

    async def start(self) -> None:
        """Запускает компоненты API."""
        await self._ensure_initialized()

        if self._started:
            return

        self._logger.info("Starting API composite")

        # Здесь может быть запуск событий startup
        if self._app:
            self._logger.info("FastAPI application ready")

        self._started = True
        self._logger.info("API composite started")

    async def shutdown(self) -> None:
        """Останавливает компоненты API."""
        await self._ensure_started()

        self._logger.info("Shutting down API composite")

        # Здесь может быть запуск событий shutdown
        if self._app:
            self._logger.info("FastAPI application stopped")

        self._started = False
        self._logger.info("API composite shut down")

    @property
    def app(self) -> FastAPI:
        """Возвращает FastAPI приложение.

        Returns:
            FastAPI приложение.

        Raises:
            RuntimeError: Если композит не инициализирован.
        """
        if not self._initialized:
            msg = "API composite is not initialized"
            raise RuntimeError(msg)
        app_value = self.get_dependency("app")
        assert isinstance(app_value, FastAPI)
        return app_value

    def get_app(self) -> FastAPI:
        """Возвращает FastAPI приложение (синхронный метод).

        Returns:
            FastAPI приложение.

        Note:
            Этот метод используется для получения app без async context.
            Убедитесь, что initialize() был вызван перед использованием.
        """
        if not self._initialized:
            msg = "API composite is not initialized"
            raise RuntimeError(msg)
        app_value = self.get_dependency("app")
        assert isinstance(app_value, FastAPI)
        return app_value
