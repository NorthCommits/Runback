from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.core.settings import Settings
from app.infrastructure.database import DatabaseProbe


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings.from_environment()
    application = FastAPI(title="Runback API", version="0.1.0", lifespan=lifespan)
    application.state.settings = resolved_settings
    application.state.database_probe = DatabaseProbe(
        database_url=resolved_settings.database_url,
        timeout_seconds=resolved_settings.database_connect_timeout_seconds,
        ssl_enabled=resolved_settings.database_ssl,
    )
    application.include_router(health_router, prefix="/api/v1")
    return application


app = create_app()
