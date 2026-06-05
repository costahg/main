import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

import pg8000.native


def get_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL não configurada.")

    return database_url


def open_connection(database_url: str) -> pg8000.native.Connection:
    parsed = urlparse(database_url)

    if not parsed.hostname:
        raise RuntimeError("DATABASE_URL sem host válido.")

    return pg8000.native.Connection(
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/") or "postgres",
        ssl_context=True,
        timeout=10,
    )


def split_sql_statements(sql: str) -> list[str]:
    return [
        statement.strip()
        for statement in sql.split(";")
        if statement.strip()
    ]


def run_sql_file(file_path: Path) -> None:
    sql = file_path.read_text(encoding="utf-8")
    statements = split_sql_statements(sql)

    if not statements:
        raise RuntimeError(f"Nenhum SQL encontrado em {file_path}")

    connection = open_connection(get_database_url())

    try:
        for statement in statements:
            connection.run(statement)

        print(f"SQL executado com sucesso: {file_path}")
    finally:
        connection.close()


def main() -> None:
    if len(sys.argv) != 2:
        raise RuntimeError("Uso: python scripts/run_sql.py caminho/do/arquivo.sql")

    run_sql_file(Path(sys.argv[1]))


if __name__ == "__main__":
    main()
