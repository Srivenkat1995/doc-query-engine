from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.config import Settings, get_settings
from app.tracing import get_trace_id

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    trace_id: str


@router.get("/health", response_model=HealthResponse)
def health_check(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        trace_id=get_trace_id(request),
    )
