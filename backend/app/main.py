from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.invoices import router as invoices_router
from app.config import get_settings
from app.observability import log_request, request_timer
from app.tracing import TRACE_ID_HEADER, normalize_trace_id


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Accept", "X-Trace-Id"],
    )

    @app.middleware("http")
    async def add_trace_id(request, call_next):
        trace_id = normalize_trace_id(request.headers.get(TRACE_ID_HEADER))
        request.state.trace_id = trace_id
        started_at = request_timer()
        try:
            response = await call_next(request)
        except Exception as error:
            log_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=(request_timer() - started_at) * 1000,
                trace_id=trace_id,
                event_name="http_request_failed",
                error_type=type(error).__name__,
            )
            raise
        response.headers[TRACE_ID_HEADER] = trace_id
        log_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=(request_timer() - started_at) * 1000,
            trace_id=trace_id,
        )
        return response

    app.include_router(health_router)
    app.include_router(invoices_router)
    return app


app = create_app()
