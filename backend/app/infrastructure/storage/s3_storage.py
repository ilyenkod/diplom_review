"""
S3 хранилище файлов (заглушка).

Полная реализация будет в фазе 4.
"""

from datetime import datetime
from io import BytesIO
from typing import Any

from app.config import settings
from app.core.interfaces.storage import FileMetadata, S3Storage, StorageResult
from app.infrastructure.logging import AppLogger


class S3StorageImpl(S3Storage):
    """Реализация S3 хранилища (заглушка)."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует S3 хранилище.

        Args:
            logger: Логгер приложения.
        """
        self._logger = logger

    async def save(
        self,
        key: str,
        content: bytes | BytesIO,
        content_type: str,
    ) -> StorageResult:
        """Сохраняет файл по ключу (заглушка)."""
        self._logger.warning("S3 storage is not implemented yet, using stub")
        return StorageResult(
            success=False,
            key=key,
            metadata=FileMetadata(
                filename=key,
                size=0,
                content_type=content_type,
                created_at=datetime.now(),
                storage_type="s3",
                storage_key=key,
            ),
            error="S3 storage not implemented",
        )

    async def get(self, key: str) -> bytes | None:
        """Загружает файл по ключу (заглушка)."""
        return None

    async def delete(self, key: str) -> bool:
        """Удаляет файл по ключу (заглушка)."""
        return False

    async def exists(self, key: str) -> bool:
        """Проверяет существование файла (заглушка)."""
        return False

    async def get_metadata(self, key: str) -> FileMetadata | None:
        """Возвращает метаданные файла (заглушка)."""
        return None

    async def get_url(self, key: str, expires_in: int = 3600) -> str | None:
        """Возвращает URL для доступа к файлу (заглушка)."""
        return None

    async def list_files(self, prefix: str = "") -> list[str]:
        """Возвращает список файлов по префиксу (заглушка)."""
        return []

    async def copy(self, source_key: str, dest_key: str) -> bool:
        """Копирует файл (заглушка)."""
        return False

    async def move(self, source_key: str, dest_key: str) -> bool:
        """Перемещает файл (заглушка)."""
        return False

    async def clear(self) -> bool:
        """Очищает хранилище (заглушка)."""
        return False

    async def upload_fileobj(
        self,
        key: str,
        file_obj: BytesIO,
        content_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> StorageResult:
        """Загружает файловый объект в S3 (заглушка)."""
        return StorageResult(
            success=False,
            key=key,
            metadata=FileMetadata(
                filename=key,
                size=0,
                content_type=content_type,
                created_at=datetime.now(),
                storage_type="s3",
                storage_key=key,
            ),
            error="S3 storage not implemented",
        )

    async def download_fileobj(self, key: str) -> BytesIO | None:
        """Загружает файловый объект из S3 (заглушка)."""
        return None

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str | None:
        """Генерирует presigned URL для доступа к файлу (заглушка)."""
        return None

    async def head_object(self, key: str) -> dict[str, Any] | None:
        """Получает метаданные объекта без загрузки содержимого (заглушка)."""
        return None

    def get_bucket_name(self) -> str:
        """Возвращает имя бакета."""
        return settings.storage.s3_bucket_name

    def get_region(self) -> str:
        """Возвращает регион."""
        return settings.storage.s3_region
