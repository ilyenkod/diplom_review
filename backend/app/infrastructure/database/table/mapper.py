"""
SQLAlchemy Mapper для связывания Table с domain сущностями.

Поскольку названия полей в таблицах и сущностях совпадают,
mapper использует автоматическое сопоставление.
"""

from sqlalchemy.orm import mapper

from app.core.domain import Analysis, Document, History, Report, User

from .analysis import analyses_table
from .document import documents_table
from .history import history_table
from .report import reports_table
from .user import users_table

# ============================================================
# Mapper: связывает Table с domain сущностью
# ============================================================
mapper(User, users_table)
mapper(Document, documents_table)
mapper(Analysis, analyses_table)
mapper(Report, reports_table)
mapper(History, history_table)
