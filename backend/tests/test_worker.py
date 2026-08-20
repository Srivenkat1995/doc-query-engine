import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.models import JobStatus, ProcessingJob
from app.task_context import ProcessingTaskPayload, TaskContext
from app.worker import (
    MAX_TASK_RETRIES,
    PermanentProcessingError,
    TransientProcessingError,
    healthcheck,
    mark_job_failed,
    process_invoice,
)


def test_task_context_is_json_serializable() -> None:
    context = TaskContext(
        trace_id="trace-123",
        invoice_id="invoice-123",
        job_id="job-123",
    )

    payload = context.to_payload()

    assert json.loads(json.dumps(payload)) == {
        "trace_id": "trace-123",
        "invoice_id": "invoice-123",
        "job_id": "job-123",
    }


def test_worker_receives_and_logs_task_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    context = TaskContext(
        trace_id="trace-123",
        invoice_id="invoice-123",
        job_id="job-123",
    )
    caplog.set_level("INFO", logger="doc_query_engine.worker")

    result = healthcheck.run(context.to_payload())

    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "doc_query_engine.worker"
    ]
    assert result == {"status": "ok", **context.to_payload()}
    assert events[-1] == {
        "event": "celery_task_received",
        "invoice_id": "invoice-123",
        "job_id": "job-123",
        "task_name": "app.worker.healthcheck",
        "trace_id": "trace-123",
    }


def test_task_context_rejects_missing_correlation_fields() -> None:
    with pytest.raises(ValueError, match="Task context requires"):
        TaskContext.from_payload({"trace_id": "trace-123"})


def test_processing_task_accepts_storage_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = ProcessingTaskPayload(
        context=TaskContext(
            trace_id="trace-123",
            invoice_id="invoice-123",
            job_id="job-123",
        ),
        storage_key="invoices/invoice-123",
    )

    monkeypatch.setattr("app.worker.mark_job_processing", lambda _: None)
    monkeypatch.setattr(
        "app.worker.execute_processing",
        lambda task_payload: {"status": "completed", **task_payload.to_payload()},
    )
    result = process_invoice.run(payload.to_payload())

    assert result == {"status": "completed", **payload.to_payload()}


def test_processing_task_has_bounded_retry_policy() -> None:
    assert process_invoice.max_retries == MAX_TASK_RETRIES
    assert process_invoice.acks_late is True
    assert process_invoice.reject_on_worker_lost is True


def test_permanent_failure_marks_job_failed() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        job = ProcessingJob(
            invoice_id="invoice-123",
            idempotency_key="job-123",
        )
        session.add(job)
        session.commit()
        mark_job_failed(job.id, "invalid document", db=session)
        session.refresh(job)
        assert job.status == JobStatus.FAILED.value
        assert job.failure_reason == "invalid document"
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_transient_failure_uses_retry_path(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = ProcessingTaskPayload(
        context=TaskContext(
            trace_id="trace-123",
            invoice_id="invoice-123",
            job_id="job-123",
        ),
        storage_key="invoices/invoice-123",
    )
    monkeypatch.setattr("app.worker.mark_job_processing", lambda _: None)
    monkeypatch.setattr("app.worker.mark_job_failed", lambda *_args: None)
    monkeypatch.setattr(
        "app.worker.execute_processing",
        lambda _payload: (_ for _ in ()).throw(
            TransientProcessingError("temporary failure")
        ),
    )

    result = process_invoice.apply(args=[payload.to_payload()], throw=False)

    assert result.failed()
    assert isinstance(result.result, TransientProcessingError)


def test_permanent_failure_does_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = ProcessingTaskPayload(
        context=TaskContext(
            trace_id="trace-123",
            invoice_id="invoice-123",
            job_id="job-123",
        ),
        storage_key="invoices/invoice-123",
    )
    failures: list[str] = []
    monkeypatch.setattr("app.worker.mark_job_processing", lambda _: None)
    monkeypatch.setattr(
        "app.worker.mark_job_failed",
        lambda _job_id, reason: failures.append(reason),
    )
    monkeypatch.setattr(
        "app.worker.execute_processing",
        lambda _payload: (_ for _ in ()).throw(
            PermanentProcessingError("permanent failure")
        ),
    )

    result = process_invoice.apply(args=[payload.to_payload()], throw=False)

    assert result.failed()
    assert failures == ["permanent failure"]
