"""
Модуль SQLAlchemy Table определений.

Использует подход Table + Mapper:
- Table: описание структуры таблицы в БД (здесь)
- Mapper: связывает Table с domain сущностью (mapper.py)
- Domain: бизнес-логика сущностей (в app.core.domain)
"""

from .base import Base
from .user import users_table
from .document import documents_table
from .analysis import analyses_table
from .report import reports_table
from .history import history_table
from .mapper import mapper  # noqa: F401

__all__ = [
    # Базовый класс для метаданных
    "Base",
    # Таблицы (SQLAlchemy Table)
    "users_table",
    "documents_table",
    "analyses_table",
    "reports_table",
    "history_table",
]
