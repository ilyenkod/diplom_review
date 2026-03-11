"""
Domain сущность Report.

Содержит бизнес-логику отчета по анализу документа, не зависящую от способа хранения.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Report:
    """Domain сущность отчета по анализу документа."""

    id: str
    analysis_id: str
    overall_assessment: str | None = None
    recommendations: list[str] = field(default_factory=list)
    supervisor_comments: list[str] = field(default_factory=list)
    generated_at: datetime | None = None

    def add_recommendation(self, recommendation: str) -> None:
        """Добавляет рекомендацию в отчет."""
        self.recommendations.append(recommendation)

    def add_supervisor_comment(self, comment: str) -> None:
        """Добавляет комментарий руководителя в отчет."""
        self.supervisor_comments.append(comment)

    def set_overall_assessment(self, assessment: str) -> None:
        """Устанавливает общую оценку."""
        self.overall_assessment = assessment
