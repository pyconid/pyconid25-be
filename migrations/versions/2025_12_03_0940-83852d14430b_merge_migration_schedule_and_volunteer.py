"""merge migration schedule and volunteer

Revision ID: 83852d14430b
Revises: b643409f7fa7, edb6af6709d4
Create Date: 2025-12-03 09:40:10.568510

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "83852d14430b"
down_revision: Union[str, None] = ("b643409f7fa7", "edb6af6709d4")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
