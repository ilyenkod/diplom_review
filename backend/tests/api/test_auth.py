"""API тесты эндпоинтов аутентификации."""

from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.domain import User
from app.infrastructure.api.deps import get_db
from app.infrastructure.api.v1 import auth


@pytest.fixture
def test_user() -> User:
    return User(
        id="user-test-id",
        email="test@example.com",
        hashed_password="hashed_pw",
        full_name="Test User",
        is_active=True,
        role="student",
        created_at=datetime.now(UTC),
    )


@pytest.fixture
async def test_app(db_session: AsyncSession) -> FastAPI:
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1")

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


@pytest.fixture
async def client(test_app: FastAPI):
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac


@pytest.mark.unit
async def test_register_success(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPass123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.unit
async def test_register_duplicate_email(client: AsyncClient) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "StrongPass123",
        "full_name": "User One",
    }
    resp1 = await client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = await client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409


@pytest.mark.unit
async def test_register_weak_password(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "password": "short",
            "full_name": "Weak Pass User",
        },
    )
    # Pydantic validation rejects passwords shorter than 8 chars
    assert response.status_code == 422


@pytest.mark.unit
async def test_register_invalid_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "StrongPass123",
            "full_name": "Bad Email User",
        },
    )
    assert response.status_code == 422


@pytest.mark.unit
async def test_login_success(client: AsyncClient) -> None:
    # First register
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "StrongPass123",
            "full_name": "Login User",
        },
    )
    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "StrongPass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


@pytest.mark.unit
async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpw@example.com",
            "password": "StrongPass123",
            "full_name": "Wrong PW User",
        },
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401


@pytest.mark.unit
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "StrongPass123"},
    )
    assert response.status_code == 401


@pytest.mark.unit
async def test_refresh_token_success(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "password": "StrongPass123",
            "full_name": "Refresh User",
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "StrongPass123"},
    )
    tokens = login_resp.json()

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.unit
async def test_refresh_token_invalid(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.value"},
    )
    assert response.status_code == 401
