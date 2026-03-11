"""
Модуль базы данных.

Содержит Table определения и конфигурацию для миграций.
Domain сущности находятся в app.core.domain.
"""

from app.core.domain import (
    Analysis,
    Document,
    History,
    Report,
    User,
)
from app.infrastructure.database.table import (
    Base,
    analyses_table,
    documents_table,
    history_table,
    reports_table,
    users_table,
)

__all__ = [
    # Базовый класс
    "Base",
    # Сущности (domain models)
    "User",
    "Document",
    "Analysis",
    "Report",
    "History",
    # Таблицы (SQLAlchemy Table)
    "users_table",
    "documents_table",
    "analyses_table",
    "reports_table",
    "history_table",
]
