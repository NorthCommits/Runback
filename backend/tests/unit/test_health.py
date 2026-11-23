import asyncio

import pytest
from fastapi.testclient import TestClient

from app.infrastructure import database
from app.infrastructure.database import DatabaseProbe
from app.main import create_app


class ReadyProbe:
    def __init__(self, ready: bool) -> None:
        self.ready = ready

    async def is_ready(self) -> bool:
        return self.ready


class Connection:
    async def execute(self, _: str) -> None:
        return None

    async def close(self) -> None:
        return None


def test_live_health_reports_ok() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_ready_when_dependencies_are_available() -> None:
    app = create_app()
    app.state.database_probe = ReadyProbe(ready=True)

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_returns_service_unavailable_when_dependencies_are_unavailable() -> None:
    app = create_app()
    app.state.database_probe = ReadyProbe(ready=False)

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "dependencies_unavailable"}


def test_database_probe_requires_tls_for_supabase_connections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_arguments: dict[str, object] = {}

    async def connect(*_: object, **kwargs: object) -> Connection:
        captured_arguments.update(kwargs)
        return Connection()

    monkeypatch.setattr(database.asyncpg, "connect", connect)
    probe = DatabaseProbe(
        database_url="postgresql://runback:password@example.com/runback",
        timeout_seconds=3.0,
        ssl_enabled=True,
    )

    assert asyncio.run(probe.is_ready()) is True
    assert captured_arguments["ssl"] == "require"
