-- Ejecuta esto una sola vez en Supabase SQL Editor.
-- Las tres primeras columnas ya tienen equivalentes en la app Streamlit.
alter table usuarios add column if not exists casino_played integer not null default 0;
alter table usuarios add column if not exists casino_date text not null default '';
alter table usuarios add column if not exists wins integer not null default 0;
alter table usuarios add column if not exists losses integer not null default 0;

-- Recomendado para producción: historial auditable de movimientos.
create table if not exists casino_movimientos (
  id uuid primary key default gen_random_uuid(),
  device_id text not null references usuarios(device_id) on delete cascade,
  juego text not null check (juego in ('slots', 'roulette')),
  apuesta integer not null check (apuesta between 5 and 500),
  premio integer not null default 0,
  resultado jsonb not null default '{}'::jsonb,
  creado_en timestamptz not null default now()
);
