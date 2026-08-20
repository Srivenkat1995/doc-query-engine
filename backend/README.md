# Backend

FastAPI service for the document parsing and query engine.

## Local setup

From the `backend/` directory, create a virtual environment and install the
package with the test and development extras:

```text
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test,dev]'
```

## Run the API

```text
uvicorn app.main:app --reload
```

The health endpoint is available at `http://localhost:8000/health`.

Every request receives an `X-Trace-Id` response header. Clients may send a
canonical UUID in the same header to preserve correlation across services;
missing or invalid values are replaced with a generated UUID4.

The API emits JSON request events containing the event name, method, path, HTTP
status, duration, and trace ID. Request bodies, query values, headers, file
contents, credentials, and tokens are not included.

Background task payloads carry `trace_id`, `invoice_id`, and `job_id`. The worker
validates these fields and includes them in its JSON task event. Upload dispatch
is introduced separately from this propagation contract.

The local storage adapter writes documents below `DOC_QUERY_STORAGE_ROOT`,
which defaults to `./uploads`. Writes are atomic, reads return bytes, deletes
are idempotent, and absolute or path-traversal keys are rejected. The upload API
will adopt this adapter in a later commit.

Upload validation accepts `application/pdf`, `image/jpeg`, and `image/png`.
Empty files and files larger than 5MB are rejected before storage or database
work begins. Validation errors expose stable codes for the API layer.

`POST /invoices/upload` accepts a multipart field named `file`, stores the
validated bytes through the storage adapter, and creates an invoice with
`uploaded` status. It returns the invoice metadata after both writes succeed.
Processing dispatch is intentionally not part of this endpoint yet.

`POST /invoices/{invoice_id}/jobs` creates a queued processing-job identity from
an `idempotency_key`. Repeating the same key for the same invoice returns the
same job with HTTP 200; a new key returns HTTP 201. This commit creates the
durable identity only—Celery dispatch is introduced separately.

`POST /invoices/{invoice_id}/jobs/{job_id}/dispatch` sends the job to the
`documents` Celery queue and returns HTTP 202 with the trace ID. Its payload
contains the invoice ID, job ID, trace ID, and storage key. The worker accepts
and logs the task. Transient failures retry at most three times with exponential
backoff; permanent failures and exhausted retries mark the job `failed` with a
reason. Extraction is introduced separately.

`GET /invoices/{invoice_id}/jobs/{job_id}/status` returns the invoice status,
job status, attempt count, failure reason, and timestamps. It verifies that the
job belongs to the requested invoice.

The extraction boundary is defined by `ExtractionProvider`. Providers return
structured fields, line items, raw source text, confidence values, and citations.
The worker does not depend on a specific OCR or model provider; the deterministic
implementation is introduced separately.

The deterministic provider now persists fields, line items, citations, and raw
text in one extraction transaction with invoice `ready` and job `completed`
state. Retrieve the result with `GET /invoices/{invoice_id}/extraction`.

Fields below the 0.75 final-confidence threshold are marked `needs_review` with
the stable reason `low_confidence`; other valid fields continue through the
pipeline. Arithmetic mismatch flags are introduced separately.

Arithmetic reconciliation now creates a `total_mismatch` issue containing the
printed total, calculated line-item total, and signed difference. Neither total
is replaced. Issues are returned from the extraction endpoint for review.

Extraction failures receive exactly one optional repair attempt. If repair is
unavailable or fails, raw source text is preserved, a `schema_repair_failed`
issue is stored, and the invoice moves to `needs_review`.

If a worker cannot find the stored source file, it records a terminal
`Stored invoice file is missing` failure instead of retrying an unrecoverable
condition indefinitely.

Citation records are stored separately with invoice ID, entity type, entity ID,
page, source text, and optional bounding-box coordinates. This keeps provenance
queryable independently from the extracted value tables.

Raw extraction text is split into stable line-aware search chunks. Each chunk
has an invoice-local position and SHA-256 content hash; reprocessing replaces
the set rather than duplicating it. Vector generation is introduced separately.

Search chunks now receive normalized 384-dimensional embeddings from the local
`all-MiniLM-L6-v2` model. The Docker image downloads the model during build into
the Hugging Face cache, so worker tasks do not download it on first use.

`GET /invoices` returns the invoice batch summary. Use `needs_review=true` to
prioritize invoices with field flags or review issues, and `failed=true` to show
processing failures.

Structured filters include `vendor`, `total_min`, `total_max`,
`due_date_before`, `due_date_after`, and `status`. These filters execute in the
database before any future semantic ranking.

`GET /invoices/search/semantic?q=consulting&limit=10` embeds the query with the
local model and ranks persisted chunks by pgvector cosine similarity. Results
include invoice metadata, chunk content, and stable content hashes.

`GET /invoices/search/hybrid` accepts the same query plus structured filters.
The database narrows candidates using vendor, totals, dates, status, and review
issues before vector similarity ranking. Results include citation record IDs.

`DeterministicExtractionProvider` parses the line-oriented fixtures in
`tests/fixtures/` without external credentials. It supports clean and deliberately
messy examples, including low-confidence fields and unreconciled printed totals.
It is a demo/test provider, not a claim of OCR accuracy for arbitrary PDFs.

The connectivity-ready worker can be started with:

```text
celery -A app.worker.celery_app worker --loglevel=INFO --queues=documents
```

Apply database migrations with:

```text
alembic upgrade head
```

## Verify the backend

```text
pytest
ruff check .
```

## Configuration

Settings are loaded from environment variables with the `DOC_QUERY_` prefix.
For example, `DOC_QUERY_ENVIRONMENT=test` sets the application environment.
`DOC_QUERY_REDIS_URL` configures the Celery broker and result backend. A local
`.env` file is supported and should not be committed; use
[`backend/.env.example`](./.env.example) as a template for required values.
`DOC_QUERY_DATABASE_URL` configures SQLAlchemy, `DOC_QUERY_STORAGE_ROOT`
configures local file storage, and `DOC_QUERY_CORS_ORIGINS` accepts a
comma-separated list of allowed browser origins such as
`https://review.example.com,https://admin.example.com`.
