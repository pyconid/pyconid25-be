"""seed ticket data

Revision ID: seedticket0001
Revises: f6498b11dc19
Create Date: 2025-09-26 18:00:00.000000

"""

from alembic import op
import uuid

revision = "seedticket0001"
down_revision = "f6498b11dc19"
branch_labels = None
depends_on = None


def upgrade():
    ticket_data = [
        ("Early Bird - Regular", 350000, "In Person", False, True),
        ("Early Bird - Student", 300000, "Student", False, True),
        ("Regular", 450000, "In Person", False, True),
        ("Student", 400000, "Student", False, True),
        ("Corporate", 750000, "In Person", False, True),
        ("Patron", 1750000, "Patron", False, True),
        ("Online", 200000, "Online", False, True),
    ]
    for name, price, user_type, is_sold_out, is_active in ticket_data:
        op.execute(
            f"""
            INSERT INTO public.ticket (id, name, price, user_participant_type, is_sold_out, is_active)
            VALUES ('{uuid.uuid4()}', '{name}', {price}, '{user_type}', {str(is_sold_out).lower()}, {str(is_active).lower()})
            """
        )


def downgrade():
    op.execute("DELETE FROM public.ticket")
