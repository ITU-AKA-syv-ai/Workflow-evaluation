"""remove status column from results

Revision ID: 3ab80448324a
Revises: 80fd4afd6633
Create Date: 2026-05-04 20:34:06.368610

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3ab80448324a"
down_revision: str | Sequence[str] | None = "80fd4afd6633"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("results", "status")


def downgrade() -> None:
    op.add_column(
        "results",
        sa.Column("status", sa.String(), nullable=False, server_default="PENDING"),
    )
