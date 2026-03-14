"""
Локальное хранилище файлов.

Реализует интерфейс LocalStorage для работы с файловой системой.
"""

import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path

from app.core.interfaces.storage import FileMetadata, LocalStorage, StorageResult
from app.infrastructure.logging import AppLogger


class FileSystemStorage(LocalStorage):
    """Локальное файловое хранилище."""

    def __init__(self, base_path: Path, logger: AppLogger) -> None:
        """Инициализирует локальное хранилище.

        Args:
            base_path: Базовый путь к хранилищу.
            logger: Логгер приложения.
        """
        self._base_path = base_path
        self._logger = logger
        self._base_path.mkdir(parents=True, exist_ok=True)

    def get_base_path(self) -> Path:
        """Возвращает базовый путь к хранилищу.

        Returns:
            Базовый путь.
        """
        return self._base_path

    def set_base_path(self, path: Path) -> None:
        """Устанавливает базовый путь к хранилищу.

        Args:
            path: Новый базовый путь.
        """
        self._base_path = path
        self._base_path.mkdir(parents=True, exist_ok=True)

    async def ensure_directory(self, key: str) -> Path:
        """Убеждается, что директория для файла существует.

        Args:
            key: Ключ файла (путь относительно base_path).

        Returns:
            Полный путь к директории.
        """
        file_path = self.get_full_path(key)
        directory = file_path.parent
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def get_full_path(self, key: str) -> Path:
        """Возвращает полный путь к файлу.

        Args:
            key: Ключ файла (путь относительно base_path).

        Returns:
            Полный путь к файлу.
        """
        return self._base_path / key

    async def save(
        self,
        key: str,
        content: bytes | BytesIO,
        content_type: str,
    ) -> StorageResult:
        """Сохраняет файл по ключу.

        Args:
            key: Ключ файла.
            content: Содержимое файла.
            content_type: MIME тип.

        Returns:
            Результат сохранения.
        """
        try:
            await self.ensure_directory(key)
            file_path = self.get_full_path(key)

            if isinstance(content, BytesIO):
                content.seek(0)
                file_path.write_bytes(content.getvalue())
            else:
                file_path.write_bytes(content)

            metadata = FileMetadata(
                filename=Path(key).name,
                size=file_path.stat().st_size,
                content_type=content_type,
                created_at=datetime.now(),
                storage_type="local",
                storage_key=key,
            )

            return StorageResult(
                success=True,
                key=key,
                metadata=metadata,
            )

        except Exception as e:
            self._logger.error(f"Failed to save file {key}", extra={"error": str(e)})
            return StorageResult(
                success=False,
                key=key,
                metadata=FileMetadata(
                    filename=Path(key).name,
                    size=0,
                    content_type=content_type,
                    created_at=datetime.now(),
                    storage_type="local",
                ),
                error=str(e),
            )

    async def get(self, key: str) -> bytes | None:
        """Загружает файл по ключу.

        Args:
            key: Ключ файла.

        Returns:
            Содержимое файла или None если файл не найден.
        """
        try:
            file_path = self.get_full_path(key)
            if file_path.exists():
                return file_path.read_bytes()
            return None
        except Exception:
            return None

    async def delete(self, key: str) -> bool:
        """Удаляет файл по ключу.

        Args:
            key: Ключ файла.

        Returns:
            True если файл был удален, иначе False.
        """
        try:
            file_path = self.get_full_path(key)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """Проверяет существование файла.

        Args:
            key: Ключ файла.

        Returns:
            True если файл существует, иначе False.
        """
        file_path = self.get_full_path(key)
        return file_path.exists()

    async def get_metadata(self, key: str) -> FileMetadata | None:
        """Возвращает метаданные файла.

        Args:
            key: Ключ файла.

        Returns:
            Метаданные файла или None если файл не найден.
        """
        try:
            file_path = self.get_full_path(key)
            if file_path.exists():
                stat = file_path.stat()
                return FileMetadata(
                    filename=Path(key).name,
                    size=stat.st_size,
                    content_type="application/octet-stream",
                    created_at=datetime.fromtimestamp(stat.st_ctime),
                    updated_at=datetime.fromtimestamp(stat.st_mtime),
                    storage_type="local",
                    storage_key=key,
                )
            return None
        except Exception:
            return None

    async def get_url(self, key: str, expires_in: int = 3600) -> str | None:
        """Возвращает URL для доступа к файлу (если применимо).

        Note:
            Для локального хранилища URL не применим.

        Args:
            key: Ключ файла.
            expires_in: Время жизни URL (игнорируется).

        Returns:
            None.
        """
        return None

    async def list_files(self, prefix: str = "") -> list[str]:
        """Возвращает список файлов по префиксу.

        Args:
            prefix: Префикс для поиска.

        Returns:
            Список ключей файлов.
        """
        try:
            base_path = self._base_path
            if prefix:
                base_path = base_path / prefix

            files: list[str] = []
            for file_path in base_path.rglob("*"):
                if file_path.is_file():
                    key = str(file_path.relative_to(self._base_path))
                    files.append(key)
            return files
        except Exception:
            return []

    async def copy(self, source_key: str, dest_key: str) -> bool:
        """Копирует файл.

        Args:
            source_key: Исходный ключ.
            dest_key: Ключ назначения.

        Returns:
            True если успешно, иначе False.
        """
        try:
            source_path = self.get_full_path(source_key)
            dest_path = self.get_full_path(dest_key)

            if source_path.exists():
                await self.ensure_directory(dest_key)
                shutil.copy2(source_path, dest_path)
                return True
            return False
        except Exception:
            return False

    async def move(self, source_key: str, dest_key: str) -> bool:
        """Перемещает файл.

        Args:
            source_key: Исходный ключ.
            dest_key: Ключ назначения.

        Returns:
            True если успешно, иначе False.
        """
        try:
            source_path = self.get_full_path(source_key)
            dest_path = self.get_full_path(dest_key)

            if source_path.exists():
                await self.ensure_directory(dest_key)
                shutil.move(str(source_path), str(dest_path))
                return True
            return False
        except Exception:
            return False

    async def clear(self) -> bool:
        """Очищает хранилище.

        Returns:
            True если успешно, иначе False.
        """
        try:
            for item in self._base_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            return True
        except Exception:
            return False
