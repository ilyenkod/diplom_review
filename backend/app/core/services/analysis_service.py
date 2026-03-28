"""
Сервис анализа документов.

Организует запуск всех анализаторов для документа, агрегирует результаты и вычисляет общую оценку.
"""

from dataclasses import dataclass
from typing import Any

from app.core.analyzers import (
    CitationsAnalyzer,
    ConclusionsAnalyzer,
    GOSTAnalyzer,
    LogicAnalyzer,
    PurposeAnalyzer,
    RelevanceAnalyzer,
    StructureAnalyzer,
    StyleAnalyzer,
)
from app.core.analyzers.base_analyzer import AnalyzerResult, BaseAnalyzer
from app.core.const import AnalysisCriteria, AssessmentLevel, CacheTTL
from app.core.domain import Analysis, AnalysisStatus
from app.core.exceptions import (
    AnalysisAlreadyRunningError,
    AnalysisFailedError,
    AnalysisNotFoundError,
    AnalyzerError,
    DocumentNotFoundError,
)
from app.core.interfaces.database import AnalysisRepository, DocumentRepository
from app.core.interfaces.llm import LLMClient
from app.infrastructure.cache.repository import CacheRepository
from app.infrastructure.logging import AppLogger


@dataclass
class AnalysisConfig:
    """Конфигурация запуска анализа."""

    use_cache: bool = True
    cache_ttl: int = CacheTTL.ANALYSIS
    parallel_analyzers: bool = True


class AnalysisService:
    """Сервис для анализа документов."""

    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        document_repo: DocumentRepository,
        cache_repo: CacheRepository,
        llm_client: LLMClient,
        logger: AppLogger,
        config: AnalysisConfig | None = None,
    ) -> None:
        """Инициализирует сервис анализа.

        Args:
            analysis_repo: Репозиторий анализов.
            document_repo: Репозиторий документов.
            cache_repo: Репозиторий кэша.
            llm_client: Клиент LLM.
            logger: Логгер приложения.
            config: Конфигурация анализа.
        """
        self._analysis_repo = analysis_repo
        self._document_repo = document_repo
        self._cache_repo = cache_repo
        self._llm_client = llm_client
        self._logger = logger
        self._config = config or AnalysisConfig()
        self._analyzers: dict[str, BaseAnalyzer] = {}

    def _initialize_analyzers(self) -> None:
        """Инициализирует все анализаторы."""
        if self._analyzers:
            return

        self._analyzers[AnalysisCriteria.STRUCTURE] = StructureAnalyzer(
            self._llm_client, self._logger
        )
        self._analyzers[AnalysisCriteria.PURPOSE] = PurposeAnalyzer(self._llm_client, self._logger)
        self._analyzers[AnalysisCriteria.RELEVANCE] = RelevanceAnalyzer(
            self._llm_client, self._logger
        )
        self._analyzers[AnalysisCriteria.CONCLUSIONS] = ConclusionsAnalyzer(
            self._llm_client, self._logger
        )
        self._analyzers[AnalysisCriteria.LOGIC] = LogicAnalyzer(self._llm_client, self._logger)
        self._analyzers[AnalysisCriteria.STYLE] = StyleAnalyzer(self._llm_client, self._logger)
        self._analyzers[AnalysisCriteria.CITATIONS] = CitationsAnalyzer(
            self._llm_client, self._logger
        )
        self._analyzers[AnalysisCriteria.GOST] = GOSTAnalyzer(self._llm_client, self._logger)

        self._logger.info("Analyzers initialized", extra={"count": len(self._analyzers)})

    async def start_analysis(self, document_id: str) -> Analysis:
        """Запускает анализ документа.

        Args:
            document_id: ID документа для анализа.

        Returns:
            Созданная запись анализа со статусом PENDING.

        Raises:
            DocumentNotFoundError: Если документ не найден.
            AnalysisAlreadyRunningError: Если анализ уже выполняется.
        """
        # Проверяем существование документа
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        # Проверяем, есть ли активный анализ
        latest_analysis = await self._analysis_repo.get_latest_by_document_id(document_id)
        if latest_analysis is not None and latest_analysis.is_processing:
            raise AnalysisAlreadyRunningError(document_id)

        # Создаем новую запись анализа
        analysis = Analysis(
            id=self._generate_id(),
            document_id=document_id,
            status=AnalysisStatus.PENDING.value,
        )
        analysis.start()

        created_analysis = await self._analysis_repo.create(analysis)

        self._logger.info(
            "Analysis started",
            extra={
                "analysis_id": analysis.id,
                "document_id": document_id,
            },
        )

        return created_analysis

    async def analyze_document(self, document_id: str, analysis_id: str | None = None) -> Analysis:
        """Выполняет полный анализ документа.

        Args:
            document_id: ID документа для анализа.
            analysis_id: Опциональный ID существующего анализа.

        Returns:
            Результат анализа с общей оценкой и результатами по критериям.

        Raises:
            DocumentNotFoundError: Если документ не найден.
            AnalysisFailedError: Если анализ завершился с ошибкой.
            AnalyzerError: Если анализатор вернул ошибку.
        """
        # Проверяем существование документа
        document = await self._document_repo.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(document_id)

        # Проверяем кэш
        if self._config.use_cache:
            cached_analysis = await self._cache_repo.get_analysis(document_id)
            if cached_analysis is not None:
                self._logger.info(
                    "Analysis retrieved from cache",
                    extra={"document_id": document_id},
                )
                if isinstance(cached_analysis, Analysis):
                    return cached_analysis
                # Если из кэша пришел словарь, создаем объект Analysis
                return Analysis(
                    id=cached_analysis.get("id", ""),
                    document_id=cached_analysis.get("document_id", document_id),
                    status=cached_analysis.get("status", AnalysisStatus.PENDING.value),
                    overall_score=cached_analysis.get("overall_score"),
                    results=cached_analysis.get("results", {}),
                )

        # Инициализируем анализаторы
        self._initialize_analyzers()

        # Создаем или получаем анализ
        if analysis_id is None:
            analysis = await self.start_analysis(document_id)
        else:
            found_analysis = await self._analysis_repo.get_by_id(analysis_id)
            if found_analysis is None:
                raise AnalysisNotFoundError(analysis_id)
            analysis = found_analysis
            analysis.start()

        try:
            self._logger.info(
                "Running analyzers",
                extra={
                    "analysis_id": analysis.id,
                    "document_id": document_id,
                    "analyzers": list(self._analyzers.keys()),
                },
            )

            # Запускаем все анализаторы
            results: dict[str, AnalyzerResult] = {}
            document_content = document.content or ""
            for analyzer_name, analyzer in self._analyzers.items():
                try:
                    result = await analyzer.analyze(document_content)
                    results[analyzer_name] = result
                    self._logger.debug(
                        f"Analyzer {analyzer_name} completed",
                        extra={
                            "analyzer": analyzer_name,
                            "score": result.score,
                        },
                    )
                except AnalyzerError as e:
                    self._logger.error(
                        f"Analyzer {analyzer_name} failed: {e.message}",
                        extra={"analyzer": analyzer_name, "error": e.message},
                    )
                    raise AnalysisFailedError(
                        f"Analyzer {analyzer_name} failed: {e.message}"
                    ) from e

            # Агрегируем результаты
            aggregated_results = self._aggregate_results(results)

            # Вычисляем общую оценку
            overall_score = self._calculate_overall_score(results)

            # Завершаем анализ
            analysis.complete(overall_score, aggregated_results)

            # Сохраняем результаты
            await self._analysis_repo.update_result(
                analysis.id,
                overall_score,
                aggregated_results,
            )

            # Кэшируем результаты
            if self._config.use_cache:
                await self._cache_repo.set_analysis(
                    document_id,
                    analysis,
                    ttl=self._config.cache_ttl,
                )

            self._logger.info(
                "Analysis completed",
                extra={
                    "analysis_id": analysis.id,
                    "document_id": document_id,
                    "overall_score": overall_score,
                },
            )

            return analysis

        except Exception as e:
            # Помечаем анализ как неудачный
            error_message = str(e)
            analysis.fail(error_message)
            await self._analysis_repo.update_status(analysis.id, AnalysisStatus.FAILED.value)

            self._logger.error(
                "Analysis failed",
                extra={
                    "analysis_id": analysis.id,
                    "document_id": document_id,
                    "error": error_message,
                },
            )

            if isinstance(e, (DocumentNotFoundError, AnalysisFailedError, AnalyzerError)):
                raise
            raise AnalysisFailedError(error_message) from e

    def _aggregate_results(self, results: dict[str, AnalyzerResult]) -> dict[str, Any]:
        """Агрегирует результаты всех анализаторов.

        Args:
            results: Словарь результатов по анализаторам.

        Returns:
            Агрегированные результаты.
        """
        aggregated: dict[str, Any] = {}

        for analyzer_name, result in results.items():
            aggregated[analyzer_name] = {
                "score": result.score,
                "max_score": result.score,
                "comments": result.comments,
                "recommendations": result.recommendations,
                "analyzer_name": result.analyzer_name,
                "analyzer_description": result.analyzer_description,
            }

            if result.details:
                aggregated[analyzer_name]["details"] = result.details

        return aggregated

    def _calculate_overall_score(self, results: dict[str, AnalyzerResult]) -> float:
        """Вычисляет общую оценку на основе весов критериев.

        Args:
            results: Словарь результатов по анализаторам.

        Returns:
            Общая оценка в диапазоне [0, 10].
        """
        total_weighted_score = 0.0
        total_weight = 0.0

        for criterion, result in results.items():
            weight = AnalysisCriteria.WEIGHTS.get(criterion, 1.0)
            max_score = AnalysisCriteria.MAX_SCORES.get(criterion, 10.0)

            # Нормализуем оценку к диапазону [0, max_score]
            normalized_score = min(result.score, max_score)

            # Добавляем взвешенную оценку
            total_weighted_score += normalized_score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        # Нормализуем к диапазону [0, 10]
        overall_score = total_weighted_score / total_weight
        return min(max(overall_score, 0.0), 10.0)

    def get_assessment_level(self, score: float) -> str:
        """Возвращает уровень оценки по числовому значению.

        Args:
            score: Оценка от 0 до 10.

        Returns:
            Уровень оценки (excellent, good, satisfactory, poor).
        """
        if score >= AssessmentLevel.SCORE_RANGES[AssessmentLevel.EXCELLENT][0]:
            return AssessmentLevel.EXCELLENT
        elif score >= AssessmentLevel.SCORE_RANGES[AssessmentLevel.GOOD][0]:
            return AssessmentLevel.GOOD
        elif score >= AssessmentLevel.SCORE_RANGES[AssessmentLevel.SATISFACTORY][0]:
            return AssessmentLevel.SATISFACTORY
        else:
            return AssessmentLevel.POOR

    async def get_analysis(self, analysis_id: str) -> Analysis:
        """Возвращает анализ по ID.

        Args:
            analysis_id: ID анализа.

        Returns:
            Анализ.

        Raises:
            AnalysisNotFoundError: Если анализ не найден.
        """
        analysis = await self._analysis_repo.get_by_id(analysis_id)
        if analysis is None:
            raise AnalysisNotFoundError(analysis_id)
        return analysis

    async def get_document_analyses(self, document_id: str) -> list[Analysis]:
        """Возвращает все анализы документа.

        Args:
            document_id: ID документа.

        Returns:
            Список анализов документа.
        """
        return await self._analysis_repo.get_by_document_id(document_id)

    async def reanalyze_document(self, document_id: str) -> Analysis:
        """Повторно анализирует документ.

        Args:
            document_id: ID документа для повторного анализа.

        Returns:
            Новый анализ.

        Raises:
            DocumentNotFoundError: Если документ не найден.
        """
        # Инвалидируем кэш
        if self._config.use_cache:
            await self._cache_repo.delete_analysis(document_id)

        # Запускаем новый анализ
        return await self.analyze_document(document_id)

    def _generate_id(self) -> str:
        """Генерирует уникальный ID.

        Returns:
            Уникальный ID.
        """
        import uuid

        return str(uuid.uuid4())
