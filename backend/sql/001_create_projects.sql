create extension if not exists pgcrypto;

create table if not exists public.projects (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    notes text,
    created_at timestamptz not null default now()
);

insert into public.projects (name, notes)
values
    ('Tigrify', 'Primeiro registro real vindo do Supabase.')
on conflict do nothing;
