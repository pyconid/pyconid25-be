"""merge streaming and check-in migration

Revision ID: 26760cbe21a5
Revises: 60bce827bab3, 643d2c34e927
Create Date: 2025-12-01 16:23:49.287566

"""

from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = "26760cbe21a5"
down_revision: Union[str, None] = ("60bce827bab3", "643d2c34e927")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
