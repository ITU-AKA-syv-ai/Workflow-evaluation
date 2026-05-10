"""add result tags and model metadata

Revision ID: 32339e7d4b28
Revises: 7b70cc1b2f82
Create Date: 2026-05-07 13:15:58.665377

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "32339e7d4b28"
down_revision: str | Sequence[str] | None = "7b70cc1b2f82"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("results", sa.Column("tags", postgresql.JSONB(), nullable=True))
    op.add_column("results", sa.Column("model_name", sa.String(), nullable=True))
    op.add_column("results", sa.Column("model_version", sa.String(), nullable=True))

    op.execute("UPDATE results SET tags = '[]' WHERE tags IS NULL")

    op.alter_column("results", "tags", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("results", "model_version")
    op.drop_column("results", "model_name")
    op.drop_column("results", "tags")
