import os
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

DEFAULT_ADMIN_SESSION_TTL_SECONDS = 30 * 60
DEFAULT_RATE_LIMIT_WINDOW_SECONDS = 60

LOCAL_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)

PRODUCTION_ORIGINS = (
    "https://tigrify.site",
    "https://www.tigrify.site",
)


class ControlledSettingsError(RuntimeError):
    """Raised when protected runtime configuration is missing or unsafe."""


@dataclass(frozen=True)
class DatabaseConfig:
    user: str
    password: str
    host: str
    port: int
    database: str


@dataclass(frozen=True)
class AdminSettings:
    username: str | None
    password_hash: str | None


@dataclass(frozen=True)
class SessionSettings:
    secret: str | None
    ttl_seconds: int


@dataclass(frozen=True)
class RateLimitSettings:
    window_seconds: int


@dataclass(frozen=True)
class ProtectedSettings:
    admin: AdminSettings
    encryption_key: str | None
    session: SessionSettings
    rate_limit: RateLimitSettings


def get_allowed_origins() -> list[str]:
    extra_origins = os.environ.get("ALLOWED_ORIGINS", "")
    custom_origins = [
        _normalize_origin(origin)
        for origin in extra_origins.split(",")
        if origin.strip()
    ]

    origins = [*LOCAL_ORIGINS, *PRODUCTION_ORIGINS, *custom_origins]
    _ensure_no_wildcard_origins(origins)

    return list(dict.fromkeys(origins))


def get_database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


def parse_database_url(database_url: str) -> DatabaseConfig:
    parsed = urlparse(database_url)

    if not parsed.hostname:
        raise ValueError("DATABASE_URL sem host válido.")

    return DatabaseConfig(
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/") or "postgres",
    )


def get_admin_settings() -> AdminSettings:
    return AdminSettings(
        username=_get_optional_env("ADMIN_USERNAME"),
        password_hash=_get_optional_env("ADMIN_PASSWORD_HASH"),
    )


def get_session_settings() -> SessionSettings:
    return SessionSettings(
        secret=_get_optional_env("SESSION_SECRET"),
        ttl_seconds=_get_positive_int_env(
            "ADMIN_SESSION_TTL_SECONDS",
            DEFAULT_ADMIN_SESSION_TTL_SECONDS,
        ),
    )


def get_rate_limit_settings() -> RateLimitSettings:
    return RateLimitSettings(
        window_seconds=_get_positive_int_env(
            "RATE_LIMIT_WINDOW_SECONDS",
            DEFAULT_RATE_LIMIT_WINDOW_SECONDS,
        ),
    )


def get_protected_settings() -> ProtectedSettings:
    return ProtectedSettings(
        admin=get_admin_settings(),
        encryption_key=_get_optional_env("ENCRYPTION_KEY"),
        session=get_session_settings(),
        rate_limit=get_rate_limit_settings(),
    )


def require_admin_settings() -> AdminSettings:
    admin_settings = get_admin_settings()

    missing = [
        name
        for name, value in (
            ("ADMIN_USERNAME", admin_settings.username),
            ("ADMIN_PASSWORD_HASH", admin_settings.password_hash),
        )
        if value is None
    ]

    if missing:
        raise ControlledSettingsError(
            f"Configuracao protegida ausente: {', '.join(missing)}."
        )

    return admin_settings


def require_encryption_key() -> str:
    encryption_key = _get_optional_env("ENCRYPTION_KEY")

    if encryption_key is None:
        raise ControlledSettingsError("Configuracao protegida ausente: ENCRYPTION_KEY.")

    return encryption_key


def require_session_secret() -> str:
    session_secret = _get_optional_env("SESSION_SECRET")

    if session_secret is None:
        raise ControlledSettingsError("Configuracao protegida ausente: SESSION_SECRET.")

    return session_secret


def _get_optional_env(name: str) -> str | None:
    value = os.environ.get(name)

    if value is None:
        return None

    stripped = value.strip()
    return stripped or None


def _get_positive_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except ValueError as error:
        raise ControlledSettingsError(f"{name} deve ser um inteiro positivo.") from error

    if value <= 0:
        raise ControlledSettingsError(f"{name} deve ser um inteiro positivo.")

    return value


def _normalize_origin(origin: str) -> str:
    return origin.strip().rstrip("/")


def _ensure_no_wildcard_origins(origins: list[str]) -> None:
    if any(origin == "*" for origin in origins):
        raise ControlledSettingsError("ALLOWED_ORIGINS nao pode conter wildcard.")
