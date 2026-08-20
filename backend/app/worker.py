from celery import Celery

from app.config import get_settings
from app.observability import log_worker_task
from app.task_context import TaskContext

settings = get_settings()

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