"""
SQLAlchemy Table для documents.

Содержит описание структуры таблицы documents в БД.
Mapper находится в mapper.py.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base

# ============================================================
# Описание таблицы documents (SQLAlchemy Table)
# ============================================================
documents_table = Table(
    "documents",
    Base.metadata,
    Column(
        "id",
        String,
        primary_key=True,
        comment="Уникальный идентификатор документа (UUID)",
    ),
    Column(
        "user_id",
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID владельца документа",
    ),
    Column(
        "filename",
        String(255),
        nullable=False,
        comment="Сгенерированное имя файла (UUID-based)",
    ),
    Column(
        "original_filename",
        String(255),
        nullable=False,
        comment="Оригинальное имя файла при загрузке",
    ),
    Column(
        "file_path",
        String(500),
        nullable=True,
        comment="Путь к файлу в локальном хранилище",
    ),
    Column(
        "s3_key",
        String(500),
        nullable=True,
        comment="Ключ объекта в S3 хранилище",
    ),
    Column(
        "file_size",
        BigInteger,
        nullable=False,
        comment="Размер файла в байтах",
    ),
    Column(
        "file_type",
        String(10),
        nullable=False,
        comment="Тип файла (docx, pdf, txt)",
    ),
    Column(
        "content",
        Text,
        nullable=True,
        comment="Извлеченный текст из документа",
    ),
    Column(
        "metadata",
        JSONB,
        nullable=False,
        default={},
        comment="Дополнительные метаданные документа (author, title, pages_count и т.д.)",
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Время создания записи",
    ),
    Column(
        "updated_at",
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Время последнего обновления",
    ),
    CheckConstraint(
        "(file_path IS NOT NULL AND s3_key IS NULL) OR (file_path IS NULL AND s3_key IS NOT NULL)",
        name="document_storage_constraint",
        comment="Файл должен храниться либо локально, либо в S3, но не одновременно",
    ),
    CheckConstraint(
        "file_type IN ('docx', 'pdf', 'txt')",
        name="check_document_file_type",
        comment="Разрешенные типы файлов",
    ),
    comment="Загруженные дипломные работы",
)

# Индексы для оптимизации запросов
Index("idx_documents_user_id", documents_table.c.user_id)
Index("idx_documents_file_type", documents_table.c.file_type)
Index("idx_documents_created_at", documents_table.c.created_at.desc())
