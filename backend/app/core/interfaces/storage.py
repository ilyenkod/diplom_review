"""
Интерфейсы для работы с хранилищем файлов.

Определяет контракты для сохранения, загрузки и удаления файлов.
Следует принципу Dependency Inversion: бизнес-логика зависит от абстракций.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any


@dataclass
class FileMetadata:
    """Метаданные файла."""

    filename: str
    size: int
    content_type: str
    created_at: datetime
    updated_at: datetime | None = None
    storage_type: str = "local"
    storage_key: str | None = None


@dataclass
class StorageResult:
    """Результат операции хранения."""

    success: bool
    key: str
    metadata: FileMetadata
    error: str | None = None


class Storage(ABC):
    """Базовый интерфейс хранилища файлов."""

    @abstractmethod
    async def save(
        self,
        key: str,
        content: bytes | BytesIO,
        content_type: str,
    ) -> StorageResult:
        """Сохраняет файл по ключу."""
        raise NotImplementedError

    @abstractmethod
    async def get(self, key: str) -> bytes | None:
        """Загружает файл по ключу."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Удаляет файл по ключу."""
        raise NotImplementedError

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Проверяет существование файла."""
        raise NotImplementedError

    @abstractmethod
    async def get_metadata(self, key: str) -> FileMetadata | None:
        """Возвращает метаданные файла."""
        raise NotImplementedError

    @abstractmethod
    async def get_url(self, key: str, expires_in: int = 3600) -> str | None:
        """Возвращает URL для доступа к файлу (если применимо)."""
        raise NotImplementedError

    @abstractmethod
    async def list_files(self, prefix: str = "") -> list[str]:
        """Возвращает список файлов по префиксу."""
        raise NotImplementedError

    @abstractmethod
    async def copy(self, source_key: str, dest_key: str) -> bool:
        """Копирует файл."""
        raise NotImplementedError

    @abstractmethod
    async def move(self, source_key: str, dest_key: str) -> bool:
        """Перемещает файл."""
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> bool:
        """Очищает хранилище."""
        raise NotImplementedError


class LocalStorage(Storage):
    """Интерфейс для локального хранилища."""

    @abstractmethod
    def get_base_path(self) -> Path:
        """Возвращает базовый путь к хранилищу."""
        raise NotImplementedError

    @abstractmethod
    def set_base_path(self, path: Path) -> None:
        """Устанавливает базовый путь к хранилищу."""
        raise NotImplementedError

    @abstractmethod
    async def ensure_directory(self, key: str) -> Path:
        """Убеждается, что директория для файла существует."""
        raise NotImplementedError

    @abstractmethod
    def get_full_path(self, key: str) -> Path:
        """Возвращает полный путь к файлу."""
        raise NotImplementedError


class S3Storage(Storage):
    """Интерфейс для S3 хранилища."""

    @abstractmethod
    async def upload_fileobj(
        self,
        key: str,
        file_obj: BytesIO,
        content_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> StorageResult:
        """Загружает файловый объект в S3."""
        raise NotImplementedError

    @abstractmethod
    async def download_fileobj(self, key: str) -> BytesIO | None:
        """Загружает файловый объект из S3."""
        raise NotImplementedError

    @abstractmethod
    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "get_object",
    ) -> str | None:
        """Генерирует presigned URL для доступа к файлу."""
        raise NotImplementedError

    @abstractmethod
    async def head_object(self, key: str) -> dict[str, Any] | None:
        """Получает метаданные объекта без загрузки содержимого."""
        raise NotImplementedError

    @abstractmethod
    def get_bucket_name(self) -> str:
        """Возвращает имя бакета."""
        raise NotImplementedError

    @abstractmethod
    def get_region(self) -> str:
        """Возвращает регион."""
        raise NotImplementedError
