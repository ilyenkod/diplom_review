"""
Unit-тесты для кэша.

Тестирует:
- CacheClient интерфейс
- RedisCacheRepository
"""

import json
from unittest.mock import MagicMock

import pytest

from app.core.domain import Analysis, Document, Report, User
from app.core.interfaces.cache import CacheClient
from app.infrastructure.cache.redis_client import RedisCacheClient
from app.infrastructure.cache.repository import RedisCacheRepository


# ========== Mock Cache Client Tests ==========


@pytest.mark.unit
class TestMockCacheClient:
    """Тесты для mock клиента кэша."""

    @pytest.mark.asyncio
    async def test_set_and_get(self, mock_cache_client):
        """Тестирует установку и получение значения."""
        await mock_cache_client.set("key1", "value1")

        value = await mock_cache_client.get("key1")

        assert value == "value1"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, mock_cache_client):
        """Тестирует получение несуществующего ключа."""
        value = await mock_cache_client.get("nonexistent")

        assert value is None

    @pytest.mark.asyncio
    async def test_delete_existing_key(self, mock_cache_client):
        """Тестирует удаление существующего ключа."""
        await mock_cache_client.set("key1", "value1")

        result = await mock_cache_client.delete("key1")

        assert result is True
        assert await mock_cache_client.get("key1") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, mock_cache_client):
        """Тестирует удаление несуществующего ключа."""
        result = await mock_cache_client.delete("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, mock_cache_client):
        """Тестирует проверку существования ключа."""
        await mock_cache_client.set("key1", "value1")

        assert await mock_cache_client.exists("key1") is True
        assert await mock_cache_client.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_keys_with_pattern(self, mock_cache_client):
        """Тестирует поиск ключей по шаблону."""
        await mock_cache_client.set("user:1", "data1")
        await mock_cache_client.set("user:2", "data2")
        await mock_cache_client.set("document:1", "data3")

        user_keys = await mock_cache_client.keys("user:*")

        assert len(user_keys) == 2
        assert "user:1" in user_keys
        assert "user:2" in user_keys

    @pytest.mark.asyncio
    async def test_clear(self, mock_cache_client):
        """Тестирует очистку кэша."""
        await mock_cache_client.set("key1", "value1")
        await mock_cache_client.set("key2", "value2")

        result = await mock_cache_client.clear()

        assert result is True
        assert await mock_cache_client.exists("key1") is False
        assert await mock_cache_client.exists("key2") is False

    @pytest.mark.asyncio
    async def test_ttl(self, mock_cache_client):
        """Тестирует получение TTL ключа."""
        await mock_cache_client.set("key1", "value1")

        ttl = await mock_cache_client.ttl("key1")

        assert ttl == -1  # No expiry set

        ttl = await mock_cache_client.ttl("nonexistent")

        assert ttl == -2  # Key doesn't exist


# ========== RedisCacheRepository Tests ==========


@pytest.mark.unit
class TestRedisCacheRepository:
    """Тесты для репозитория кэша."""

    @pytest.mark.asyncio
    async def test_get_user(self, cache_repository, mock_cache_client):
        """Тестирует получение пользователя из кэша."""
        user_data = json.dumps({"id": "user-1", "email": "test@example.com"})
        await mock_cache_client.set("user:user-1", user_data)

        cached_user = await cache_repository.get_user("user-1")

        assert cached_user == user_data

    @pytest.mark.asyncio
    async def test_set_user(self, cache_repository, mock_cache_client):
        """Тестирует сохранение пользователя в кэш."""
        user_data = {"id": "user-1", "email": "test@example.com"}

        result = await cache_repository.set_user("user-1", user_data, ttl=3600)

        assert result is True
        cached_data = await mock_cache_client.get("user:user-1")
        assert cached_data is not None

    @pytest.mark.asyncio
    async def test_delete_user(self, cache_repository, mock_cache_client):
        """Тестирует удаление пользователя из кэша."""
        await mock_cache_client.set("user:user-1", "data")

        result = await cache_repository.delete_user("user-1")

        assert result is True
        assert await mock_cache_client.exists("user:user-1") is False

    @pytest.mark.asyncio
    async def test_get_document(self, cache_repository, mock_cache_client):
        """Тестирует получение документа из кэша."""
        doc_data = json.dumps({"id": "doc-1", "filename": "test.txt"})
        await mock_cache_client.set("document:doc-1", doc_data)

        cached_doc = await cache_repository.get_document("doc-1")

        assert cached_doc == doc_data

    @pytest.mark.asyncio
    async def test_set_document(self, cache_repository, mock_cache_client):
        """Тестирует сохранение документа в кэш."""
        doc_data = {"id": "doc-1", "filename": "test.txt"}

        result = await cache_repository.set_document("doc-1", doc_data)

        assert result is True
        assert await mock_cache_client.exists("document:doc-1") is True

    @pytest.mark.asyncio
    async def test_delete_document(self, cache_repository, mock_cache_client):
        """Тестирует удаление документа из кэша."""
        await mock_cache_client.set("document:doc-1", "data")

        result = await cache_repository.delete_document("doc-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_get_analysis(self, cache_repository, mock_cache_client):
        """Тестирует получение анализа из кэша."""
        analysis_data = json.dumps({"id": "analysis-1", "score": 8.5})
        await mock_cache_client.set("analysis:doc-1", analysis_data)

        cached_analysis = await cache_repository.get_analysis("doc-1")

        assert cached_analysis == analysis_data

    @pytest.mark.asyncio
    async def test_set_analysis(self, cache_repository, mock_cache_client):
        """Тестирует сохранение анализа в кэш."""
        analysis = Analysis(
            id="analysis-1",
            document_id="doc-1",
            status="completed",
            overall_score=8.5,
        )

        result = await cache_repository.set_analysis("doc-1", analysis, ttl=7200)

        assert result is True
        assert await mock_cache_client.exists("analysis:doc-1") is True

    @pytest.mark.asyncio
    async def test_delete_analysis(self, cache_repository, mock_cache_client):
        """Тестирует удаление анализа из кэша."""
        await mock_cache_client.set("analysis:doc-1", "data")

        result = await cache_repository.delete_analysis("doc-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_get_report(self, cache_repository, mock_cache_client):
        """Тестирует получение отчета из кэша."""
        report_data = json.dumps({"id": "report-1", "assessment": "Good"})
        await mock_cache_client.set("report:analysis-1", report_data)

        cached_report = await cache_repository.get_report("analysis-1")

        assert cached_report == report_data

    @pytest.mark.asyncio
    async def test_set_report(self, cache_repository, mock_cache_client):
        """Тестирует сохранение отчета в кэш."""
        report = Report(
            id="report-1",
            analysis_id="analysis-1",
            overall_assessment="Good work",
        )

        result = await cache_repository.set_report("analysis-1", report)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_report(self, cache_repository, mock_cache_client):
        """Тестирует удаление отчета из кэша."""
        await mock_cache_client.set("report:analysis-1", "data")

        result = await cache_repository.delete_report("analysis-1")

        assert result is True

    @pytest.mark.asyncio
    async def test_invalidate_user_cache(self, cache_repository, mock_cache_client):
        """Тестирует инвалидацию кэша пользователя."""
        # Set up cache
        await mock_cache_client.set("user:user-1", "user_data")
        await mock_cache_client.set("document:doc-1", "doc_data")
        await mock_cache_client.set("document:doc-2", "doc_data2")

        result = await cache_repository.invalidate_user_cache("user-1")

        assert result is True
        assert await mock_cache_client.exists("user:user-1") is False

    @pytest.mark.asyncio
    async def test_invalidate_document_cache(self, cache_repository, mock_cache_client):
        """Тестирует инвалидацию кэша документа."""
        # Set up cache
        await mock_cache_client.set("document:doc-1", "doc_data")
        await mock_cache_client.set("analysis:doc-1", "analysis_data")
        await mock_cache_client.set("report:analysis-1", "report_data")

        result = await cache_repository.invalidate_document_cache("doc-1")

        assert result is True
        assert await mock_cache_client.exists("document:doc-1") is False
        assert await mock_cache_client.exists("analysis:doc-1") is False
        assert await mock_cache_client.exists("report:analysis-1") is False


# ========== CacheClient Interface Tests ==========


@pytest.mark.unit
class TestCacheClientInterface:
    """Тесты для интерфейса CacheClient."""

    @pytest.mark.asyncio
    async def test_cache_client_contracts(self, mock_cache_client):
        """Тестирует выполнение контракта CacheClient."""
        # Test that all required methods exist and are callable
        assert hasattr(mock_cache_client, "get")
        assert hasattr(mock_cache_client, "set")
        assert hasattr(mock_cache_client, "delete")
        assert hasattr(mock_cache_client, "exists")
        assert hasattr(mock_cache_client, "expire")
        assert hasattr(mock_cache_client, "ttl")
        assert hasattr(mock_cache_client, "keys")
        assert hasattr(mock_cache_client, "clear")

        # Test they are async methods
        import inspect

        for method_name in ["get", "set", "delete", "exists", "expire", "ttl", "keys", "clear"]:
            method = getattr(mock_cache_client, method_name)
            assert inspect.iscoroutinefunction(method)

    @pytest.mark.asyncio
    async def test_cache_client_with_complex_data(self, mock_cache_client):
        """Тестирует работу со сложными данными."""
        import json

        complex_data = {
            "nested": {"key": "value"},
            "list": [1, 2, 3],
            "string": "test",
            "number": 42,
        }

        # Serialize and store
        serialized = json.dumps(complex_data)
        await mock_cache_client.set("complex", serialized)

        # Retrieve and deserialize
        retrieved = await mock_cache_client.get("complex")
        parsed = json.loads(retrieved)

        assert parsed == complex_data
