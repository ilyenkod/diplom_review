"""Pydantic схемы для документов."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.core.domain.document import FileType


class FileTypeEnum(StrEnum):
    """Тип файла для API."""

    DOCX = FileType.DOCX.value
    PDF = FileType.PDF.value
    TXT = FileType.TXT.value


class DocumentBase(BaseModel):
    """Базовая схема документа."""

    original_filename: str = Field(..., description="Оригинальное имя файла")
    file_type: FileTypeEnum = Field(..., description="Тип файла")


class DocumentUpload(DocumentBase):
    """Схема загрузки документа."""

    file_size: int = Field(..., ge=1, description="Размер файла в байтах")
    content: str | None = Field(default=None, description="Извлеченный текст документа")


class DocumentResponse(BaseModel):
    """Схема ответа с данными документа."""

    id: str = Field(..., description="ID документа")
    user_id: str = Field(..., description="ID пользователя")
    filename: str = Field(..., description="Имя файла в хранилище")
    original_filename: str = Field(..., description="Оригинальное имя файла")
    file_size: int = Field(..., description="Размер файла в байтах")
    file_type: FileTypeEnum = Field(..., description="Тип файла")
    file_path: str | None = Field(
        default=None, description="Путь к файлу (для локального хранилища)"
    )
    s3_key: str | None = Field(default=None, description="Ключ S3 (для S3 хранилища)")
    content: str | None = Field(default=None, description="Извлеченный текст документа")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Метаданные документа")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime | None = Field(default=None, description="Время обновления")

    class Config:
        """Конфигурация Pydantic."""

        from_attributes = True


class DocumentListResponse(BaseModel):
    """Схема ответа со списком документов."""

    id: str = Field(..., description="ID документа")
    filename: str = Field(..., description="Имя файла")
    original_filename: str = Field(..., description="Оригинальное имя файла")
    file_type: FileTypeEnum = Field(..., description="Тип файла")
    file_size: int = Field(..., description="Размер файла в байтах")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime | None = Field(default=None, description="Время обновления")

    class Config:
        """Конфигурация Pydantic."""

        from_attributes = True


class DocumentUpdate(BaseModel):
    """Схема обновления документа."""

    content: str | None = Field(default=None, description="Новое содержимое документа")
    metadata: dict[str, Any] | None = Field(default=None, description="Новые метаданные")
