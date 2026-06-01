"""
Тесты для репозитория кэша.
"""

from unittest.mock import AsyncMock

import pytest

from app.core.interfaces.cache import CacheClient
from app.infrastructure.cache.repository import RedisCacheRepository
from app.infrastructure.logging import AppLogger


class TestRedisCacheRepository:
    """Тесты класса RedisCacheRepository."""

    @pytest.fixture
    def mock_cache_client(self) -> CacheClient:
        """Возвращает мок клиента кэша."""

        client = AsyncMock(spec=CacheClient)
        client.get = AsyncMock(return_value='{"id": "test"}')
        client.set = AsyncMock(return_value=True)
        client.delete = AsyncMock(return_value=True)
        client.keys = AsyncMock(return_value=[])
        return client

    @pytest.fixture
    def repository(self, mock_cache_client: CacheClient, logger: AppLogger) -> RedisCacheRepository:
        """Возвращает репозиторий кэша для тестов."""
        return RedisCacheRepository(mock_cache_client, logger)

    async def test_get_user(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест получения пользователя из кэша."""
        user_data = '{"id": "user123", "name": "Test User"}'
        mock_cache_client.get = AsyncMock(return_value=user_data)

        result = await repository.get_user("user123")
        assert result == user_data
        mock_cache_client.get.assert_called_once_with("user:user123")

    async def test_set_user(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест сохранения пользователя в кэш."""
        user_data = '{"id": "user123", "name": "Test User"}'
        result = await repository.set_user("user123", user_data, ttl=1800)
        assert result is True
        mock_cache_client.set.assert_called_once_with("user:user123", user_data, 1800)

    async def test_set_user_default_ttl(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест сохранения пользователя с TTL по умолчанию."""
        user_data = '{"id": "user123"}'
        result = await repository.set_user("user123", user_data)
        assert result is True
        mock_cache_client.set.assert_called_once_with("user:user123", user_data, 3600)

    async def test_delete_user(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест удаления пользователя из кэша."""
        result = await repository.delete_user("user123")
        assert result is True
        mock_cache_client.delete.assert_called_once_with("user:user123")

    async def test_get_document(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест получения документа из кэша."""
        doc_data = '{"id": "doc123", "filename": "test.pdf"}'
        mock_cache_client.get = AsyncMock(return_value=doc_data)

        result = await repository.get_document("doc123")
        assert result == doc_data
        mock_cache_client.get.assert_called_once_with("document:doc123")

    async def test_set_document(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест сохранения документа в кэш."""
        doc_data = '{"id": "doc123", "content": "..."}'
        result = await repository.set_document("doc123", doc_data, ttl=1800)
        assert result is True
        mock_cache_client.set.assert_called_once_with("document:doc123", doc_data, 1800)

    async def test_delete_document(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест удаления документа из кэша."""
        result = await repository.delete_document("doc123")
        assert result is True
        mock_cache_client.delete.assert_called_once_with("document:doc123")

    async def test_get_analysis(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест получения анализа из кэша."""
        analysis_data = '{"id": "analysis123", "score": 8.5}'
        mock_cache_client.get = AsyncMock(return_value=analysis_data)

        result = await repository.get_analysis("analysis123")
        assert result == analysis_data
        mock_cache_client.get.assert_called_once_with("analysis:analysis123")

    async def test_set_analysis(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест сохранения анализа в кэш."""
        analysis_data = '{"id": "analysis123", "score": 8.5}'
        result = await repository.set_analysis("analysis123", analysis_data, ttl=5400)
        assert result is True
        mock_cache_client.set.assert_called_once_with("analysis:analysis123", analysis_data, 5400)

    async def test_set_analysis_default_ttl(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест сохранения анализа с TTL по умолчанию."""
        analysis_data = '{"id": "analysis123"}'
        result = await repository.set_analysis("analysis123", analysis_data)
        assert result is True
        mock_cache_client.set.assert_called_once_with("analysis:analysis123", analysis_data, 7200)

    async def test_delete_analysis(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест удаления анализа из кэша."""
        result = await repository.delete_analysis("analysis123")
        assert result is True
        mock_cache_client.delete.assert_called_once_with("analysis:analysis123")

    async def test_get_report(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест получения отчета из кэша."""
        report_data = '{"analysis_id": "analysis123", "content": "..."}'
        mock_cache_client.get = AsyncMock(return_value=report_data)

        result = await repository.get_report("analysis123")
        assert result == report_data
        mock_cache_client.get.assert_called_once_with("report:analysis123")

    async def test_set_report(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест сохранения отчета в кэш."""
        report_data = '{"analysis_id": "analysis123", "content": "..."}'
        result = await repository.set_report("analysis123", report_data, ttl=1800)
        assert result is True
        mock_cache_client.set.assert_called_once_with("report:analysis123", report_data, 1800)

    async def test_set_report_default_ttl(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест сохранения отчета с TTL по умолчанию."""
        report_data = '{"analysis_id": "analysis123"}'
        result = await repository.set_report("analysis123", report_data)
        assert result is True
        mock_cache_client.set.assert_called_once_with("report:analysis123", report_data, 3600)

    async def test_delete_report(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест удаления отчета из кэша."""
        result = await repository.delete_report("analysis123")
        assert result is True
        mock_cache_client.delete.assert_called_once_with("report:analysis123")

    async def test_invalidate_user_cache(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест инвалидации кэша пользователя."""
        mock_cache_client.keys = AsyncMock(return_value=["document:doc1", "document:doc2"])

        result = await repository.invalidate_user_cache("user123")
        assert result is True
        mock_cache_client.delete.assert_any_call("user:user123")
        mock_cache_client.delete.assert_any_call("document:doc1")
        mock_cache_client.delete.assert_any_call("document:doc2")

    async def test_invalidate_user_cache_no_documents(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест инвалидации кэша пользователя без документов."""
        mock_cache_client.keys = AsyncMock(return_value=[])

        result = await repository.invalidate_user_cache("user123")
        assert result is True
        mock_cache_client.delete.assert_called_once_with("user:user123")

    async def test_invalidate_document_cache(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест инвалидации кэша документа."""
        mock_cache_client.keys = AsyncMock(
            side_effect=[
                ["analysis:analysis1", "analysis:analysis2"],
                ["report:report1"],
            ]
        )

        result = await repository.invalidate_document_cache("doc123")
        assert result is True
        mock_cache_client.delete.assert_any_call("document:doc123")
        mock_cache_client.delete.assert_any_call("analysis:analysis1")
        mock_cache_client.delete.assert_any_call("analysis:analysis2")
        mock_cache_client.delete.assert_any_call("report:report1")

    async def test_invalidate_document_cache_no_related_items(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест инвалидации кэша документа без связанных элементов."""
        mock_cache_client.keys = AsyncMock(side_effect=[[], []])

        result = await repository.invalidate_document_cache("doc123")
        assert result is True
        mock_cache_client.delete.assert_called_once_with("document:doc123")

    async def test_get_user_not_found(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест получения несуществующего пользователя."""
        mock_cache_client.get = AsyncMock(return_value=None)

        result = await repository.get_user("nonexistent")
        assert result is None

    async def test_get_document_not_found(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест получения несуществующего документа."""
        mock_cache_client.get = AsyncMock(return_value=None)

        result = await repository.get_document("nonexistent")
        assert result is None

    async def test_get_analysis_not_found(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест получения несуществующего анализа."""
        mock_cache_client.get = AsyncMock(return_value=None)

        result = await repository.get_analysis("nonexistent")
        assert result is None

    async def test_get_report_not_found(
        self, repository: RedisCacheRepository, mock_cache_client: CacheClient
    ) -> None:
        """Тест получения несуществующего отчета."""
        mock_cache_client.get = AsyncMock(return_value=None)

        result = await repository.get_report("nonexistent")
        assert result is None
