"""
Тесты для модуля промптов LLM.
"""

import pytest

from app.infrastructure.llm.prompts import (
    PromptBuilder,
    PromptTemplate,
    get_prompt_for_analyzer,
)


class TestPromptTemplate:
    """Тесты класса PromptTemplate."""

    def test_create_template(self) -> None:
        """Тест создания шаблона промпта."""
        template = PromptTemplate(
            system_prompt="You are a helpful assistant.",
            user_template="Analyze this: {text}",
        )
        assert template.system_prompt == "You are a helpful assistant."
        assert template.user_template == "Analyze this: {text}"

    def test_format_user_prompt(self) -> None:
        """Тест форматирования пользовательского промпта."""
        template = PromptTemplate(
            system_prompt="You are a helpful assistant.",
            user_template="Analyze this: {text} with criteria {criteria}",
        )
        result = template.format_user_prompt(text="test text", criteria="structure")
        assert result == "Analyze this: test text with criteria structure"

    def test_format_with_missing_variable(self) -> None:
        """Тест форматирования с отсутствующей переменной."""
        template = PromptTemplate(
            system_prompt="You are a helpful assistant.",
            user_template="Analyze this: {text}",
        )
        with pytest.raises(KeyError):
            template.format_user_prompt(criteria="structure")


class TestPromptBuilder:
    """Тесты класса PromptBuilder."""

    def test_initial_state(self) -> None:
        """Тест начального состояния билдера."""
        builder = PromptBuilder()
        assert builder._system_prompt is None
        assert builder._context is None

    def test_set_system_prompt(self) -> None:
        """Тест установки системного промпта."""
        builder = PromptBuilder().set_system_prompt("System message")
        assert builder._system_prompt == "System message"

    def test_set_context(self) -> None:
        """Тест установки контекста."""
        context = {"document_type": "thesis", "word_count": 10000}
        builder = PromptBuilder().set_context(context)
        assert builder._context == context

    def test_add_requirement(self) -> None:
        """Тест добавления требования."""
        builder = PromptBuilder().add_requirement("Check structure")
        builder.add_requirement("Check style")
        assert builder._requirements == ["Check structure", "Check style"]

    def test_add_example(self) -> None:
        """Тест добавления примера."""
        builder = PromptBuilder().add_example("Good example")
        assert builder._examples == ["Good example"]

    def test_add_constraint(self) -> None:
        """Тест добавления ограничения."""
        builder = PromptBuilder().add_constraint("Max 1000 words")
        assert builder._constraints == ["Max 1000 words"]

    def test_set_output_format(self) -> None:
        """Тест установки формата вывода."""
        builder = PromptBuilder().set_output_format("JSON")
        assert builder._output_format == "JSON"

    def test_build_without_system_prompt(self) -> None:
        """Тест сборки промпта без системного сообщения."""
        with pytest.raises(ValueError, match="System prompt is required"):
            PromptBuilder().build()

    def test_build_simple(self) -> None:
        """Тест сборки простого промпта."""
        builder = PromptBuilder().set_system_prompt("Analyze the text")
        template = builder.build()
        assert template.system_prompt == "Analyze the text"
        assert "{text}" in template.user_template
        assert "Text to analyze:" in template.user_template

    def test_build_with_requirements(self) -> None:
        """Тест сборки промпта с требованиями."""
        builder = PromptBuilder().set_system_prompt("Analyze the text")
        builder.add_requirement("Check structure")
        builder.add_requirement("Check style")
        template = builder.build()
        assert "Check structure" in template.user_template
        assert "Check style" in template.user_template

    def test_build_with_examples(self) -> None:
        """Тест сборки промпта с примерами."""
        builder = PromptBuilder().set_system_prompt("Analyze the text")
        builder.add_example("Good structure example")
        template = builder.build()
        assert "Good structure example" in template.user_template

    def test_build_with_constraints(self) -> None:
        """Тест сборки промпта с ограничениями."""
        builder = PromptBuilder().set_system_prompt("Analyze the text")
        builder.add_constraint("Max 1000 words")
        template = builder.build()
        assert "Max 1000 words" in template.user_template

    def test_build_with_output_format(self) -> None:
        """Тест сборки промпта с форматом вывода."""
        builder = PromptBuilder().set_system_prompt("Analyze the text")
        builder.set_output_format("JSON with fields: score, comments, recommendations")
        template = builder.build()
        assert "JSON with fields: score, comments, recommendations" in template.user_template

    def test_build_complete(self) -> None:
        """Тест сборки полного промпта."""
        builder = (
            PromptBuilder()
            .set_system_prompt("Analyze the document structure")
            .set_context({"document_type": "thesis"})
            .add_requirement("Check introduction")
            .add_requirement("Check main sections")
            .add_requirement("Check conclusion")
            .add_example("Introduction: This thesis explores...")
            .add_constraint("Return score from 0 to 10")
            .set_output_format("JSON")
        )
        template = builder.build()

        assert template.system_prompt == "Analyze the document structure"
        assert "{text}" in template.user_template
        assert "Check introduction" in template.user_template
        assert "Check main sections" in template.user_template
        assert "Check conclusion" in template.user_template
        assert "Introduction: This thesis explores..." in template.user_template
        assert "Return score from 0 to 10" in template.user_template
        assert "JSON" in template.user_template


class TestPromptTemplates:
    """Тесты функций для получения промптов для анализаторов."""

    def test_get_structure_prompt(self) -> None:
        """Тест получения промпта для анализатора структуры."""
        template = get_prompt_for_analyzer("structure")
        assert template is not None
        assert "{text}" in template.user_template

    def test_get_purpose_prompt(self) -> None:
        """Тест получения промпта для анализатора цели."""
        template = get_prompt_for_analyzer("purpose")
        assert template is not None
        assert "{text}" in template.user_template

    def test_get_relevance_prompt(self) -> None:
        """Тест получения промпта для анализатора актуальности."""
        template = get_prompt_for_analyzer("relevance")
        assert template is not None

    def test_get_conclusions_prompt(self) -> None:
        """Тест получения промпта для анализатора выводов."""
        template = get_prompt_for_analyzer("conclusions")
        assert template is not None

    def test_get_logic_prompt(self) -> None:
        """Тест получения промпта для анализатора логики."""
        template = get_prompt_for_analyzer("logic")
        assert template is not None

    def test_get_style_prompt(self) -> None:
        """Тест получения промпта для анализатора стиля."""
        template = get_prompt_for_analyzer("style")
        assert template is not None

    def test_get_citations_prompt(self) -> None:
        """Тест получения промпта для анализатора цитирования."""
        template = get_prompt_for_analyzer("citations")
        assert template is not None

    def test_get_gost_prompt(self) -> None:
        """Тест получения промпта для анализатора ГОСТ."""
        template = get_prompt_for_analyzer("gost")
        assert template is not None

    def test_get_unknown_analyzer_prompt(self) -> None:
        """Тест получения промпта для неизвестного анализатора."""
        with pytest.raises(ValueError, match="Unknown analyzer"):
            get_prompt_for_analyzer("unknown")

    def test_format_structure_prompt(self) -> None:
        """Тест форматирования промпта для структуры."""
        template = get_prompt_for_analyzer("structure")
        result = template.format_user_prompt(text="Test document text")
        assert "Test document text" in result

    def test_format_purpose_prompt_with_context(self) -> None:
        """Тест форматирования промпта для цели с контекстом."""
        template = get_prompt_for_analyzer("purpose")
        result = template.format_user_prompt(
            text="Test document text",
            purpose="To analyze something",
            tasks="Task 1\nTask 2",
        )
        assert "Test document text" in result

    def test_format_relevance_prompt_with_topic(self) -> None:
        """Тест форматирования промпта для актуальности с темой."""
        template = get_prompt_for_analyzer("relevance")
        result = template.format_user_prompt(text="Test document text", topic="AI in education")
        assert "Test document text" in result

    def test_format_conclusions_prompt(self) -> None:
        """Тест форматирования промпта для выводов."""
        template = get_prompt_for_analyzer("conclusions")
        result = template.format_user_prompt(text="Test document text")
        assert "Test document text" in result

    def test_format_logic_prompt(self) -> None:
        """Тест форматирования промпта для логики."""
        template = get_prompt_for_analyzer("logic")
        result = template.format_user_prompt(text="Test document text")
        assert "Test document text" in result

    def test_format_style_prompt(self) -> None:
        """Тест форматирования промпта для стиля."""
        template = get_prompt_for_analyzer("style")
        result = template.format_user_prompt(text="Test document text")
        assert "Test document text" in result

    def test_format_citations_prompt(self) -> None:
        """Тест форматирования промпта для цитирования."""
        template = get_prompt_for_analyzer("citations")
        result = template.format_user_prompt(text="Test document text")
        assert "Test document text" in result

    def test_format_gost_prompt(self) -> None:
        """Тест форматирования промпта для ГОСТ."""
        template = get_prompt_for_analyzer("gost")
        result = template.format_user_prompt(text="Test document text")
        assert "Test document text" in result
