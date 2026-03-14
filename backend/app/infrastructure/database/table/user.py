"""
SQLAlchemy Table для users.

Содержит описание структуры таблицы users в БД.
Mapper находится в mapper.py.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    String,
    Table,
)

from .base import Base

# ============================================================
# Описание таблицы users (SQLAlchemy Table)
# ============================================================
users_table = Table(
    "users",
    Base.metadata,
    Column(
        "id",
        String,
        primary_key=True,
        comment="Уникальный идентификатор пользователя (UUID)",
    ),
    Column(
        "email",
        String(255),
        nullable=False,
        unique=True,
        comment="Email пользователя (уникальный)",
    ),
    Column(
        "hashed_password",
        String(255),
        nullable=False,
        comment="Хешированный пароль",
    ),
    Column(
        "full_name",
        String(255),
        nullable=False,
        comment="Полное имя пользователя",
    ),
    Column(
        "is_active",
        Boolean,
        nullable=False,
        default=True,
        comment="Флаг активности пользователя",
    ),
    Column(
        "role",
        String(50),
        nullable=False,
        default="student",
        comment="Роль пользователя (student, admin, supervisor)",
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
    CheckConstraint("role IN ('student', 'admin', 'supervisor')", name="check_user_role"),
    comment="Пользователи системы (студенты, админы, руководители)",
)

# Индексы для оптимизации запросов
Index("idx_users_email", users_table.c.email)
Index("idx_users_role", users_table.c.role)
