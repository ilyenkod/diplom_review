"""
Domain сущность User.

Содержит бизнес-логику пользователя, не зависящую от способа хранения.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """Роль пользователя в системе."""

    STUDENT = "student"
    ADMIN = "admin"
    SUPERVISOR = "supervisor"


@dataclass
class User:
    """Domain сущность пользователя."""

    id: str
    email: str
    hashed_password: str
    full_name: str
    is_active: bool = True
    role: str = UserRole.STUDENT.value
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def set_password(self, hashed_password: str) -> None:
        """Устанавливает новый пароль (уже хешированный)."""
        self.hashed_password = hashed_password

    @property
    def is_student(self) -> bool:
        """Проверяет, является ли пользователь студентом."""
        return self.role == UserRole.STUDENT.value

    @property
    def is_admin(self) -> bool:
        """Проверяет, является ли пользователь администратором."""
        return self.role == UserRole.ADMIN.value

    @property
    def is_supervisor(self) -> bool:
        """Проверяет, является ли пользователь руководителем."""
        return self.role == UserRole.SUPERVISOR.value
