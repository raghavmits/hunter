"""baseline

Revision ID: 7be17b146aa2
Revises:
Create Date: 2026-08-19 12:33:52.538299

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "7be17b146aa2"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
