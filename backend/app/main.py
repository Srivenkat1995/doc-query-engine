from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.invoices import router as invoices_router
from app.config import get_settings
from app.tracing import TRACE_ID_HEADER, normalize_trace_id


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    @app.middleware("http")
    async def add_trace_id(request, call_next):
        trace_id = normalize_trace_id(request.headers.get(TRACE_ID_HEADER))
        request.state.trace_id = trace_id
        response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response

    app.include_router(health_router)
    app.include_router(invoices_router)
    return app


app = create_app()
