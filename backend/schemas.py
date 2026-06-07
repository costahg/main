from __future__ import annotations

from datetime import date
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_EVENT_HANDLER = re.compile(r"\bon[a-z]+\s*=", re.IGNORECASE)
_DANGEROUS_SCHEMES = re.compile(
    r"\b(?:javascript|vbscript)\s*:|\bdata\s*:\s*text/html",
    re.IGNORECASE,
)
_CPF_ALLOWED_CHARS = re.compile(r"^[\d.\-\s]+$")

_OPTIONAL_FIELDS = {"rg", "passaporte", "departamento"}

_PUBLIC_FIELD_BY_INTERNAL = {
    "nome_viajante": "nomeViajante",
    "matricula": "matricula",
    "solicitante_email": "solicitanteEmail",
    "centro_custo": "centroCusto",
    "dditel": "dditel",
    "dddtel": "dddtel",
    "tel": "tel",
    "cpf": "cpf",
    "email_viajante": "emailViajante",
    "cargo": "cargo",
    "rg": "rg",
    "passaporte": "passaporte",
    "departamento": "departamento",
    "data_admissao": "dataAdmissao",
    "data_nascimento": "dataNascimento",
}


def _public_field_name(field_name: str) -> str:
    return _PUBLIC_FIELD_BY_INTERNAL.get(field_name, field_name)


def _normalize_text(value: Any, field_name: str) -> Any:
    if not isinstance(value, str):
        return value

    if _CONTROL_CHARS.search(value):
        raise ValueError("contem caracteres nao permitidos")

    normalized = " ".join(value.strip().split())

    if field_name in _OPTIONAL_FIELDS and normalized == "":
        return None

    if normalized == "":
        raise ValueError("campo obrigatorio")

    if (
        "<" in normalized
        or ">" in normalized
        or _EVENT_HANDLER.search(normalized)
        or _DANGEROUS_SCHEMES.search(normalized)
    ):
        raise ValueError("contem conteudo nao permitido")

    return normalized


def _validate_email(value: str) -> str:
    normalized = value.lower()

    if not _EMAIL.fullmatch(normalized):
        raise ValueError("e-mail invalido")

    return normalized


def _validate_digits(value: str, length_pattern: str, message: str) -> str:
    if not re.fullmatch(length_pattern, value):
        raise ValueError(message)

    return value


def _validate_cpf(value: str) -> str:
    if not _CPF_ALLOWED_CHARS.fullmatch(value):
        raise ValueError("CPF invalido")

    digits = re.sub(r"\D", "", value)

    if len(digits) != 11 or len(set(digits)) == 1:
        raise ValueError("CPF invalido")

    first_digit = _calculate_cpf_digit(digits[:9], weight_start=10)
    second_digit = _calculate_cpf_digit(digits[:10], weight_start=11)

    if digits[-2:] != f"{first_digit}{second_digit}":
        raise ValueError("CPF invalido")

    return digits


def _calculate_cpf_digit(digits: str, weight_start: int) -> int:
    total = sum(int(digit) * weight for digit, weight in zip(digits, range(weight_start, 1, -1)))
    remainder = (total * 10) % 11
    return 0 if remainder == 10 else remainder


class TravelRegistrationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=False)

    nome_viajante: str = Field(alias="nomeViajante")
    matricula: str
    solicitante_email: str = Field(alias="solicitanteEmail")
    centro_custo: str = Field(alias="centroCusto")
    dditel: str = "55"
    dddtel: str
    tel: str
    cpf: str
    email_viajante: str = Field(alias="emailViajante")
    cargo: str
    rg: str | None = None
    passaporte: str | None = None
    departamento: str | None = None
    data_admissao: date = Field(alias="dataAdmissao")
    data_nascimento: date = Field(alias="dataNascimento")

    @field_validator("*", mode="before")
    @classmethod
    def normalize_strings(cls, value: Any, info: Any) -> Any:
        return _normalize_text(value, info.field_name)

    @field_validator("solicitante_email", "email_viajante")
    @classmethod
    def validate_email_fields(cls, value: str) -> str:
        return _validate_email(value)

    @field_validator("centro_custo")
    @classmethod
    def validate_centro_custo(cls, value: str) -> str:
        normalized = value.upper()

        if not normalized.startswith("T"):
            raise ValueError("centro de custo invalido")

        return normalized

    @field_validator("dditel")
    @classmethod
    def validate_ddi(cls, value: str) -> str:
        return _validate_digits(value, r"\d{1,4}", "DDI invalido")

    @field_validator("dddtel")
    @classmethod
    def validate_ddd(cls, value: str) -> str:
        return _validate_digits(value, r"\d{2}", "DDD invalido")

    @field_validator("tel")
    @classmethod
    def validate_tel(cls, value: str) -> str:
        return _validate_digits(value, r"\d{8,9}", "telefone invalido")

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, value: str) -> str:
        return _validate_cpf(value)


def validation_error_fields(error: ValidationError) -> dict[str, str]:
    fields: dict[str, str] = {}

    for item in error.errors():
        loc = item.get("loc", ())
        if not loc:
            continue

        field_name = str(loc[0])
        public_name = _public_field_name(field_name)
        message = _public_error_message(item)

        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")

        fields.setdefault(public_name, message)

    return fields


def _public_error_message(item: dict[str, Any]) -> str:
    error_type = str(item.get("type", ""))

    if error_type == "missing":
        return "campo obrigatorio"

    if error_type == "extra_forbidden":
        return "campo nao permitido"

    if error_type.startswith("date_"):
        return "data invalida"

    message = str(item.get("msg", "valor invalido"))

    if message.startswith("Value error, "):
        return message.removeprefix("Value error, ")

    return message
