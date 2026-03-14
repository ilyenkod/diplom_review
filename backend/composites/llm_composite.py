"""
Композит для сборки компонентов LLM.

Создает LLM клиента (OpenAI/Anthropic) с настройкой параметров и retry логикой.
"""

from app.config import settings
from app.core.interfaces.llm import LLMClient, LLMConfig
from app.infrastructure.llm.client import StubLLMClient
from app.infrastructure.logging import AppLogger
from composites.base import BaseComposite


class LLMComposite(BaseComposite):
    """Композит для управления LLM клиентом."""

    def __init__(self, logger: AppLogger) -> None:
        """Инициализирует композит LLM.

        Args:
            logger: Логгер приложения.
        """
        super().__init__()
        self._logger = logger
        self._client: LLMClient | None = None
        self._config: LLMConfig | None = None

    async def initialize(self) -> None:
        """Инициализирует компоненты LLM."""
        if self._initialized:
            return

        self._logger.info("Initializing LLM composite")

        # Создание конфигурации LLM
        self._config = LLMConfig(
            model=settings.llm.openai_model
            if settings.llm.provider == "openai"
            else settings.llm.anthropic_model,
            max_tokens=settings.llm.max_tokens,
            temperature=settings.llm.temperature,
            timeout=settings.llm.timeout,
            max_retries=settings.llm.max_retries,
        )

        # Создание клиента LLM
        # В фазе 2 используем заглушку, реальная интеграция будет позже
        self._client = StubLLMClient(self._config, self._logger)
        self._logger.info(
            f"LLM client initialized: {settings.llm.provider} (stub mode)",
            extra={"model": self._config.model},
        )

        # Сохраняем зависимости
        self.set_dependency("llm_client", self._client)
        self.set_dependency("llm_config", self._config)

        self._initialized = True
        self._logger.info("LLM composite initialized")

    async def start(self) -> None:
        """Запускает компоненты LLM."""
        await self._ensure_initialized()

        if self._started:
            return

        self._logger.info("Starting LLM composite")

        # Проверка валидности API ключа (если не заглушка)
        if self._client and not isinstance(self._client, StubLLMClient):
            is_valid = await self._client.validate_api_key()
            if is_valid:
                self._logger.info("LLM API key validated")
            else:
                self._logger.warning("LLM API key validation failed")

        self._started = True
        self._logger.info("LLM composite started")

    async def shutdown(self) -> None:
        """Останавливает компоненты LLM."""
        await self._ensure_started()

        self._logger.info("Shutting down LLM composite")

        # LLM клиент не требует явного закрытия соединения
        # Клиент OpenAI/Anthropic управляется автоматически

        self._started = False
        self._logger.info("LLM composite shut down")

    @property
    def client(self) -> LLMClient:
        """Возвращает клиент LLM.

        Returns:
            LLMClient.

        Raises:
            RuntimeError: Если композит не инициализирован.
        """
        if not self._initialized:
            msg = "LLM composite is not initialized"
            raise RuntimeError(msg)
        return self.get_dependency("llm_client")

    @property
    def config(self) -> LLMConfig:
        """Возвращает конфигурацию LLM.

        Returns:
            LLMConfig.

        Raises:
            RuntimeError: Если композит не инициализирован.
        """
        if not self._initialized:
            msg = "LLM composite is not initialized"
            raise RuntimeError(msg)
        return self.get_dependency("llm_config")
