"""
Интерфейсы для работы с LLM провайдерами.

Определяет контракты для взаимодействия с языковыми моделями.
Следует принципу Dependency Inversion: бизнес-логика зависит от абстракций.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    """Сообщение для LLM."""

    role: str
    content: str


@dataclass
class LLMResponse:
    """Ответ от LLM."""

    content: str
    model: str
    tokens_used: dict[str, int] | None = None
    finish_reason: str | None = None


@dataclass
class LLMConfig:
    """Конфигурация LLM клиента."""

    model: str
    max_tokens: int
    temperature: float
    timeout: int
    max_retries: int


class LLMClient(ABC):
    """Интерфейс клиента для работы с LLM."""

    @abstractmethod
    async def chat_completion(
        self,
        messages: list[Message],
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        """Выполняет чат-комплешион с LLM."""
        raise NotImplementedError

    @abstractmethod
    async def completion(
        self,
        prompt: str,
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        """Выполняет комплешион с LLM (single prompt)."""
        raise NotImplementedError

    @abstractmethod
    async def stream_completion(
        self,
        messages: list[Message],
        config: LLMConfig | None = None,
    ) -> None:
        """Выполняет стриминговую комплешион с LLM.

        Yields чанки ответа.
        """
        raise NotImplementedError

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Подсчитывает количество токенов в тексте."""
        raise NotImplementedError

    @abstractmethod
    async def validate_api_key(self) -> bool:
        """Проверяет валидность API ключа."""
        raise NotImplementedError

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Возвращает информацию о модели."""
        raise NotImplementedError


class LLMRetryPolicy(ABC):
    """Интерфейс для политики повторных попыток."""

    @abstractmethod
    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Определяет, нужно ли повторить запрос."""
        raise NotImplementedError

    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        """Возвращает задержку перед следующей попыткой в секундах."""
        raise NotImplementedError


class LLMResponseParser(ABC):
    """Интерфейс для парсинга ответов от LLM."""

    @abstractmethod
    def parse_json_response(self, response: str) -> dict[str, Any]:
        """Парсит JSON ответ от LLM."""
        raise NotImplementedError

    @abstractmethod
    def extract_score(self, response: str) -> float | None:
        """Извлекает оценку из ответа LLM."""
        raise NotImplementedError

    @abstractmethod
    def extract_comments(self, response: str) -> list[str]:
        """Извлекает комментарии из ответа LLM."""
        raise NotImplementedError

    @abstractmethod
    def extract_recommendations(self, response: str) -> list[str]:
        """Извлекает рекомендации из ответа LLM."""
        raise NotImplementedError

    @abstractmethod
    def validate_response_format(self, response: str, expected_format: str) -> bool:
        """Проверяет формат ответа LLM."""
        raise NotImplementedError
