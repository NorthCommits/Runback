from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("workspace_id", "name", name="uq_projects_workspace_name"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Environment(Base):
    __tablename__ = "environments"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_environments_project_name"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IngestToken(Base):
    __tablename__ = "ingest_tokens"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(255))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    scopes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Trace(Base):
    __tablename__ = "traces"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "ingest_idempotency_key",
            name="uq_traces_project_idempotency_key",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    environment_id: Mapped[UUID] = mapped_column(ForeignKey("environments.id", ondelete="RESTRICT"))
    parent_trace_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("traces.id", ondelete="SET NULL")
    )
    source_framework: Mapped[str] = mapped_column(String(255))
    source_version: Mapped[str | None] = mapped_column(String(255))
    agent_name: Mapped[str | None] = mapped_column(String(255))
    agent_version: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(64))
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    schema_version: Mapped[str] = mapped_column(String(64))
    ingest_idempotency_key: Mapped[str] = mapped_column(String(255))
    replay_mode: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payload(Base):
    __tablename__ = "payloads"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    trace_id: Mapped[UUID] = mapped_column(ForeignKey("traces.id", ondelete="CASCADE"))
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    redaction_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Span(Base):
    __tablename__ = "spans"
    __table_args__ = (
        UniqueConstraint("trace_id", "source_span_id", name="uq_spans_trace_source_span_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    trace_id: Mapped[UUID] = mapped_column(ForeignKey("traces.id", ondelete="CASCADE"))
    parent_span_id: Mapped[UUID | None] = mapped_column(ForeignKey("spans.id", ondelete="SET NULL"))
    source_span_id: Mapped[str | None] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(1024))
    kind: Mapped[str] = mapped_column(String(64))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(64))
    status_message: Mapped[str | None] = mapped_column(Text)
    attributes: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    events: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    links: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    input_payload_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("payloads.id", ondelete="SET NULL")
    )
    output_payload_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("payloads.id", ondelete="SET NULL")
    )
    redaction_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    workspace_id: Mapped[UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"))
    project_id: Mapped[UUID | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"))
    actor_id: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(255))
    target_type: Mapped[str] = mapped_column(String(255))
    target_id: Mapped[str] = mapped_column(String(255))
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
