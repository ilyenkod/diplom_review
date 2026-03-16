"""
Процессор для обработки PDF файлов.

Извлекает текст из документов PDF с использованием pdfplumber.
"""

import asyncio
from io import BytesIO
from pathlib import Path

import pdfplumber

from app.infrastructure.logging import AppLogger
from app.infrastructure.processors.base import BaseProcessor, ProcessorResult


class PdfProcessor(BaseProcessor):
    """Процессор для PDF файлов."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует PDF процессор.

        Args:
            logger: Логгер приложения.
        """
        self._logger = logger

    def get_supported_extensions(self) -> set[str]:
        """Возвращает множество поддерживаемых расширений файлов.

        Returns:
            Множество поддерживаемых расширений.
        """
        return {"pdf"}

    async def process(self, file_path: Path) -> ProcessorResult:
        """Обрабатывает PDF документ и извлекает текст.

        Args:
            file_path: Путь к файлу.

        Returns:
            Результат обработки с текстом или ошибкой.
        """
        try:
            text = await asyncio.to_thread(self._extract_text_sync, file_path)
            self._logger.info(
                "PDF file processed successfully",
                extra={"file_path": str(file_path), "text_length": len(text)},
            )
            return ProcessorResult(
                success=True,
                text=text,
                metadata={"format": "pdf"},
            )
        except Exception as e:
            self._logger.error(
                "Failed to process PDF file",
                extra={"file_path": str(file_path), "error": str(e)},
            )
            return ProcessorResult(
                success=False,
                text="",
                error=str(e),
            )

    async def process_bytes(self, content: bytes) -> ProcessorResult:
        """Обрабатывает PDF документ из байтов и извлекает текст.

        Args:
            content: Содержимое файла в байтах.

        Returns:
            Результат обработки с текстом или ошибкой.
        """
        try:
            text = await asyncio.to_thread(self._extract_text_from_bytes_sync, content)
            self._logger.info(
                "PDF bytes processed successfully",
                extra={"content_length": len(content), "text_length": len(text)},
            )
            return ProcessorResult(
                success=True,
                text=text,
                metadata={"format": "pdf"},
            )
        except Exception as e:
            self._logger.error(
                "Failed to process PDF bytes",
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
        text_parts = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_parts.append(page_text.strip())

        return "\n\n".join(text_parts)

    def _extract_text_from_bytes_sync(self, content: bytes) -> str:
        """Синхронное извлечение текста из байтов.

        Args:
            content: Содержимое файла в байтах.

        Returns:
            Извлеченный текст.
        """
        text_parts = []

        with pdfplumber.open(BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_parts.append(page_text.strip())

        return "\n\n".join(text_parts)
