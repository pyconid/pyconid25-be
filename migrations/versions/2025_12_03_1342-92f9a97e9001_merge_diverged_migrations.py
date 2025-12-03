"""Merge diverged migrations

Revision ID: 92f9a97e9001
Revises: 6feac25c0745, 83852d14430b
Create Date: 2025-12-03 13:42:39.739118

"""
from typing import Sequence, Union

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = '92f9a97e9001'
down_revision: Union[str, None] = ('6feac25c0745', '83852d14430b') # pyright: ignore[reportAssignmentType]
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
