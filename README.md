# Document Parsing & Query Engine

> Turn messy invoices into structured, queryable data with source-grounded review.

This application helps AP and finance operations reviewers find invoice
exceptions before approving payments. It preserves extracted values, confidence,
review reasons, and source references used to verify them.

## Stack

- **Frontend:** Next.js, React, and Tailwind
- **Backend:** Python, FastAPI, and Pydantic
- **Datastore:** PostgreSQL with JSONB and `pgvector`
- **Processing:** Celery and Redis
- **Local environment:** Docker Compose

## Current capabilities

- Upload PDF, JPEG, and PNG invoices up to 5MB.
- Store invoice metadata in PostgreSQL.
- Process jobs asynchronously through Celery and Redis.
- Extract deterministic fixture invoices into fields and line items.
- Persist raw text, confidence signals, citations, issues, and search chunks.
- Generate local `all-MiniLM-L6-v2` embeddings in PostgreSQL `pgvector`.
- Flag low-confidence fields without discarding valid fields.
- Flag total/line-item mismatches without changing either total.
- Recover from malformed extraction with one repair attempt and review fallback.
- Search using structured filters, semantic ranking, or both.
- Review fields, issues, citations, and source-text highlights in the UI.
- Track requests and worker tasks with correlation IDs.

## Local setup

Install Docker Desktop, then start the stack from the repository root:

```text
docker-compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`
- PostgreSQL + `pgvector`: internal port `5432`
- Redis: internal port `6379`
- Celery worker: internal background service

The backend applies Alembic migrations during startup. PostgreSQL, Redis, and
uploaded files use named Docker volumes. Stop services with
`docker-compose down`; remove local data with `docker-compose down -v`.

For service-specific setup, see [`backend/README.md`](./backend/README.md) and
[`frontend/README.md`](./frontend/README.md).

## Representative workflow

1. Choose an invoice in the frontend.
2. Client-side validation checks type and size before upload.
3. The API stores the file and creates an idempotent processing job.
4. The worker extracts fields, citations, and chunks in one transaction.
5. The UI polls status and links to the invoice review page.
6. Review flagged fields, arithmetic issues, and source citations before acting.

## Search examples

```text
GET /invoices?vendor=Acme&total_min=1000&status=ready
GET /invoices/search/semantic?q=consulting%20services&limit=10
GET /invoices/search/hybrid?q=payment%20terms&vendor=Acme&total_min=1000
```

## Development checks

Backend:

```text
cd backend
python -m pytest
python -m ruff check .
```

Frontend:

```text
cd frontend
npm ci
npm run lint
npm run build
```

GitHub Actions runs these checks and validates Compose configuration on pushes
to `main` and pull requests.

## Production Compose deployment

`docker-compose.production.yml` is a production-oriented self-hosting baseline.
It keeps PostgreSQL, Redis, the API, the worker, and the Next.js server on a
private Compose network; only the frontend port is published. It does not
create a public deployment or replace a managed ingress, TLS certificate,
backup policy, secret manager, or observability platform.

Create a deployment environment file outside version control with these values:

- `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`
- `DOC_QUERY_DATABASE_URL` using the same database credentials and the
  `postgresql+psycopg` driver
- `DOC_QUERY_REDIS_URL` pointing at the Redis service or a managed Redis URL
- `DOC_QUERY_CORS_ORIGINS` as a comma-separated list of trusted browser origins
- Optional `PORT` for the published frontend port

For local development, copy the backend template from [`backend/.env.example`](./backend/.env.example)
and keep a production-safe `.env` file out of version control.

Start it with the production Compose file and verify the frontend root and
backend `/health` endpoint through the configured ingress. Never commit the
environment file or place credentials in image layers. Uploaded files and
PostgreSQL/Redis data use named volumes; configure backups and retention before
using real financial documents. For internet-facing use, put the frontend
behind TLS and add authentication, rate limiting, malware scanning, and secret
rotation.

## Deliberate limitations

- The deterministic provider supports documented line-oriented fixtures; it is
  not an arbitrary-document OCR accuracy claim.
- Source-text highlighting is used when reliable PDF coordinate alignment is
  unavailable.
- Authentication, multi-tenancy, approvals, payments, ERP integration,
  handwriting, non-English invoices, fraud detection, and production virus
  scanning are not implemented.

## Decision record

See [`decisions.md`](./decisions.md) for product framing, alternatives,
trade-offs, reliability decisions, and deliberately excluded scope.
