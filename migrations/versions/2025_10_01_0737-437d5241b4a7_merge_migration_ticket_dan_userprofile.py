"""merge migration ticket dan userprofile

Revision ID: 437d5241b4a7
Revises: 5614148f2bd2, 1f29f50ed6be
Create Date: 2025-10-01 07:37:58.528219

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "437d5241b4a7"
down_revision: Union[str, None] = ("5614148f2bd2", "1f29f50ed6be")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
