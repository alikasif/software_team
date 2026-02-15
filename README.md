# Splitwise MVP Backend

API-first backend scaffold for a Splitwise-style application using FastAPI and PostgreSQL.

## Current Status
- Scaffold is in place for modules, routing, config, DB wiring, and tests layout.
- Business endpoints and financial logic are planned but not fully implemented yet.
- See `shared/task_list.json` for delivery status by task.

## Tech Stack
- FastAPI
- PostgreSQL
- SQLAlchemy 2.x
- Alembic
- JWT auth (planned)

## Local Setup
1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set secrets/DB connection.
4. Ensure PostgreSQL is running and reachable by `DATABASE_URL`.

## Run
- API server: `uvicorn app.main:app --reload`
- Health check: `GET /health`
- Versioned API base: `/api/v1`

## Database Migration Commands
- Create revision: `alembic revision -m "<message>"`
- Apply migrations: `alembic upgrade head`
- Roll back one: `alembic downgrade -1`

## Documentation
- Docs index: `docs/README.md`
- API usage: `docs/api_usage.md`
- Runbook and consistency notes: `docs/runbook.md`

## Project Layout
See `shared/project_structure.json` for the canonical structure summary.
