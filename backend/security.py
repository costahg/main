from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from cryptography.fernet import Fernet, InvalidToken

from settings import (
    ControlledSettingsError,
    get_rate_limit_settings,
    get_session_settings,
    require_admin_settings,
    require_encryption_key,
    require_session_secret,
)


PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
DEFAULT_PASSWORD_HASH_ITERATIONS = 600_000
SESSION_COOKIE_NAME = "admin_session"
ADMIN_LOGIN_RATE_LIMIT = 5
PUBLIC_SUBMISSION_RATE_LIMIT = 10
DEFAULT_RATE_LIMIT = 10


class RateLimitExceeded(RuntimeError):
    """Raised when a process-local rate limit bucket rejects an attempt."""


@dataclass
class _RateLimitStore:
    attempts_by_key: dict[tuple[str, str], deque[float]] = field(default_factory=dict)


_DEFAULT_RATE_LIMIT_STORE = _RateLimitStore()


class SecurityService:
    def __init__(
        self,
        *,
        now_func: Callable[[], float] | None = None,
        rate_limit_store: _RateLimitStore | None = None,
    ) -> None:
        self._now_func = now_func or time.time
        self._rate_limit_store = rate_limit_store or _DEFAULT_RATE_LIMIT_STORE

    def verify_admin_password(self, password: str) -> bool:
        admin_settings = require_admin_settings()
        password_hash = admin_settings.password_hash

        if password_hash is None:
            raise ControlledSettingsError("Configuracao protegida ausente: ADMIN_PASSWORD_HASH.")

        try:
            algorithm, iterations_text, salt, expected_hash = password_hash.split("$", 3)
            iterations = int(iterations_text)
        except ValueError:
            return False

        if algorithm != PASSWORD_HASH_ALGORITHM or iterations <= 0 or not salt or not expected_hash:
            return False

        candidate_hash = _derive_password_hash(password, iterations=iterations, salt=salt)
        return hmac.compare_digest(candidate_hash, expected_hash)

    def create_session_cookie(self) -> str:
        session_secret = require_session_secret()
        ttl_seconds = get_session_settings().ttl_seconds
        expires_at = int(self._now_func() + ttl_seconds)
        payload = {
            "exp": expires_at,
            "nonce": secrets.token_urlsafe(16),
        }
        encoded_payload = _base64url_encode(_json_payload(payload))
        signature = _sign(encoded_payload, session_secret)

        return f"{encoded_payload}.{signature}"

    def validate_session_cookie(self, cookie_value: str | None) -> bool:
        if not cookie_value:
            return False

        session_secret = require_session_secret()

        try:
            encoded_payload, signature = cookie_value.split(".", 1)
        except ValueError:
            return False

        expected_signature = _sign(encoded_payload, session_secret)
        if not hmac.compare_digest(signature, expected_signature):
            return False

        try:
            payload = json.loads(_base64url_decode(encoded_payload))
        except (binascii.Error, UnicodeEncodeError, ValueError, json.JSONDecodeError):
            return False

        expires_at = payload.get("exp")
        nonce = payload.get("nonce")

        if not isinstance(expires_at, int) or not isinstance(nonce, str) or not nonce:
            return False

        return expires_at > int(self._now_func())

    def encrypt_optional(self, value: str | None) -> str | None:
        if value is None:
            return None

        fernet = _get_fernet()
        return fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt_optional(self, value: str | None) -> str | None:
        if value is None:
            return None

        fernet = _get_fernet()

        try:
            return fernet.decrypt(value.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError) as error:
            raise ControlledSettingsError("Falha controlada ao descriptografar campo sensivel.") from error

    def check_rate_limit(self, bucket: str, key: str) -> None:
        settings = get_rate_limit_settings()
        limit = _rate_limit_for_bucket(bucket)
        now = self._now_func()
        cutoff = now - settings.window_seconds
        store_key = (bucket, key)
        attempts = self._rate_limit_store.attempts_by_key.setdefault(store_key, deque())

        while attempts and attempts[0] <= cutoff:
            attempts.popleft()

        if len(attempts) >= limit:
            raise RateLimitExceeded("rate limit excedido")

        attempts.append(now)


def generate_admin_password_hash(
    password: str,
    *,
    iterations: int = DEFAULT_PASSWORD_HASH_ITERATIONS,
    salt: str | None = None,
) -> str:
    if iterations <= 0:
        raise ValueError("iterations deve ser positivo")

    password_salt = salt or secrets.token_urlsafe(16)
    derived_hash = _derive_password_hash(password, iterations=iterations, salt=password_salt)

    return f"{PASSWORD_HASH_ALGORITHM}${iterations}${password_salt}${derived_hash}"


def _derive_password_hash(password: str, *, iterations: int, salt: str) -> str:
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return _base64url_encode(derived)


def _get_fernet() -> Fernet:
    encryption_key = require_encryption_key()

    try:
        return Fernet(encryption_key.encode("ascii"))
    except (ValueError, TypeError) as error:
        raise ControlledSettingsError("ENCRYPTION_KEY invalida.") from error


def _rate_limit_for_bucket(bucket: str) -> int:
    if bucket == "admin_login":
        return ADMIN_LOGIN_RATE_LIMIT

    if bucket == "public_submission":
        return PUBLIC_SUBMISSION_RATE_LIMIT

    return DEFAULT_RATE_LIMIT


def _json_payload(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def _sign(encoded_payload: str, session_secret: str) -> str:
    digest = hmac.new(
        session_secret.encode("utf-8"),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(digest)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))
