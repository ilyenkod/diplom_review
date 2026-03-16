"""
SQLAlchemy Mapper для связывания Table с domain сущностями.

Поскольку названия полей в таблицах и сущностях совпадают,
mapper использует автоматическое сопоставление.
"""

from sqlalchemy.orm import registry

from app.core.domain import Analysis, Document, History, Report, User

from .analysis import analyses_table
from .document import documents_table
from .history import history_table
from .report import reports_table
from .user import users_table

# ============================================================
# Mapper: связывает Table с domain сущностью
# ============================================================
mapper_registry = registry()

# Регистрируем все мапперы
mapper_registry.map_imperatively(User, users_table)
mapper_registry.map_imperatively(Document, documents_table)
mapper_registry.map_imperatively(Analysis, analyses_table)
mapper_registry.map_imperatively(Report, reports_table)
mapper_registry.map_imperatively(History, history_table)
