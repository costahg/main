import pytest

from settings import (
    ControlledSettingsError,
    get_allowed_origins,
    get_protected_settings,
    get_rate_limit_settings,
    require_admin_settings,
    require_encryption_key,
    require_session_secret,
)


def test_allowed_origins_include_exact_production_origins_without_wildcard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)

    origins = get_allowed_origins()

    assert "https://tigrify.site" in origins
    assert "https://www.tigrify.site" in origins
    assert "https://tigrify.site/" not in origins
    assert "*" not in origins


def test_allowed_origins_normalize_custom_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        " https://preview.tigrify.site/,http://localhost:4173/ ",
    )

    origins = get_allowed_origins()

    assert "https://preview.tigrify.site" in origins
    assert "http://localhost:4173" in origins
    assert "https://preview.tigrify.site/" not in origins


def test_allowed_origins_reject_wildcard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALLOWED_ORIGINS", "*,https://preview.tigrify.site")

    with pytest.raises(ControlledSettingsError):
        get_allowed_origins()


def test_protected_settings_expose_typed_runtime_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", "pbkdf2_sha256$100000$salt$hash")
    monkeypatch.setenv("ENCRYPTION_KEY", "encryption-key")
    monkeypatch.setenv("SESSION_SECRET", "session-secret")
    monkeypatch.setenv("ADMIN_SESSION_TTL_SECONDS", "900")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "120")

    settings = get_protected_settings()

    assert settings.admin.username == "admin"
    assert settings.admin.password_hash == "pbkdf2_sha256$100000$salt$hash"
    assert settings.encryption_key == "encryption-key"
    assert settings.session.secret == "session-secret"
    assert settings.session.ttl_seconds == 900
    assert settings.rate_limit.window_seconds == 120


def test_secret_defaults_are_absent_but_numeric_defaults_are_typed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD_HASH",
        "ENCRYPTION_KEY",
        "SESSION_SECRET",
        "ADMIN_SESSION_TTL_SECONDS",
        "RATE_LIMIT_WINDOW_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = get_protected_settings()
    rate_limit = get_rate_limit_settings()

    assert settings.admin.username is None
    assert settings.admin.password_hash is None
    assert settings.encryption_key is None
    assert settings.session.secret is None
    assert isinstance(settings.session.ttl_seconds, int)
    assert settings.session.ttl_seconds > 0
    assert isinstance(rate_limit.window_seconds, int)
    assert rate_limit.window_seconds > 0


def test_require_helpers_fail_controlled_when_secret_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in (
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD_HASH",
        "ENCRYPTION_KEY",
        "SESSION_SECRET",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ControlledSettingsError):
        require_admin_settings()

    with pytest.raises(ControlledSettingsError):
        require_encryption_key()

    with pytest.raises(ControlledSettingsError):
        require_session_secret()


def test_positive_integer_settings_reject_invalid_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ADMIN_SESSION_TTL_SECONDS", "0")

    with pytest.raises(ControlledSettingsError):
        get_protected_settings()

    monkeypatch.setenv("ADMIN_SESSION_TTL_SECONDS", "900")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "invalid")

    with pytest.raises(ControlledSettingsError):
        get_rate_limit_settings()
