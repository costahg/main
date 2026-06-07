from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest

import database


class FakeConnection:
    def __init__(self, rows: list[tuple[object, ...]] | None = None) -> None:
        self.rows = rows or []
        self.calls: list[tuple[str, dict[str, object]]] = []

    def run(self, query: str, **params: object) -> list[tuple[object, ...]]:
        self.calls.append((query, params))
        return self.rows


@contextmanager
def fake_open_connection(connection: FakeConnection) -> Iterator[FakeConnection]:
    yield connection


def install_fake_connection(
    monkeypatch: pytest.MonkeyPatch,
    connection: FakeConnection,
) -> None:
    monkeypatch.setattr(
        database,
        "open_database_connection",
        lambda: fake_open_connection(connection),
    )


def encrypted_record() -> database.EncryptedTravelRegistration:
    return database.EncryptedTravelRegistration(
        nome_viajante_encrypted="encrypted-name",
        matricula_encrypted="encrypted-registration-number",
        solicitante_email_encrypted="encrypted-requester-email",
        centro_custo_encrypted="encrypted-cost-center",
        dditel_encrypted="encrypted-ddi",
        dddtel_encrypted="encrypted-ddd",
        tel_encrypted="encrypted-phone",
        cpf_encrypted="encrypted-cpf",
        email_viajante_encrypted="encrypted-traveler-email",
        cargo_encrypted="encrypted-role",
        rg_encrypted=None,
        passaporte_encrypted="encrypted-passport",
        departamento_encrypted=None,
        data_admissao_encrypted="encrypted-hire-date",
        data_nascimento_encrypted="encrypted-birth-date",
    )


def test_create_travel_registration_inserts_encrypted_record_and_returns_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(rows=[("registration-id",)])
    install_fake_connection(monkeypatch, connection)

    registration_id = database.create_travel_registration(encrypted_record())

    query, params = connection.calls[0]
    assert registration_id == "registration-id"
    assert "insert into public.travel_registrations" in query.lower()
    assert "returning id::text" in query.lower()
    assert params == {
        "nome_viajante_encrypted": "encrypted-name",
        "matricula_encrypted": "encrypted-registration-number",
        "solicitante_email_encrypted": "encrypted-requester-email",
        "centro_custo_encrypted": "encrypted-cost-center",
        "dditel_encrypted": "encrypted-ddi",
        "dddtel_encrypted": "encrypted-ddd",
        "tel_encrypted": "encrypted-phone",
        "cpf_encrypted": "encrypted-cpf",
        "email_viajante_encrypted": "encrypted-traveler-email",
        "cargo_encrypted": "encrypted-role",
        "rg_encrypted": None,
        "passaporte_encrypted": "encrypted-passport",
        "departamento_encrypted": None,
        "data_admissao_encrypted": "encrypted-hire-date",
        "data_nascimento_encrypted": "encrypted-birth-date",
    }


def test_list_travel_registrations_maps_encrypted_rows_in_desc_request_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(
        rows=[
            (
                "registration-id",
                "encrypted-name",
                "encrypted-registration-number",
                "2026-06-07 12:00:00+00",
                "encrypted-requester-email",
                "encrypted-cost-center",
                "encrypted-ddi",
                "encrypted-ddd",
                "encrypted-phone",
                "encrypted-cpf",
                "encrypted-traveler-email",
                "encrypted-role",
                None,
                "encrypted-passport",
                None,
                "encrypted-hire-date",
                "encrypted-birth-date",
                "2026-06-07 12:00:00+00",
                "2026-06-07 12:00:00+00",
            )
        ]
    )
    install_fake_connection(monkeypatch, connection)

    rows = database.list_travel_registrations(limit=250)

    query, params = connection.calls[0]
    assert "from public.travel_registrations" in query.lower()
    assert "order by data_solicitacao desc" in query.lower()
    assert params == {"limit": 100}
    assert rows == [
        database.EncryptedTravelRegistrationRow(
            id="registration-id",
            nome_viajante_encrypted="encrypted-name",
            matricula_encrypted="encrypted-registration-number",
            data_solicitacao="2026-06-07 12:00:00+00",
            solicitante_email_encrypted="encrypted-requester-email",
            centro_custo_encrypted="encrypted-cost-center",
            dditel_encrypted="encrypted-ddi",
            dddtel_encrypted="encrypted-ddd",
            tel_encrypted="encrypted-phone",
            cpf_encrypted="encrypted-cpf",
            email_viajante_encrypted="encrypted-traveler-email",
            cargo_encrypted="encrypted-role",
            rg_encrypted=None,
            passaporte_encrypted="encrypted-passport",
            departamento_encrypted=None,
            data_admissao_encrypted="encrypted-hire-date",
            data_nascimento_encrypted="encrypted-birth-date",
            created_at="2026-06-07 12:00:00+00",
            updated_at="2026-06-07 12:00:00+00",
        )
    ]


def test_delete_travel_registration_deletes_by_id_without_personal_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(rows=[("registration-id",)])
    install_fake_connection(monkeypatch, connection)

    deleted = database.delete_travel_registration("registration-id")

    query, params = connection.calls[0]
    lowered_query = query.lower()
    assert deleted is True
    assert "delete from public.travel_registrations" in lowered_query
    assert "where id = :registration_id" in lowered_query
    assert "returning id::text" in lowered_query
    assert "_encrypted" not in lowered_query
    assert params == {"registration_id": "registration-id"}


def test_delete_travel_registration_returns_false_when_id_does_not_exist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakeConnection(rows=[])
    install_fake_connection(monkeypatch, connection)

    assert database.delete_travel_registration("missing-id") is False
