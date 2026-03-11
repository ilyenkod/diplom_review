"""
Базовый класс для ORM метаданных.

Используется для создания пространства метаданных SQLAlchemy.
"""

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """
    Базовый класс для всех таблиц в приложении.

    Используется для общего метаданного пространства.
    """
    pass
