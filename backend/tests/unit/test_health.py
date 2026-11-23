import asyncio

import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings
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


def test_ingestion_validation_returns_a_structured_error_with_correlation_id() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ingest/traces",
            headers={"X-Correlation-ID": "test-correlation"},
            json={"schema_version": "v1"},
        )

    assert response.status_code == 422
    assert response.headers["X-Correlation-ID"] == "test-correlation"
    assert response.json()["code"] == "validation_error"
    assert response.json()["correlation_id"] == "test-correlation"


def test_ingestion_validation_encodes_cross_field_errors() -> None:
    app = create_app()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ingest/traces",
            json={
                "schema_version": "v1",
                "environment_id": "00000000-0000-0000-0000-000000000001",
                "idempotency_key": "cross-field-error",
                "traces": [
                    {
                        "trace_id": "00000000-0000-0000-0000-000000000002",
                        "source_framework": "test",
                        "started_at": "2026-11-23T12:00:01Z",
                        "ended_at": "2026-11-23T12:00:00Z",
                        "status": "completed",
                        "spans": [
                            {
                                "span_id": "00000000-0000-0000-0000-000000000003",
                                "name": "root",
                                "kind": "agent",
                                "start_time": "2026-11-23T12:00:00Z",
                                "status": "completed",
                            }
                        ],
                    }
                ],
            },
        )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert response.json()["errors"][0]["type"] == "value_error"


def test_ingestion_rejects_requests_larger_than_the_configured_limit() -> None:
    app = create_app(
        Settings(
            database_url="postgresql://runback:runback@localhost:5432/runback",
            ingest_max_body_bytes=10,
        )
    )

    with TestClient(app) as client:
        response = client.post("/api/v1/ingest/traces", json={"schema_version": "v1"})

    assert response.status_code == 413
    assert response.json()["code"] == "request_too_large"
