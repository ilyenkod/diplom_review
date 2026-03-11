"""
SQLAlchemy Table для reports.

Содержит описание структуры таблицы reports в БД.
Mapper находится в mapper.py.
"""

from datetime import datetime

from sqlalchemy import (
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
# Описание таблицы reports (SQLAlchemy Table)
# ============================================================
reports_table = Table(
    "reports",
    Base.metadata,
    Column(
        "id",
        String,
        primary_key=True,
        comment="Уникальный идентификатор отчета (UUID)",
    ),
    Column(
        "analysis_id",
        String,
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        comment="ID связанного анализа",
    ),
    Column(
        "overall_assessment",
        Text,
        nullable=True,
        comment="Общая оценка качества работы текстом",
    ),
    Column(
        "recommendations",
        JSONB,
        nullable=False,
        default=[],
        comment="Список рекомендаций для улучшения",
    ),
    Column(
        "supervisor_comments",
        JSONB,
        nullable=False,
        default=[],
        comment="Комментарии в стиле научного руководителя",
    ),
    Column(
        "generated_at",
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        comment="Время генерации отчета",
    ),
    comment="Сгенерированные отчеты по результатам анализа",
)

# Индексы для оптимизации запросов
Index("idx_reports_analysis_id", reports_table.c.analysis_id)
