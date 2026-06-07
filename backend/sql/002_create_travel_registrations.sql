create extension if not exists pgcrypto;

create table if not exists public.travel_registrations (
    id uuid primary key default gen_random_uuid(),

    nome_viajante_encrypted text not null,
    matricula_encrypted text not null,
    data_solicitacao timestamptz not null default now(),

    solicitante_email_encrypted text not null,
    centro_custo_encrypted text not null,

    dditel_encrypted text not null,
    dddtel_encrypted text not null,
    tel_encrypted text not null,

    cpf_encrypted text not null,
    email_viajante_encrypted text not null,

    cargo_encrypted text not null,
    rg_encrypted text,
    passaporte_encrypted text,
    departamento_encrypted text,

    data_admissao_encrypted text not null,
    data_nascimento_encrypted text not null,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists idx_travel_registrations_data_solicitacao_desc
    on public.travel_registrations (data_solicitacao desc);
