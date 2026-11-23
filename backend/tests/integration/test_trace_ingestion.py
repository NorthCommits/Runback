import asyncio
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.settings import Settings
from app.infrastructure.database import create_engine, create_session_factory
from app.infrastructure.models import (
    Environment,
    IngestToken,
    Payload,
    Project,
    Span,
    Trace,
    Workspace,
)
from app.infrastructure.payloads import LocalPayloadStore
from app.main import create_app
from app.services.tokens import create_token_secret, hash_token

DATABASE_URL = os.getenv("RUNBACK_INTEGRATION_DATABASE_URL")
FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "sample_trace.json"


@pytest.mark.skipif(
    DATABASE_URL is None,
    reason="RUNBACK_INTEGRATION_DATABASE_URL is not configured",
)
def test_trace_ingestion_persists_redacted_idempotent_trace() -> None:
    asyncio.run(run_trace_ingestion_scenario())


async def run_trace_ingestion_scenario() -> None:
    assert DATABASE_URL is not None
    engine = create_engine(DATABASE_URL, ssl_enabled=False)
    session_factory = create_session_factory(engine)
    token = create_token_secret()
    workspace_id = uuid4()
    project_id = uuid4()
    environment_id = uuid4()
    trace_id = uuid4()
    parent_span_id = uuid4()
    child_span_id = uuid4()
    payload_storage_path = Path("/tmp") / f"runback-integration-{uuid4()}"
    payload_store = LocalPayloadStore(payload_storage_path)
    try:
        async with session_factory() as session:
            async with session.begin():
                session.add(Workspace(id=workspace_id, name=f"integration-{workspace_id}"))
                await session.flush()
                session.add(
                    Project(
                        id=project_id,
                        workspace_id=workspace_id,
                        name="runback-api",
                    )
                )
                await session.flush()
                session.add(Environment(id=environment_id, project_id=project_id, name="test"))
                session.add(
                    IngestToken(
                        project_id=project_id,
                        label="integration",
                        token_hash=hash_token(token),
                        scopes={"ingest": True},
                    )
                )

        payload = json.loads(FIXTURE_PATH.read_text())
        payload["environment_id"] = str(environment_id)
        payload["idempotency_key"] = "integration-capture"
        trace = payload["traces"][0]
        trace["trace_id"] = str(trace_id)
        trace["spans"][0]["span_id"] = str(parent_span_id)
        trace["spans"][1]["span_id"] = str(child_span_id)
        trace["spans"][1]["parent_span_id"] = str(parent_span_id)
        app = create_app(
            Settings(
                database_url=DATABASE_URL,
                payload_storage_path=payload_storage_path,
            )
        )
        with TestClient(app) as client:
            first_response = client.post(
                "/api/v1/ingest/traces",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )
            second_response = client.post(
                "/api/v1/ingest/traces",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
            )

        assert first_response.status_code == 202
        assert first_response.json()["traces"] == [{"trace_id": str(trace_id), "replayed": False}]
        assert second_response.status_code == 202
        assert second_response.json()["traces"] == [{"trace_id": str(trace_id), "replayed": True}]

        async with session_factory() as session:
            traces = (await session.scalars(select(Trace).where(Trace.id == trace_id))).all()
            spans = (await session.scalars(select(Span).where(Span.trace_id == trace_id))).all()
            payloads = (
                await session.scalars(select(Payload).where(Payload.trace_id == trace_id))
            ).all()

        assert len(traces) == 1
        assert len(spans) == 2
        assert {span.parent_span_id for span in spans} == {None, parent_span_id}
        assert len(payloads) == 1
        assert payloads[0].storage_key is not None
        assert payloads[0].content == {"storage_key": payloads[0].storage_key}
        assert payloads[0].content_size_bytes > 0
        assert await payload_store.read(payloads[0].storage_key) == {
            "api_key": "[REDACTED]",
            "question": "hello",
        }
        assert payloads[0].redaction_summary["redacted_fields"] == 1
    finally:
        await engine.dispose()
