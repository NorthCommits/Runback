from alembic import op
import sqlalchemy as sa


revision = "0002_payload_references"
down_revision = "0001_canonical_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payloads", sa.Column("storage_key", sa.String(length=1024), nullable=True))
    op.add_column(
        "payloads",
        sa.Column(
            "content_size_bytes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_unique_constraint("uq_payloads_storage_key", "payloads", ["storage_key"])


def downgrade() -> None:
    op.drop_constraint("uq_payloads_storage_key", "payloads", type_="unique")
    op.drop_column("payloads", "content_size_bytes")
    op.drop_column("payloads", "storage_key")
