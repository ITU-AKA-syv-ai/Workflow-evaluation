"""create results table

Revision ID: 3ed9c3418547
Revises:
Create Date: 2026-03-27 19:48:27.943850

"""
from typing import Sequence, Union

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
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("request", sa.JSON),
        sa.Column("result", sa.JSON),
    )


def downgrade() -> None:
    op.drop_table("results")
