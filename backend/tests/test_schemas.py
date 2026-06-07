from datetime import date

import pytest
from pydantic import ValidationError

from schemas import TravelRegistrationCreate, validation_error_fields


def valid_payload() -> dict[str, object]:
    return {
        "nomeViajante": "  Maria   de   Souza  ",
        "matricula": "  98765 ",
        "solicitanteEmail": " SOLICITANTE@Empresa.com ",
        "centroCusto": " t123456 ",
        "dditel": "55",
        "dddtel": "11",
        "tel": "999999999",
        "cpf": "529.982.247-25",
        "emailViajante": " MARIA.SOUZA@Empresa.com ",
        "cargo": " Analista   Senior ",
        "rg": " 12 345 678 ",
        "passaporte": "  AB 123456 ",
        "departamento": " Operacoes   Comerciais ",
        "dataAdmissao": "2024-02-01",
        "dataNascimento": "1990-03-10",
    }


def assert_field_error(payload: dict[str, object], field: str) -> None:
    with pytest.raises(ValidationError) as exc_info:
        TravelRegistrationCreate.model_validate(payload)

    fields = validation_error_fields(exc_info.value)
    assert field in fields
    assert fields[field]


def test_valid_payload_generates_normalized_internal_model() -> None:
    registration = TravelRegistrationCreate.model_validate(valid_payload())

    assert registration.nome_viajante == "Maria de Souza"
    assert registration.matricula == "98765"
    assert registration.solicitante_email == "solicitante@empresa.com"
    assert registration.centro_custo == "T123456"
    assert registration.dditel == "55"
    assert registration.dddtel == "11"
    assert registration.tel == "999999999"
    assert registration.cpf == "52998224725"
    assert registration.email_viajante == "maria.souza@empresa.com"
    assert registration.cargo == "Analista Senior"
    assert registration.rg == "12 345 678"
    assert registration.passaporte == "AB 123456"
    assert registration.departamento == "Operacoes Comerciais"
    assert registration.data_admissao == date(2024, 2, 1)
    assert registration.data_nascimento == date(1990, 3, 10)
    assert not hasattr(registration, "data_solicitacao")


def test_optional_blank_fields_are_normalized_to_none() -> None:
    payload = valid_payload()
    payload.update({"rg": "   ", "passaporte": "", "departamento": None})

    registration = TravelRegistrationCreate.model_validate(payload)

    assert registration.rg is None
    assert registration.passaporte is None
    assert registration.departamento is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("nomeViajante", ""),
        ("matricula", " "),
        ("solicitanteEmail", "not-an-email"),
        ("centroCusto", "A123456"),
        ("dditel", "12345"),
        ("dddtel", "1"),
        ("tel", "1234567"),
        ("cpf", "111.111.111-11"),
        ("emailViajante", "maria@"),
        ("cargo", "<script>alert(1)</script>"),
        ("dataAdmissao", "2024-02-31"),
        ("dataNascimento", "not-a-date"),
    ],
)
def test_invalid_payload_generates_field_error_map(field: str, value: object) -> None:
    payload = valid_payload()
    payload[field] = value

    assert_field_error(payload, field)


def test_missing_required_fields_generate_public_field_names() -> None:
    payload = valid_payload()
    del payload["nomeViajante"]
    del payload["cpf"]

    with pytest.raises(ValidationError) as exc_info:
        TravelRegistrationCreate.model_validate(payload)

    fields = validation_error_fields(exc_info.value)

    assert "nomeViajante" in fields
    assert "cpf" in fields


def test_control_characters_are_rejected() -> None:
    payload = valid_payload()
    payload["nomeViajante"] = "Maria\nSouza"

    assert_field_error(payload, "nomeViajante")


def test_dangerous_payload_keys_are_rejected() -> None:
    payload = valid_payload()
    payload["dataSolicitacao"] = "2026-06-07T12:00:00Z"

    assert_field_error(payload, "dataSolicitacao")
