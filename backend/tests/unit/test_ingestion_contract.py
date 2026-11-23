from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.ingestion import TraceBatchInput


def trace_batch_payload() -> dict[str, object]:
    trace_id = uuid4()
    span_id = uuid4()
    return {
        "schema_version": "v1",
        "environment_id": str(uuid4()),
        "idempotency_key": "capture-123",
        "traces": [
            {
                "trace_id": str(trace_id),
                "source_framework": "openai-agents",
                "started_at": "2026-11-23T12:00:00Z",
                "status": "completed",
                "spans": [
                    {
                        "span_id": str(span_id),
                        "name": "planner",
                        "kind": "agent",
                        "start_time": "2026-11-23T12:00:00Z",
                        "status": "completed",
                    }
                ],
            }
        ],
    }


def test_trace_batch_accepts_versioned_canonical_input() -> None:
    batch = TraceBatchInput.model_validate(trace_batch_payload())

    assert batch.schema_version == "v1"
    assert batch.traces[0].spans[0].name == "planner"


def test_trace_batch_rejects_unknown_parent_span() -> None:
    payload = trace_batch_payload()
    trace = payload["traces"][0]
    assert isinstance(trace, dict)
    spans = trace["spans"]
    assert isinstance(spans, list)
    span = spans[0]
    assert isinstance(span, dict)
    span["parent_span_id"] = str(uuid4())

    with pytest.raises(ValidationError, match="parent_span_id"):
        TraceBatchInput.model_validate(payload)


def test_trace_batch_rejects_span_with_reverse_timestamps() -> None:
    payload = trace_batch_payload()
    trace = payload["traces"][0]
    assert isinstance(trace, dict)
    spans = trace["spans"]
    assert isinstance(spans, list)
    span = spans[0]
    assert isinstance(span, dict)
    span["end_time"] = "2026-11-23T11:59:59Z"

    with pytest.raises(ValidationError, match="end_time"):
        TraceBatchInput.model_validate(payload)


def test_trace_batch_rejects_unknown_parent_trace() -> None:
    payload = trace_batch_payload()
    trace = payload["traces"][0]
    assert isinstance(trace, dict)
    trace["parent_trace_id"] = str(uuid4())

    with pytest.raises(ValidationError, match="parent_trace_id"):
        TraceBatchInput.model_validate(payload)


def test_trace_batch_requires_timezone_aware_timestamps() -> None:
    payload = trace_batch_payload()
    trace = payload["traces"][0]
    assert isinstance(trace, dict)
    trace["started_at"] = datetime(2026, 11, 23, 12, 0, tzinfo=UTC).replace(tzinfo=None)

    with pytest.raises(ValidationError, match="timezone"):
        TraceBatchInput.model_validate(payload)
