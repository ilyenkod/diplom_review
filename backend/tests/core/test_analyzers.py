"""
Unit-тесты для анализаторов документов.

Тестирует все анализаторы:
- structure_analyzer.py
- purpose_analyzer.py
- relevance_analyzer.py
- conclusions_analyzer.py
- logic_analyzer.py
- style_analyzer.py
- citations_analyzer.py
- gost_analyzer.py
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

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
from app.core.const import AnalysisCriteria


# ========== Base Analyzer Tests ==========


@pytest.mark.unit
class TestBaseAnalyzerBehavior:
    """Тесты базового поведения анализаторов."""

    @pytest.fixture
    def structure_analyzer(self, mock_llm_client, logger):
        """Возвращает анализатор структуры."""
        return StructureAnalyzer(mock_llm_client, logger)

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, structure_analyzer):
        """Тестирует инициализацию анализатора."""
        assert structure_analyzer.name == AnalysisCriteria.STRUCTURE
        assert structure_analyzer.description == AnalysisCriteria.DESCRIPTIONS[AnalysisCriteria.STRUCTURE]
        assert structure_analyzer.max_score == AnalysisCriteria.MAX_SCORES[AnalysisCriteria.STRUCTURE]

    @pytest.mark.asyncio
    async def test_analyzer_empty_document(self, structure_analyzer):
        """Тестирует анализ пустого документа."""
        result = await structure_analyzer.analyze("   ")

        assert result.score == 0.0
        assert "пуст" in result.comments[0].lower()

    @pytest.mark.asyncio
    async def test_analyzer_successful_analysis(self, structure_analyzer, mock_llm_client):
        """Тестирует успешный анализ."""
        test_response = json.dumps(
            {
                "score": 8.5,
                "comments": ["Good structure", "All sections present"],
                "recommendations": ["Add more details to introduction"],
                "details": {"sections": ["introduction", "main", "conclusion"]},
            }
        )
        mock_llm_client.set_response(test_response)

        result = await structure_analyzer.analyze("Test document content")

        assert result.score == 8.5
        assert len(result.comments) == 2
        assert len(result.recommendations) == 1
        assert result.details is not None
        assert result.analyzer_name == AnalysisCriteria.STRUCTURE

    @pytest.mark.asyncio
    async def test_analyzer_invalid_json_response(self, structure_analyzer, mock_llm_client):
        """Тестирует обработку невалидного JSON ответа."""
        mock_llm_client.set_response("not a valid json")

        with pytest.raises(ValueError, match="Failed to parse"):
            await structure_analyzer.analyze("Test content")

    @pytest.mark.asyncio
    async def test_analyzer_score_clamping(self, structure_analyzer, mock_llm_client):
        """Тестирует ограничение оценки в допустимом диапазоне."""
        # Test score > max_score
        mock_llm_client.set_response(json.dumps({"score": 15.0, "comments": [], "recommendations": []}))
        result = await structure_analyzer.analyze("Test")
        assert result.score == structure_analyzer.max_score

        # Test negative score
        mock_llm_client.set_response(json.dumps({"score": -5.0, "comments": [], "recommendations": []}))
        result = await structure_analyzer.analyze("Test")
        assert result.score == 0.0


# ========== Structure Analyzer Tests ==========


@pytest.mark.unit
class TestStructureAnalyzer:
    """Тесты для анализатора структуры."""

    @pytest.fixture
    def analyzer(self, mock_llm_client, logger):
        """Возвращает анализатор структуры."""
        return StructureAnalyzer(mock_llm_client, logger)

    @pytest.mark.asyncio
    async def test_structure_analyzer_name_and_description(self, analyzer):
        """Тестирует имя и описание анализатора."""
        assert analyzer.name == "structure"
        assert analyzer.description == AnalysisCriteria.DESCRIPTIONS["structure"]

    @pytest.mark.asyncio
    async def test_structure_analyzer_builds_prompt(self, analyzer, mock_llm_client):
        """Тестирует построение промпта."""
        mock_llm_client.set_response(
            json.dumps({"score": 7.0, "comments": [], "recommendations": []})
        )

        result = await analyzer.analyze("Test document content")

        # Check that analysis completed successfully
        assert result is not None
        assert result.score == 7.0


# ========== Purpose Analyzer Tests ==========


@pytest.mark.unit
class TestPurposeAnalyzer:
    """Тесты для анализатора цели и задач."""

    @pytest.fixture
    def analyzer(self, mock_llm_client, logger):
        """Возвращает анализатор цели и задач."""
        return PurposeAnalyzer(mock_llm_client, logger)

    @pytest.mark.asyncio
    async def test_purpose_analyzer_initialization(self, analyzer):
        """Тестирует инициализацию анализатора."""
        assert analyzer.name == "purpose"
        assert analyzer.description == AnalysisCriteria.DESCRIPTIONS["purpose"]
        assert analyzer.max_score == AnalysisCriteria.MAX_SCORES["purpose"]

    @pytest.mark.asyncio
    async def test_purpose_analyzer_analysis(self, analyzer, mock_llm_client):
        """Тестирует анализ цели и задач."""
        test_response = json.dumps(
            {
                "score": 8.0,
                "comments": ["Clear goal", "Tasks are well-defined"],
                "recommendations": ["Add more specific tasks"],
            }
        )
        mock_llm_client.set_response(test_response)

        result = await analyzer.analyze("Goal: Analyze data. Tasks: 1. Collect, 2. Process.")

        assert result.score == 8.0
        assert len(result.comments) == 2
        assert len(result.recommendations) == 1


# ========== Relevance Analyzer Tests ==========


@pytest.mark.unit
class TestRelevanceAnalyzer:
    """Тесты для анализатора актуальности."""

    @pytest.fixture
    def analyzer(self, mock_llm_client, logger):
        """Возвращает анализатор актуальности."""
        return RelevanceAnalyzer(mock_llm_client, logger)

    @pytest.mark.asyncio
    async def test_relevance_analyzer_initialization(self, analyzer):
        """Тестирует инициализацию анализатора."""
        assert analyzer.name == "relevance"
        assert analyzer.description == AnalysisCriteria.DESCRIPTIONS["relevance"]

    @pytest.mark.asyncio
    async def test_relevance_analyzer_analysis(self, analyzer, mock_llm_client):
        """Тестирует анализ актуальности темы."""
        test_response = json.dumps(
            {
                "score": 7.5,
                "comments": ["Topic is relevant"],
                "recommendations": ["Add recent references"],
            }
        )
        mock_llm_client.set_response(test_response)

        result = await analyzer.analyze("Document about modern AI technologies")

        assert result.score == 7.5
        assert len(result.comments) >= 1


# ========== Conclusions Analyzer Tests ==========


@pytest.mark.unit
class TestConclusionsAnalyzer:
    """Тесты для анализатора выводов."""

    @pytest.fixture
    def analyzer(self, mock_llm_client, logger):
        """Возвращает анализатор выводов."""
        return ConclusionsAnalyzer(mock_llm_client, logger)

    @pytest.mark.asyncio
    async def test_conclusions_analyzer_initialization(self, analyzer):
        """Тестирует инициализацию анализатора."""
        assert analyzer.name == "conclusions"
        assert analyzer.description == AnalysisCriteria.DESCRIPTIONS["conclusions"]

    @pytest.mark.asyncio
    async def test_conclusions_analyzer_analysis(self, analyzer, mock_llm_client):
        """Тестирует анализ выводов."""
        test_response = json.dumps(
            {
                "score": 9.0,
                "comments": ["Clear conclusions"],
                "recommendations": ["Add future work"],
            }
        )
        mock_llm_client.set_response(test_response)

        result = await analyzer.analyze(
            "In conclusion, this research shows that AI is effective for analysis."
        )

        assert result.score == 9.0
        assert len(result.comments) >= 1


# ========== Logic Analyzer Tests ==========


@pytest.mark.unit
class TestLogicAnalyzer:
    """Тесты для анализатора логики."""

    @pytest.fixture
    def analyzer(self, mock_llm_client, logger):
        """Возвращает анализатор логики."""
        return LogicAnalyzer(mock_llm_client, logger)

    @pytest.mark.asyncio
    async def test_logic_analyzer_initialization(self, analyzer):
        """Тестирует инициализацию анализатора."""
        assert analyzer.name == "logic"
        assert analyzer.description == AnalysisCriteria.DESCRIPTIONS["logic"]

    @pytest.mark.asyncio
    async def test_logic_analyzer_analysis(self, analyzer, mock_llm_client):
        """Тестирует анализ логической связности."""
        test_response = json.dumps(
            {
                "score": 8.0,
                "comments": ["Good flow"],
                "recommendations": ["Better transitions"],
            }
        )
        mock_llm_client.set_response(test_response)

        result = await analyzer.analyze("First point. Second point. Conclusion follows logically.")

        assert result.score == 8.0


# ========== Style Analyzer Tests ==========


@pytest.mark.unit
class TestStyleAnalyzer:
    """Тесты для анализатора стиля."""

    @pytest.fixture
    def analyzer(self, mock_llm_client, logger):
        """Возвращает анализатор стиля."""
        return StyleAnalyzer(mock_llm_client, logger)

    @pytest.mark.asyncio
    async def test_style_analyzer_initialization(self, analyzer):
        """Тестирует инициализацию анализатора."""
        assert analyzer.name == "style"
        assert analyzer.description == AnalysisCriteria.DESCRIPTIONS["style"]

    @pytest.mark.asyncio
    async def test_style_analyzer_analysis(self, analyzer, mock_llm_client):
        """Тестирует анализ научного стиля."""
        test_response = json.dumps(
            {
                "score": 7.5,
                "comments": ["Formal style"],
                "recommendations": ["Avoid contractions"],
            }
        )
        mock_llm_client.set_response(test_response)

        result = await analyzer.analyze(
            "The research methodology involves data collection and analysis."
        )

        assert result.score == 7.5


# ========== Citations Analyzer Tests ==========


@pytest.mark.unit
class TestCitationsAnalyzer:
    """Тесты для анализатора цитирования."""

    @pytest.fixture
    def analyzer(self, mock_llm_client, logger):
        """Возвращает анализатор цитирования."""
        return CitationsAnalyzer(mock_llm_client, logger)

    @pytest.mark.asyncio
    async def test_citations_analyzer_initialization(self, analyzer):
        """Тестирует инициализацию анализатора."""
        assert analyzer.name == "citations"
        assert analyzer.description == AnalysisCriteria.DESCRIPTIONS["citations"]

    @pytest.mark.asyncio
    async def test_citations_analyzer_analysis(self, analyzer, mock_llm_client):
        """Тестирует анализ цитирования."""
        test_response = json.dumps(
            {
                "score": 8.5,
                "comments": ["Proper citations"],
                "recommendations": ["Add more recent sources"],
            }
        )
        mock_llm_client.set_response(test_response)

        result = await analyzer.analyze(
            "According to Smith (2020), the results show significant improvement."
        )

        assert result.score == 8.5


# ========== GOST Analyzer Tests ==========


@pytest.mark.unit
class TestGOSTAnalyzer:
    """Тесты для анализатора ГОСТ."""

    @pytest.fixture
    def analyzer(self, mock_llm_client, logger):
        """Возвращает анализатор ГОСТ."""
        return GOSTAnalyzer(mock_llm_client, logger)

    @pytest.mark.asyncio
    async def test_gost_analyzer_initialization(self, analyzer):
        """Тестирует инициализацию анализатора."""
        assert analyzer.name == "gost"
        assert analyzer.description == AnalysisCriteria.DESCRIPTIONS["gost"]

    @pytest.mark.asyncio
    async def test_gost_analyzer_analysis(self, analyzer, mock_llm_client):
        """Тестирует анализ соответствия ГОСТ."""
        test_response = json.dumps(
            {
                "score": 9.0,
                "comments": ["Follows GOST standards"],
                "recommendations": ["Check page numbering"],
            }
        )
        mock_llm_client.set_response(test_response)

        result = await analyzer.analyze("Document formatted according to GOST requirements.")

        assert result.score == 9.0


# ========== Analyzer Integration Tests ==========


@pytest.mark.unit
class TestAnalyzersIntegration:
    """Интеграционные тесты для анализаторов."""

    @pytest.fixture
    def all_analyzers(self, mock_llm_client, logger):
        """Возвращает все анализаторы."""
        return {
            "structure": StructureAnalyzer(mock_llm_client, logger),
            "purpose": PurposeAnalyzer(mock_llm_client, logger),
            "relevance": RelevanceAnalyzer(mock_llm_client, logger),
            "conclusions": ConclusionsAnalyzer(mock_llm_client, logger),
            "logic": LogicAnalyzer(mock_llm_client, logger),
            "style": StyleAnalyzer(mock_llm_client, logger),
            "citations": CitationsAnalyzer(mock_llm_client, logger),
            "gost": GOSTAnalyzer(mock_llm_client, logger),
        }

    @pytest.mark.asyncio
    async def test_all_analyzers_have_valid_names(self, all_analyzers):
        """Тестирует, что все анализаторы имеют валидные имена."""
        for name, analyzer in all_analyzers.items():
            assert analyzer.name == name
            assert analyzer.description is not None
            assert analyzer.max_score > 0

    @pytest.mark.asyncio
    async def test_all_analyzers_can_analyze(self, all_analyzers, mock_llm_client):
        """Тестирует, что все анализаторы могут анализировать документы."""
        mock_llm_client.set_response(
            json.dumps(
                {"score": 7.5, "comments": ["Test comment"], "recommendations": ["Test recommendation"]}
            )
        )

        for name, analyzer in all_analyzers.items():
            result = await analyzer.analyze("Test document content")
            assert result.score == 7.5
            assert result.analyzer_name == name

    @pytest.mark.asyncio
    async def test_all_analyzers_handle_percentage_scores(self, all_analyzers, mock_llm_client):
        """Тестирует обработку оценок в процентах."""
        # Some LLMs might return scores as percentages (0-100)
        mock_llm_client.set_response(json.dumps({"score": 85, "comments": [], "recommendations": []}))

        for analyzer in all_analyzers.values():
            result = await analyzer.analyze("Test content")
            # Score should be normalized to max_score (10 or specified value)
            assert 0 <= result.score <= analyzer.max_score
