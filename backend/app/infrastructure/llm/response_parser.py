"""Парсинг ответов от LLM.

Реализует интерфейс LLMResponseParser для обработки JSON ответов от LLM.
"""

import json
import re
from typing import Any

from app.core.exceptions import InvalidLLMResponseError
from app.core.interfaces.llm import LLMResponseParser as BaseLLMResponseParser
from app.infrastructure.logging import AppLogger


class ResponseParser(BaseLLMResponseParser):
    """Парсер ответов от LLM."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует парсер.

        Args:
            logger: Логгер приложения.
        """
        self._logger = logger

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
            # Пытаемся распарсить ответ как есть
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Пробуем найти JSON в ответе (может быть окружен текстом)
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    msg = f"Failed to parse JSON from LLM response: {response[:200]}"
                    self._logger.error(msg, extra={"response": response})
                    raise InvalidLLMResponseError(msg) from e

            msg = f"No JSON found in LLM response: {response[:200]}"
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
