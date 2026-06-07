import hmac
from datetime import date
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from database import (
    EncryptedTravelRegistrationRow,
    EncryptedTravelRegistration,
    check_database_connection,
    create_travel_registration,
    delete_travel_registration,
    list_travel_registrations,
    list_projects,
)
from schemas import TravelRegistrationCreate, validation_error_fields
from security import RateLimitExceeded, SESSION_COOKIE_NAME, SecurityService
from settings import (
    ControlledSettingsError,
    get_allowed_origins,
    get_session_settings,
    require_admin_settings,
)

app = FastAPI(title="Tigrify API")
security_service = SecurityService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AdminLoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health() -> dict[str, bool | str]:
    return {
        "ok": True,
        "message": "FastAPI respondeu com sucesso.",
    }


@app.get("/db-health")
def db_health() -> dict[str, bool | str]:
    try:
        connected = check_database_connection()

        return {
            "ok": connected,
            "database": "connected" if connected else "unexpected_response",
        }
    except RuntimeError:
        return {
            "ok": False,
            "database": "missing DATABASE_URL",
        }
    except Exception as error:
        _log_safe_internal_error("database_health_check_failed", error)

        return {
            "ok": False,
            "database": "connection_failed",
            "errorType": type(error).__name__,
        }


@app.get("/projects")
def get_projects() -> dict[str, object]:
    try:
        return {
            "ok": True,
            "projects": list_projects(),
        }
    except Exception as error:
        _log_safe_internal_error("project_list_failed", error)

        raise HTTPException(
            status_code=500,
            detail="Não foi possível carregar os projetos.",
        ) from error


@app.post("/admin/login")
async def admin_login(request: Request, credentials: AdminLoginRequest) -> JSONResponse:
    try:
        security_service.check_rate_limit("admin_login", _client_key(request))
        admin_settings = require_admin_settings()
        username_matches = (
            admin_settings.username is not None
            and hmac.compare_digest(credentials.username, admin_settings.username)
        )
        password_matches = security_service.verify_admin_password(credentials.password)

        if not (username_matches and password_matches):
            _log_safe_event("admin_login_failed", error_type="InvalidCredentials")
            return _invalid_credentials_response()

        cookie_value = security_service.create_session_cookie()
        ttl_seconds = get_session_settings().ttl_seconds
        response = JSONResponse(
            status_code=200,
            content={"ok": True},
        )
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=cookie_value,
            max_age=ttl_seconds,
            httponly=True,
            secure=True,
            samesite="strict",
            path="/",
        )

        return response
    except RateLimitExceeded:
        return _rate_limit_response()
    except ControlledSettingsError as error:
        _log_safe_internal_error("admin_login_failed", error)
        return _internal_admin_error()
    except Exception as error:
        _log_safe_internal_error("admin_login_failed", error)
        return _internal_admin_error()


@app.get("/admin/session")
def admin_session(request: Request) -> dict[str, bool]:
    try:
        authenticated = security_service.validate_session_cookie(
            request.cookies.get(SESSION_COOKIE_NAME)
        )
    except ControlledSettingsError as error:
        _log_safe_internal_error("admin_session_check_failed", error)
        authenticated = False

    return {
        "ok": True,
        "authenticated": authenticated,
    }


@app.post("/admin/logout")
def admin_logout() -> JSONResponse:
    response = JSONResponse(
        status_code=200,
        content={"ok": True},
    )
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )

    return response


@app.post("/travel-registrations")
async def submit_travel_registration(request: Request) -> JSONResponse:
    try:
        security_service.check_rate_limit("public_submission", _client_key(request))
        payload = await request.json()

        if not isinstance(payload, dict):
            return _validation_response({"body": "payload invalido"})

        registration = TravelRegistrationCreate.model_validate(payload)
        encrypted_record = _encrypt_registration(registration)
        registration_id = create_travel_registration(encrypted_record)

        _log_safe_event(
            "travel_registration_created",
            registration_id=registration_id,
        )

        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "id": registration_id,
            },
        )
    except ValidationError as error:
        return _validation_response(validation_error_fields(error))
    except RateLimitExceeded:
        return _rate_limit_response()
    except ControlledSettingsError as error:
        _log_safe_internal_error("travel_registration_submission_failed", error)
        return _internal_registration_error()
    except Exception as error:
        _log_safe_internal_error("travel_registration_submission_failed", error)
        return _internal_registration_error()


@app.get("/admin/travel-registrations")
def admin_list_travel_registrations(request: Request) -> JSONResponse:
    if not _has_valid_admin_session(request):
        return _unauthorized_admin_response()

    try:
        registrations = [
            _decrypt_admin_registration(row)
            for row in list_travel_registrations()
        ]

        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "registrations": registrations,
            },
        )
    except ControlledSettingsError as error:
        _log_safe_internal_error("admin_travel_registration_list_failed", error)
        return _internal_admin_registration_error()
    except Exception as error:
        _log_safe_internal_error("admin_travel_registration_list_failed", error)
        return _internal_admin_registration_error()


@app.delete("/admin/travel-registrations/{registration_id}")
def admin_delete_travel_registration(request: Request, registration_id: str) -> JSONResponse:
    if not _has_valid_admin_session(request):
        return _unauthorized_admin_response()

    try:
        if not delete_travel_registration(registration_id):
            return JSONResponse(
                status_code=404,
                content={
                    "ok": False,
                    "error": "not_found",
                    "message": "Registro nao encontrado.",
                },
            )

        _log_safe_event(
            "admin_deleted_registration",
            registration_id=registration_id,
        )

        return JSONResponse(
            status_code=200,
            content={"ok": True},
        )
    except Exception as error:
        _log_safe_internal_error(
            "admin_travel_registration_delete_failed",
            error,
            registration_id=registration_id,
        )
        return _internal_admin_registration_error()


def _encrypt_registration(registration: TravelRegistrationCreate) -> EncryptedTravelRegistration:
    return EncryptedTravelRegistration(
        nome_viajante_encrypted=_encrypt_required(registration.nome_viajante),
        matricula_encrypted=_encrypt_required(registration.matricula),
        solicitante_email_encrypted=_encrypt_required(registration.solicitante_email),
        centro_custo_encrypted=_encrypt_required(registration.centro_custo),
        dditel_encrypted=_encrypt_required(registration.dditel),
        dddtel_encrypted=_encrypt_required(registration.dddtel),
        tel_encrypted=_encrypt_required(registration.tel),
        cpf_encrypted=_encrypt_required(registration.cpf),
        email_viajante_encrypted=_encrypt_required(registration.email_viajante),
        cargo_encrypted=_encrypt_required(registration.cargo),
        rg_encrypted=security_service.encrypt_optional(registration.rg),
        passaporte_encrypted=security_service.encrypt_optional(registration.passaporte),
        departamento_encrypted=security_service.encrypt_optional(registration.departamento),
        data_admissao_encrypted=_encrypt_required(_date_to_iso(registration.data_admissao)),
        data_nascimento_encrypted=_encrypt_required(_date_to_iso(registration.data_nascimento)),
    )


def _encrypt_required(value: str) -> str:
    encrypted = security_service.encrypt_optional(value)

    if encrypted is None:
        raise ControlledSettingsError("Falha controlada ao criptografar campo obrigatorio.")

    return encrypted


def _date_to_iso(value: date) -> str:
    return value.isoformat()


def _has_valid_admin_session(request: Request) -> bool:
    try:
        return security_service.validate_session_cookie(
            request.cookies.get(SESSION_COOKIE_NAME)
        )
    except ControlledSettingsError as error:
        _log_safe_internal_error("admin_session_validation_failed", error)
        return False


def _decrypt_admin_registration(row: EncryptedTravelRegistrationRow) -> dict[str, str | None]:
    return {
        "id": row.id,
        "dataSolicitacao": row.data_solicitacao,
        "nomeViajante": _decrypt_required(row.nome_viajante_encrypted),
        "matricula": _decrypt_required(row.matricula_encrypted),
        "solicitanteEmail": _decrypt_required(row.solicitante_email_encrypted),
        "centroCusto": _decrypt_required(row.centro_custo_encrypted),
        "dditel": _decrypt_required(row.dditel_encrypted),
        "dddtel": _decrypt_required(row.dddtel_encrypted),
        "tel": _decrypt_required(row.tel_encrypted),
        "cpf": _decrypt_required(row.cpf_encrypted),
        "emailViajante": _decrypt_required(row.email_viajante_encrypted),
        "cargo": _decrypt_required(row.cargo_encrypted),
        "rg": security_service.decrypt_optional(row.rg_encrypted),
        "passaporte": security_service.decrypt_optional(row.passaporte_encrypted),
        "departamento": security_service.decrypt_optional(row.departamento_encrypted),
        "dataAdmissao": _decrypt_required(row.data_admissao_encrypted),
        "dataNascimento": _decrypt_required(row.data_nascimento_encrypted),
    }


def _decrypt_required(value: str) -> str:
    decrypted = security_service.decrypt_optional(value)

    if decrypted is None:
        raise ControlledSettingsError("Falha controlada ao descriptografar campo obrigatorio.")

    return decrypted


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def _validation_response(fields: dict[str, str]) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "error": "validation_error",
            "fields": fields,
        },
    )


def _invalid_credentials_response() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "ok": False,
            "error": "invalid_credentials",
            "message": "Credenciais invalidas.",
        },
    )


def _rate_limit_response() -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "ok": False,
            "error": "rate_limit_exceeded",
            "message": "Muitas tentativas. Tente novamente em instantes.",
        },
    )


def _unauthorized_admin_response() -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "ok": False,
            "error": "unauthorized",
            "message": "Sessao admin invalida.",
        },
    )


def _internal_admin_error() -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": "internal_error",
            "message": "Nao foi possivel autenticar.",
        },
    )


def _internal_admin_registration_error() -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": "internal_error",
            "message": "Nao foi possivel processar registros administrativos.",
        },
    )


def _internal_registration_error() -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": "internal_error",
            "message": "Nao foi possivel enviar o registro.",
        },
    )


def _log_safe_internal_error(
    event_name: str,
    error: Exception,
    *,
    registration_id: str | None = None,
) -> None:
    _log_safe_event(
        event_name,
        error_type=type(error).__name__,
        registration_id=registration_id,
    )


def _log_safe_event(
    event_name: str,
    *,
    error_type: str | None = None,
    registration_id: str | None = None,
) -> None:
    parts = [event_name]

    if error_type:
        parts.append(f"error_type={_safe_log_token(error_type)}")

    if registration_id:
        safe_registration_id = _safe_registration_id(registration_id)
        if safe_registration_id:
            parts.append(f"registration_id={safe_registration_id}")

    print(" ".join(parts))


def _safe_log_token(value: str) -> str:
    return "".join(
        character if character.isascii() and (character.isalnum() or character in "-_.") else "_"
        for character in value
    )[:120]


def _safe_registration_id(value: str) -> str | None:
    try:
        parsed = UUID(value)
    except ValueError:
        return None

    return str(parsed)
