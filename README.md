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

## Setup

Implementation is in progress. The completed project will provide a Docker
Compose development stack, test instructions, and deployment instructions here.

## Decisions

See [`decisions.md`](./decisions.md) for product framing, architectural
trade-offs, reliability decisions, and deliberately excluded scope.
