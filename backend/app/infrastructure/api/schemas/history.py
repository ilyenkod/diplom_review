"""Pydantic схемы для истории версий."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HistoryItem(BaseModel):
    """Схема записи истории."""

    id: str = Field(..., description="ID записи истории")
    document_id: str = Field(..., description="ID документа")
    version_number: int = Field(..., ge=1, description="Номер версии")
    analysis_id: str = Field(..., description="ID анализа")
    changes_summary: dict[str, Any] = Field(default_factory=dict, description="Сводка изменений")
    created_at: datetime = Field(..., description="Время создания версии")

    class Config:
        """Конфигурация Pydantic."""

        from_attributes = True


class HistoryDetail(HistoryItem):
    """Схема деталей истории."""

    overall_score: float | None = Field(default=None, description="Общая оценка")
    overall_score_diff: float | None = Field(default=None, description="Изменение общей оценки")
    criteria_changes: dict[str, float] = Field(
        default_factory=dict, description="Изменения по критериям"
    )
    summary: str | None = Field(default=None, description="Текстовая сводка изменений")


class VersionComparison(BaseModel):
    """Схема сравнения версий."""

    document_id: str = Field(..., description="ID документа")
    version_from: int = Field(..., ge=1, description="Номер исходной версии")
    version_to: int = Field(..., ge=1, description="Номер целевой версии")
    overall_score_diff: float = Field(..., description="Изменение общей оценки")
    criteria_diff: dict[str, float] = Field(
        default_factory=dict, description="Изменения по критериям"
    )
    improved: list[str] = Field(default_factory=list, description="Улучшенные критерии")
    degraded: list[str] = Field(default_factory=list, description="Ухудшившиеся критерии")
    unchanged: list[str] = Field(default_factory=list, description="Неизменившиеся критерии")
    summary: str = Field(..., description="Сводка изменений")


class VersionListResponse(BaseModel):
    """Схема ответа со списком версий."""

    version_number: int = Field(..., description="Номер версии")
    created_at: datetime = Field(..., description="Время создания")
    overall_score: float | None = Field(default=None, description="Общая оценка")


class HistoryListResponse(BaseModel):
    """Схема ответа со списком истории."""

    document_id: str = Field(..., description="ID документа")
    versions: list[VersionListResponse] = Field(default_factory=list, description="Список версий")
    total_versions: int = Field(..., description="Общее количество версий")


class VersionComparisonRequest(BaseModel):
    """Схема запроса на сравнение версий."""

    document_id: str = Field(..., description="ID документа")
    version_from: int = Field(..., ge=1, description="Номер исходной версии")
    version_to: int = Field(..., ge=1, description="Номер целевой версии")
