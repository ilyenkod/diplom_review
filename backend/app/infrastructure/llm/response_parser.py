"""Парсинг ответов от LLM.

Реализует интерфейс LLMResponseParser для обработки JSON ответов от LLM.
"""

import json
import re
from typing import Any

from app.core.exceptions import InvalidLLMResponseError
from app.core.interfaces.llm import LLMResponseParser as BaseLLMResponseParser
from app.infrastructure.logging import AppLogger


def validate_json_structure(json_str: str) -> bool:
    """Валидирует JSON структуру.

    Args:
        json_str: Строка с JSON.

    Returns:
        True если валидный JSON, иначе False.
    """
    try:
        parsed = json.loads(json_str)
        return isinstance(parsed, dict) and len(parsed) > 0
    except (json.JSONDecodeError, TypeError):
        return False


def parse_analysis_response(response: str) -> dict[str, Any]:
    """Парсит анализ ответа от LLM.

    Args:
        response: Ответ от LLM.

    Returns:
        Словарь с распарсенными данными.

    Raises:
        ValueError: Если не удалось распарсить ответ.
    """
    # Пытаемся найти JSON в ответе
    json_match = re.search(r"\{.*\}", response, re.DOTALL)
    if json_match:
        json_str = json_match.group()
    else:
        json_str = response

    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        msg = "Failed to parse LLM response"
        raise ValueError(msg) from e

    # Нормализация результатов
    result: dict[str, Any] = {
        "score": 0.0,
        "comments": [],
        "recommendations": [],
    }

    # Извлекаем score
    if "score" in parsed:
        try:
            score = float(parsed["score"])
            # Ограничиваем диапазон 0-10
            result["score"] = max(0.0, min(10.0, score))
        except (ValueError, TypeError):
            result["score"] = 0.0

    # Извлекаем comments
    if "comments" in parsed:
        comments = parsed["comments"]
        if isinstance(comments, list):
            result["comments"] = comments
        elif isinstance(comments, str):
            result["comments"] = [comments]

    # Извлекаем recommendations
    if "recommendations" in parsed:
        recommendations = parsed["recommendations"]
        if isinstance(recommendations, list):
            result["recommendations"] = recommendations
        elif isinstance(recommendations, str):
            result["recommendations"] = [recommendations]

    return result


class LLMResponseParser:
    """Парсер ответов от LLM."""

    def parse_json_response(self, response: str) -> dict[str, Any]:
        """Парсит JSON ответ от LLM.

        Args:
            response: Ответ от LLM.

        Returns:
            Словарь с распарсенными данными.

        Raises:
            ValueError: Если не удалось распарсить JSON.
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Пробуем найти JSON в ответе (может быть окружен текстом)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    msg = "Invalid JSON response"
                    raise ValueError(msg) from None

            msg = "Invalid JSON response"
            raise ValueError(msg) from None

    def extract_score(self, response: str) -> float | None:
        """Извлекает оценку из ответа LLM.

        Args:
            response: Ответ от LLM.

        Returns:
            Оценка или None если не найдена.
        """
        try:
            # Пытаемся найти число с плавающей точкой
            numbers = re.findall(r"\d+\.?\d*", response)
            if numbers:
                return float(numbers[0])
            return None
        except (ValueError, TypeError, IndexError):
            return None

    def extract_comments(self, response: str) -> list[str]:
        """Извлекает комментарии из ответа LLM.

        Args:
            response: Ответ от LLM.

        Returns:
            Список комментариев.
        """
        try:
            parsed = self.parse_json_response(response)
            comments = parsed.get("comments")

            if isinstance(comments, list):
                return comments
            if isinstance(comments, str):
                return [comments]

            return []
        except (ValueError, TypeError):
            # Пытаемся найти список в тексте
            # Формат: "Comments:\n1. First comment\n2. Second comment"
            if "Comments:" in response or "Комментарии:" in response:
                lines = response.split("\n")
                comments = []
                for line in lines:
                    # Ищем строки начинающиеся с цифрой или дефисом
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith("-")):
                        # Убираем номер/маркер
                        comment = re.sub(r"^[0-9]+[\.\)]?\s*", "", line)
                        comment = re.sub(r"^-\s*", "", comment)
                        if comment:
                            comments.append(comment)
                return comments

            return []

    def extract_recommendations(self, response: str) -> list[str]:
        """Извлекает рекомендации из ответа LLM.

        Args:
            response: Ответ от LLM.

        Returns:
            Список рекомендаций.
        """
        try:
            parsed = self.parse_json_response(response)
            recommendations = parsed.get("recommendations")

            if isinstance(recommendations, list):
                return recommendations
            if isinstance(recommendations, str):
                return [recommendations]

            return []
        except (ValueError, TypeError):
            # Пытаемся найти список в тексте
            # Формат: "Recommendations:\n- First recommendation\n- Second recommendation"
            if "Recommendations:" in response or "Рекомендации:" in response:
                lines = response.split("\n")
                recommendations = []
                for line in lines:
                    # Ищем строки начинающиеся с дефисом или цифры
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith("-")):
                        # Убираем номер/маркер
                        recommendation = re.sub(r"^[0-9]+[\.\)]?\s*", "", line)
                        recommendation = re.sub(r"^-\s*", "", recommendation)
                        if recommendation:
                            recommendations.append(recommendation)
                return recommendations

            return []

    def validate_response_format(self, response: str, expected_format: str) -> bool:
        """Проверяет формат ответа LLM.

        Args:
            response: Ответ от LLM.
            expected_format: Ожидаемый формат (например, "JSON").

        Returns:
            True если формат соответствует ожидаемому, иначе False.
        """
        if expected_format.upper() == "JSON":
            return validate_json_structure(response)
        return True


class ResponseParser(BaseLLMResponseParser):
    """Парсер ответов от LLM (реализация интерфейса)."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует парсер.

        Args:
            logger: Логгер приложения.
        """
        self._logger = logger
        self._parser = LLMResponseParser()

    def parse_json_response(self, response: str) -> dict[str, Any]:
        """Парсит JSON ответ от LLM.

        Args:
            response: Ответ от LLM.

        Returns:
            Словарь с распарсенными данными.

        Raises:
            InvalidLLMResponseError: Если не удалось распарсить JSON.
        """
        try:
            return self._parser.parse_json_response(response)
        except ValueError as e:
            msg = f"Failed to parse JSON from LLM response: {response[:200]}"
            self._logger.error(msg, extra={"response": response})
            raise InvalidLLMResponseError(msg) from e

    def extract_score(self, response: str) -> float | None:
        """Извлекает оценку из ответа LLM.

        Args:
            response: Ответ от LLM.

        Returns:
            Оценка от 0 до 100 или None если не найдена.
        """
        try:
            parsed = self.parse_json_response(response)
            score = parsed.get("score")

            if isinstance(score, (int, float)):
                return float(score)

            # Проверяем вариации именования поля
            for key in ["evaluation", "grade", "rating", "mark"]:
                if key in parsed and isinstance(parsed[key], (int, float)):
                    return float(parsed[key])

            return None
        except Exception:
            return None

    def extract_comments(self, response: str) -> list[str]:
        """Извлекает комментарии из ответа LLM.

        Args:
            response: Ответ от LLM.

        Returns:
            Список комментариев.
        """
        try:
            parsed = self.parse_json_response(response)
            comments = parsed.get("comments")

            if isinstance(comments, list):
                return comments

            if isinstance(comments, str):
                return [comments]

            # Проверяем вариации именования поля
            for key in ["comment", "notes", "feedback", "observations"]:
                if key in parsed:
                    value = parsed[key]
                    if isinstance(value, list):
                        return value
                    if isinstance(value, str):
                        return [value]

            return []
        except Exception:
            return []

    def extract_recommendations(self, response: str) -> list[str]:
        """Извлекает рекомендации из ответа LLM.

        Args:
            response: Ответ от LLM.

        Returns:
            Список рекомендаций.
        """
        try:
            parsed = self.parse_json_response(response)

            # Прямой поиск рекомендаций
            for key in ["recommendations", "recommendation", "suggestions", "suggestion", "advice"]:
                if key in parsed:
                    value = parsed[key]
                    if isinstance(value, list):
                        return value
                    if isinstance(value, str):
                        return [value]

            # Проверяем детали
            if "details" in parsed and isinstance(parsed["details"], dict):
                details = parsed["details"]
                for key in ["recommendations", "recommendation", "suggestions", "improvement_suggestions"]:
                    if key in details:
                        value = details[key]
                        if isinstance(value, list):
                            return value
                        if isinstance(value, str):
                            return [value]

            return []
        except Exception:
            return []

    def validate_response_format(self, response: str, expected_format: str) -> bool:
        """Проверяет формат ответа LLM.

        Args:
            response: Ответ от LLM.
            expected_format: Ожидаемый формат (например, "JSON").

        Returns:
            True если формат соответствует ожидаемому, иначе False.
        """
        if expected_format.upper() == "JSON":
            try:
                parsed = json.loads(response)
                # Проверяем что это словарь и содержит хотя бы одно поле
                return isinstance(parsed, dict) and len(parsed) > 0
            except json.JSONDecodeError:
                # Пробуем найти JSON в ответе
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        return isinstance(parsed, dict) and len(parsed) > 0
                    except json.JSONDecodeError:
                        return False
                return False

        return True
