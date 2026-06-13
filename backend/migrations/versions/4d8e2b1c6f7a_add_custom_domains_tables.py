"""Add custom_domains and domain_verifications tables

Revision ID: 4d8e2b1c6f7a
Revises: 3c9f1a2b4d5e
Create Date: 2026-06-13
"""

from alembic import op
import sqlalchemy as sa


revision = "4d8e2b1c6f7a"
down_revision = "3c9f1a2b4d5e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "custom_domains",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("domain_name", sa.String(length=255), nullable=False),
        sa.Column("subdomain", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("registration_status", sa.String(length=50), nullable=True),
        sa.Column("canister_id", sa.String(length=255), nullable=False),
        sa.Column("icp_request_id", sa.String(length=255), nullable=True),
        sa.Column("dns_configured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cname_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("txt_record_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("acme_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ssl_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ssl_issued_at", sa.DateTime(), nullable=True),
        sa.Column("ssl_expires_at", sa.DateTime(), nullable=True),
        sa.Column("dns_instructions", sa.Text(), nullable=True),
        sa.Column("ic_domains_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("activated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_custom_domains_id", "custom_domains", ["id"], unique=False)
    op.create_index("ix_custom_domains_project_id", "custom_domains", ["project_id"], unique=False)
    op.create_index("ix_custom_domains_user_id", "custom_domains", ["user_id"], unique=False)
    op.create_index("ix_custom_domains_domain_name", "custom_domains", ["domain_name"], unique=False)

    op.create_table(
        "domain_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=False),
        sa.Column("record_type", sa.String(length=10), nullable=False),
        sa.Column("record_name", sa.String(length=255), nullable=False),
        sa.Column("record_value", sa.String(length=255), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_checked", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["domain_id"], ["custom_domains.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_domain_verifications_id", "domain_verifications", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_domain_verifications_id", table_name="domain_verifications")
    op.drop_table("domain_verifications")
    op.drop_index("ix_custom_domains_domain_name", table_name="custom_domains")
    op.drop_index("ix_custom_domains_user_id", table_name="custom_domains")
    op.drop_index("ix_custom_domains_project_id", table_name="custom_domains")
    op.drop_index("ix_custom_domains_id", table_name="custom_domains")
    op.drop_table("custom_domains")
