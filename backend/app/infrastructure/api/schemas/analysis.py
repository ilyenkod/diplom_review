"""Pydantic схемы для анализов документов."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.core.domain.analysis import AnalysisStatus


class AnalysisStatusEnum(StrEnum):
    """Статус анализа для API."""

    PENDING = AnalysisStatus.PENDING.value
    PROCESSING = AnalysisStatus.PROCESSING.value
    COMPLETED = AnalysisStatus.COMPLETED.value
    FAILED = AnalysisStatus.FAILED.value


class AnalysisRequest(BaseModel):
    """Схема запроса на анализ."""

    document_id: str = Field(..., description="ID документа для анализа")
    options: dict[str, Any] | None = Field(
        default=None, description="Опции анализа (критерии, пороги и т.д.)"
    )


class AnalysisResponse(BaseModel):
    """Схема ответа с данными анализа."""

    id: str = Field(..., description="ID анализа")
    document_id: str = Field(..., description="ID документа")
    status: AnalysisStatusEnum = Field(..., description="Статус анализа")
    overall_score: float | None = Field(default=None, description="Общая оценка (0-100)")
    results: dict[str, Any] = Field(
        default_factory=dict, description="Результаты анализа по критериям"
    )
    started_at: datetime | None = Field(default=None, description="Время начала анализа")
    completed_at: datetime | None = Field(default=None, description="Время завершения анализа")
    error_message: str | None = Field(default=None, description="Сообщение об ошибке")  # noqa: RUF001
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime | None = Field(default=None, description="Время обновления")

    class Config:
        """Конфигурация Pydantic."""

        from_attributes = True


class AnalysisDetailResponse(AnalysisResponse):
    """Схема ответа с деталями анализа."""

    duration: float | None = Field(default=None, description="Длительность анализа в секундах")
    criteria_scores: dict[str, float] = Field(
        default_factory=dict, description="Оценки по критериям"
    )
    recommendations: list[str] = Field(default_factory=list, description="Рекомендации")


class AnalysisStatusResponse(BaseModel):
    """Схема ответа со статусом анализа."""

    id: str = Field(..., description="ID анализа")
    status: AnalysisStatusEnum = Field(..., description="Статус анализа")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Прогресс в процентах")
    started_at: datetime | None = Field(default=None, description="Время начала анализа")
    completed_at: datetime | None = Field(default=None, description="Время завершения анализа")


class AnalysisReanalyzeRequest(BaseModel):
    """Схема запроса на повторный анализ."""

    document_id: str = Field(..., description="ID документа для повторного анализа")
    force: bool = Field(default=False, description="Принудительно запустить анализ")
