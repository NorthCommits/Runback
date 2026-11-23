from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.ingestion import (
    IngestedTrace,
    SpanInput,
    TraceBatchInput,
    TraceBatchResponse,
    TraceInput,
)
from app.infrastructure.models import (
    AuditEvent,
    Environment,
    IngestToken,
    Payload,
    Project,
    Span,
    Trace,
)
from app.infrastructure.payloads import LocalPayloadStore
from app.services.redaction import payload_size_bytes, redact_payload
from app.services.tokens import hash_token


class IngestionError(Exception):
    def __init__(self, status_code: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.code = code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class IngestPrincipal:
    project_id: UUID
    workspace_id: UUID


class TraceIngestionService:
    def __init__(
        self,
        session: AsyncSession,
        sensitive_keys: frozenset[str],
        max_payload_bytes: int,
        payload_store: LocalPayloadStore,
    ) -> None:
        self._session = session
        self._sensitive_keys = sensitive_keys
        self._max_payload_bytes = max_payload_bytes
        self._payload_store = payload_store

    async def ingest(self, authorization: str | None, batch: TraceBatchInput) -> TraceBatchResponse:
        async with self._session.begin():
            principal = await self._authenticate(authorization)
            await self._verify_environment(batch.environment_id, principal.project_id)
            results: list[IngestedTrace] = []
            for trace in self._ordered_traces(batch.traces):
                results.append(await self._ingest_trace(principal, batch, trace))
            self._session.add(
                AuditEvent(
                    workspace_id=principal.workspace_id,
                    project_id=principal.project_id,
                    action="trace.ingested",
                    target_type="trace_batch",
                    target_id=batch.idempotency_key,
                    details={
                        "trace_count": len(batch.traces),
                        "schema_version": batch.schema_version,
                    },
                )
            )
        return TraceBatchResponse(traces=results, received_at=datetime.now(UTC))

    async def _authenticate(self, authorization: str | None) -> IngestPrincipal:
        if authorization is None or not authorization.startswith("Bearer "):
            raise IngestionError(401, "invalid_ingest_token", "A bearer ingest token is required")
        token = authorization.removeprefix("Bearer ").strip()
        if not token.startswith("rb_"):
            raise IngestionError(401, "invalid_ingest_token", "The ingest token is invalid")
        result = await self._session.execute(
            select(IngestToken, Project.workspace_id)
            .join(Project, Project.id == IngestToken.project_id)
            .where(IngestToken.token_hash == hash_token(token))
        )
        row = result.one_or_none()
        if row is None:
            raise IngestionError(401, "invalid_ingest_token", "The ingest token is invalid")
        ingest_token, workspace_id = row
        now = datetime.now(UTC)
        if ingest_token.revoked_at is not None or (
            ingest_token.expires_at is not None and ingest_token.expires_at <= now
        ):
            raise IngestionError(401, "invalid_ingest_token", "The ingest token is inactive")
        if not ingest_token.scopes.get("ingest", False):
            raise IngestionError(
                403,
                "insufficient_scope",
                "The ingest token lacks the ingest scope",
            )
        return IngestPrincipal(project_id=ingest_token.project_id, workspace_id=workspace_id)

    async def _verify_environment(self, environment_id: UUID, project_id: UUID) -> None:
        environment = await self._session.scalar(
            select(Environment).where(
                Environment.id == environment_id,
                Environment.project_id == project_id,
            )
        )
        if environment is None:
            raise IngestionError(
                422,
                "invalid_environment",
                "The environment does not belong to this project",
            )

    async def _ingest_trace(
        self,
        principal: IngestPrincipal,
        batch: TraceBatchInput,
        trace: TraceInput,
    ) -> IngestedTrace:
        result = await self._session.execute(
            insert(Trace)
            .values(
                id=trace.trace_id,
                workspace_id=principal.workspace_id,
                project_id=principal.project_id,
                environment_id=batch.environment_id,
                parent_trace_id=trace.parent_trace_id,
                source_framework=trace.source_framework,
                source_version=trace.source_version,
                agent_name=trace.agent_name,
                agent_version=trace.agent_version,
                started_at=trace.started_at,
                ended_at=trace.ended_at,
                status=trace.status,
                attributes=trace.attributes,
                schema_version=batch.schema_version,
                ingest_idempotency_key=self._trace_idempotency_key(
                    batch.idempotency_key, trace.trace_id
                ),
                replay_mode=None,
            )
            .on_conflict_do_nothing(index_elements=["project_id", "ingest_idempotency_key"])
            .returning(Trace.id)
        )
        created_trace_id = result.scalar_one_or_none()
        if created_trace_id is None:
            existing_trace_id = await self._session.scalar(
                select(Trace.id).where(
                    Trace.project_id == principal.project_id,
                    Trace.ingest_idempotency_key
                    == self._trace_idempotency_key(batch.idempotency_key, trace.trace_id),
                )
            )
            if existing_trace_id is None:
                raise IngestionError(
                    409,
                    "trace_conflict",
                    "The trace identifier conflicts with existing data",
                )
            return IngestedTrace(trace_id=existing_trace_id, replayed=True)
        await self._store_spans(trace, created_trace_id)
        return IngestedTrace(trace_id=created_trace_id, replayed=False)

    async def _store_spans(self, trace: TraceInput, trace_id: UUID) -> None:
        source_to_internal_id = {span.span_id: span.span_id for span in trace.spans}
        remaining = {span.span_id: span for span in trace.spans}
        while remaining:
            ready_spans = [
                span
                for span in remaining.values()
                if span.parent_span_id is None or span.parent_span_id not in remaining
            ]
            for span in ready_spans:
                await self._store_span(span, trace_id, source_to_internal_id)
                del remaining[span.span_id]

    @staticmethod
    def _ordered_traces(traces: list[TraceInput]) -> list[TraceInput]:
        remaining = {trace.trace_id: trace for trace in traces}
        ordered_traces: list[TraceInput] = []
        while remaining:
            ready_traces = [
                trace
                for trace in remaining.values()
                if trace.parent_trace_id is None or trace.parent_trace_id not in remaining
            ]
            for trace in ready_traces:
                ordered_traces.append(trace)
                del remaining[trace.trace_id]
        return ordered_traces

    async def _store_span(
        self,
        span: SpanInput,
        trace_id: UUID,
        source_to_internal_id: dict[UUID, UUID],
    ) -> None:
        input_payload_id, input_summary = await self._store_payload(span.input, trace_id)
        output_payload_id, output_summary = await self._store_payload(span.output, trace_id)
        self._session.add(
            Span(
                id=span.span_id,
                trace_id=trace_id,
                parent_span_id=(
                    source_to_internal_id[span.parent_span_id]
                    if span.parent_span_id is not None
                    else None
                ),
                source_span_id=str(span.span_id),
                name=span.name,
                kind=span.kind,
                start_time=span.start_time,
                end_time=span.end_time,
                status=span.status,
                status_message=span.status_message,
                attributes=span.attributes,
                events=span.events,
                links=span.links,
                input_payload_id=input_payload_id,
                output_payload_id=output_payload_id,
                redaction_summary={"input": input_summary, "output": output_summary},
            )
        )

    async def _store_payload(
        self,
        content: dict[str, Any] | list[Any] | str | int | float | bool | None,
        trace_id: UUID,
    ) -> tuple[UUID | None, dict[str, Any]]:
        if content is None:
            return None, {}
        redacted_payload = redact_payload(content, self._sensitive_keys)
        if payload_size_bytes(redacted_payload.content) > self._max_payload_bytes:
            raise IngestionError(
                413,
                "payload_too_large",
                "A span payload exceeds the configured limit",
            )
        payload_reference = await self._payload_store.write(trace_id, redacted_payload.content)
        payload = Payload(
            trace_id=trace_id,
            content={"storage_key": payload_reference.storage_key},
            storage_key=payload_reference.storage_key,
            content_size_bytes=payload_reference.content_size_bytes,
            redaction_summary=redacted_payload.redaction_summary,
        )
        self._session.add(payload)
        await self._session.flush()
        return payload.id, redacted_payload.redaction_summary

    @staticmethod
    def _trace_idempotency_key(batch_key: str, trace_id: UUID) -> str:
        return f"{batch_key}:{trace_id}"
