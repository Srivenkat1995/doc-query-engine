# decisions.md

This is my running log of the calls I made while building this — not a spec I wrote up front and then implemented. I've tried to keep it honest: what I chose, what I almost chose instead, and what I just didn't have time for.

**Implementation status:** the repository is at the planning baseline. The application, tests, and deployment are not complete yet. Claims below about runtime behavior are acceptance criteria until code and tests verify them.

## Who I'm building this for

The target user is someone in AP or finance operations with a folder of vendor invoices before a payment run. Some invoices are clean digital PDFs; others are slightly crooked scans. Some contain printed totals that do not add up to the line items.

Right now that person opens every invoice and checks the vendor, amount, due date, and unusual terms manually. The product lets them upload a batch, ask questions such as "show me anything from Acme over $1,000" or "which of these have stricter-than-net-30 terms," and get answers linked to the exact source location on the page.

The citation link is central because the product exists to establish trust. A reviewer must not approve a payment from a number they cannot verify in two clicks. Each decision below answers whether it improves verification or merely adds presentation.

Invoices are the chosen document type for two reasons. First, the problem statement's example query — `total > $1000 AND vendor = 'Acme'` — assumes structured financial data. Second, an incorrect invoice number has a direct, checkable cost: an incorrect payment. That makes the product’s value testable: can a reviewer catch a bad field before approval?

The acceptance bar for messy-input handling is strict: across a batch of real invoices, including deliberately degraded scans and hand-edited totals, no field may return silently wrong. Every field must be correct or visibly flagged for review. Any document that violates this rule blocks completion.

The confidence threshold is an open calibration decision. The initial threshold is a conservative starting point and requires testing against representative invoices before it is treated as final.

**What I deliberately didn't build:** logins/multi-tenant permissions, approval workflows, non-English invoices, handwriting recognition, any ERP integration, or actually executing payments. All real things a shipped product would need eventually. None of them are the hard part of the actual problem I was given, which is turning messy documents into data someone can safely act on — so I left them out on purpose rather than running out of time and quietly not mentioning it.

**How I'll know it's actually working:** a reviewer looks at a flagged field, glances at the highlighted region on the page, and either confirms it or fixes it in a few seconds. Faster than opening the original PDF and finding the number by eye. If checking a flagged field ever takes longer than just reading the original invoice would have, the tool isn't actually saving anyone anything, no matter how sophisticated the extraction underneath it is.

One rule shapes the decisions below: a false positive costs the reviewer a few seconds of unnecessary checking; a false negative can send a payment with an incorrect amount. These mistakes are not equivalent, so the system over-flags rather than under-flags.

The primary failure scenario is a batch in which three or four of twelve invoices contain flags—a skewed scan or a mismatched total. That is the tool doing its job: it surfaces issues in seconds instead of leaving them to be found accidentally during reconciliation.

That defines the primary output: a short exception list, not a generic collection of search results. Alex needs to identify the two or three invoices requiring attention before approving the rest. Search supports investigation of an exception; it is not the main workflow.

## Scoping the requirements

The system needs to take invoices — PDF, JPEG, PNG, up to 5MB, single or multi-page — and pull out vendor, total, due date, line items, and payment terms into something structured, with a bounding box on every field so it can be traced back visually. On top of that, it needs to answer both exact filters (`vendor = 'Acme' AND total > 1000`) and plain-English questions in the same search.

The critical requirement is safe handling of bad input. A skewed scan, a total that does not match the line items, or a low-confidence field must appear as a visible, actionable issue—not as a silent wrong number.

For this project, "messy" means three things: skewed or low-quality scans, arithmetic that does not reconcile between totals and line items, and model output that fails schema validation. Handwriting recognition, non-Latin invoices, and adversarial or fraudulent documents are excluded; each requires a separate OCR, internationalization, or fraud-detection effort.

### A note on scale

The scale estimate below is a ceiling check, not a sizing target. The actual user is a small operations team processing invoices in bursts around payment runs, not a service receiving four-digit QPS continuously. The architecture keeps the inexpensive shape that scales—background processing and one datastore—while excluding infrastructure that only pays off at hyperscale.

Rough math, for the record:
- Average read load: 5,000,000 / 86,400 ≈ 58 QPS, designed toward a 1,000 QPS peak
- Ingestion: ~100,000 uploads/day, ~1.16/sec average, ~50/sec at peak
- Storage: ~1MB/doc raw, ~40KB/doc for structured data + embeddings
- Bandwidth: ~250MB/s peak in, ~20MB/s peak out

None of this drove an actual build decision — it's a ceiling check, not a target.

## Failure modes and decisions

### Uploads blowing up the API server

Streaming a 5MB file through the API ties up memory, worker threads, and connections during upload bursts. Presigned URLs avoid that cost: the client receives a short-lived token, uploads directly to object storage, and notifies the backend when the upload completes. The API never handles the file bytes.

What I skipped here: virus scanning on upload, resumable uploads, progress bars over websockets. None of it is needed to prove the pattern works under a 5MB cap.

### OCR and extraction being slow, and rate limits

OCR and LLM extraction is a 3–10 second operation and does not belong in a request handler. In-process background tasks disappear on process restart and provide weak retry behavior. Polling a jobs table adds contention. Celery with Redis provides task isolation and bounded retry with backoff for rate limits such as `429` responses.

Skipped: autoscaling the worker pool, dead-letter queues, priority queues. One queue and one pool is enough to prove the isolation works.

### Search getting slow once there's real data

Hybrid search—an exact filter plus a semantic match—can degrade through unindexed scans or repeated embedding calls. A separate vector database introduces consistency failures when one write succeeds and the other fails. PostgreSQL with `pgvector` keeps relational data and vectors together; JSON indexes narrow the candidate set before vector ranking.

I did originally think about adding an in-memory cache for repeated query embeddings, and honestly I almost kept it just because it showed up in my first draft. But at the actual scale this thing runs at, it's solving a problem I don't have — it just adds a cache-vs-database drift risk for basically no payoff right now. Cut it. If this ever saw real traffic, it's the first thing I'd add back.

### The one I spent the most time on: invoices that aren't clean

This is the core problem. Real invoices are untidy: scans arrive skewed, totals can appear in unexpected locations, and model output can fail schema validation. A silently incorrect number can cause an incorrect payment, so messy-input handling is a primary feature.

**When a field comes back low-confidence:** confidence is tracked per field, not per document. Values below the threshold are flagged; valid fields continue through the pipeline. The review screen uses the same citation interaction for normal verification and correction.

**When the extraction does not validate against the schema:** the system makes one repair attempt by sending the validation error and original text back to the model. If repair fails, it stores the raw extracted text and creates a review flag. It does not loop or coerce invalid data into the schema.

**When the total does not match the line items:** the system does not recompute or replace the printed total. Fees and discounts may not appear as separate line items, so either value remains possible. The system flags the mismatch and displays both numbers for review.

Handwriting recognition and non-English invoices remain excluded. Each requires a separate OCR or internationalization effort. This project handles confidence and arithmetic consistency.

## Implementation stack

This is the chosen stack, not a claim that every component is already implemented.

- FastAPI for the API
- S3-compatible object storage with presigned PUT URLs
- Celery + Redis for the task queue
- A vision-capable LLM call for OCR/layout, instead of a Tesseract-plus-layout-model pipeline — costs a bit more per page, but handles skewed scans and weird table layouts a lot better, which mattered given everything above
- LLM extraction constrained to a Pydantic invoice schema, with the one-repair-pass fallback
- A standard embedding model, stored and queried through `pgvector` in the same Postgres instance as everything else
- Postgres (JSONB + `pgvector`) as the only datastore, no separate cache layer

Docker Compose makes the frontend, API, PostgreSQL/`pgvector`, Redis, and worker
reproducible locally. GitHub Actions runs formatting, linting, and tests on pull
requests. The local extraction fixture and local embedding model keep the core
workflow runnable without paid external API credentials.

## Failure-focused tests

The test suite targets the failures most likely to damage trust:

- Feed a broken extraction through the pipeline and check it does exactly one repair attempt, then falls back to a review flag instead of looping or quietly coercing bad data into shape
- Seed an invoice where the total doesn't match the line items and check it gets flagged, with neither number silently changed
- Run a combined structured-filter-plus-semantic query against seeded data and check it returns the right subset — this is the kind of thing that's easy to quietly break with a bad SQL join
- Try to upload an oversized or wrong-type file and confirm it's rejected at the token step, not discovered later inside a worker

Benchmarking OCR accuracy against a labeled dataset is excluded. It requires a separate data-collection and measurement project.

## Reliability decisions

These are implementation requirements.

### Processing is idempotent

Each processing task has a stable job identity tied to the invoice and processing
attempt. Replaying a task does not create duplicate invoice records, fields,
citations, searchable chunks, or embeddings. Unique constraints and upserts
protect writes, and each stage checks whether its work is already committed
before repeating it.

### Structured and vector writes must be atomic

The extracted JSONB data, citations, searchable chunks, embeddings, and final
`ready` status are committed in one PostgreSQL transaction. If extraction,
embedding generation, or vector insertion fails, the transaction rolls back; the
invoice cannot appear ready with incomplete search data. Retry handling moves the
invoice to a retryable processing state or a terminal failed state according to
a bounded policy.

### Every job must be diagnosable

Every upload receives a `trace_id`. The frontend passes it to the API, the API
passes it into the background task, and the worker includes it in structured JSON
logs along with the invoice ID, job ID, stage, duration, and error details. This
creates one path for debugging a document from upload through extraction and
search indexing without logging document contents or secrets.

### The embedding model must be ready before the first job

The Docker image downloads and caches `all-MiniLM-L6-v2` during the image build,
not during the first Celery task. Worker startup loads the cached model and fails
fast if it is unavailable. This keeps a predictable build step out of production
task execution.

### Citation accuracy is time-boxed, not hand-waved

Absolute PDF bounding-box alignment is valuable only if it is reliable. Test it
at multiple page sizes and viewport scales. If the mapping is inaccurate, use
static page rendering or source-text highlighting instead of a misleading
overlay. Record the trade-off here with evidence from the implementation.

## Definition of done

The central workflow is complete only when a reviewer can:

1. Start the project from the documented setup.
2. Upload a clean invoice and see structured results.
3. Upload a deliberately degraded or mismatched invoice.
4. See the relevant field or arithmetic issue flagged without silent correction.
5. Trace the job using its correlation ID.
6. Replay processing without duplicate database or vector records.
7. Click a citation and reach a reliable source location.
8. Search using structured filters and semantic meaning.
9. Run the failure-focused test suite.

If any of these steps is only described but not demonstrated, it remains an open
implementation item rather than a completed feature.

## How it all fits together

```text
                               ┌──────────────────────────────────────────────────────────┐
                               │                       CLIENT TIER                        │
                               │  (Upload UI | Citation Preview | Search Interface)       │
                               └──────────────┬────────────────────────────▲──────────────┘
                                              │ 1. Request Upload Token    │ 6. Poll / Webhook
                                              │    & Submit Job Trigger    │    Status & View
                                              ▼                            │
 ┌─────────────────────────────────────────────────────────────────────────┴──────────────┐
 │                                 API & GATEWAY TIER                                     │
 │          (Presigned URL Issuer | Auth & Rate Limiter | Search Query Router)            │
 └──────────────┬─────────────────────────────┬───────────────────────────────────────────┘
                │ 2. Direct Binary Upload     │ 3. Enqueue Ingestion Job ({ doc_id, storage_key })
                ▼                             ▼
 ┌──────────────────────────────┐   ┌─────────────────────────────────────────────────────┐
 │        OBJECT STORAGE        │   │               DISTRIBUTED TASK QUEUE                │
 │  (Raw PDFs / Images: S3/R2)  │   │             (Job Distribution Broker)                 │
 └──────────────┬───────────────┘   └─────────────────────────┬───────────────────────────┘
                │                                             │
                │ 4. Read Raw Bytes                           │ 5. Pull Next Job
                └──────────────────────┬──────────────────────┘
                                       ▼
                     ┌───────────────────────────────────┐
                     │     ASYNC PARSING WORKER POOL     │
                     │ ┌───────────────────────────────┐ │
                     │ │  Layout & OCR Engine          │ │
                     │ ├───────────────────────────────┤ │
                     │ │  Pydantic Extraction Engine   │ │
                     │ ├───────────────────────────────┤ │
                     │ │  Chunking & Embedding Engine  │ │
                     │ └───────────────────────────────┘ │
                     └─────────────────┬─────────────────┘
                                       │
                                       │ 7. Write Extracted JSON, BBoxes & Vectors
                                       ▼
                     ┌───────────────────────────────────┐
                     │         UNIFIED DATASTORE         │
                     │  (Relational + JSONB + Vectors)   │
                     └───────────────────────────────────┘
```


**Upload:** the API validates the file metadata and issues a short-lived presigned URL. The browser uploads the raw file directly to object storage, then confirms completion with the API. The API creates the processing job and returns `202` with the invoice and job IDs without waiting for extraction.

**Processing:** the worker retrieves the stored file, runs layout/OCR, performs schema-constrained extraction, applies the bounded repair and arithmetic checks, creates searchable chunks and embeddings, and commits fields, citations, chunks, vectors, and status in one transaction. Task replay is idempotent and cannot create duplicate records.

**Search:** the API accepts structured filters, semantic text, or both. It applies indexed relational filters first, ranks the remaining candidates with `pgvector` similarity, and returns snippets with invoice and citation references. Query embeddings are generated directly without a cache layer.

**Citation:** each extracted field includes a page, source text, and bounding-box reference. The frontend uses that reference to focus the document preview on the source region. If coordinate mapping is unreliable, the UI uses static rendering or source-text highlighting rather than displaying an inaccurate overlay.