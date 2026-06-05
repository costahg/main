from collections.abc import Iterator
from contextlib import contextmanager

import pg8000.native

from settings import get_database_url, parse_database_url

QUERY_TIMEOUT_SECONDS = 5
PROJECTS_LIMIT = 20


@contextmanager
def open_database_connection() -> Iterator[pg8000.native.Connection]:
    database_url = get_database_url()

    if not database_url:
        raise RuntimeError("DATABASE_URL não configurada.")

    config = parse_database_url(database_url)
    connection = pg8000.native.Connection(
        user=config.user,
        password=config.password,
        host=config.host,
        port=config.port,
        database=config.database,
        ssl_context=True,
        timeout=QUERY_TIMEOUT_SECONDS,
    )

    try:
        yield connection
    finally:
        connection.close()


def check_database_connection() -> bool:
    with open_database_connection() as connection:
        result = connection.run("select 1")
        return bool(result and result[0][0] == 1)


def list_projects() -> list[dict[str, str | None]]:
    query = f"""
        select
            id::text,
            name,
            notes,
            created_at::text
        from public.projects
        order by created_at desc
        limit {PROJECTS_LIMIT}
    """

    with open_database_connection() as connection:
        rows = connection.run(query)

    return [
        {
            "id": row[0],
            "name": row[1],
            "notes": row[2],
            "createdAt": row[3],
        }
        for row in rows
    ]
