"""
Базовый класс для ORM метаданных.

Используется для создания пространства метаданных SQLAlchemy.
"""

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeEngine


class JSONBType(JSON):
    """JSON, который рендерится как JSONB в PostgreSQL и как JSON в других диалектах (SQLite)."""

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class Base(DeclarativeBase):
    """
    Базовый класс для всех таблиц в приложении.

    Используется для общего метаданного пространства.
    """

    pass
