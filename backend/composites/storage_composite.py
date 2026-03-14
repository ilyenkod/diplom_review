"""
Композит для сборки компонентов хранилища.

Выбирает реализацию (local/s3) по конфигу и создает storage адаптер.
"""

from pathlib import Path

from app.config import settings
from app.core.interfaces.storage import Storage
from app.infrastructure.logging import AppLogger
from app.infrastructure.storage.local_storage import FileSystemStorage
from app.infrastructure.storage.s3_storage import S3StorageImpl
from composites.base import BaseComposite


class StorageComposite(BaseComposite):
    """Композит для управления хранилищем файлов."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует композит хранилища.

        Args:
            logger: Логгер приложения.
        """
        super().__init__()
        self._logger = logger
        self._storage: Storage | None = None

    async def initialize(self) -> None:
        """Инициализирует компоненты хранилища."""
        if self._initialized:
            return

        self._logger.info("Initializing storage composite")

        # Выбор реализации хранилища по конфигу
        storage_backend = settings.storage.backend
        self._logger.info(f"Using storage backend: {storage_backend}")

        if storage_backend == "local":
            self._storage = FileSystemStorage(Path(settings.storage.local_path), self._logger)
        elif storage_backend == "s3":
            self._storage = S3StorageImpl(self._logger)
        else:
            msg = f"Unknown storage backend: {storage_backend}"
            raise RuntimeError(msg)

        # Сохраняем зависимость
        self.set_dependency("storage", self._storage)

        self._initialized = True
        self._logger.info("Storage composite initialized", extra={"backend": storage_backend})

    async def start(self) -> None:
        """Запускает компоненты хранилища."""
        await self._ensure_initialized()

        if self._started:
            return

        self._logger.info("Starting storage composite")

        # Проверка доступности хранилища
        if isinstance(self._storage, FileSystemStorage):
            base_path = self._storage.get_base_path()
            if base_path.exists() and base_path.is_dir():
                self._logger.info(f"Local storage path verified: {base_path}")
            else:
                self._logger.warning(f"Local storage path does not exist: {base_path}")

        self._started = True
        self._logger.info("Storage composite started")

    async def shutdown(self) -> None:
        """Останавливает компоненты хранилища."""
        await self._ensure_started()

        self._logger.info("Shutting down storage composite")

        # Очистка временных ресурсов если необходимо
        if self._storage and isinstance(self._storage, FileSystemStorage):
            await self._storage.clear()

        self._started = False
        self._logger.info("Storage composite shut down")

    @property
    def storage(self) -> Storage:
        """Возвращает хранилище файлов.

        Returns:
            Storage.

        Raises:
            RuntimeError: Если композит не инициализирован.
        """
        if not self._initialized:
            msg = "Storage composite is not initialized"
            raise RuntimeError(msg)
        return self.get_dependency("storage")
