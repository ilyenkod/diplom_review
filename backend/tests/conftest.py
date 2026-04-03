"""
Конфигурация для тестов.

Настраивает pytest и предоставляет фикстуры для тестов.
"""

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

# Set up environment variables for testing BEFORE importing app modules
os.environ.setdefault("TESTING", "1")
os.environ.setdefault("LLM_PROVIDER", "stub")
os.environ.setdefault("LLM_OPENAI_API_KEY", "test-key-for-testing")
os.environ.setdefault("LLM_ANTHROPIC_API_KEY", "test-key-for-testing")
os.environ.setdefault("DB_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")

# Add backend to path if needed
backend_path = Path(__file__).parent.parent / "app"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))


import pytest
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings
from app.core.const import FileFormats
from app.core.domain import Analysis, Document, Report, User
from app.core.interfaces.cache import CacheClient
from app.core.interfaces.llm import LLMClient, LLMConfig, LLMResponse, Message
from app.core.interfaces.storage import Storage
from app.infrastructure.cache.redis_client import RedisCacheClient
from app.infrastructure.cache.repository import RedisCacheRepository
from app.infrastructure.database.repositories.analysis_repo import AnalysisRepository
from app.infrastructure.database.repositories.base import BaseRepository
from app.infrastructure.database.repositories.document_repo import DocumentRepository
from app.infrastructure.database.repositories.history_repo import HistoryRepository
from app.infrastructure.database.repositories.report_repo import ReportRepository
from app.infrastructure.database.repositories.user_repo import UserRepository
from app.infrastructure.logging import AppLogger
from app.infrastructure.llm.client import StubLLMClient


# ========== Fixtures for Database ==========


@pytest.fixture
async def db_engine():
    """Создает тестовый движок базы данных в памяти."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    from app.infrastructure.database.table import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    """Создает тестовую сессию базы данных."""
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture
def user_repository(db_session):
    """Возвращает репозиторий пользователей."""
    return UserRepository(db_session)


@pytest.fixture
def document_repository(db_session):
    """Возвращает репозиторий документов."""
    return DocumentRepository(db_session)


@pytest.fixture
def analysis_repository(db_session):
    """Возвращает репозиторий анализов."""
    return AnalysisRepository(db_session)


@pytest.fixture
def report_repository(db_session):
    """Возвращает репозиторий отчетов."""
    return ReportRepository(db_session)


@pytest.fixture
def history_repository(db_session):
    """Возвращает репозиторий истории."""
    return HistoryRepository(db_session)


# ========== Fixtures for Cache ==========


class MockCacheClient(CacheClient):
    """Mock клиент кэша для тестов."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}

    async def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        self._cache[key] = value
        return True

    async def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        return key in self._cache

    async def expire(self, key: str, ttl: int) -> bool:
        return key in self._cache

    async def ttl(self, key: str) -> int:
        return -1 if key in self._cache else -2

    async def keys(self, pattern: str = "*") -> list[str]:
        import fnmatch

        return [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]

    async def clear(self) -> bool:
        self._cache.clear()
        return True

    async def ping(self) -> bool:
        """Проверяет доступность кэша."""
        return True


@pytest.fixture
def mock_cache_client():
    """Возвращает mock клиент кэша."""
    return MockCacheClient()


@pytest.fixture
def cache_repository(mock_cache_client):
    """Возвращает репозиторий кэша."""
    logger = MagicMock(spec=AppLogger)
    return RedisCacheRepository(mock_cache_client, logger)


# ========== Fixtures for LLM Client ==========


class MockLLMClient(LLMClient):
    """Mock клиент LLM для тестов."""

    def __init__(self) -> None:
        self._config = LLMConfig(
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7,
            timeout=30,
            max_retries=3,
        )
        self._response = json.dumps(
            {
                "score": 8.5,
                "comments": ["Test comment 1", "Test comment 2"],
                "recommendations": ["Test recommendation 1"],
            }
        )

    def set_response(self, response: str) -> None:
        """Устанавливает ответ для теста."""
        self._response = response

    async def chat_completion(
        self,
        messages: list[Message],
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        return LLMResponse(
            content=self._response,
            model=self._config.model,
            tokens_used={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        )

    async def completion(
        self,
        prompt: str,
        config: LLMConfig | None = None,
    ) -> LLMResponse:
        return await self.chat_completion([Message(role="user", content=prompt)], config)

    async def stream_completion(
        self,
        messages: list[Message],
        config: LLMConfig | None = None,
    ) -> None:
        raise NotImplementedError

    def count_tokens(self, text: str) -> int:
        return len(text) // 4

    async def validate_api_key(self) -> bool:
        return True

    def get_model_info(self) -> dict[str, Any]:
        return {
            "provider": "mock",
            "model": self._config.model,
        }


@pytest.fixture
def mock_llm_client():
    """Возвращает mock клиент LLM."""
    return MockLLMClient()


@pytest.fixture
def stub_llm_client():
    """Возвращает заглушку клиента LLM."""
    config = LLMConfig(
        model="stub-model",
        max_tokens=1000,
        temperature=0.7,
        timeout=30,
        max_retries=3,
    )
    logger = MagicMock(spec=AppLogger)
    return StubLLMClient(config, logger)


# ========== Fixtures for Storage ==========


class MockStorage(Storage):
    """Mock хранилище для тестов."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}

    async def save(self, filename: str, content: bytes) -> Any:
        self._files[filename] = content
        return MagicMock(success=True, text=None)

    async def delete(self, filename: str) -> bool:
        if filename in self._files:
            del self._files[filename]
            return True
        return False

    async def get(self, filename: str) -> bytes | None:
        return self._files.get(filename)

    async def exists(self, filename: str) -> bool:
        return filename in self._files

    async def get_url(self, filename: str, ttl: int = 3600) -> str | None:
        return f"http://localhost:8000/files/{filename}" if filename in self._files else None


@pytest.fixture
def mock_storage():
    """Возвращает mock хранилище."""
    return MockStorage()


# ========== Fixtures for Processors ==========


@pytest.fixture
def mock_processor_result():
    """Возвращает mock результат процессора."""
    return MagicMock(
        success=True,
        text="Processed text content",
        error=None,
        metadata={"pages": 1},
    )


@pytest.fixture
def mock_processors(mock_processor_result):
    """Возвращает mock процессоры для разных форматов."""
    return {
        FileFormats.DOCX: MagicMock(
            process_bytes=AsyncMock(return_value=mock_processor_result),
            process=AsyncMock(return_value=mock_processor_result),
        ),
        FileFormats.PDF: MagicMock(
            process_bytes=AsyncMock(return_value=mock_processor_result),
            process=AsyncMock(return_value=mock_processor_result),
        ),
        FileFormats.TXT: MagicMock(
            process_bytes=AsyncMock(return_value=mock_processor_result),
            process=AsyncMock(return_value=mock_processor_result),
        ),
    }


# ========== Fixtures for Logger ==========


@pytest.fixture
def logger():
    """Возвращает логгер для тестов."""
    return MagicMock(spec=AppLogger)


# ========== Fixtures for Sample Data ==========


@pytest.fixture
def sample_user():
    """Возвращает тестового пользователя."""
    return User(
        id="user-123",
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
        role="student",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_document():
    """Возвращает тестовый документ."""
    return Document(
        id="doc-123",
        user_id="user-123",
        filename="test.txt",
        original_filename="test.txt",
        file_size=1024,
        file_type="txt",
        file_path="test.txt",
        content="Test document content",
    )


@pytest.fixture
def sample_analysis():
    """Возвращает тестовый анализ."""
    return Analysis(
        id="analysis-123",
        document_id="doc-123",
        status="completed",
        overall_score=8.5,
        results={
            "structure": {"score": 8.0, "comments": ["Good structure"]},
            "style": {"score": 9.0, "comments": ["Excellent style"]},
        },
    )


@pytest.fixture
def sample_report():
    """Возвращает тестовый отчет."""
    return Report(
        id="report-123",
        analysis_id="analysis-123",
        overall_assessment="Good work (8.5/10.0)",
        recommendations=["Improve structure"],
        supervisor_comments=["Well done"],
    )


# ========== Pytest Configuration ==========


def pytest_configure(config):
    """Настройка pytest."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow")
