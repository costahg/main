from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass

import pg8000.native

from settings import get_database_url, parse_database_url

QUERY_TIMEOUT_SECONDS = 5
PROJECTS_LIMIT = 20
TRAVEL_REGISTRATIONS_LIMIT = 100


@dataclass(frozen=True)
class EncryptedTravelRegistration:
    nome_viajante_encrypted: str
    matricula_encrypted: str
    solicitante_email_encrypted: str
    centro_custo_encrypted: str
    dditel_encrypted: str
    dddtel_encrypted: str
    tel_encrypted: str
    cpf_encrypted: str
    email_viajante_encrypted: str
    cargo_encrypted: str
    rg_encrypted: str | None
    passaporte_encrypted: str | None
    departamento_encrypted: str | None
    data_admissao_encrypted: str
    data_nascimento_encrypted: str


@dataclass(frozen=True)
class EncryptedTravelRegistrationRow:
    id: str
    nome_viajante_encrypted: str
    matricula_encrypted: str
    data_solicitacao: str
    solicitante_email_encrypted: str
    centro_custo_encrypted: str
    dditel_encrypted: str
    dddtel_encrypted: str
    tel_encrypted: str
    cpf_encrypted: str
    email_viajante_encrypted: str
    cargo_encrypted: str
    rg_encrypted: str | None
    passaporte_encrypted: str | None
    departamento_encrypted: str | None
    data_admissao_encrypted: str
    data_nascimento_encrypted: str
    created_at: str
    updated_at: str


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


def create_travel_registration(record: EncryptedTravelRegistration) -> str:
    query = """
        insert into public.travel_registrations (
            nome_viajante_encrypted,
            matricula_encrypted,
            solicitante_email_encrypted,
            centro_custo_encrypted,
            dditel_encrypted,
            dddtel_encrypted,
            tel_encrypted,
            cpf_encrypted,
            email_viajante_encrypted,
            cargo_encrypted,
            rg_encrypted,
            passaporte_encrypted,
            departamento_encrypted,
            data_admissao_encrypted,
            data_nascimento_encrypted
        ) values (
            :nome_viajante_encrypted,
            :matricula_encrypted,
            :solicitante_email_encrypted,
            :centro_custo_encrypted,
            :dditel_encrypted,
            :dddtel_encrypted,
            :tel_encrypted,
            :cpf_encrypted,
            :email_viajante_encrypted,
            :cargo_encrypted,
            :rg_encrypted,
            :passaporte_encrypted,
            :departamento_encrypted,
            :data_admissao_encrypted,
            :data_nascimento_encrypted
        )
        returning id::text
    """

    with open_database_connection() as connection:
        rows = connection.run(query, **asdict(record))

    if not rows:
        raise RuntimeError("Travel registration insert did not return an id.")

    return str(rows[0][0])


def list_travel_registrations(
    limit: int = TRAVEL_REGISTRATIONS_LIMIT,
) -> list[EncryptedTravelRegistrationRow]:
    bounded_limit = max(1, min(limit, TRAVEL_REGISTRATIONS_LIMIT))
    query = """
        select
            id::text,
            nome_viajante_encrypted,
            matricula_encrypted,
            data_solicitacao::text,
            solicitante_email_encrypted,
            centro_custo_encrypted,
            dditel_encrypted,
            dddtel_encrypted,
            tel_encrypted,
            cpf_encrypted,
            email_viajante_encrypted,
            cargo_encrypted,
            rg_encrypted,
            passaporte_encrypted,
            departamento_encrypted,
            data_admissao_encrypted,
            data_nascimento_encrypted,
            created_at::text,
            updated_at::text
        from public.travel_registrations
        order by data_solicitacao desc
        limit :limit
    """

    with open_database_connection() as connection:
        rows = connection.run(query, limit=bounded_limit)

    return [
        EncryptedTravelRegistrationRow(
            id=str(row[0]),
            nome_viajante_encrypted=row[1],
            matricula_encrypted=row[2],
            data_solicitacao=str(row[3]),
            solicitante_email_encrypted=row[4],
            centro_custo_encrypted=row[5],
            dditel_encrypted=row[6],
            dddtel_encrypted=row[7],
            tel_encrypted=row[8],
            cpf_encrypted=row[9],
            email_viajante_encrypted=row[10],
            cargo_encrypted=row[11],
            rg_encrypted=row[12],
            passaporte_encrypted=row[13],
            departamento_encrypted=row[14],
            data_admissao_encrypted=row[15],
            data_nascimento_encrypted=row[16],
            created_at=str(row[17]),
            updated_at=str(row[18]),
        )
        for row in rows
    ]


def delete_travel_registration(registration_id: str) -> bool:
    query = """
        delete from public.travel_registrations
        where id = :registration_id
        returning id::text
    """

    with open_database_connection() as connection:
        rows = connection.run(query, registration_id=registration_id)

    return bool(rows)
