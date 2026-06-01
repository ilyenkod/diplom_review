"""
Тесты для парсера ответов LLM.
"""


import pytest

from app.infrastructure.llm.response_parser import (
    LLMResponseParser,
    parse_analysis_response,
    validate_json_structure,
)


class TestValidateJsonStructure:
    """Тесты функции validate_json_structure."""

    def test_valid_json(self) -> None:
        """Тест валидации корректного JSON."""
        valid_json = '{"score": 8.5, "comments": ["test"]}'
        result = validate_json_structure(valid_json)
        assert result is True

    def test_invalid_json(self) -> None:
        """Тест валидации некорректного JSON."""
        invalid_json = '{score: 8.5, comments: ["test"]}'
        result = validate_json_structure(invalid_json)
        assert result is False

    def test_empty_string(self) -> None:
        """Тест валидации пустой строки."""
        result = validate_json_structure("")
        assert result is False

    def test_not_json(self) -> None:
        """Тест валидации строки которая не является JSON."""
        result = validate_json_structure("This is just text")
        assert result is False

    def test_json_with_required_fields(self) -> None:
        """Тест валидации JSON с обязательными полями."""
        valid_json = '{"score": 8.5, "comments": [], "recommendations": []}'
        result = validate_json_structure(valid_json)
        assert result is True


class TestLLMResponseParser:
    """Тесты класса LLMResponseParser."""

    def test_parse_json_response_valid(self) -> None:
        """Тест парсинга валидного JSON ответа."""
        parser = LLMResponseParser()
        response = '{"score": 8.5, "comments": ["test comment"], "recommendations": []}'
        result = parser.parse_json_response(response)
        assert result == {"score": 8.5, "comments": ["test comment"], "recommendations": []}

    def test_parse_json_response_invalid(self) -> None:
        """Тест парсинга невалидного JSON ответа."""
        parser = LLMResponseParser()
        response = "This is not JSON"
        with pytest.raises(ValueError, match="Invalid JSON response"):
            parser.parse_json_response(response)

    def test_parse_json_response_with_markdown(self) -> None:
        """Тест парсинга JSON ответа в markdown."""
        parser = LLMResponseParser()
        response = '```json\n{"score": 8.5, "comments": []}\n```'
        result = parser.parse_json_response(response)
        assert result == {"score": 8.5, "comments": []}

    def test_parse_json_response_with_extra_text(self) -> None:
        """Тест парсинга JSON ответа с дополнительным текстом."""
        parser = LLMResponseParser()
        response = 'Here is the analysis: {"score": 8.5, "comments": []}'
        result = parser.parse_json_response(response)
        assert result == {"score": 8.5, "comments": []}

    def test_extract_score_valid(self) -> None:
        """Тест извлечения оценки из ответа."""
        parser = LLMResponseParser()
        response = "Score: 8.5 out of 10"
        result = parser.extract_score(response)
        assert result == 8.5

    def test_extract_score_from_json(self) -> None:
        """Тест извлечения оценки из JSON."""
        parser = LLMResponseParser()
        response = '{"score": 9.0, "comments": []}'
        result = parser.extract_score(response)
        assert result == 9.0

    def test_extract_score_no_score(self) -> None:
        """Тест извлечения оценки когда она отсутствует."""
        parser = LLMResponseParser()
        response = "No score here"
        result = parser.extract_score(response)
        assert result is None

    def test_extract_score_multiple_numbers(self) -> None:
        """Тест извлечения оценки когда несколько чисел."""
        parser = LLMResponseParser()
        response = "The score is 8.5 out of 10 with 2 criteria"
        result = parser.extract_score(response)
        assert result == 8.5

    def test_extract_comments_from_json(self) -> None:
        """Тест извлечения комментариев из JSON."""
        parser = LLMResponseParser()
        response = '{"score": 8.5, "comments": ["Comment 1", "Comment 2"]}'
        result = parser.extract_comments(response)
        assert result == ["Comment 1", "Comment 2"]

    def test_extract_comments_from_list(self) -> None:
        """Тест извлечения комментариев из списка."""
        parser = LLMResponseParser()
        response = "Comments:\n1. First comment\n2. Second comment"
        result = parser.extract_comments(response)
        assert len(result) == 2
        assert "First comment" in result[0]

    def test_extract_comments_no_comments(self) -> None:
        """Тест извлечения комментариев когда они отсутствуют."""
        parser = LLMResponseParser()
        response = "No comments here"
        result = parser.extract_comments(response)
        assert result == []

    def test_extract_recommendations_from_json(self) -> None:
        """Тест извлечения рекомендаций из JSON."""
        parser = LLMResponseParser()
        response = '{"score": 8.5, "recommendations": ["Rec 1", "Rec 2"]}'
        result = parser.extract_recommendations(response)
        assert result == ["Rec 1", "Rec 2"]

    def test_extract_recommendations_from_list(self) -> None:
        """Тест извлечения рекомендаций из списка."""
        parser = LLMResponseParser()
        response = "Recommendations:\n- First recommendation\n- Second recommendation"
        result = parser.extract_recommendations(response)
        assert len(result) == 2
        assert "First recommendation" in result[0]

    def test_extract_recommendations_no_recommendations(self) -> None:
        """Тест извлечения рекомендаций когда они отсутствуют."""
        parser = LLMResponseParser()
        response = "No recommendations here"
        result = parser.extract_recommendations(response)
        assert result == []

    def test_validate_response_format_json(self) -> None:
        """Тест валидации формата ответа JSON."""
        parser = LLMResponseParser()
        response = '{"score": 8.5}'
        result = parser.validate_response_format(response, "json")
        assert result is True

    def test_validate_response_format_json_invalid(self) -> None:
        """Тест валидации невалидного JSON формата."""
        parser = LLMResponseParser()
        response = "Not a JSON"
        result = parser.validate_response_format(response, "json")
        assert result is False

    def test_validate_response_format_text(self) -> None:
        """Тест валидации текстового формата."""
        parser = LLMResponseParser()
        response = "Just some text"
        result = parser.validate_response_format(response, "text")
        assert result is True

    def test_validate_response_format_empty(self) -> None:
        """Тест валидации пустого ответа."""
        parser = LLMResponseParser()
        response = ""
        result = parser.validate_response_format(response, "json")
        assert result is False


class TestParseAnalysisResponse:
    """Тесты функции parse_analysis_response."""

    def test_parse_valid_json_response(self) -> None:
        """Тест парсинга валидного JSON ответа."""
        response = '{"score": 8.5, "comments": ["Comment 1"], "recommendations": ["Rec 1"]}'
        result = parse_analysis_response(response)
        assert result["score"] == 8.5
        assert result["comments"] == ["Comment 1"]
        assert result["recommendations"] == ["Rec 1"]

    def test_parse_response_with_missing_fields(self) -> None:
        """Тест парсинга ответа с отсутствующими полями."""
        response = '{"score": 8.5}'
        result = parse_analysis_response(response)
        assert result["score"] == 8.5
        assert result["comments"] == []
        assert result["recommendations"] == []

    def test_parse_response_with_markdown_json(self) -> None:
        """Тест парсинга JSON в markdown."""
        response = '```json\n{"score": 9.0, "comments": []}\n```'
        result = parse_analysis_response(response)
        assert result["score"] == 9.0
        assert result["comments"] == []

    def test_parse_invalid_json_raises_error(self) -> None:
        """Тест парсинга невалидного JSON вызывает ошибку."""
        response = "Invalid JSON"
        with pytest.raises(ValueError, match="Failed to parse LLM response"):
            parse_analysis_response(response)

    def test_parse_response_with_extra_fields(self) -> None:
        """Тест парсинга ответа с дополнительными полями."""
        response = '{"score": 8.5, "comments": [], "extra": "value"}'
        result = parse_analysis_response(response)
        assert result["score"] == 8.5
        assert "extra" not in result

    def test_parse_response_with_nested_fields(self) -> None:
        """Тест парсинга ответа с вложенными полями."""
        response = '{"score": 8.5, "comments": [], "details": {"total": 10}}'
        result = parse_analysis_response(response)
        assert result["score"] == 8.5
        assert result["comments"] == []
        assert "details" not in result

    def test_parse_response_with_comments_as_string(self) -> None:
        """Тест парсинга ответа с комментариями как строкой."""
        response = '{"score": 8.5, "comments": "Single comment"}'
        result = parse_analysis_response(response)
        assert result["score"] == 8.5
        assert result["comments"] == ["Single comment"]

    def test_parse_response_with_recommendations_as_string(self) -> None:
        """Тест парсинга ответа с рекомендациями как строкой."""
        response = '{"score": 8.5, "recommendations": "Single recommendation"}'
        result = parse_analysis_response(response)
        assert result["score"] == 8.5
        assert result["recommendations"] == ["Single recommendation"]

    def test_parse_response_invalid_score_type(self) -> None:
        """Тест парсинга ответа с неверным типом оценки."""
        response = '{"score": "not a number", "comments": []}'
        result = parse_analysis_response(response)
        assert result["score"] == 0.0

    def test_parse_response_score_out_of_range(self) -> None:
        """Тест парсинга ответа с оценкой вне диапазона."""
        response = '{"score": 15.0, "comments": []}'
        result = parse_analysis_response(response)
        assert result["score"] == 10.0

    def test_parse_response_negative_score(self) -> None:
        """Тест парсинга ответа с отрицательной оценкой."""
        response = '{"score": -5.0, "comments": []}'
        result = parse_analysis_response(response)
        assert result["score"] == 0.0
