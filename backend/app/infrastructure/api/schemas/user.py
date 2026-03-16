"""Pydantic схемы для пользователей."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field

from app.core.domain.user import UserRole


class UserRoleEnum(StrEnum):
    """Роль пользователя для API."""

    STUDENT = UserRole.STUDENT.value
    ADMIN = UserRole.ADMIN.value
    SUPERVISOR = UserRole.SUPERVISOR.value


class UserBase(BaseModel):
    """Базовая схема пользователя."""

    email: EmailStr = Field(..., description="Email пользователя")
    full_name: str = Field(..., min_length=1, max_length=255, description="Полное имя")


class UserCreate(UserBase):
    """Схема создания пользователя."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="Пароль",
    )
    role: UserRoleEnum = Field(default=UserRoleEnum.STUDENT, description="Роль пользователя")


class UserUpdate(BaseModel):
    """Схема обновления пользователя."""

    email: EmailStr | None = Field(default=None, description="Новый email")
    full_name: str | None = Field(
        default=None, min_length=1, max_length=255, description="Новое полное имя"
    )
    role: UserRoleEnum | None = Field(default=None, description="Новая роль")
    is_active: bool | None = Field(default=None, description="Статус активности")


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя."""

    id: str = Field(..., description="ID пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    full_name: str = Field(..., description="Полное имя")
    is_active: bool = Field(..., description="Активен ли пользователь")
    role: UserRoleEnum = Field(..., description="Роль пользователя")
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime | None = Field(default=None, description="Время обновления")

    class Config:
        """Конфигурация Pydantic."""

        from_attributes = True


class TokenResponse(BaseModel):
    """Схема ответа с токенами."""

    access_token: str = Field(..., description="Access токен")
    refresh_token: str = Field(..., description="Refresh токен")
    token_type: str = Field(default="bearer", description="Тип токена")
    expires_in: int = Field(..., description="Время жизни access токена в секундах")


class TokenRefreshRequest(BaseModel):
    """Схема запроса на обновление токена."""

    refresh_token: str = Field(..., description="Refresh токен")


class LoginRequest(BaseModel):
    """Схема запроса на вход."""

    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., description="Пароль")


class RegisterRequest(UserCreate):
    """Схема запроса на регистрацию."""

    pass
