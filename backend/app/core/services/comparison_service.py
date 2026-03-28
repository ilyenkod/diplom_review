"""
Сервис сравнения версий документов.

Сравнивает две версии документа и вычисляет разницу в оценках.
"""

from dataclasses import dataclass
from typing import Any

from app.core.const import AnalysisCriteria
from app.core.exceptions import DocumentNotFoundError, VersionNotFoundError
from app.core.interfaces.database import AnalysisRepository, DocumentRepository, HistoryRepository
from app.infrastructure.logging import AppLogger


@dataclass
class CriterionComparison:
    """Результат сравнения по критерию."""

    criterion_name: str
    criterion_description: str
    previous_score: float | None
    current_score: float | None
    difference: float | None
    trend: str  # "improved", "worsened", "unchanged"


@dataclass
class VersionComparison:
    """Результат сравнения двух версий документа."""

    document_id: str
    previous_version: int
    current_version: int
    previous_overall_score: float | None
    current_overall_score: float | None
    overall_score_diff: float | None
    overall_trend: str
    criteria_comparisons: list[CriterionComparison]
    summary: str


class ComparisonService:
    """Сервис для сравнения версий документов."""

    def __init__(
        self,
        history_repo: HistoryRepository,
        analysis_repo: AnalysisRepository,
        document_repo: DocumentRepository,
        logger: AppLogger,
    ) -> None:
        """Инициализирует сервис сравнения.

        Args:
            history_repo: Репозиторий истории версий.
            analysis_repo: Репозиторий анализов.
            document_repo: Репозиторий документов.
            logger: Логгер приложения.
        """
        self._history_repo = history_repo
        self._analysis_repo = analysis_repo
        self._document_repo = document_repo
        self._logger = logger

    async def compare_versions(
        self,
        document_id: str,
        previous_version: int,
        current_version: int,
    ) -> VersionComparison:
        """Сравнивает две версии документа.

        Args:
            document_id: ID документа.
            previous_version: Номер предыдущей версии.
            current_version: Номер текущей версии.

        Returns:
            Результат сравнения версий.

        Raises:
            DocumentNotFoundError: Если документ не найден.
            VersionNotFoundError: Если одна из версий не найдена.
        """
        # Проверяем существование документа
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        # Получаем версии
        previous_history = await self._history_repo.get_by_version(document_id, previous_version)
        current_history = await self._history_repo.get_by_version(document_id, current_version)

        if previous_history is None:
            raise VersionNotFoundError(document_id, previous_version)
        if current_history is None:
            raise VersionNotFoundError(document_id, current_version)

        # Получаем анализы
        previous_analysis = await self._analysis_repo.get_by_id(previous_history.analysis_id)
        current_analysis = await self._analysis_repo.get_by_id(current_history.analysis_id)

        if previous_analysis is None or current_analysis is None:
            raise ValueError("Analysis not found for one of the versions")

        # Сравниваем общие оценки
        previous_overall_score = previous_analysis.overall_score
        current_overall_score = current_analysis.overall_score

        overall_score_diff: float | None = None
        if previous_overall_score is not None and current_overall_score is not None:
            overall_score_diff = current_overall_score - previous_overall_score

        overall_trend = self._determine_trend(overall_score_diff)

        # Сравниваем критерии
        criteria_comparisons = self._compare_criteria(
            previous_analysis.results,
            current_analysis.results,
        )

        # Формируем сводку
        summary = self._build_comparison_summary(
            overall_score_diff,
            overall_trend,
            criteria_comparisons,
        )

        self._logger.info(
            "Versions compared",
            extra={
                "document_id": document_id,
                "previous_version": previous_version,
                "current_version": current_version,
                "overall_score_diff": overall_score_diff,
            },
        )

        return VersionComparison(
            document_id=document_id,
            previous_version=previous_version,
            current_version=current_version,
            previous_overall_score=previous_overall_score,
            current_overall_score=current_overall_score,
            overall_score_diff=overall_score_diff,
            overall_trend=overall_trend,
            criteria_comparisons=criteria_comparisons,
            summary=summary,
        )

    async def compare_latest_with_previous(
        self,
        document_id: str,
    ) -> VersionComparison:
        """Сравнивает последнюю версию с предыдущей.

        Args:
            document_id: ID документа.

        Returns:
            Результат сравнения версий.

        Raises:
            DocumentNotFoundError: Если документ не найден.
            VersionNotFoundError: Если нет предыдущей версии.
        """
        # Получаем историю версий
        histories = await self._history_repo.get_by_document_id(document_id, limit=2)

        if len(histories) < 2:
            raise VersionNotFoundError(document_id, histories[0].version_number - 1)

        current_history = histories[0]
        previous_history = histories[1]

        return await self.compare_versions(
            document_id,
            previous_history.version_number,
            current_history.version_number,
        )

    async def compare_analysis(
        self,
        previous_analysis_id: str,
        current_analysis_id: str,
    ) -> VersionComparison:
        """Сравнивает два анализа напрямую.

        Args:
            previous_analysis_id: ID предыдущего анализа.
            current_analysis_id: ID текущего анализа.

        Returns:
            Результат сравнения анализов.

        Raises:
            ValueError: Если анализы не найдены или не завершены.
        """
        # Получаем анализы
        previous_analysis = await self._analysis_repo.get_by_id(previous_analysis_id)
        current_analysis = await self._analysis_repo.get_by_id(current_analysis_id)

        if previous_analysis is None:
            raise ValueError(f"Analysis {previous_analysis_id} not found")
        if current_analysis is None:
            raise ValueError(f"Analysis {current_analysis_id} not found")

        if not previous_analysis.is_completed or not current_analysis.is_completed:
            raise ValueError("Both analyses must be completed")

        # Проверяем, что анализы относятся к одному документу
        if previous_analysis.document_id != current_analysis.document_id:
            raise ValueError("Analyses must belong to the same document")

        # Сравниваем общие оценки
        previous_overall_score = previous_analysis.overall_score
        current_overall_score = current_analysis.overall_score

        overall_score_diff: float | None = None
        if previous_overall_score is not None and current_overall_score is not None:
            overall_score_diff = current_overall_score - previous_overall_score

        overall_trend = self._determine_trend(overall_score_diff)

        # Сравниваем критерии
        criteria_comparisons = self._compare_criteria(
            previous_analysis.results,
            current_analysis.results,
        )

        # Формируем сводку
        summary = self._build_comparison_summary(
            overall_score_diff,
            overall_trend,
            criteria_comparisons,
        )

        self._logger.info(
            "Analyses compared",
            extra={
                "previous_analysis_id": previous_analysis_id,
                "current_analysis_id": current_analysis_id,
                "overall_score_diff": overall_score_diff,
            },
        )

        return VersionComparison(
            document_id=current_analysis.document_id,
            previous_version=-1,  # Не применимо при прямом сравнении анализов
            current_version=-1,
            previous_overall_score=previous_overall_score,
            current_overall_score=current_overall_score,
            overall_score_diff=overall_score_diff,
            overall_trend=overall_trend,
            criteria_comparisons=criteria_comparisons,
            summary=summary,
        )

    def _compare_criteria(
        self,
        previous_results: dict[str, Any],
        current_results: dict[str, Any],
    ) -> list[CriterionComparison]:
        """Сравнивает результаты по критериям.

        Args:
            previous_results: Результаты предыдущего анализа.
            current_results: Результаты текущего анализа.

        Returns:
            Список сравнений по критериям.
        """
        comparisons: list[CriterionComparison] = []

        for criterion in AnalysisCriteria.ALL:
            previous_data = previous_results.get(criterion)
            current_data = current_results.get(criterion)

            previous_score: float | None = None
            current_score: float | None = None

            if isinstance(previous_data, dict) and "score" in previous_data:
                previous_score = float(previous_data["score"])

            if isinstance(current_data, dict) and "score" in current_data:
                current_score = float(current_data["score"])

            difference: float | None = None
            if previous_score is not None and current_score is not None:
                difference = current_score - previous_score

            trend = self._determine_trend(difference)

            comparison = CriterionComparison(
                criterion_name=criterion,
                criterion_description=AnalysisCriteria.DESCRIPTIONS.get(criterion, criterion),
                previous_score=previous_score,
                current_score=current_score,
                difference=difference,
                trend=trend,
            )

            comparisons.append(comparison)

        return comparisons

    def _determine_trend(self, difference: float | None) -> str:
        """Определяет тенденцию изменения.

        Args:
            difference: Разница в оценках.

        Returns:
            Тенденция: "improved", "worsened", или "unchanged".
        """
        if difference is None:
            return "unchanged"

        if difference > 0.3:
            return "improved"
        elif difference < -0.3:
            return "worsened"
        else:
            return "unchanged"

    def _build_comparison_summary(
        self,
        overall_score_diff: float | None,
        overall_trend: str,
        criteria_comparisons: list[CriterionComparison],
    ) -> str:
        """Строит текстовую сводку сравнения.

        Args:
            overall_score_diff: Разница в общей оценке.
            overall_trend: Общая тенденция.
            criteria_comparisons: Сравнения по критериям.

        Returns:
            Текстовая сводка сравнения.
        """
        parts: list[str] = []

        # Общая тенденция
        if overall_trend == "improved":
            parts.append("Общая оценка улучшилась")
        elif overall_trend == "worsened":
            parts.append("Общая оценка снизилась")
        else:
            parts.append("Общая оценка существенно не изменилась")

        # Детали по общей оценке
        if overall_score_diff is not None:
            parts.append(f"Разница: {overall_score_diff:+.1f}")

        # Сильные улучшения и ухудшения
        improvements: list[str] = []
        deteriorations: list[str] = []

        for comparison in criteria_comparisons:
            if comparison.difference is None:
                continue

            if comparison.difference > 1.0:
                improvements.append(f"{comparison.criterion_name} (+{comparison.difference:.1f})")
            elif comparison.difference < -1.0:
                deteriorations.append(f"{comparison.criterion_name} ({comparison.difference:.1f})")

        if improvements:
            parts.append(f"Значительно улучшено: {', '.join(improvements)}")
        if deteriorations:
            parts.append(f"Значительно ухудшено: {', '.join(deteriorations)}")

        return ". ".join(parts)

    async def get_score_trend(
        self,
        document_id: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Возвращает тенденцию изменения оценок документа.

        Args:
            document_id: ID документа.
            limit: Максимальное количество версий для анализа.

        Returns:
            Словарь с данными о тенденции.

        Raises:
            DocumentNotFoundError: Если документ не найден.
        """
        # Проверяем существование документа
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        # Получаем историю версий
        histories = await self._history_repo.get_by_document_id(document_id, limit=limit)

        if not histories:
            return {"trend": "no_data", "scores": [], "average": None}

        # Получаем оценки
        scores: list[tuple[int, float]] = []
        for history in histories:
            analysis = await self._analysis_repo.get_by_id(history.analysis_id)
            if analysis is not None and analysis.overall_score is not None:
                scores.append((history.version_number, analysis.overall_score))

        if not scores:
            return {"trend": "no_data", "scores": [], "average": None}

        # Сортируем по номеру версии
        scores.sort(key=lambda x: x[0])

        # Вычисляем среднее
        average_score = sum(score for _, score in scores) / len(scores)

        # Определяем тенденцию
        if len(scores) >= 3:
            recent_scores = [score for _, score in scores[-3:]]
            first_scores = [score for _, score in scores[:3]]

            recent_average = sum(recent_scores) / len(recent_scores)
            first_average = sum(first_scores) / len(first_scores)

            if recent_average > first_average + 0.5:
                trend = "improving"
            elif recent_average < first_average - 0.5:
                trend = "declining"
            else:
                trend = "stable"
        elif len(scores) >= 2:
            first_score = scores[0][1]
            last_score = scores[-1][1]

            if last_score > first_score + 0.5:
                trend = "improving"
            elif last_score < first_score - 0.5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        return {
            "trend": trend,
            "scores": [{"version": version, "score": score} for version, score in scores],
            "average": average_score,
            "count": len(scores),
        }
