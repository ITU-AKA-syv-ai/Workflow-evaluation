"""merge heads

Revision ID: cfd2c8e4bf59
Revises: 32339e7d4b28, d3cbfee31357
Create Date: 2026-05-10 16:04:10.698342

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "cfd2c8e4bf59"
down_revision: str | Sequence[str] | None = ("32339e7d4b28", "d3cbfee31357")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
