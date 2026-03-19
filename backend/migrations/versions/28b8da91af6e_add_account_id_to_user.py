"""add_account_id_to_user

Revision ID: 28b8da91af6e
Revises: 654fb179dc9e
Create Date: 2026-03-19 21:49:34.184244

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "28b8da91af6e"
down_revision: Union[str, None] = "654fb179dc9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add account_id field to users table
    op.add_column("users", sa.Column("account_id", sa.String(255), nullable=True))


def downgrade() -> None:
    # Remove account_id field from users table
    op.drop_column("users", "account_id")
