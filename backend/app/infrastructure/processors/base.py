"""
Базовый класс для процессоров документов.

Определяет интерфейс для извлечения текста из документов разных форматов.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProcessorResult:
    """Результат обработки документа."""

    success: bool
    text: str
    error: str | None = None
    metadata: dict | None = None


class BaseProcessor(ABC):
    """Базовый класс процессора документов."""

    @abstractmethod
    def get_supported_extensions(self) -> set[str]:
        """Возвращает множество поддерживаемых расширений файлов.

        Returns:
            Множество поддерживаемых расширений (без точки).
        """
        raise NotImplementedError

    @abstractmethod
    async def process(self, file_path: Path) -> ProcessorResult:
        """Обрабатывает документ и извлекает текст.

        Args:
            file_path: Путь к файлу.

        Returns:
            Результат обработки с текстом или ошибкой.
        """
        raise NotImplementedError

    @abstractmethod
    async def process_bytes(self, content: bytes) -> ProcessorResult:
        """Обрабатывает документ из байтов и извлекает текст.

        Args:
            content: Содержимое файла в байтах.

        Returns:
            Результат обработки с текстом или ошибкой.
        """
        raise NotImplementedError

    def can_process(self, file_path: Path) -> bool:
        """Проверяет, может ли процессор обработать этот файл.

        Args:
            file_path: Путь к файлу.

        Returns:
            True если процессор поддерживает этот формат.
        """
        extension = file_path.suffix.lower().lstrip(".")
        return extension in self.get_supported_extensions()
