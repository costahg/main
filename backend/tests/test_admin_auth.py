from __future__ import annotations

import httpx
import pytest

import main
from security import SESSION_COOKIE_NAME, SecurityService, generate_admin_password_hash


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def admin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv(
        "ADMIN_PASSWORD_HASH",
        generate_admin_password_hash("correct-password", salt="admin-route-test-salt"),
    )
    monkeypatch.setenv("SESSION_SECRET", "admin-route-session-secret")
    monkeypatch.setenv("ADMIN_SESSION_TTL_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")


@pytest.fixture
def reset_admin_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "security_service", SecurityService(now_func=lambda: 1_000.0))


@pytest.mark.anyio
async def test_admin_login_with_valid_credentials_sets_secure_session_cookie(
    admin_env: None,
    reset_admin_rate_limit: None,
) -> None:
    transport = httpx.ASGITransport(app=main.app)

    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.post(
            "/admin/login",
            json={"username": "admin", "password": "correct-password"},
        )
        session_response = await client.get("/admin/session")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert session_response.status_code == 200
    assert session_response.json() == {"ok": True, "authenticated": True}

    cookie_header = response.headers["set-cookie"]
    assert f"{SESSION_COOKIE_NAME}=" in cookie_header
    assert "HttpOnly" in cookie_header
    assert "Secure" in cookie_header
    assert "samesite=strict" in cookie_header.lower()
    assert "Max-Age=60" in cookie_header


@pytest.mark.anyio
async def test_admin_login_with_invalid_credentials_returns_generic_unauthorized(
    admin_env: None,
    reset_admin_rate_limit: None,
) -> None:
    transport = httpx.ASGITransport(app=main.app)

    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.post(
            "/admin/login",
            json={"username": "admin", "password": "wrong-password"},
        )

    assert response.status_code == 401
    assert response.json() == {
        "ok": False,
        "error": "invalid_credentials",
        "message": "Credenciais invalidas.",
    }
    assert SESSION_COOKIE_NAME not in response.cookies


@pytest.mark.anyio
async def test_admin_session_without_valid_cookie_returns_not_authenticated(
    admin_env: None,
    reset_admin_rate_limit: None,
) -> None:
    transport = httpx.ASGITransport(app=main.app)

    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.get("/admin/session")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "authenticated": False}


@pytest.mark.anyio
async def test_admin_logout_clears_cookie_and_invalidates_client_session(
    admin_env: None,
    reset_admin_rate_limit: None,
) -> None:
    transport = httpx.ASGITransport(app=main.app)

    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        login_response = await client.post(
            "/admin/login",
            json={"username": "admin", "password": "correct-password"},
        )
        authenticated_response = await client.get("/admin/session")
        logout_response = await client.post("/admin/logout")
        logged_out_response = await client.get("/admin/session")

    assert login_response.status_code == 200
    assert authenticated_response.json() == {"ok": True, "authenticated": True}
    assert logout_response.status_code == 200
    assert logout_response.json() == {"ok": True}
    assert logged_out_response.json() == {"ok": True, "authenticated": False}

    cookie_header = logout_response.headers["set-cookie"]
    assert f"{SESSION_COOKIE_NAME}=" in cookie_header
    assert "Max-Age=0" in cookie_header


@pytest.mark.anyio
async def test_admin_login_rate_limit_uses_admin_login_bucket(
    admin_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    buckets: list[tuple[str, str]] = []

    def fake_rate_limit(bucket: str, key: str) -> None:
        buckets.append((bucket, key))
        raise main.RateLimitExceeded("blocked")

    monkeypatch.setattr(main.security_service, "check_rate_limit", fake_rate_limit)
    transport = httpx.ASGITransport(app=main.app)

    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.post(
            "/admin/login",
            headers={"x-forwarded-for": "203.0.113.10"},
            json={"username": "admin", "password": "correct-password"},
        )

    assert response.status_code == 429
    assert response.json() == {
        "ok": False,
        "error": "rate_limit_exceeded",
        "message": "Muitas tentativas. Tente novamente em instantes.",
    }
    assert buckets == [("admin_login", "203.0.113.10")]
