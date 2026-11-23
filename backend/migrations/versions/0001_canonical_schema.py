from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_canonical_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("workspace_id", "name", name="uq_projects_workspace_name"),
    )
    op.create_table(
        "environments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "name", name="uq_environments_project_name"),
    )
    op.create_table(
        "ingest_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False, unique=True),
        sa.Column("scopes", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "traces",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("environment_id", sa.Uuid(), nullable=False),
        sa.Column("parent_trace_id", sa.Uuid()),
        sa.Column("source_framework", sa.String(length=255), nullable=False),
        sa.Column("source_version", sa.String(length=255)),
        sa.Column("agent_name", sa.String(length=255)),
        sa.Column("agent_version", sa.String(length=255)),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("attributes", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("schema_version", sa.String(length=64), nullable=False),
        sa.Column("ingest_idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("replay_mode", sa.String(length=64)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["environment_id"], ["environments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["parent_trace_id"], ["traces.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("project_id", "ingest_idempotency_key", name="uq_traces_project_idempotency_key"),
    )
    op.create_table(
        "payloads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("trace_id", sa.Uuid(), nullable=False),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("redaction_summary", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["trace_id"], ["traces.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "spans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("trace_id", sa.Uuid(), nullable=False),
        sa.Column("parent_span_id", sa.Uuid()),
        sa.Column("source_span_id", sa.String(length=255)),
        sa.Column("name", sa.String(length=1024), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("status_message", sa.Text()),
        sa.Column("attributes", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("events", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("links", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("input_payload_id", sa.Uuid()),
        sa.Column("output_payload_id", sa.Uuid()),
        sa.Column("redaction_summary", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["trace_id"], ["traces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_span_id"], ["spans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["input_payload_id"], ["payloads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["output_payload_id"], ["payloads.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("trace_id", "source_span_id", name="uq_spans_trace_source_span_id"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid()),
        sa.Column("actor_id", sa.String(length=255)),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("target_type", sa.String(length=255), nullable=False),
        sa.Column("target_id", sa.String(length=255), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_traces_project_started_at", "traces", ["project_id", "started_at"])
    op.create_index("ix_spans_trace_id", "spans", ["trace_id"])
    op.create_index("ix_audit_events_workspace_created_at", "audit_events", ["workspace_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_workspace_created_at", table_name="audit_events")
    op.drop_index("ix_spans_trace_id", table_name="spans")
    op.drop_index("ix_traces_project_started_at", table_name="traces")
    op.drop_table("audit_events")
    op.drop_table("spans")
    op.drop_table("payloads")
    op.drop_table("traces")
    op.drop_table("ingest_tokens")
    op.drop_table("environments")
    op.drop_table("projects")
    op.drop_table("workspaces")
