"""add description to ticket

Revision ID: 645aef4f0e01
Revises: a513e39156cb
Create Date: 2025-09-26 22:15:52.117777

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "645aef4f0e01"
down_revision = "a513e39156cb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ticket", sa.Column("description", sa.Text(), nullable=True), schema="public"
    )


def downgrade() -> None:
    op.drop_column("ticket", "description", schema="public")
