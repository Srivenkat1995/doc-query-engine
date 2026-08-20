from __future__ import annotations

from typing import Optional

from celery import Celery
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal
from app.deterministic_extraction import DeterministicExtractionProvider
from app.extraction_persistence import persist_extraction
from app.models import JobStatus, ProcessingJob
from app.observability import log_worker_task
from app.repair import extract_with_one_repair
from app.storage import get_storage
from app.task_context import ProcessingTaskPayload, TaskContext

settings = get_settings()

MAX_TASK_RETRIES = 3
RETRY_BACKOFF_BASE_SECONDS = 2


class TransientProcessingError(RuntimeError):
    """A processing failure that is safe to retry."""


class PermanentProcessingError(RuntimeError):
    """A processing failure that must not be retried."""

celery_app = Celery(
    "doc_query_engine",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_default_queue="documents",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="app.worker.healthcheck")
def healthcheck(payload: dict[str, str]) -> dict[str, str]:
    """Validate task correlation data while checking worker connectivity."""

    context = TaskContext.from_payload(payload)
    log_worker_task(
        task_name="app.worker.healthcheck",
        trace_id=context.trace_id,
        invoice_id=context.invoice_id,
        job_id=context.job_id,
    )
    return {"status": "ok", **context.to_payload()}


def mark_job_processing(job_id: str, db: Optional[Session] = None) -> None:
    """Record a worker attempt before processing begins."""

    owns_session = db is None
    session = db or SessionLocal()
    try:
        job = session.get(ProcessingJob, job_id)
        if job is not None:
            job.status = JobStatus.PROCESSING.value
            job.attempt_count += 1
            session.commit()
    finally:
        if owns_session:
            session.close()


def mark_job_failed(job_id: str, reason: str, db: Optional[Session] = None) -> None:
    """Persist a terminal failure after retries are exhausted."""

    owns_session = db is None
    session = db or SessionLocal()
    try:
        job = session.get(ProcessingJob, job_id)
        if job is not None:
            job.status = JobStatus.FAILED.value
            job.failure_reason = reason
            session.commit()
    finally:
        if owns_session:
            session.close()


def execute_processing(payload: ProcessingTaskPayload) -> dict[str, str]:
    """Extract the stored document and commit its result with job completion."""

    db = SessionLocal()
    try:
        try:
            content = get_storage().get(payload.storage_key)
        except FileNotFoundError as error:
            raise PermanentProcessingError(
                "Stored invoice file is missing"
            ) from error
        extraction = extract_with_one_repair(
            DeterministicExtractionProvider(),
            content,
            "",
        )
        persist_extraction(
            db,
            payload.context.invoice_id,
            payload.context.job_id,
            extraction,
        )
        db.commit()
        return {"status": "completed", **payload.to_payload()}
    finally:
        db.close()


@celery_app.task(
    bind=True,
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=MAX_TASK_RETRIES,
    name="app.worker.process_invoice",
)
def process_invoice(self, payload: dict[str, str]) -> dict[str, str]:
    """Accept an invoice task; extraction is added in a later commit."""

    task_payload = ProcessingTaskPayload.from_payload(payload)
    mark_job_processing(task_payload.context.job_id)
    log_worker_task(
        task_name="app.worker.process_invoice",
        trace_id=task_payload.context.trace_id,
        invoice_id=task_payload.context.invoice_id,
        job_id=task_payload.context.job_id,
    )
    try:
        return execute_processing(task_payload)
    except PermanentProcessingError as error:
        mark_job_failed(task_payload.context.job_id, str(error))
        raise
    except TransientProcessingError as error:
        if self.request.retries >= MAX_TASK_RETRIES:
            mark_job_failed(task_payload.context.job_id, str(error))
            raise
        countdown = RETRY_BACKOFF_BASE_SECONDS ** (self.request.retries + 1)
        raise self.retry(exc=error, countdown=countdown)