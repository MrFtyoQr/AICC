"""baseline

Revision ID: 965348c7a0a7
Revises:
Create Date: 2026-10-31 01:57:25.847243

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "965348c7a0a7"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
