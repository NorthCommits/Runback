from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field, model_validator


class SpanInput(BaseModel):
    span_id: UUID
    parent_span_id: UUID | None = None
    name: str = Field(min_length=1, max_length=1024)
    kind: str = Field(min_length=1, max_length=64)
    start_time: AwareDatetime
    end_time: AwareDatetime | None = None
    status: str = Field(min_length=1, max_length=64)
    status_message: str | None = Field(default=None, max_length=10_000)
    attributes: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list, max_length=1_000)
    links: list[dict[str, Any]] = Field(default_factory=list, max_length=1_000)
    input: dict[str, Any] | list[Any] | str | int | float | bool | None = None
    output: dict[str, Any] | list[Any] | str | int | float | bool | None = None

    @model_validator(mode="after")
    def validate_timestamps(self) -> "SpanInput":
        if self.end_time is not None and self.end_time < self.start_time:
            raise ValueError("end_time must not precede start_time")
        return self


class TraceInput(BaseModel):
    trace_id: UUID
    parent_trace_id: UUID | None = None
    source_framework: str = Field(min_length=1, max_length=255)
    source_version: str | None = Field(default=None, max_length=255)
    agent_name: str | None = Field(default=None, max_length=255)
    agent_version: str | None = Field(default=None, max_length=255)
    started_at: AwareDatetime
    ended_at: AwareDatetime | None = None
    status: str = Field(min_length=1, max_length=64)
    attributes: dict[str, Any] = Field(default_factory=dict)
    spans: list[SpanInput] = Field(min_length=1, max_length=1_000)

    @model_validator(mode="after")
    def validate_structure(self) -> "TraceInput":
        if self.ended_at is not None and self.ended_at < self.started_at:
            raise ValueError("ended_at must not precede started_at")
        span_ids = {span.span_id for span in self.spans}
        if len(span_ids) != len(self.spans):
            raise ValueError("span_id values must be unique")
        parents = {span.span_id: span.parent_span_id for span in self.spans}
        for span_id, parent_span_id in parents.items():
            if parent_span_id is not None and parent_span_id not in span_ids:
                raise ValueError("parent_span_id must reference a span in the trace")
            if parent_span_id == span_id:
                raise ValueError("a span cannot parent itself")
        for span_id in parents:
            seen: set[UUID] = set()
            current_span_id: UUID | None = span_id
            while current_span_id is not None:
                if current_span_id in seen:
                    raise ValueError("span parent references must not contain a cycle")
                seen.add(current_span_id)
                current_span_id = parents[current_span_id]
        return self


class TraceBatchInput(BaseModel):
    schema_version: Literal["v1"]
    environment_id: UUID
    idempotency_key: str = Field(min_length=1, max_length=218)
    traces: list[TraceInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_trace_relationships(self) -> "TraceBatchInput":
        trace_ids = {trace.trace_id for trace in self.traces}
        if len(trace_ids) != len(self.traces):
            raise ValueError("trace_id values must be unique")
        parents = {trace.trace_id: trace.parent_trace_id for trace in self.traces}
        for trace_id, parent_trace_id in parents.items():
            if parent_trace_id is not None and parent_trace_id not in trace_ids:
                raise ValueError("parent_trace_id must reference a trace in the batch")
            if parent_trace_id == trace_id:
                raise ValueError("a trace cannot parent itself")
        for trace_id in parents:
            seen: set[UUID] = set()
            current_trace_id: UUID | None = trace_id
            while current_trace_id is not None:
                if current_trace_id in seen:
                    raise ValueError("trace parent references must not contain a cycle")
                seen.add(current_trace_id)
                current_trace_id = parents[current_trace_id]
        return self


class IngestedTrace(BaseModel):
    trace_id: UUID
    replayed: bool


class TraceBatchResponse(BaseModel):
    traces: list[IngestedTrace]
    received_at: datetime
