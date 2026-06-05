from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import check_database_connection, list_projects
from settings import get_allowed_origins

app = FastAPI(title="Tigrify API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        print(f"Database health check failed: {type(error).__name__}: {error}")

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
        print(f"Project list failed: {type(error).__name__}: {error}")

        raise HTTPException(
            status_code=500,
            detail="Não foi possível carregar os projetos.",
        ) from error
