"""
Сервис отчетов.

Формирует общую оценку документа, генерирует рекомендации и замечания руководителя.
"""

from app.core.const import AnalysisCriteria, AssessmentLevel
from app.core.domain import Analysis, Report
from app.core.exceptions import AnalysisNotFoundError, ReportGenerationError
from app.core.interfaces.database import AnalysisRepository, ReportRepository
from app.core.interfaces.llm import LLMClient, LLMConfig, Message
from app.infrastructure.logging import AppLogger


class ReportService:
    """Сервис для генерации отчетов по анализу документов."""

    def __init__(
        self,
        report_repo: ReportRepository,
        analysis_repo: AnalysisRepository,
        llm_client: LLMClient,
        logger: AppLogger,
    ) -> None:
        """Инициализирует сервис отчетов.

        Args:
            report_repo: Репозиторий отчетов.
            analysis_repo: Репозиторий анализов.
            llm_client: Клиент LLM.
            logger: Логгер приложения.
        """
        self._report_repo = report_repo
        self._analysis_repo = analysis_repo
        self._llm_client = llm_client
        self._logger = logger

    async def generate_report(self, analysis_id: str) -> Report:
        """Генерирует отчет по анализу.

        Args:
            analysis_id: ID анализа.

        Returns:
            Сгенерированный отчет.

        Raises:
            AnalysisNotFoundError: Если анализ не найден.
            ReportGenerationError: Если не удалось сгенерировать отчет.
        """
        # Получаем анализ
        analysis = await self._analysis_repo.get_by_id(analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError(analysis_id)

        if not analysis.is_completed:
            raise ReportGenerationError("Analysis is not completed yet")

        try:
            # Проверяем, существует ли уже отчет
            existing_report = await self._report_repo.get_by_analysis_id(analysis_id)

            if existing_report is not None:
                self._logger.info(
                    "Report already exists",
                    extra={"report_id": existing_report.id, "analysis_id": analysis_id},
                )
                return existing_report

            # Формируем общую оценку
            overall_assessment = self._form_overall_assessment(analysis)

            # Генерируем рекомендации
            recommendations = self._generate_recommendations(analysis)

            # Генерируем замечания руководителя
            supervisor_comments = await self._generate_supervisor_comments(analysis)

            # Создаем отчет
            report = Report(
                id=self._generate_id(),
                analysis_id=analysis_id,
                overall_assessment=overall_assessment,
                recommendations=recommendations,
                supervisor_comments=supervisor_comments,
            )

            created_report = await self._report_repo.create(report)

            self._logger.info(
                "Report generated",
                extra={
                    "report_id": created_report.id,
                    "analysis_id": analysis_id,
                    "overall_assessment": overall_assessment,
                },
            )

            return created_report

        except Exception as e:
            self._logger.error(
                "Report generation failed",
                extra={"analysis_id": analysis_id, "error": str(e)},
            )
            if isinstance(e, (AnalysisNotFoundError, ReportGenerationError)):
                raise
            raise ReportGenerationError(f"Failed to generate report: {e!s}") from e

    def _form_overall_assessment(self, analysis: Analysis) -> str:
        """Формирует общую оценку документа.

        Args:
            analysis: Анализ документа.

        Returns:
            Текстовая общая оценка.
        """
        if analysis.overall_score is None:
            return "Не удалось сформировать оценку"

        score = analysis.overall_score

        # Определяем уровень оценки
        if score >= AssessmentLevel.SCORE_RANGES[AssessmentLevel.EXCELLENT][0]:
            level = AssessmentLevel.EXCELLENT
        elif score >= AssessmentLevel.SCORE_RANGES[AssessmentLevel.GOOD][0]:
            level = AssessmentLevel.GOOD
        elif score >= AssessmentLevel.SCORE_RANGES[AssessmentLevel.SATISFACTORY][0]:
            level = AssessmentLevel.SATISFACTORY
        else:
            level = AssessmentLevel.POOR

        label = AssessmentLevel.LABELS[level]
        description = AssessmentLevel.DESCRIPTIONS[level]

        # Формируем детальную оценку на основе критериев
        details = self._get_criteria_details(analysis)

        return f"{label} ({score:.1f}/10.0). {description}. {details}"

    def _get_criteria_details(self, analysis: Analysis) -> str:
        """Возвращает детальную информацию по критериям.

        Args:
            analysis: Анализ документа.

        Returns:
            Текст с деталями по критериям.
        """
        if not analysis.results:
            return "Нет данных по критериям"

        strengths: list[str] = []
        weaknesses: list[str] = []

        for criterion, result_data in analysis.results.items():
            if not isinstance(result_data, dict):
                continue

            score = result_data.get("score", 0.0)
            criterion_name = AnalysisCriteria.DESCRIPTIONS.get(criterion, criterion)

            if score >= 7.0:
                strengths.append(criterion_name)
            elif score < 5.0:
                weaknesses.append(criterion_name)

        details_parts: list[str] = []
        if strengths:
            details_parts.append(f"Сильные стороны: {', '.join(strengths)}")
        if weaknesses:
            details_parts.append(f"Требует улучшения: {', '.join(weaknesses)}")

        return (
            ". ".join(details_parts)
            if details_parts
            else "Все критерии на удовлетворительном уровне"
        )

    def _generate_recommendations(self, analysis: Analysis) -> list[str]:
        """Генерирует рекомендации на основе результатов анализа.

        Args:
            analysis: Анализ документа.

        Returns:
            Список рекомендаций.
        """
        if not analysis.results:
            return ["Недостаточно данных для рекомендаций"]

        recommendations: list[str] = []

        for criterion, result_data in analysis.results.items():
            if not isinstance(result_data, dict):
                continue

            score = result_data.get("score", 0.0)
            criterion_recommendations = result_data.get("recommendations", [])

            if score < 7.0 and criterion_recommendations:
                criterion_name = AnalysisCriteria.DESCRIPTIONS.get(criterion, criterion)
                recommendations.append(
                    f"По критерию '{criterion_name}': {'; '.join(criterion_recommendations)}"
                )

        # Если нет конкретных рекомендаций, добавляем общие
        if not recommendations:
            recommendations.append("Документ в целом соответствует требованиям")

        return recommendations

    async def _generate_supervisor_comments(self, analysis: Analysis) -> list[str]:
        """Генерирует замечания "как у руководителя" с комментариями.

        Args:
            analysis: Анализ документа.

        Returns:
            Список замечаний руководителя.
        """
        if not analysis.results:
            return ["Недостаточно данных для комментариев руководителя"]

        try:
            # Формируем промпт для LLM
            prompt = self._build_supervisor_prompt(analysis)

            config = LLMConfig(
                model="gpt-3.5-turbo",
                max_tokens=500,
                temperature=0.7,
                timeout=30,
                max_retries=2,
            )

            response = await self._llm_client.chat_completion(
                messages=[Message(role="user", content=prompt)],
                config=config,
            )

            # Парсим ответ
            comments = self._parse_supervisor_response(response.content)

            return comments if comments else ["Документ требует внимательного рассмотрения"]

        except Exception as e:
            self._logger.warning(
                "Failed to generate supervisor comments",
                extra={"analysis_id": analysis.id, "error": str(e)},
            )
            # Возвращаем базовые комментарии при ошибке
            return self._generate_basic_supervisor_comments(analysis)

    def _build_supervisor_prompt(self, analysis: Analysis) -> str:
        """Строит промпт для генерации комментариев руководителя.

        Args:
            analysis: Анализ документа.

        Returns:
            Промпт для LLM.
        """
        results_summary = []
        for criterion, result_data in analysis.results.items():
            if not isinstance(result_data, dict):
                continue

            score = result_data.get("score", 0.0)
            comments = result_data.get("comments", [])
            criterion_name = AnalysisCriteria.DESCRIPTIONS.get(criterion, criterion)

            results_summary.append(f"- {criterion_name}: {score}/10.0")
            if comments:
                results_summary.append(f"  Комментарии: {'; '.join(comments)}")

        prompt = f"""Ты опытный научный руководитель дипломных работ. Проанализируй следующие результаты проверки дипломной работы и напиши 3-5 конкретных замечаний в строгом, но конструктивном стиле, как если бы ты был руководителем студента.

Общая оценка: {analysis.overall_score:.1f}/10.0

Результаты по критериям:
{chr(10).join(results_summary)}

Требования к замечаниям:
1. Каждое замечание должно быть конкретным и конструктивным
2. Используй профессиональный научный стиль
3. Указывай, что именно нужно исправить или улучшить
4. При желаемой оценке 7.0+, отмечай критические проблемы
5. Формат ответа: каждое замечание с новой строки

Напиши замечания:"""

        return prompt

    def _parse_supervisor_response(self, response: str) -> list[str]:
        """Парсит ответ LLM с комментариями руководителя.

        Args:
            response: Ответ от LLM.

        Returns:
            Список комментариев.
        """
        # Разбиваем по строкам и фильтруем пустые
        comments = [line.strip() for line in response.split("\n") if line.strip()]

        # Убираем нумерацию, если есть
        cleaned_comments = []
        for comment in comments:
            # Убираем префиксы типа "1.", "-", "*", "•"
            cleaned = comment.lstrip("1234567890-•*.")
            cleaned = cleaned.strip()

            if cleaned and len(cleaned) > 10:  # Игнорируем слишком короткие
                cleaned_comments.append(cleaned)

        return cleaned_comments[:5]  # Возвращаем не более 5 комментариев

    def _generate_basic_supervisor_comments(self, analysis: Analysis) -> list[str]:
        """Генерирует базовые комментарии руководителя без LLM.

        Args:
            analysis: Анализ документа.

        Returns:
            Список базовых комментариев.
        """
        comments: list[str] = []

        if analysis.overall_score is None:
            return ["Документ требует анализа"]

        score = analysis.overall_score

        if score < 5.0:
            comments.append("Работа требует существенной переработки по всем критериям")
        elif score < 7.0:
            comments.append("Работа требует доработки по отмеченным критериям")
        elif score < 8.5:
            comments.append(
                "Работа соответствует базовым требованиям, возможны незначительные улучшения"
            )
        else:
            comments.append("Работа выполнена на высоком уровне")

        # Добавляем конкретные замечания по критериям с низкими оценками
        weak_criteria = []
        for criterion, result_data in analysis.results.items():
            if not isinstance(result_data, dict):
                continue

            score = result_data.get("score", 0.0)
            if score < 5.0:
                criterion_name = AnalysisCriteria.DESCRIPTIONS.get(criterion, criterion)
                weak_criteria.append(criterion_name)

        if weak_criteria:
            comments.append(f"Особое внимание уделите: {', '.join(weak_criteria)}")

        comments.append("Рекомендую согласовать план доработки с руководителем")

        return comments

    async def get_report(self, report_id: str) -> Report:
        """Возвращает отчет по ID.

        Args:
            report_id: ID отчета.

        Returns:
            Отчет.

        Raises:
            ReportGenerationError: Если отчет не найден.
        """
        from app.core.exceptions import ReportNotFoundError

        report = await self._report_repo.get_by_id(report_id)
        if report is None:
            raise ReportNotFoundError(report_id)
        return report

    async def get_report_by_analysis(self, analysis_id: str) -> Report | None:
        """Возвращает отчет по ID анализа.

        Args:
            analysis_id: ID анализа.

        Returns:
            Отчет или None если не найден.
        """
        return await self._report_repo.get_by_analysis_id(analysis_id)

    def _generate_id(self) -> str:
        """Генерирует уникальный ID.

        Returns:
            Уникальный ID.
        """
        import uuid

        return str(uuid.uuid4())
