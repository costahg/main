import os
from urllib.parse import unquote, urlparse

import pg8000.native
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://main-3tj.pages.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "ok": True,
        "message": "FastAPI respondeu com sucesso.",
    }


def parse_database_url(database_url: str):
    parsed = urlparse(database_url)

    return {
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "database": parsed.path.lstrip("/") or "postgres",
    }


@app.get("/db-health")
def db_health():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        return {
            "ok": False,
            "database": "missing DATABASE_URL",
        }

    conn = None

    try:
        config = parse_database_url(database_url)

        conn = pg8000.native.Connection(
            user=config["user"],
            password=config["password"],
            host=config["host"],
            port=config["port"],
            database=config["database"],
            ssl_context=True,
            timeout=5,
        )

        result = conn.run("select 1")
        connected = bool(result and result[0][0] == 1)

        return {
            "ok": connected,
            "database": "connected" if connected else "unexpected_response",
        }

    except Exception as error:
        print(f"Database health check failed: {type(error).__name__}: {error}")

        return {
            "ok": False,
            "database": "connection_failed",
            "error_type": type(error).__name__,
        }

    finally:
        if conn is not None:
            conn.close()
