# Document Parsing & Query Engine

> Turning messy invoices into structured, queryable data with spatial visual grounding.

This project helps AP and finance operations reviewers find invoice exceptions
quickly and verify extracted values against the original document before acting
on them.

## Planned stack

- **Frontend:** Next.js, React, and Tailwind
- **Backend:** Python, FastAPI, and Pydantic
- **Datastore:** PostgreSQL with JSONB and `pgvector`
- **Processing:** Celery and Redis
- **Local environment:** Docker Compose

## Core workflow

1. Upload a PDF, JPEG, or PNG invoice up to 5MB.
2. Process it asynchronously into structured invoice fields.
3. Flag low-confidence values and totals that do not reconcile with line items.
4. Review each flagged value against its source citation.
5. Search invoices using structured filters and semantic similarity.

The system is designed to surface uncertainty rather than silently correct
financial data.

## Local setup

Install Docker Desktop with the Compose plugin, then start the complete local
stack from the repository root:

```text
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- PostgreSQL with `pgvector`: internal service on port `5432`
- Redis: internal service on port `6379`
- Celery worker: internal background service

The default development database values are defined in `docker-compose.yml` and
can be overridden with a root `.env` file. The database and Redis data persist
in named Docker volumes. Stop the stack with `docker compose down`; remove local
data explicitly with `docker compose down -v`.

The worker currently exposes a connectivity-ready Celery entrypoint. Invoice
processing tasks are introduced in later implementation steps.

The backend applies the Alembic migrations during container startup. The current
persistence boundary supports creating and retrieving invoice metadata through
the `POST /invoices` and `GET /invoices/{id}` endpoints. File upload and
processing are added in later implementation steps.

For backend-only or frontend-only setup, see [`backend/README.md`](./backend/README.md)
and [`frontend/README.md`](./frontend/README.md).

## Continuous integration

GitHub Actions runs on pushes to `main` and on pull requests. It checks:

- Backend dependency installation, Ruff, and Pytest.
- Frontend `npm ci`, ESLint, and production build.
- Docker Compose configuration validity.

The current CI jobs do not start the full service stack because the existing
backend tests do not require PostgreSQL or Redis. Integration tests will add
those service dependencies when persistence and processing behavior are
introduced.

## Decisions

See [`decisions.md`](./decisions.md) for product framing, architectural
trade-offs, reliability decisions, and deliberately excluded scope.
