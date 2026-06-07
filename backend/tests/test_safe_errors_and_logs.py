from __future__ import annotations

import httpx
import pytest

import database
import main
from security import RateLimitExceeded
from tests.test_travel_registrations import valid_payload


SENSITIVE_VALUES = [
    "Maria de Souza",
    "52998224725",
    "999999999",
    "12345678",
    "AB123456",
    "1990-03-10",
    "2024-02-01",
    "maria.souza@empresa.com",
    "solicitante@empresa.com",
    "T123456",
]
REGISTRATION_ID = "123e4567-e89b-12d3-a456-426614174000"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def assert_no_sensitive_values(log_output: str) -> None:
    for value in SENSITIVE_VALUES:
        assert value not in log_output

    assert "password" not in log_output.lower()
    assert "stack" not in log_output.lower()
    assert "payload" not in log_output.lower()


@pytest.mark.anyio
async def test_public_creation_logs_only_safe_registration_id(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(main.security_service, "check_rate_limit", lambda bucket, key: None)
    monkeypatch.setattr(main.security_service, "encrypt_optional", lambda value: f"encrypted::{value}")
    monkeypatch.setattr(main, "create_travel_registration", lambda record: REGISTRATION_ID)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/travel-registrations", json=valid_payload())

    assert response.status_code == 200
    log_output = capsys.readouterr().out
    assert "travel_registration_created" in log_output
    assert f"registration_id={REGISTRATION_ID}" in log_output
    assert_no_sensitive_values(log_output)


@pytest.mark.anyio
async def test_invalid_login_logs_no_username_email_or_password(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("ADMIN_USERNAME", "admin@empresa.com")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "invalid-hash-format")
    monkeypatch.setattr(main.security_service, "check_rate_limit", lambda bucket, key: None)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.post(
            "/admin/login",
            json={"username": "admin@empresa.com", "password": "wrong-password"},
        )

    assert response.status_code == 401
    assert response.json() == {
        "ok": False,
        "error": "invalid_credentials",
        "message": "Credenciais invalidas.",
    }
    log_output = capsys.readouterr().out
    assert "admin_login_failed" in log_output
    assert "error_type=InvalidCredentials" in log_output
    assert "admin@empresa.com" not in log_output
    assert "wrong-password" not in log_output


@pytest.mark.anyio
async def test_rate_limit_response_is_safe_and_does_not_log_request_body(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def blocked(bucket: str, key: str) -> None:
        raise RateLimitExceeded("blocked for maria.souza@empresa.com 52998224725")

    monkeypatch.setattr(main.security_service, "check_rate_limit", blocked)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/travel-registrations", json=valid_payload())

    assert response.status_code == 429
    assert response.json() == {
        "ok": False,
        "error": "rate_limit_exceeded",
        "message": "Muitas tentativas. Tente novamente em instantes.",
    }
    assert_no_sensitive_values(capsys.readouterr().out)


@pytest.mark.anyio
async def test_admin_list_failure_logs_safe_error_type_without_sensitive_exception_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(main.security_service, "validate_session_cookie", lambda cookie: True)

    def fail_list() -> list[database.EncryptedTravelRegistrationRow]:
        raise RuntimeError("stack leaked Maria de Souza 52998224725 maria.souza@empresa.com")

    monkeypatch.setattr(main, "list_travel_registrations", fail_list)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.get("/admin/travel-registrations")

    assert response.status_code == 500
    assert response.json() == {
        "ok": False,
        "error": "internal_error",
        "message": "Nao foi possivel processar registros administrativos.",
    }
    log_output = capsys.readouterr().out
    assert "admin_travel_registration_list_failed" in log_output
    assert "error_type=RuntimeError" in log_output
    assert_no_sensitive_values(log_output)


@pytest.mark.anyio
async def test_admin_delete_failure_logs_registration_id_without_sensitive_exception_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(main.security_service, "validate_session_cookie", lambda cookie: True)

    def fail_delete(registration_id: str) -> bool:
        raise RuntimeError("stack leaked T123456 1990-03-10 AB123456")

    monkeypatch.setattr(main, "delete_travel_registration", fail_delete)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.delete(f"/admin/travel-registrations/{REGISTRATION_ID}")

    assert response.status_code == 500
    assert response.json() == {
        "ok": False,
        "error": "internal_error",
        "message": "Nao foi possivel processar registros administrativos.",
    }
    log_output = capsys.readouterr().out
    assert "admin_travel_registration_delete_failed" in log_output
    assert "error_type=RuntimeError" in log_output
    assert f"registration_id={REGISTRATION_ID}" in log_output
    assert_no_sensitive_values(log_output)


@pytest.mark.anyio
async def test_legacy_internal_error_log_omits_sensitive_exception_message(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_projects() -> list[dict[str, str | None]]:
        raise RuntimeError("stack leaked Maria de Souza 52998224725 T123456")

    monkeypatch.setattr(main, "list_projects", fail_projects)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/projects")

    assert response.status_code == 500
    assert "projetos" in response.json()["detail"]
    log_output = capsys.readouterr().out
    assert "project_list_failed" in log_output
    assert "error_type=RuntimeError" in log_output
    assert_no_sensitive_values(log_output)
