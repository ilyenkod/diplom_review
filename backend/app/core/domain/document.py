"""
Domain сущность Document.

Содержит бизнес-логику документа, не зависящую от способа хранения.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class FileType(str, Enum):
    """Тип файла документа."""

    DOCX = "docx"
    PDF = "pdf"
    TXT = "txt"


@dataclass
class Document:
    """Domain сущность документа."""

    id: str
    user_id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    file_path: str | None = None
    s3_key: str | None = None
    content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_local_storage(self) -> bool:
        """Проверяет, хранится ли файл локально."""
        return self.file_path is not None

    @property
    def is_s3_storage(self) -> bool:
        """Проверяет, хранится ли файл в S3."""
        return self.s3_key is not None

    @property
    def file_extension(self) -> str:
        """Возвращает расширение файла."""
        return f".{self.file_type}"

    def update_content(self, content: str) -> None:
        """Обновляет содержимое документа."""
        self.content = content

    def update_metadata(self, metadata: dict[str, Any]) -> None:
        """Обновляет метаданные документа (сливает с существующими)."""
        self.metadata = {**(self.metadata or {}), **metadata}
