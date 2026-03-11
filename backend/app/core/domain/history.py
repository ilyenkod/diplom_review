"""
Domain сущность History.

Содержит бизнес-логику записи истории версий документа, не зависящую от способа хранения.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class History:
    """Domain сущность записи истории версий документа."""

    id: str
    document_id: str
    version_number: int
    analysis_id: str
    changes_summary: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None

    @property
    def has_changes(self) -> bool:
        """Проверяет, есть ли изменения в сводке."""
        return bool(self.changes_summary)

    @property
    def overall_score_diff(self) -> float | None:
        """Возвращает изменение общей оценки (если есть)."""
        return self.changes_summary.get("overall_score_diff")

    @property
    def criteria_changes(self) -> dict[str, float] | None:
        """Возвращает изменения по критериям (если есть)."""
        return self.changes_summary.get("criteria_changes")

    @property
    def summary(self) -> str | None:
        """Возвращает текстовую сводку изменений."""
        return self.changes_summary.get("summary")
