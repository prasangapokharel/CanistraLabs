"""Initial schema creation

Revision ID: 001_initial_schema
Revises:
Create Date: 2024-03-18 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("canister_id", sa.String(255), nullable=True),
        sa.Column("principal_id", sa.String(255), nullable=True),
        sa.Column("url", sa.String(255), nullable=True),
        sa.Column("code_content", sa.Text(), nullable=True),
        sa.Column("language", sa.String(50), nullable=False, server_default="motoko"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deployed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canister_id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index(op.f("ix_projects_canister_id"), "projects", ["canister_id"], unique=True)
    op.create_index(op.f("ix_projects_id"), "projects", ["id"], unique=False)
    op.create_index(op.f("ix_projects_principal_id"), "projects", ["principal_id"], unique=False)
    op.create_index(op.f("ix_projects_url"), "projects", ["url"], unique=True)
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)

    # Create canisters table
    op.create_table(
        "canisters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("canister_name", sa.String(255), nullable=False),
        sa.Column("principal_id", sa.String(255), nullable=False),
        sa.Column("canister_hash", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("cycles_balance", sa.String(100), nullable=True),
        sa.Column("memory_usage", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canister_name"),
        sa.UniqueConstraint("principal_id"),
    )
    op.create_index(op.f("ix_canisters_id"), "canisters", ["id"], unique=False)
    op.create_index(op.f("ix_canisters_principal_id"), "canisters", ["principal_id"], unique=True)
    op.create_index(op.f("ix_canisters_project_id"), "canisters", ["project_id"], unique=False)

    # Create deployments table
    op.create_table(
        "deployments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("logs", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("task_id", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id"),
    )
    op.create_index(op.f("ix_deployments_id"), "deployments", ["id"], unique=False)
    op.create_index(op.f("ix_deployments_project_id"), "deployments", ["project_id"], unique=False)
    op.create_index(op.f("ix_deployments_task_id"), "deployments", ["task_id"], unique=True)

    # Create project_enrollments table
    op.create_table(
        "project_enrollments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="editor"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "project_id", name="uq_user_project"),
    )
    op.create_index(op.f("ix_project_enrollments_id"), "project_enrollments", ["id"], unique=False)
    op.create_index(
        op.f("ix_project_enrollments_project_id"),
        "project_enrollments",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_project_enrollments_user_id"), "project_enrollments", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_project_enrollments_user_id"), table_name="project_enrollments")
    op.drop_index(op.f("ix_project_enrollments_project_id"), table_name="project_enrollments")
    op.drop_index(op.f("ix_project_enrollments_id"), table_name="project_enrollments")
    op.drop_table("project_enrollments")

    op.drop_index(op.f("ix_deployments_task_id"), table_name="deployments")
    op.drop_index(op.f("ix_deployments_project_id"), table_name="deployments")
    op.drop_index(op.f("ix_deployments_id"), table_name="deployments")
    op.drop_table("deployments")

    op.drop_index(op.f("ix_canisters_project_id"), table_name="canisters")
    op.drop_index(op.f("ix_canisters_principal_id"), table_name="canisters")
    op.drop_index(op.f("ix_canisters_id"), table_name="canisters")
    op.drop_table("canisters")

    op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_url"), table_name="projects")
    op.drop_index(op.f("ix_projects_principal_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_id"), table_name="projects")
    op.drop_index(op.f("ix_projects_canister_id"), table_name="projects")
    op.drop_table("projects")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
