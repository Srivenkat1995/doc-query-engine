import json

import pytest

from app.task_context import ProcessingTaskPayload, TaskContext
from app.worker import healthcheck, process_invoice


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


def test_processing_task_accepts_storage_key() -> None:
    payload = ProcessingTaskPayload(
        context=TaskContext(
            trace_id="trace-123",
            invoice_id="invoice-123",
            job_id="job-123",
        ),
        storage_key="invoices/invoice-123",
    )

    result = process_invoice.run(payload.to_payload())

    assert result == {"status": "accepted", **payload.to_payload()}
