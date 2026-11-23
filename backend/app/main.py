from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import RequestResponseEndpoint

from app.api.errors import install_error_handlers
from app.api.v1.health import router as health_router
from app.api.v1.ingestion import router as ingestion_router
from app.core.settings import Settings
from app.infrastructure.database import (
    DatabaseProbe,
    create_engine,
    create_session_factory,
)
from app.infrastructure.payloads import LocalPayloadStore


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    engine = create_engine(
        application.state.settings.database_url,
        application.state.settings.database_ssl,
    )
    application.state.session_factory = create_session_factory(engine)
    try:
        yield
    finally:
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_environment()
    application = FastAPI(title="Runback API", version="0.1.0", lifespan=lifespan)
    application.state.settings = resolved_settings
    application.state.database_probe = DatabaseProbe(
        database_url=resolved_settings.database_url,
        timeout_seconds=resolved_settings.database_connect_timeout_seconds,
        ssl_enabled=resolved_settings.database_ssl,
    )
    application.state.payload_store = LocalPayloadStore(resolved_settings.payload_storage_path)
    @application.middleware("http")
    async def add_correlation_id(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request.state.correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
        content_length = request.headers.get("content-length")
        request_too_large = False
        if content_length is not None:
            try:
                request_too_large = int(content_length) > resolved_settings.ingest_max_body_bytes
            except ValueError:
                request_too_large = True
        if request.url.path == "/api/v1/ingest/traces" and request_too_large:
            response: Response = JSONResponse(
                status_code=413,
                content={
                    "code": "request_too_large",
                    "detail": "The request exceeds the configured limit",
                    "correlation_id": request.state.correlation_id,
                },
            )
        else:
            response = await call_next(request)
        response.headers["X-Correlation-ID"] = request.state.correlation_id
        return response

    install_error_handlers(application)
    application.include_router(health_router, prefix="/api/v1")
    application.include_router(ingestion_router, prefix="/api/v1")
    return application


app = create_app()
