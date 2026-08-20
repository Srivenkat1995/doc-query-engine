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
`.env` file is supported and should not be committed.
