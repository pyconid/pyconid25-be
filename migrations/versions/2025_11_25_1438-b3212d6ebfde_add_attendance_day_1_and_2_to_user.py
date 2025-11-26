"""add_attendance_day_1_and_2_to_user

Revision ID: b3212d6ebfde
Revises: e4b791d43166
Create Date: 2025-11-25 14:38:44.483756

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b3212d6ebfde"
down_revision: Union[str, None] = "e4b791d43166"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "user",
        sa.Column(
            "attendance_day_1", sa.Boolean(), nullable=True, server_default=sa.false()
        ),
    )
    op.add_column(
        "user",
        sa.Column("attendance_day_1_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column(
            "attendance_day_2", sa.Boolean(), nullable=True, server_default=sa.false()
        ),
    )
    op.add_column(
        "user",
        sa.Column("attendance_day_2_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("user", "attendance_day_2")
    op.drop_column("user", "attendance_day_1")
    op.drop_column("user", "attendance_day_2_at")
    op.drop_column("user", "attendance_day_1_at")
