from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.invoices import router as invoices_router
from app.config import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.include_router(health_router)
    app.include_router(invoices_router)
    return app


app = create_app()
