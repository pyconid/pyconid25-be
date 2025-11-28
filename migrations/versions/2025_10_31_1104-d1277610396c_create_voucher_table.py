"""create voucher table

Revision ID: d1277610396c
Revises: c4cc3804ceda
Create Date: 2025-10-31 11:04:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d1277610396c"
down_revision: Union[str, None] = "c4cc3804ceda"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "voucher",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column(
            "email_whitelist", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("quota", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
        schema="public",
    )
    op.create_index(
        op.f("ix_public_voucher_id"), "voucher", ["id"], unique=False, schema="public"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_public_voucher_id"), table_name="voucher", schema="public")
    op.drop_table("voucher", schema="public")
