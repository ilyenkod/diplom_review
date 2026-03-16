"""
Процессор для обработки TXT файлов.

Извлекает текст из простых текстовых файлов.
"""

import asyncio
from pathlib import Path

from app.infrastructure.logging import AppLogger
from app.infrastructure.processors.base import BaseProcessor, ProcessorResult


class TxtProcessor(BaseProcessor):
    """Процессор для TXT файлов."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует TXT процессор.

        Args:
            logger: Логгер приложения.
        """
        self._logger = logger

    def get_supported_extensions(self) -> set[str]:
        """Возвращает множество поддерживаемых расширений файлов.

        Returns:
            Множество поддерживаемых расширений.
        """
        return {"txt"}

    async def process(self, file_path: Path) -> ProcessorResult:
        """Обрабатывает TXT файл и извлекает текст.

        Args:
            file_path: Путь к файлу.

        Returns:
            Результат обработки с текстом или ошибкой.
        """
        try:
            text = await asyncio.to_thread(self._extract_text_sync, file_path)
            self._logger.info(
                "TXT file processed successfully",
                extra={"file_path": str(file_path), "text_length": len(text)},
            )
            return ProcessorResult(
                success=True,
                text=text,
                metadata={"format": "txt", "lines": text.count("\n") + 1},
            )
        except Exception as e:
            self._logger.error(
                "Failed to process TXT file",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return ProcessorResult(
                success=False,
                text="",
                error=str(e),
            )

    async def process_bytes(self, content: bytes) -> ProcessorResult:
        """Обрабатывает TXT документ из байтов и извлекает текст.

        Args:
            content: Содержимое файла в байтах.

        Returns:
            Результат обработки с текстом или ошибкой.
        """
        try:
            text = await asyncio.to_thread(self._extract_text_from_bytes_sync, content)
            self._logger.info(
                "TXT bytes processed successfully",
                extra={"content_length": len(content), "text_length": len(text)},
            )
            return ProcessorResult(
                success=True,
                text=text,
                metadata={"format": "txt", "lines": text.count("\n") + 1},
            )
        except Exception as e:
            self._logger.error(
                "Failed to process TXT bytes",
                extra={"content_length": len(content), "error": str(e)},
            )
            return ProcessorResult(
                success=False,
                text="",
                error=str(e),
            )

    def _extract_text_sync(self, file_path: Path) -> str:
        """Синхронное извлечение текста из файла.

        Args:
            file_path: Путь к файлу.

        Returns:
            Извлеченный текст.
        """
        # Пытаемся определить кодировку
        encodings = ["utf-8", "utf-8-sig", "cp1251", "iso-8859-1"]

        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue

        # Если ни одна кодировка не подошла, используем latin1
        return file_path.read_text(encoding="latin1", errors="replace")

    def _extract_text_from_bytes_sync(self, content: bytes) -> str:
        """Синхронное извлечение текста из байтов.

        Args:
            content: Содержимое файла в байтах.

        Returns:
            Извлеченный текст.
        """
        # Пытаемся определить кодировку
        encodings = ["utf-8", "utf-8-sig", "cp1251", "iso-8859-1"]

        for encoding in encodings:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue

        # Если ни одна кодировка не подошла, используем latin1
        return content.decode("latin1", errors="replace")
