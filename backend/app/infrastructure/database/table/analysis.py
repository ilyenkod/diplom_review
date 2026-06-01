"""
SQLAlchemy Table для analyses.

Содержит описание структуры таблицы analyses в БД.
Mapper находится в mapper.py.
"""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Table,
    Text,
)
from .base import Base, JSONBType

# ============================================================
# Описание таблицы analyses (SQLAlchemy Table)
# ============================================================
analyses_table = Table(
    "analyses",
    Base.metadata,
    Column(
        "id",
        String,
        primary_key=True,
        comment="Уникальный идентификатор анализа (UUID)",
    ),
    Column(
        "document_id",
        String,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID анализируемого документа",
    ),
    Column(
        "status",
        String(50),
        nullable=False,
        default="pending",
        comment="Статус анализа (pending, processing, completed, failed)",
    ),
    Column(
        "overall_score",
        Numeric(3, 1),
        nullable=True,
        comment="Общая оценка работы (0.0 - 10.0)",
    ),
    Column(
        "results",
        JSONBType,
        nullable=False,
        default={},
        comment="Результаты анализа по каждому критерию",
    ),
    Column(
        "started_at",
        DateTime(timezone=True),
        nullable=True,
        comment="Время начала анализа",
    ),
    Column(
        "completed_at",
        DateTime(timezone=True),
        nullable=True,
        comment="Время завершения анализа",
    ),
    Column(
        "error_message",
        Text,
        nullable=True,
        comment="Сообщение об ошибке при неудачном анализе",
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
        "status IN ('pending', 'processing', 'completed', 'failed')",
        name="check_analysis_status",
        comment="Разрешенные статусы анализа",
    ),
    CheckConstraint(
        "overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 10)",
        name="check_overall_score_range",
        comment="Общая оценка должна быть в диапазоне от 0 до 10",
    ),
    comment="Результаты анализа документов",
)

# Индексы для оптимизации запросов
Index("idx_analyses_document_id", analyses_table.c.document_id)
Index("idx_analyses_status", analyses_table.c.status)
Index("idx_analyses_overall_score", analyses_table.c.overall_score)
Index("idx_analyses_created_at", analyses_table.c.created_at.desc())
