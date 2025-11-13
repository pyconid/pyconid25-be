"""merge migration create voucher and add column on user table

Revision ID: 3f255debcd19
Revises: d1277610396c, 2804c0cd6ed9
Create Date: 2025-11-13 13:28:24.529013

"""

from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = "3f255debcd19"
down_revision: Union[str, None] = ("d1277610396c", "2804c0cd6ed9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
