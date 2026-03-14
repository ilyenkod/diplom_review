"""
Клиент LLM для работы с языковыми моделями.

Реализует интерфейс LLMClient с поддержкой OpenAI и Anthropic.
"""

import asyncio
from typing import Any

import anthropic
import openai
from openai import AsyncOpenAI

from app.config import settings
from app.core.interfaces.llm import (
    LLMClient,
    LLMConfig,
    LLMResponse,
    LLMRetryPolicy,
    Message,
)
from app.infrastructure.logging import AppLogger


class ExponentialBackoffRetryPolicy(LLMRetryPolicy):
    """Политика повторных попыток с экспоненциальной задержкой."""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0) -> None:
        """Инициализирует политику повтора.

        Args:
            max_retries: Максимальное количество попыток.
            base_delay: Базовая задержка в секундах.
        """
        self._max_retries = max_retries
        self._base_delay = base_delay

    def should_retry(self, attempt: int, error: Exception) -> bool:
        """Определяет, нужно ли повторить запрос.

        Args:
            attempt: Номер попытки.
            error: Ошибка.

        Returns:
            True если нужно повторить, иначе False.
        """
        if attempt >= self._max_retries:
            return False

        # Повторяем при временных ошибках
        if isinstance(error, (openai.APITimeoutError, anthropic.APITimeoutError)):
            return True

        if isinstance(error, (openai.RateLimitError, anthropic.RateLimitError)):
            return True

        if isinstance(error, (openai.APIConnectionError, anthropic.APIConnectionError)):
            return True

        return False

    def get_delay(self, attempt: int) -> float:
        """Возвращает задержку перед следующей попыткой в секундах.

        Args:
            attempt: Номер попытки.

        Returns:
            Задержка в секундах.
        """
        return self._base_delay * (2**attempt)


class OpenAILLMClient(LLMClient):
    """Клиент OpenAI."""

    def __init__(self, config: LLMConfig, logger: AppLogger) -> None:
        """Инициализирует клиент OpenAI.

        Args:
            config: Конфигурация LLM.
            logger: Логгер приложения.
        """
        self._config = config
        self._logger = logger
        self._client = AsyncOpenAI(
            api_key=settings.llm.openai_api_key,
            timeout=config.timeout,
            max_retries=0,  # Управляем повторами сами
        )
        self._retry_policy = ExponentialBackoffRetryPolicy(max_retries=config.max_retries)

    async def chat_completion(
        self,
        messages: list[Message],
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        """Выполняет чат-комплешион с LLM.

        Args:
            messages: Список сообщений.
            config: Опциональная конфигурация.

        Returns:
            Ответ от LLM.

        Raises:
            RuntimeError: Если все попытки неудачны.
        """
        llm_config = config or self._config
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        last_error: Exception | None = None

        for attempt in range(self._retry_policy._max_retries + 1):
            try:
                response = await self._client.chat.completions.create(
                    model=llm_config.model,
                    messages=openai_messages,
                    max_tokens=llm_config.max_tokens,
                    temperature=llm_config.temperature,
                )

                return LLMResponse(
                    content=response.choices[0].message.content or "",
                    model=response.model,
                    tokens_used={
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens
                        if response.usage
                        else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    },
                    finish_reason=response.choices[0].finish_reason,
                )

            except Exception as e:
                last_error = e

                if self._retry_policy.should_retry(attempt + 1, e):
                    delay = self._retry_policy.get_delay(attempt + 1)
                    self._logger.warning(
                        f"LLM request failed (attempt {attempt + 1}), retrying in {delay}s",
                        extra={"error": str(e)},
                    )
                    await asyncio.sleep(delay)
                else:
                    break

        msg = f"LLM request failed after {self._retry_policy._max_retries + 1} attempts"
        raise RuntimeError(msg) from last_error

    async def completion(
        self,
        prompt: str,
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        """Выполняет комплешион с LLM (single prompt).

        Args:
            prompt: Промпт.
            config: Опциональная конфигурация.

        Returns:
            Ответ от LLM.
        """
        return await self.chat_completion([Message(role="user", content=prompt)], config)

    async def stream_completion(
        self,
        messages: list[Message],
        config: LLMConfig | None = None,
    ) -> None:
        """Выполняет стриминговую комплешион с LLM.

        Args:
            messages: Список сообщений.
            config: Опциональная конфигурация.

        Note:
            Полная реализация будет позже.
        """
        # Заглушка для фазы 2
        raise NotImplementedError("Streaming not implemented yet")

    def count_tokens(self, text: str) -> int:
        """Подсчитывает количество токенов в тексте.

        Args:
            text: Текст.

        Returns:
            Количество токенов.
        """
        # Приблизительная оценка: 4 символа ~ 1 токен для английского
        return len(text) // 4

    async def validate_api_key(self) -> bool:
        """Проверяет валидность API ключа.

        Returns:
            True если ключ валиден, иначе False.
        """
        try:
            await self.completion(
                "test",
                LLMConfig(
                    model="gpt-3.5-turbo", max_tokens=10, temperature=0.0, timeout=10, max_retries=1
                ),
            )
            return True
        except Exception:
            return False

    def get_model_info(self) -> dict[str, Any]:
        """Возвращает информацию о модели.

        Returns:
            Словарь с информацией о модели.
        """
        return {
            "provider": "openai",
            "model": self._config.model,
            "max_tokens": self._config.max_tokens,
            "temperature": self._config.temperature,
        }


class StubLLMClient(LLMClient):
    """Заглушка клиента LLM для тестирования и разработки."""

    def __init__(self, config: LLMConfig, logger: AppLogger) -> None:
        """Инициализирует заглушку клиента LLM.

        Args:
            config: Конфигурация LLM.
            logger: Логгер приложения.
        """
        self._config = config
        self._logger = logger

    async def chat_completion(
        self,
        messages: list[Message],
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        """Выполняет чат-комплешион с LLM (заглушка).

        Args:
            messages: Список сообщений.
            config: Опциональная конфигурация.

        Returns:
            Ответ от LLM (заглушка).
        """
        self._logger.info("LLM stub: chat_completion called")
        return LLMResponse(
            content="Stub response from LLM client",
            model=self._config.model,
            tokens_used={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

    async def completion(
        self,
        prompt: str,
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        """Выполняет комплешион с LLM (заглушка).

        Args:
            prompt: Промпт.
            config: Опциональная конфигурация.

        Returns:
            Ответ от LLM (заглушка).
        """
        return await self.chat_completion([Message(role="user", content=prompt)], config)

    async def stream_completion(
        self,
        messages: list[Message],
        config: LLMConfig | None = None,
    ) -> None:
        """Выполняет стриминговую комплешион с LLM (заглушка)."""
        raise NotImplementedError("Streaming not implemented yet")

    def count_tokens(self, text: str) -> int:
        """Подсчитывает количество токенов в тексте (заглушка).

        Args:
            text: Текст.

        Returns:
            Количество токенов.
        """
        return len(text) // 4

    async def validate_api_key(self) -> bool:
        """Проверяет валидность API ключа (заглушка).

        Returns:
            True если ключ валиден, иначе False.
        """
        return True

    def get_model_info(self) -> dict[str, Any]:
        """Возвращает информацию о модели (заглушка).

        Returns:
            Словарь с информацией о модели.
        """
        return {
            "provider": "stub",
            "model": self._config.model,
            "max_tokens": self._config.max_tokens,
            "temperature": self._config.temperature,
        }
