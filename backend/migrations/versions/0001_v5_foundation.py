"""Create the empty V5 foundation.

Revision ID: 0001_v5_foundation
Revises:
Create Date: 2026-09-04
"""

from collections.abc import Sequence

revision: str = "0001_v5_foundation"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Keep the V5 baseline intentionally free of domain tables."""


def downgrade() -> None:
    """Keep the V5 baseline intentionally free of domain tables."""
