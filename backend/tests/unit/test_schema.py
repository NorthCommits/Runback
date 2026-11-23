from sqlalchemy import UniqueConstraint

from app.infrastructure.models import IngestToken, Span, Trace


def test_ingest_tokens_store_only_unique_hashes() -> None:
    token_hash = IngestToken.__table__.c.token_hash

    assert token_hash.unique is True


def test_traces_are_idempotent_per_project() -> None:
    unique_constraints = {
        constraint.name
        for constraint in Trace.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert "uq_traces_project_idempotency_key" in unique_constraints


def test_spans_preserve_unique_source_identity_within_a_trace() -> None:
    unique_constraints = {
        constraint.name
        for constraint in Span.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert "uq_spans_trace_source_span_id" in unique_constraints
