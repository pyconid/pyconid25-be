"""merge streaming_table_and_add_attendance_day

Revision ID: 60bce827bab3
Revises: 3a190131d228, b3212d6ebfde
Create Date: 2025-11-26 09:46:08.823396

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "60bce827bab3"
down_revision: Union[str, None] = ("3a190131d228", "b3212d6ebfde")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
