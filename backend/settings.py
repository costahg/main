import os
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

LOCAL_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)

PRODUCTION_ORIGINS = (
    "https://tigrify.site",
    "https://www.tigrify.site",
)


@dataclass(frozen=True)
class DatabaseConfig:
    user: str
    password: str
    host: str
    port: int
    database: str


def get_allowed_origins() -> list[str]:
    extra_origins = os.environ.get("ALLOWED_ORIGINS", "")
    custom_origins = [
        origin.strip().rstrip("/")
        for origin in extra_origins.split(",")
        if origin.strip()
    ]

    return [*LOCAL_ORIGINS, *PRODUCTION_ORIGINS, *custom_origins]


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
