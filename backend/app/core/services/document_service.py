"""
Сервис документов.

Предоставляет функции для загрузки, обработки и управления документами.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.config import get_settings
from app.core.const import FileFormats
from app.core.domain import Document
from app.core.exceptions import (
    DocumentNotFoundError,
    DocumentProcessingError,
    FileSizeExceededError,
    InvalidFileTypeError,
)
from app.core.interfaces.database import DocumentRepository
from app.core.interfaces.storage import Storage
from app.infrastructure.logging import AppLogger
from app.infrastructure.processors.base import BaseProcessor, ProcessorResult

if TYPE_CHECKING:
    from collections.abc import MutableMapping


@dataclass
class UploadResult:
    """Результат загрузки документа."""

    document: Document
    extracted_text: str


@dataclass
class DocumentMetadata:
    """Метаданные документа."""

    format: str
    paragraphs: int = 0
    lines: int = 0
    words: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


class DocumentService:
    """Сервис для работы с документами."""

    def __init__(
        self,
        document_repo: DocumentRepository,
        storage: Storage,
        logger: AppLogger,
        processors: MutableMapping[str, BaseProcessor],
    ) -> None:
        """Инициализирует сервис документов.

        Args:
            document_repo: Репозиторий документов.
            storage: Хранилище файлов.
            logger: Логгер приложения.
            processors: Словарь процессоров для разных форматов файлов.
        """
        self._document_repo = document_repo
        self._storage = storage
        self._logger = logger
        self._processors = processors

    async def upload_document(
        self,
        user_id: str,
        filename: str,
        original_filename: str,
        file_size: int,
        file_type: str,
        content: bytes,
    ) -> Document:
        """Загружает документ в хранилище и сохраняет в БД.

        Args:
            user_id: ID пользователя.
            filename: Имя файла в хранилище.
            original_filename: Оригинальное имя файла.
            file_size: Размер файла в байтах.
            file_type: Тип файла (docx, pdf, txt).
            content: Содержимое файла в байтах.

        Returns:
            Созданный документ.

        Raises:
            DocumentValidationError: Если валидация файла не прошла.
            DocumentProcessingError: Если обработка файла не удалась.
        """
        # Валидируем файл
        self._validate_file(filename, file_size)

        # Выбираем процессор по типу файла
        processor = self._select_processor(file_type)

        # Извлекаем текст
        process_result = await processor.process_bytes(content)
        if not process_result.success:
            raise DocumentProcessingError(
                f"Failed to process {file_type} file: {process_result.error}"
            )

        # Формируем ключ для хранения
        storage_key = self._generate_storage_key(user_id, filename)

        # Сохраняем файл в хранилище
        content_type = FileFormats.MIME_TYPES.get(file_type, "application/octet-stream")
        save_result = await self._storage.save(storage_key, content, content_type)
        if not save_result.success:
            raise DocumentProcessingError(f"Failed to save file to storage: {save_result.error}")

        # Формируем метаданные
        metadata = self._extract_metadata(process_result)

        # Создаем документ в БД
        storage_settings = get_settings().storage
        document = Document(
            id=self._generate_document_id(),
            user_id=user_id,
            filename=storage_key,
            original_filename=original_filename,
            file_size=file_size,
            file_type=file_type,
            file_path=storage_key if storage_settings.backend == "local" else None,
            s3_key=storage_key if storage_settings.backend == "s3" else None,
            content=process_result.text,
            metadata=metadata,
            created_at=datetime.now(UTC),
        )

        created_document = await self._document_repo.create(document)

        # Обновляем содержимое отдельно (если нужно для больших текстов)
        if len(process_result.text) > 10000:
            await self._document_repo.update_content(created_document.id, process_result.text)

        self._logger.info(
            "Document uploaded successfully",
            extra={
                "document_id": created_document.id,
                "user_id": user_id,
                "filename": original_filename,
                "file_size": file_size,
                "file_type": file_type,
            },
        )

        return created_document

    async def get_document(self, document_id: str) -> Document | None:
        """Получает документ по ID.

        Args:
            document_id: ID документа.

        Returns:
            Документ или None если не найден.
        """
        return await self._document_repo.get_by_id(document_id)

    async def get_user_documents(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """Получает документы пользователя.

        Args:
            user_id: ID пользователя.
            limit: Максимальное количество документов.
            offset: Смещение.

        Returns:
            Список документов пользователя.
        """
        return await self._document_repo.get_by_user_id(user_id, limit, offset)

    async def delete_document(
        self,
        document_id: str,
        user_id: str,
    ) -> bool:
        """Удаляет документ.

        Args:
            document_id: ID документа.
            user_id: ID пользователя (для проверки прав).

        Returns:
            True если документ был удален, иначе False.

        Raises:
            DocumentNotFoundError: Если документ не найден.
        """
        # Получаем документ
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            return False

        # Проверяем, что документ принадлежит пользователю
        if document.user_id != user_id:
            self._logger.warning(
                "User attempted to delete document from another user",
                extra={"document_id": document_id, "user_id": user_id},
            )
            return False

        # Удаляем файл из хранилища
        if document.file_path:
            await self._storage.delete(document.file_path)
        elif document.s3_key:
            await self._storage.delete(document.s3_key)

        # Удаляем документ из БД
        result = await self._document_repo.delete(document_id)

        if result:
            self._logger.info(
                "Document deleted successfully",
                extra={"document_id": document_id, "user_id": user_id},
            )

        return result

    def _validate_file(self, filename: str, file_size: int) -> None:
        """Валидирует файл перед загрузкой.

        Args:
            filename: Имя файла.
            file_size: Размер файла в байтах.

        Raises:
            InvalidFileTypeError: Если тип файла не поддерживается.
            FileSizeExceededError: Если размер файла превышает лимит.
        """
        # Проверяем тип файла по расширению
        extension = filename.lower().split(".")[-1] if "." in filename else ""
        if extension not in FileFormats.ALLOWED:
            raise InvalidFileTypeError(extension, list(FileFormats.ALLOWED))

        # Проверяем размер файла
        max_size = get_settings().upload.max_file_size
        if file_size > max_size:
            raise FileSizeExceededError(file_size, max_size)

    def _select_processor(self, file_type: str) -> BaseProcessor:
        """Выбирает процессор по типу файла.

        Args:
            file_type: Тип файла (docx, pdf, txt).

        Returns:
            Процессор для указанного типа файла.

        Raises:
            InvalidFileTypeError: Если процессор не найден.
        """
        processor = self._processors.get(file_type)
        if processor is None:
            raise InvalidFileTypeError(file_type, list(self._processors.keys()))
        return processor

    def _generate_storage_key(self, user_id: str, filename: str) -> str:
        """Генерирует ключ для хранения файла.

        Args:
            user_id: ID пользователя.
            filename: Имя файла.

        Returns:
            Ключ для хранения.
        """
        from pathlib import Path

        # Добавляем timestamp для уникальности
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        extension = Path(filename).suffix
        base_name = Path(filename).stem

        return f"{user_id}/{timestamp}_{base_name}{extension}"

    def _generate_document_id(self) -> str:
        """Генерирует уникальный ID документа.

        Returns:
            Уникальный ID документа.
        """
        import uuid

        return str(uuid.uuid4())

    def _extract_metadata(self, process_result: ProcessorResult) -> dict[str, Any]:
        """Извлекает метаданные из результата обработки.

        Args:
            process_result: Результат обработки файла.

        Returns:
            Словарь метаданных.
        """
        metadata: dict[str, Any] = {"format": "unknown"}

        if process_result.metadata:
            metadata.update(process_result.metadata)

        # Подсчитываем слова и символы
        text = process_result.text
        words = text.split()
        metadata["words_count"] = len(words)
        metadata["characters_count"] = len(text)
        metadata["lines_count"] = text.count("\n") + 1

        # Определяем примерное количество страниц
        if metadata.get("format") == "pdf":
            # Для PDF примерная оценка (взята из метаданных процессора)
            pages = text.count("\f") + 1
            metadata["estimated_pages"] = pages
        else:
            # Для docx и txt: примерно 300 слов на страницу
            estimated_pages = max(1, len(words) // 300)
            metadata["estimated_pages"] = estimated_pages

        return metadata

    async def extract_text(
        self,
        file_type: str,
        content: bytes,
    ) -> str:
        """Извлекает текст из файла.

        Args:
            file_type: Тип файла (docx, pdf, txt).
            content: Содержимое файла в байтах.

        Returns:
            Извлеченный текст.

        Raises:
            DocumentProcessingError: Если обработка файла не удалась.
            InvalidFileTypeError: Если процессор не найден.
        """
        processor = self._select_processor(file_type)
        result = await processor.process_bytes(content)

        if not result.success:
            raise DocumentProcessingError(f"Failed to extract text: {result.error}")

        return result.text

    async def reprocess_document(
        self,
        document_id: str,
        user_id: str,
    ) -> Document:
        """Перерабатывает документ (повторно извлекает текст).

        Args:
            document_id: ID документа.
            user_id: ID пользователя (для проверки прав).

        Returns:
            Обновленный документ.

        Raises:
            DocumentNotFoundError: Если документ не найден.
            DocumentProcessingError: Если переработка не удалась.
        """
        # Получаем документ
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        # Проверяем права
        if document.user_id != user_id:
            self._logger.warning(
                "User attempted to reprocess document from another user",
                extra={"document_id": document_id, "user_id": user_id},
            )
            raise DocumentNotFoundError(document_id)

        # Загружаем файл из хранилища
        storage_key = document.file_path or document.s3_key
        if storage_key is None:
            raise DocumentProcessingError("Document has no storage key")

        content = await self._storage.get(storage_key)
        if content is None:
            raise DocumentProcessingError("Failed to load file from storage")

        # Перерабатываем файл
        processor = self._select_processor(document.file_type)
        result = await processor.process_bytes(content)

        if not result.success:
            raise DocumentProcessingError(f"Failed to reprocess document: {result.error}")

        # Обновляем метаданные
        metadata = self._extract_metadata(result)
        document.update_metadata(metadata)

        # Обновляем содержимое
        await self._document_repo.update_content(document_id, result.text)
        document.content = result.text

        self._logger.info(
            "Document reprocessed successfully",
            extra={"document_id": document_id, "user_id": user_id},
        )

        return document
