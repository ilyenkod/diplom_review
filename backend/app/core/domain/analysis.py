"""
Domain сущность Analysis.

Содержит бизнес-логику анализа документа, не зависящую от способа хранения.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AnalysisStatus(str, Enum):
    """Статус анализа документа."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Analysis:
    """Domain сущность анализа документа."""

    id: str
    document_id: str
    status: str = AnalysisStatus.PENDING.value
    overall_score: float | None = None
    results: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def start(self) -> None:
        """Отмечает анализ как начатый."""
        self.status = AnalysisStatus.PROCESSING.value
        self.started_at = datetime.utcnow()

    def complete(self, overall_score: float, results: dict[str, Any]) -> None:
        """Отмечает анализ как завершенный."""
        self.status = AnalysisStatus.COMPLETED.value
        self.overall_score = overall_score
        self.results = results
        self.completed_at = datetime.utcnow()
        self.error_message = None

    def fail(self, error_message: str) -> None:
        """Отмечает анализ как неудачный."""
        self.status = AnalysisStatus.FAILED.value
        self.error_message = error_message
        self.completed_at = datetime.utcnow()

    @property
    def is_pending(self) -> bool:
        """Проверяет, находится ли анализ в ожидании."""
        return self.status == AnalysisStatus.PENDING.value

    @property
    def is_processing(self) -> bool:
        """Проверяет, выполняется ли анализ."""
        return self.status == AnalysisStatus.PROCESSING.value

    @property
    def is_completed(self) -> bool:
        """Проверяет, завершен ли анализ успешно."""
        return self.status == AnalysisStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """Проверяет, завершился ли анализ с ошибкой."""
        return self.status == AnalysisStatus.FAILED.value

    @property
    def duration(self) -> float | None:
        """Возвращает длительность анализа в секундах."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
