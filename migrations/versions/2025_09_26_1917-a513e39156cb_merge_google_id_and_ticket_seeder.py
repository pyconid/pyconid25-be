"""merge google_id and ticket seeder

Revision ID: a513e39156cb
Revises: 1788b33307f3, seedticket0001
Create Date: 2025-09-26 19:17:40.665481

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "a513e39156cb"
down_revision: Union[str, None] = ("1788b33307f3", "seedticket0001")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
