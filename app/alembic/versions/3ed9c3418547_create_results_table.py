"""create results table

Revision ID: 3ed9c3418547
Revises:
Create Date: 2026-03-27 19:48:27.943850

"""

from collections.abc import Sequence
from sqlalchemy.dialects.postgresql import UUID
import uuid

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3ed9c3418547"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("request", sa.JSON),
        sa.Column("result", sa.JSON),
    )


def downgrade() -> None:
    op.drop_table("results")
