"""
SQLAlchemy Table для history.

Содержит описание структуры таблицы history в БД.
Mapper находится в mapper.py.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


# ============================================================
# Описание таблицы history (SQLAlchemy Table)
# ============================================================
history_table = Table(
    "history",
    Base.metadata,
    Column(
        "id",
        String,
        primary_key=True,
        comment="Уникальный идентификатор записи истории (UUID)",
    ),
    Column(
        "document_id",
        String,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID документа",
    ),
    Column(
        "version_number",
        Integer,
        nullable=False,
        comment="Номер версии документа",
    ),
    Column(
        "analysis_id",
        String,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID анализа для данной версии",
    ),
    Column(
        "changes_summary",
        JSONB,
        nullable=False,
        default={},
        comment="Сводка изменений между версиями",
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Время создания записи истории",
    ),
    CheckConstraint(
        "version_number > 0",
        name="check_version_number_positive",
        comment="Номер версии должен быть положительным",
    ),
    UniqueConstraint(
        "document_id",
        "version_number",
        name="unique_document_version",
        comment="Для одного документа версии должны быть уникальными",
    ),
    comment="История версий документов",
)

# Индексы для оптимизации запросов
Index("idx_history_document_id", history_table.c.document_id)
Index("idx_history_version_number", history_table.c.document_id, history_table.c.version_number)
Index("idx_history_created_at", history_table.c.created_at.desc())
