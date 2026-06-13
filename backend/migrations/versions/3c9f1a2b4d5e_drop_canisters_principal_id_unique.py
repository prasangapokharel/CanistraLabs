"""Drop incorrect unique index on canisters.principal_id

One ICP principal (user identity) owns many canisters — principal_id must not be unique.

Revision ID: 3c9f1a2b4d5e
Revises: 2a8c4e1f9b0d
Create Date: 2026-06-13
"""

from alembic import op


revision = "3c9f1a2b4d5e"
down_revision = "2a8c4e1f9b0d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_canisters_principal_id", table_name="canisters")
    op.create_index(
        "ix_canisters_principal_id",
        "canisters",
        ["principal_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_canisters_principal_id", table_name="canisters")
    op.create_index(
        "ix_canisters_principal_id",
        "canisters",
        ["principal_id"],
        unique=True,
    )
