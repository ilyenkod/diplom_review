"""
Unit-тесты для LLM клиента.

Тестирует:
- LLMClient интерфейс
- StubLLMClient
- LLMResponse
- LLMConfig
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.core.interfaces.llm import LLMClient, LLMConfig, LLMResponse, Message
from app.infrastructure.llm.client import StubLLMClient


# ========== LLMConfig Tests ==========


@pytest.mark.unit
class TestLLMConfig:
    """Тесты для конфигурации LLM."""

    def test_llm_config_creation(self):
        """Тестирует создание конфигурации LLM."""
        config = LLMConfig(
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7,
            timeout=30,
            max_retries=3,
        )

        assert config.model == "gpt-3.5-turbo"
        assert config.max_tokens == 1000
        assert config.temperature == 0.7
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_llm_config_defaults(self):
        """Тестирует создание конфигурации с указанием всех полей."""
        config = LLMConfig(
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7,
            timeout=30,
            max_retries=3,
        )

        assert config.model == "gpt-3.5-turbo"
        assert config.max_tokens == 1000
        assert config.temperature == 0.7
        assert config.timeout == 30
        assert config.max_retries == 3


# ========== LLMResponse Tests ==========


@pytest.mark.unit
class TestLLMResponse:
    """Тесты для ответа LLM."""

    def test_llm_response_creation(self):
        """Тестирует создание ответа LLM."""
        response = LLMResponse(
            content="Test response",
            model="gpt-3.5-turbo",
            tokens_used={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
        )

        assert response.content == "Test response"
        assert response.model == "gpt-3.5-turbo"
        assert response.tokens_used["total_tokens"] == 30
        assert response.finish_reason == "stop"

    def test_llm_response_optional_fields(self):
        """Тестирует опциональные поля ответа."""
        response = LLMResponse(
            content="Test response",
            model="gpt-3.5-turbo",
            tokens_used={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )

        assert response.content == "Test response"
        assert response.finish_reason is None


# ========== Message Tests ==========


@pytest.mark.unit
class TestMessage:
    """Тесты для сообщений LLM."""

    def test_message_creation(self):
        """Тестирует создание сообщения."""
        message = Message(role="user", content="Hello, world!")

        assert message.role == "user"
        assert message.content == "Hello, world!"

    def test_message_system_role(self):
        """Тестирует системное сообщение."""
        message = Message(role="system", content="You are a helpful assistant.")

        assert message.role == "system"


# ========== StubLLMClient Tests ==========


@pytest.mark.unit
class TestStubLLMClient:
    """Тесты для заглушки LLM клиента."""

    @pytest.fixture
    def stub_client(self, logger):
        """Возвращает заглушку клиента LLM."""
        config = LLMConfig(
            model="stub-model",
            max_tokens=1000,
            temperature=0.7,
            timeout=30,
            max_retries=3,
        )
        return StubLLMClient(config, logger)

    @pytest.mark.asyncio
    async def test_chat_completion(self, stub_client):
        """Тестирует чат-комплешион."""
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello!"),
        ]

        response = await stub_client.chat_completion(messages)

        assert response is not None
        assert response.content == "Stub response from LLM client"
        assert response.model == "stub-model"
        assert response.tokens_used is not None

    @pytest.mark.asyncio
    async def test_completion(self, stub_client):
        """Тестирует комплешион (single prompt)."""
        prompt = "Analyze this text"

        response = await stub_client.completion(prompt)

        assert response is not None
        assert response.content == "Stub response from LLM client"

    @pytest.mark.asyncio
    async def test_completion_with_config(self, stub_client):
        """Тестирует комплешион с кастомной конфигурацией."""
        custom_config = LLMConfig(
            model="custom-model",
            max_tokens=500,
            temperature=0.5,
            timeout=30,
            max_retries=3,
        )

        response = await stub_client.completion("Test prompt", custom_config)

        assert response is not None

    @pytest.mark.asyncio
    async def test_stream_completion_not_implemented(self, stub_client):
        """Тестирует, что стриминг не реализован."""
        messages = [Message(role="user", content="Test")]

        with pytest.raises(NotImplementedError):
            await stub_client.stream_completion(messages)

    def test_count_tokens(self, stub_client):
        """Тестирует подсчет токенов."""
        text = "This is a test string with some words."

        tokens = stub_client.count_tokens(text)

        assert tokens > 0
        assert isinstance(tokens, int)

    @pytest.mark.asyncio
    async def test_validate_api_key(self, stub_client):
        """Тестирует валидацию API ключа."""
        result = await stub_client.validate_api_key()

        assert result is True  # Stub always returns True

    def test_get_model_info(self, stub_client):
        """Тестирует получение информации о модели."""
        info = stub_client.get_model_info()

        assert info is not None
        assert "provider" in info
        assert "model" in info
        assert info["provider"] == "stub"


# ========== MockLLMClient Tests ==========


@pytest.mark.unit
class TestMockLLMClient:
    """Тесты для mock клиента LLM."""

    @pytest.mark.asyncio
    async def test_mock_llm_client_set_response(self, mock_llm_client):
        """Тестирует установку кастомного ответа."""
        custom_response = json.dumps({"score": 9.5, "comments": ["Excellent"]})
        mock_llm_client.set_response(custom_response)

        response = await mock_llm_client.completion("Test")

        assert response.content == custom_response

    @pytest.mark.asyncio
    async def test_mock_llm_client_chat_completion(self, mock_llm_client):
        """Тестирует чат-комплешион."""
        messages = [Message(role="user", content="Test")]

        response = await mock_llm_client.chat_completion(messages)

        assert response is not None
        assert response.content is not None
        assert response.model == "gpt-3.5-turbo"
        assert response.tokens_used["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_mock_llm_client_count_tokens(self, mock_llm_client):
        """Тестирует подсчет токенов."""
        text = "This is a test string with multiple words"

        tokens = mock_llm_client.count_tokens(text)

        # Simple approximation: len(text) // 4
        expected = len(text) // 4
        assert tokens == expected

    @pytest.mark.asyncio
    async def test_mock_llm_client_validate_api_key(self, mock_llm_client):
        """Тестирует валидацию API ключа."""
        result = await mock_llm_client.validate_api_key()

        assert result is True

    def test_mock_llm_client_get_model_info(self, mock_llm_client):
        """Тестирует получение информации о модели."""
        info = mock_llm_client.get_model_info()

        assert info["provider"] == "mock"
        assert info["model"] == "gpt-3.5-turbo"


# ========== LLMClient Interface Tests ==========


@pytest.mark.unit
class TestLLMClientInterface:
    """Тесты для интерфейса LLMClient."""

    @pytest.mark.asyncio
    async def test_llm_client_contracts(self, mock_llm_client):
        """Тестирует выполнение контракта LLMClient."""
        # Test that all required methods exist and are callable
        assert hasattr(mock_llm_client, "chat_completion")
        assert hasattr(mock_llm_client, "completion")
        assert hasattr(mock_llm_client, "stream_completion")
        assert hasattr(mock_llm_client, "count_tokens")
        assert hasattr(mock_llm_client, "validate_api_key")
        assert hasattr(mock_llm_client, "get_model_info")

        # Test they are async methods where appropriate
        import inspect

        async_methods = ["chat_completion", "completion", "stream_completion", "validate_api_key"]
        for method_name in async_methods:
            method = getattr(mock_llm_client, method_name)
            assert inspect.iscoroutinefunction(method)

        sync_methods = ["count_tokens", "get_model_info"]
        for method_name in sync_methods:
            method = getattr(mock_llm_client, method_name)
            assert not inspect.iscoroutinefunction(method)

    @pytest.mark.asyncio
    async def test_llm_client_with_multiple_messages(self, mock_llm_client):
        """Тестирует работу с несколькими сообщениями."""
        messages = [
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello!"),
            Message(role="assistant", content="Hi there! How can I help?"),
            Message(role="user", content="What is AI?"),
        ]

        response = await mock_llm_client.chat_completion(messages)

        assert response is not None
        assert response.content is not None

    @pytest.mark.asyncio
    async def test_llm_client_response_structure(self, mock_llm_client):
        """Тестирует структуру ответа."""
        response = await mock_llm_client.completion("Test")

        # Check response has all expected fields
        assert hasattr(response, "content")
        assert hasattr(response, "model")
        assert hasattr(response, "tokens_used")
        assert hasattr(response, "finish_reason")

        # Check tokens_used structure
        assert "prompt_tokens" in response.tokens_used
        assert "completion_tokens" in response.tokens_used
        assert "total_tokens" in response.tokens_used
