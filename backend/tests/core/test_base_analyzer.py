"""
Тесты для базового анализатора.
"""

from unittest.mock import AsyncMock

import pytest

from app.core.analyzers.base_analyzer import (
    AnalyzerCriteria,
    AnalyzerResult,
    BaseAnalyzer,
)
from app.core.interfaces.llm import LLMClient, LLMResponse
from app.infrastructure.logging import AppLogger


class MockAnalyzer(BaseAnalyzer):
    """Мок анализатора для тестов."""

    def __init__(self, llm_client: LLMClient, logger: AppLogger) -> None:
        """Инициализирует мок анализатора."""
        super().__init__(
            name="mock_analyzer",
            description="Mock analyzer for testing",
            llm_client=llm_client,
            logger=logger,
        )

    def _build_prompt(self, text: str, **kwargs) -> list:
        """Строит промпт для анализа."""
        from app.core.interfaces.llm import Message

        return [Message(role="user", content=f"Analyze: {text}")]


class TestAnalyzerResult:
    """Тесты класса AnalyzerResult."""

    def test_create_result(self) -> None:
        """Тест создания результата."""
        result = AnalyzerResult(
            score=8.5,
            comments=["Comment 1", "Comment 2"],
            recommendations=["Rec 1"],
        )
        assert result.score == 8.5
        assert result.comments == ["Comment 1", "Comment 2"]
        assert result.recommendations == ["Rec 1"]

    def test_create_result_with_empty_lists(self) -> None:
        """Тест создания результата с пустыми списками."""
        result = AnalyzerResult(score=10.0, comments=[], recommendations=[])
        assert result.score == 10.0
        assert result.comments == []
        assert result.recommendations == []

    def test_create_result_min_score(self) -> None:
        """Тест создания результата с минимальной оценкой."""
        result = AnalyzerResult(score=0.0, comments=[], recommendations=[])
        assert result.score == 0.0

    def test_create_result_max_score(self) -> None:
        """Тест создания результата с максимальной оценкой."""
        result = AnalyzerResult(score=10.0, comments=[], recommendations=[])
        assert result.score == 10.0

    def test_to_dict(self) -> None:
        """Тест конвертации в словарь."""
        result = AnalyzerResult(
            score=8.5,
            comments=["Comment 1"],
            recommendations=["Rec 1"],
        )
        result_dict = result.to_dict()
        assert result_dict["score"] == 8.5
        assert result_dict["comments"] == ["Comment 1"]
        assert result_dict["recommendations"] == ["Rec 1"]

    def test_to_dict_with_analyzer_info(self) -> None:
        """Тест конвертации в словарь с информацией об анализаторе."""
        result = AnalyzerResult(
            score=8.5,
            comments=["Comment 1"],
            recommendations=["Rec 1"],
            analyzer_name="test_analyzer",
            analyzer_description="Test analyzer",
        )
        result_dict = result.to_dict()
        assert result_dict["analyzer_name"] == "test_analyzer"
        assert result_dict["analyzer_description"] == "Test analyzer"


class TestAnalyzerCriteria:
    """Тесты класса AnalyzerCriteria."""

    def test_create_criteria(self) -> None:
        """Тест создания критериев."""
        criteria = AnalyzerCriteria(
            name="structure",
            description="Structure analysis",
            max_score=10.0,
        )
        assert criteria.name == "structure"
        assert criteria.description == "Structure analysis"
        assert criteria.max_score == 10.0

    def test_to_dict(self) -> None:
        """Тест конвертации в словарь."""
        criteria = AnalyzerCriteria(
            name="style",
            description="Style analysis",
            max_score=10.0,
        )
        criteria_dict = criteria.to_dict()
        assert criteria_dict["name"] == "style"
        assert criteria_dict["description"] == "Style analysis"
        assert criteria_dict["max_score"] == 10.0


class TestBaseAnalyzer:
    """Тесты базового анализатора."""

    @pytest.fixture
    def mock_llm_client(self) -> LLMClient:
        """Возвращает мок клиента LLM."""
        client = AsyncMock(spec=LLMClient)
        client.completion = AsyncMock(
            return_value=LLMResponse(
                content='{"score": 8.5, "comments": [], "recommendations": []}',
                model="test-model",
                tokens_used={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
                finish_reason="stop",
            )
        )
        return client

    @pytest.fixture
    def analyzer(self, mock_llm_client: LLMClient, logger: AppLogger) -> MockAnalyzer:
        """Возвращает мок анализатор."""
        return MockAnalyzer(mock_llm_client, logger)

    async def test_analyze_success(
        self, analyzer: MockAnalyzer, mock_llm_client: LLMClient
    ) -> None:
        """Тест успешного анализа."""
        text = "Test document text"
        result = await analyzer.analyze(text)

        assert result.score == 8.5
        assert result.comments == []
        assert result.recommendations == []
        mock_llm_client.completion.assert_called_once()

    async def test_analyze_with_criteria(self, analyzer: MockAnalyzer) -> None:
        """Тест анализа с критериями."""
        text = "Test document text"
        result = await analyzer.analyze(text)

        assert result.score >= 0.0
        assert result.score <= 10.0
        assert result.comments is not None
        assert result.recommendations is not None

    async def test_analyze_with_empty_text(self, analyzer: MockAnalyzer) -> None:
        """Тест анализа с пустым текстом."""
        result = await analyzer.analyze("")

        assert result.score >= 0.0
        assert result.score <= 10.0

    async def test_analyze_gets_criteria(self, analyzer: MockAnalyzer) -> None:
        """Тест получения критериев анализатора."""
        criteria = analyzer.get_criteria()

        assert criteria.name == "mock_analyzer"
        assert criteria.description == "Mock analyzer for testing"
        assert criteria.max_score == 10.0

    async def test_analyze_parses_llm_response(
        self, analyzer: MockAnalyzer, mock_llm_client: LLMClient
    ) -> None:
        """Тест парсинга ответа от LLM."""
        mock_llm_client.completion = AsyncMock(
            return_value='{"score": 9.0, "comments": ["Good structure"], "recommendations": ["Add more details"]}'
        )

        text = "Test document text"
        result = await analyzer.analyze(text)

        assert result.score == 9.0
        assert result.comments == ["Good structure"]
        assert result.recommendations == ["Add more details"]

    async def test_analyze_with_invalid_json(
        self, analyzer: MockAnalyzer, mock_llm_client: LLMClient
    ) -> None:
        """Тест анализа с невалидным JSON."""
        mock_llm_client.completion = AsyncMock(return_value="Invalid JSON")

        with pytest.raises(ValueError, match="Failed to parse LLM response"):
            await analyzer.analyze("Test text")

    async def test_analyze_with_score_out_of_range(
        self, analyzer: MockAnalyzer, mock_llm_client: LLMClient
    ) -> None:
        """Тест анализа с оценкой вне диапазона."""
        mock_llm_client.completion = AsyncMock(
            return_value='{"score": 15.0, "comments": [], "recommendations": []}'
        )

        text = "Test document text"
        result = await analyzer.analyze(text)

        assert result.score == 10.0  # Должен быть ограничен максимумом

    async def test_analyze_with_negative_score(
        self, analyzer: MockAnalyzer, mock_llm_client: LLMClient
    ) -> None:
        """Тест анализа с отрицательной оценкой."""
        mock_llm_client.completion = AsyncMock(
            return_value='{"score": -5.0, "comments": [], "recommendations": []}'
        )

        text = "Test document text"
        result = await analyzer.analyze(text)

        assert result.score == 0.0  # Должен быть ограничен минимумом

    async def test_analyze_with_missing_fields(
        self, analyzer: MockAnalyzer, mock_llm_client: LLMClient
    ) -> None:
        """Тест анализа с отсутствующими полями."""
        mock_llm_client.completion = AsyncMock(return_value='{"score": 8.5}')

        text = "Test document text"
        result = await analyzer.analyze(text)

        assert result.score == 8.5
        assert result.comments == []
        assert result.recommendations == []

    async def test_analyze_with_empty_response(
        self, analyzer: MockAnalyzer, mock_llm_client: LLMClient
    ) -> None:
        """Тест анализа с пустым ответом."""
        mock_llm_client.completion = AsyncMock(
            return_value='{"score": 0.0, "comments": [], "recommendations": []}'
        )

        text = "Test document text"
        result = await analyzer.analyze(text)

        assert result.score == 0.0
        assert result.comments == []
        assert result.recommendations == []

    def test_analyzer_name(self, analyzer: MockAnalyzer) -> None:
        """Тест имени анализатора."""
        assert analyzer.name == "mock_analyzer"

    def test_analyzer_description(self, analyzer: MockAnalyzer) -> None:
        """Тест описания анализатора."""
        assert analyzer.description == "Mock analyzer for testing"

    def test_analyzer_max_score(self, analyzer: MockAnalyzer) -> None:
        """Тест максимальной оценки анализатора."""
        assert analyzer.max_score == 10.0
