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
