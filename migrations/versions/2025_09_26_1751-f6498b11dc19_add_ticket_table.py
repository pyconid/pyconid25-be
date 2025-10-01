"""add ticket table

Revision ID: f6498b11dc19
Revises: d1567689c00d
Create Date: 2025-09-26 17:51:50.458890

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f6498b11dc19"
down_revision: Union[str, None] = "d1567689c00d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticket",
        sa.Column("id", sa.UUID(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("user_participant_type", sa.String(), nullable=False),
        sa.Column(
            "is_sold_out", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        schema="public",
    )


def downgrade() -> None:
    op.drop_table("ticket", schema="public")
