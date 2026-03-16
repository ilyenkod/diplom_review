"""Pydantic схемы для отчетов."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ReportResponse(BaseModel):
    """Схема ответа с данными отчета."""

    id: str = Field(..., description="ID отчета")
    analysis_id: str = Field(..., description="ID анализа")
    overall_assessment: str | None = Field(default=None, description="Общая оценка")
    recommendations: list[str] = Field(default_factory=list, description="Рекомендации")
    supervisor_comments: list[str] = Field(
        default_factory=list, description="Комментарии руководителя"
    )
    generated_at: datetime | None = Field(default=None, description="Время генерации")

    class Config:
        """Конфигурация Pydantic."""

        from_attributes = True


class ReportDetailResponse(ReportResponse):
    """Схема ответа с деталями отчета."""

    analysis_results: dict[str, Any] = Field(default_factory=dict, description="Результаты анализа")
    criteria_scores: dict[str, float] = Field(
        default_factory=dict, description="Оценки по критериям"
    )
    overall_score: float = Field(..., description="Общая оценка (0-100)")
    strengths: list[str] = Field(default_factory=list, description="Сильные стороны")
    weaknesses: list[str] = Field(default_factory=list, description="Слабые стороны")


class ReportGenerateRequest(BaseModel):
    """Схема запроса на генерацию отчета."""

    analysis_id: str = Field(..., description="ID анализа для генерации отчета")
    format: str = Field(default="pdf", description="Формат отчета (pdf, docx, json)")


class ReportDownloadResponse(BaseModel):
    """Схема ответа для скачивания отчета."""

    file_url: str = Field(..., description="URL для скачивания файла")
    filename: str = Field(..., description="Имя файла")
    content_type: str = Field(..., description="Тип содержимого")
    size: int = Field(..., description="Размер файла в байтах")


class AssessmentLevel(str):
    """Уровни оценки."""

    EXCELLENT = "excellent"
    GOOD = "good"
    SATISFACTORY = "satisfactory"
    UNSATISFACTORY = "unsatisfactory"


class OverallAssessment(BaseModel):
    """Схема общей оценки."""

    level: str = Field(..., description="Уровень оценки")
    score: float = Field(..., ge=0.0, le=100.0, description="Оценка")
    description: str = Field(..., description="Описание уровня")
