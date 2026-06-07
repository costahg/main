from __future__ import annotations

import httpx
import pytest

import database
import main
from security import SESSION_COOKIE_NAME


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def encrypted_row() -> database.EncryptedTravelRegistrationRow:
    return database.EncryptedTravelRegistrationRow(
        id="registration-id",
        nome_viajante_encrypted="enc:nome_viajante",
        matricula_encrypted="enc:matricula",
        data_solicitacao="2026-06-07T12:00:00+00:00",
        solicitante_email_encrypted="enc:solicitante_email",
        centro_custo_encrypted="enc:centro_custo",
        dditel_encrypted="enc:dditel",
        dddtel_encrypted="enc:dddtel",
        tel_encrypted="enc:tel",
        cpf_encrypted="enc:cpf",
        email_viajante_encrypted="enc:email_viajante",
        cargo_encrypted="enc:cargo",
        rg_encrypted="enc:rg",
        passaporte_encrypted="enc:passaporte",
        departamento_encrypted="enc:departamento",
        data_admissao_encrypted="enc:data_admissao",
        data_nascimento_encrypted="enc:data_nascimento",
        created_at="2026-06-07T12:00:00+00:00",
        updated_at="2026-06-07T12:00:00+00:00",
    )


@pytest.mark.anyio
async def test_admin_registration_list_without_session_returns_unauthorized_without_repository_or_decrypt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(main.security_service, "validate_session_cookie", lambda cookie: False)
    monkeypatch.setattr(main, "list_travel_registrations", lambda: calls.append("repository"))
    monkeypatch.setattr(main.security_service, "decrypt_optional", lambda value: calls.append("decrypt"))

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.get("/admin/travel-registrations")

    assert response.status_code == 401
    assert response.json() == {
        "ok": False,
        "error": "unauthorized",
        "message": "Sessao admin invalida.",
    }
    assert calls == []


@pytest.mark.anyio
async def test_admin_registration_list_with_session_returns_decrypted_camel_case_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decrypt_calls: list[str | None] = []

    def fake_decrypt(value: str | None) -> str | None:
        decrypt_calls.append(value)
        return None if value is None else value.removeprefix("enc:")

    monkeypatch.setattr(main.security_service, "validate_session_cookie", lambda cookie: True)
    monkeypatch.setattr(main, "list_travel_registrations", lambda: [encrypted_row()])
    monkeypatch.setattr(main.security_service, "decrypt_optional", fake_decrypt)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        client.cookies.set(SESSION_COOKIE_NAME, "valid-session")
        response = await client.get("/admin/travel-registrations")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "registrations": [
            {
                "id": "registration-id",
                "dataSolicitacao": "2026-06-07T12:00:00+00:00",
                "nomeViajante": "nome_viajante",
                "matricula": "matricula",
                "solicitanteEmail": "solicitante_email",
                "centroCusto": "centro_custo",
                "dditel": "dditel",
                "dddtel": "dddtel",
                "tel": "tel",
                "cpf": "cpf",
                "emailViajante": "email_viajante",
                "cargo": "cargo",
                "rg": "rg",
                "passaporte": "passaporte",
                "departamento": "departamento",
                "dataAdmissao": "data_admissao",
                "dataNascimento": "data_nascimento",
            }
        ],
    }
    assert decrypt_calls == [
        "enc:nome_viajante",
        "enc:matricula",
        "enc:solicitante_email",
        "enc:centro_custo",
        "enc:dditel",
        "enc:dddtel",
        "enc:tel",
        "enc:cpf",
        "enc:email_viajante",
        "enc:cargo",
        "enc:rg",
        "enc:passaporte",
        "enc:departamento",
        "enc:data_admissao",
        "enc:data_nascimento",
    ]


@pytest.mark.anyio
async def test_admin_registration_list_internal_error_returns_generic_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(main.security_service, "validate_session_cookie", lambda cookie: True)

    def fail_list() -> list[database.EncryptedTravelRegistrationRow]:
        raise RuntimeError("database password leaked in stack")

    monkeypatch.setattr(main, "list_travel_registrations", fail_list)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        client.cookies.set(SESSION_COOKIE_NAME, "valid-session")
        response = await client.get("/admin/travel-registrations")

    assert response.status_code == 500
    body = response.json()
    assert body == {
        "ok": False,
        "error": "internal_error",
        "message": "Nao foi possivel processar registros administrativos.",
    }
    assert "database password" not in str(body).lower()
    assert "stack" not in str(body).lower()


@pytest.mark.anyio
async def test_admin_registration_delete_without_session_returns_unauthorized_without_repository(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(main.security_service, "validate_session_cookie", lambda cookie: False)
    monkeypatch.setattr(
        main,
        "delete_travel_registration",
        lambda registration_id: calls.append(registration_id),
    )

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        response = await client.delete("/admin/travel-registrations/registration-id")

    assert response.status_code == 401
    assert response.json() == {
        "ok": False,
        "error": "unauthorized",
        "message": "Sessao admin invalida.",
    }
    assert calls == []


@pytest.mark.anyio
async def test_admin_registration_delete_with_session_deletes_existing_registration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deleted_ids: list[str] = []

    def fake_delete(registration_id: str) -> bool:
        deleted_ids.append(registration_id)
        return True

    monkeypatch.setattr(main.security_service, "validate_session_cookie", lambda cookie: True)
    monkeypatch.setattr(main, "delete_travel_registration", fake_delete)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        client.cookies.set(SESSION_COOKIE_NAME, "valid-session")
        response = await client.delete("/admin/travel-registrations/registration-id")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert deleted_ids == ["registration-id"]


@pytest.mark.anyio
async def test_admin_registration_delete_with_session_returns_404_when_id_does_not_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    deleted_ids: list[str] = []

    def fake_delete(registration_id: str) -> bool:
        deleted_ids.append(registration_id)
        return False

    monkeypatch.setattr(main.security_service, "validate_session_cookie", lambda cookie: True)
    monkeypatch.setattr(main, "delete_travel_registration", fake_delete)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        client.cookies.set(SESSION_COOKIE_NAME, "valid-session")
        response = await client.delete("/admin/travel-registrations/missing-id")

    assert response.status_code == 404
    assert response.json() == {
        "ok": False,
        "error": "not_found",
        "message": "Registro nao encontrado.",
    }
    assert deleted_ids == ["missing-id"]
