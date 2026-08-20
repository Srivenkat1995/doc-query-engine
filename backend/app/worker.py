from celery import Celery

from app.config import get_settings

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
def healthcheck() -> str:
    """Provide a no-op task for validating worker connectivity."""

    return "ok"