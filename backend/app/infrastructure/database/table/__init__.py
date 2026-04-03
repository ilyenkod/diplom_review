"""
Модуль SQLAlchemy Table определений.

Использует подход Table + Mapper:
- Table: описание структуры таблицы в БД (здесь)
- Mapper: связывает Table с domain сущностью (mapper.py)
- Domain: бизнес-логика сущностей (в app.core.domain)
"""

from .analysis import analyses_table
from .base import Base
from .document import documents_table
from .history import history_table
from .mapper import mapper_registry
from .report import reports_table
from .user import users_table

__all__ = [
    "Base",
    "analyses_table",
    "documents_table",
    "history_table",
    "mapper_registry",
    "reports_table",
    "users_table",
]
