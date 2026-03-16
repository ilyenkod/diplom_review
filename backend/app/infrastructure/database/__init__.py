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
    "Analysis",
    "Base",
    "Document",
    "History",
    "Report",
    "User",
    "analyses_table",
    "documents_table",
    "history_table",
    "reports_table",
    "users_table",
]
