"""Общие Pydantic схемы для API."""

from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Схема ошибки."""

    error: str = Field(..., description="Тип ошибки")
    message: str = Field(..., description="Описание ошибки")
    details: dict[str, Any] | None = Field(default=None, description="Дополнительные детали")


class ValidationErrorDetail(BaseModel):
    """Детали ошибки валидации."""

    field: str = Field(..., description="Поле с ошибкой")  # noqa: RUF001
    message: str = Field(..., description="Сообщение об ошибке")  # noqa: RUF001


class ValidationErrorResponse(BaseModel):
    """Схема ошибки валидации."""

    error: str = Field(default="validation_error", description="Тип ошибки")
    message: str = Field(default="Validation failed", description="Описание ошибки")
    details: list[ValidationErrorDetail] = Field(..., description="Детали ошибок")


class PaginationParams(BaseModel):
    """Параметры пагинации для запроса."""

    limit: int = Field(default=100, ge=1, le=1000, description="Максимальное количество записей")
    offset: int = Field(default=0, ge=0, description="Смещение")


class PaginationMeta(BaseModel):
    """Метаданные пагинации."""

    total: int = Field(..., description="Общее количество записей")
    limit: int = Field(..., description="Максимальное количество записей на странице")
    offset: int = Field(..., description="Текущее смещение")
    has_next: bool = Field(..., description="Есть ли следующая страница")
    has_prev: bool = Field(..., description="Есть ли предыдущая страница")


class PaginatedResponse(BaseModel, generic_types=(T,)):  # type: ignore[valid-type]
    """Схема ответа с пагинацией."""

    items: list[T] = Field(..., description="Список элементов")
    meta: PaginationMeta = Field(..., description="Метаданные пагинации")


class HealthCheckResponse(BaseModel):
    """Схема ответа проверки здоровья."""

    status: str = Field(..., description="Статус сервиса")
    version: str = Field(..., description="Версия API")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время проверки")


class SuccessResponse(BaseModel):
    """Схема успешного ответа."""

    message: str = Field(..., description="Сообщение об успехе")  # noqa: RUF001
