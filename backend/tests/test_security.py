import time

import pytest
from cryptography.fernet import Fernet

from settings import ControlledSettingsError
from security import (
    RateLimitExceeded,
    SecurityService,
    generate_admin_password_hash,
)


def configure_security_env(monkeypatch: pytest.MonkeyPatch, password: str = "correct-password") -> None:
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD_HASH", generate_admin_password_hash(password, salt="test-salt"))
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode("ascii"))
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret")
    monkeypatch.setenv("ADMIN_SESSION_TTL_SECONDS", "60")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")


def test_admin_password_verification_accepts_valid_password_and_rejects_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_security_env(monkeypatch)
    service = SecurityService()

    assert service.verify_admin_password("correct-password") is True
    assert service.verify_admin_password("wrong-password") is False


def test_admin_password_verification_requires_configured_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_security_env(monkeypatch)
    monkeypatch.delenv("ADMIN_PASSWORD_HASH")

    with pytest.raises(ControlledSettingsError):
        SecurityService().verify_admin_password("correct-password")


def test_session_cookie_is_signed_validated_and_rejects_tampering(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_security_env(monkeypatch)
    service = SecurityService(now_func=lambda: 1_000.0)

    cookie_value = service.create_session_cookie()

    assert service.validate_session_cookie(cookie_value) is True
    assert service.validate_session_cookie(f"{cookie_value}tampered") is False
    assert service.validate_session_cookie(None) is False
    assert service.validate_session_cookie("not-a-valid-cookie") is False


def test_expired_session_cookie_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_security_env(monkeypatch)
    service = SecurityService(now_func=lambda: 1_000.0)
    cookie_value = service.create_session_cookie()

    expired_service = SecurityService(now_func=lambda: 1_061.0)

    assert expired_service.validate_session_cookie(cookie_value) is False


def test_encrypt_decrypt_roundtrip_keeps_ciphertext_different_from_plaintext(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_security_env(monkeypatch)
    service = SecurityService()
    plaintext = "Maria 52998224725 maria@example.com"

    ciphertext = service.encrypt_optional(plaintext)

    assert ciphertext is not None
    assert ciphertext != plaintext
    assert plaintext not in ciphertext
    assert service.decrypt_optional(ciphertext) == plaintext
    assert service.encrypt_optional(None) is None
    assert service.decrypt_optional(None) is None


def test_encryption_requires_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_security_env(monkeypatch)
    monkeypatch.delenv("ENCRYPTION_KEY")

    with pytest.raises(ControlledSettingsError):
        SecurityService().encrypt_optional("sensitive")


def test_rate_limit_blocks_repeated_attempts_with_controlled_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_security_env(monkeypatch)
    current_time = time.time()
    service = SecurityService(now_func=lambda: current_time)

    for _ in range(5):
        service.check_rate_limit("admin_login", "login-block")

    with pytest.raises(RateLimitExceeded):
        service.check_rate_limit("admin_login", "login-block")


def test_rate_limit_window_expiry_allows_new_attempts(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_security_env(monkeypatch)
    current_time = 1_000.0
    service = SecurityService(now_func=lambda: current_time)

    for _ in range(5):
        service.check_rate_limit("admin_login", "login-expiry")

    current_time = 1_061.0

    service.check_rate_limit("admin_login", "login-expiry")


def test_public_submission_rate_limit_uses_separate_minimum_bucket(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_security_env(monkeypatch)
    service = SecurityService(now_func=lambda: 1_000.0)

    for _ in range(10):
        service.check_rate_limit("public_submission", "public-block")

    with pytest.raises(RateLimitExceeded):
        service.check_rate_limit("public_submission", "public-block")
