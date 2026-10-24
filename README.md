# User accounts

A small FastAPI app with registration, login, active sessions, and a plain HTML/CSS/JavaScript frontend.

## Run

```bash
uv sync
uv run python main.py
```

Open http://127.0.0.1:8000 for the frontend or http://127.0.0.1:8000/docs for the API.
The app starts without Supabase credentials. Account operations return HTTP 503 until configured.

## Configure later

Copy `.env.example` to `.env`. Fill `SUPABASE_URL`, `SUPABASE_KEY`, and `SECRET_KEY` (a random secret of at least 32 bytes).
Use a backend-only Supabase secret/service role key. Never put it in the frontend.
Restart the server after changing configuration.

The app uses custom username/password accounts and JWT sessions stored in Supabase tables, rather than Supabase Auth.
Run this SQL manually in your Supabase SQL editor when you are ready:

```sql
create table public."user" (
    username text primary key,
    password text not null
);
create table public.active_session (
    username text primary key references public."user" (username) on delete cascade,
    access_token text not null,
    expiry_time timestamptz not null
);
alter table public."user" enable row level security;
alter table public.active_session enable row level security;
revoke all on table public."user", public.active_session from anon, authenticated;
grant select, insert, update, delete on table public."user", public.active_session to service_role;
```

If the tables already exist, ensure they have these columns and unique usernames instead of running `create table` again.
`USER_COLLECTION` and `SESSION` can override table names; despite their original names, these now refer to SQL tables.

## Endpoints

- `POST /users/register`: JSON username and password.
- `POST /users/token`: form-encoded username and password; returns a bearer token.
- `GET /users/me`: validates the bearer token and active session; returns the username.
- `POST /users/logout`: validates and removes the bearer token's session.

Use `Authorization: Bearer <token>` for authenticated requests. Passwords are limited to 72 UTF-8 bytes for bcrypt.
The frontend keeps its token in memory; refreshing the page requires signing in again.
An existing valid session is reused after password verification. Logout revokes it.

## Test

```bash
uv run python -m unittest discover -s tests -v
```

Tests use a fake Supabase database. They do not write to a real account.
See [CHANGES_REPORT.md](CHANGES_REPORT.md) for mistakes, corrections, and validation results.
