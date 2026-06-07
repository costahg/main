from __future__ import annotations

from dataclasses import asdict

import httpx
import pytest

import database
import main


def valid_payload() -> dict[str, object]:
    return {
        "nomeViajante": "Maria de Souza",
        "matricula": "98765",
        "solicitanteEmail": "solicitante@empresa.com",
        "centroCusto": "T123456",
        "dditel": "55",
        "dddtel": "11",
        "tel": "999999999",
        "cpf": "52998224725",
        "emailViajante": "maria.souza@empresa.com",
        "cargo": "Analista Senior",
        "rg": "12345678",
        "passaporte": "AB123456",
        "departamento": "Operacoes Comerciais",
        "dataAdmissao": "2024-02-01",
        "dataNascimento": "1990-03-10",
    }


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def reset_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main.security_service, "check_rate_limit", lambda bucket, key: None)


@pytest.mark.anyio
async def test_public_travel_registration_creates_encrypted_record(
    monkeypatch: pytest.MonkeyPatch,
    reset_rate_limit: None,
) -> None:
    encrypted_values: list[str | None] = []
    persisted_records: list[database.EncryptedTravelRegistration] = []

    def fake_encrypt(value: str | None) -> str | None:
        encrypted_values.append(value)
        return None if value is None else f"encrypted::{value}"

    def fake_create(record: database.EncryptedTravelRegistration) -> str:
        persisted_records.append(record)
        return "created-registration-id"

    monkeypatch.setattr(main.security_service, "encrypt_optional", fake_encrypt)
    monkeypatch.setattr(main, "create_travel_registration", fake_create)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/travel-registrations", json=valid_payload())

    assert response.status_code == 200
    assert response.json() == {"ok": True, "id": "created-registration-id"}
    assert len(persisted_records) == 1

    persisted = asdict(persisted_records[0])
    assert "Maria de Souza" not in persisted.values()
    assert "52998224725" not in persisted.values()
    assert persisted["nome_viajante_encrypted"] == "encrypted::Maria de Souza"
    assert persisted["data_admissao_encrypted"] == "encrypted::2024-02-01"
    assert persisted["data_nascimento_encrypted"] == "encrypted::1990-03-10"
    assert "2026-06-07" not in persisted.values()
    assert "dataSolicitacao" not in encrypted_values


@pytest.mark.anyio
async def test_public_travel_registration_rejects_invalid_payload_with_field_contract(
    reset_rate_limit: None,
) -> None:
    payload = valid_payload()
    payload["cpf"] = "11111111111"
    payload["centroCusto"] = "A123"

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/travel-registrations", json=payload)

    assert response.status_code == 422
    assert response.json() == {
        "ok": False,
        "error": "validation_error",
        "fields": {
            "centroCusto": "centro de custo invalido",
            "cpf": "CPF invalido",
        },
    }


@pytest.mark.anyio
async def test_public_travel_registration_returns_safe_internal_error(
    monkeypatch: pytest.MonkeyPatch,
    reset_rate_limit: None,
) -> None:
    monkeypatch.setattr(main.security_service, "encrypt_optional", lambda value: f"encrypted::{value}")

    def fail_create(record: database.EncryptedTravelRegistration) -> str:
        raise RuntimeError("database password leaked in stack")

    monkeypatch.setattr(main, "create_travel_registration", fail_create)

    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/travel-registrations", json=valid_payload())

    assert response.status_code == 500
    body = response.json()
    assert body == {
        "ok": False,
        "error": "internal_error",
        "message": "Nao foi possivel enviar o registro.",
    }
    assert "database password" not in str(body).lower()
    assert "stack" not in str(body).lower()
