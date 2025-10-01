"""seed ticket description

Revision ID: 5614148f2bd2
Revises: 645aef4f0e01
Create Date: 2025-09-26 22:23:50.773660

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5614148f2bd2"
down_revision: Union[str, None] = "645aef4f0e01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    descriptions = {
        "Early Bird - Regular": """This ticket is for individual who pays for the ticket themselves. The price of this ticket is not the true cost, it is subsidized thanks for our sponsor.
This ticket includes :
- In Person and Online access for the conference
- Food and Snack for 2 days
- PyCon ID 2025 Merchandise""",
        "Early Bird - Student": """This ticket is for students (school or university) only. The price of this ticket is heavily subsidized to give chance for students to join the conference.
This ticket includes :
- In Person and Online access for the conference
- Food and Snack for 2 days
- PyCon ID 2025 Merchandise""",
        "Regular": """This ticket is for individual who pays for the ticket themselves. The price of this ticket is not the true cost, it is subsidized thanks for our sponsor.
This ticket includes :
- In Person and Online access for the conference
- Food and Snack for 2 days
- PyCon ID 2025 Merchandise""",
        "Student": """This ticket is for students (school or university) only. The price of this ticket is heavily subsidized to give chance for students to join the conference.
This ticket includes :
- In Person and Online access for the conference
- Food and Snack for 2 days
- PyCon ID 2025 Merchandise""",
        "Corporate": """This ticket is for individual who pays for the ticket themselves. The price of this ticket is the true cost of the conference.
This ticket includes :
- Company recognition at the conference
- In Person and Online access for the conference
- Food and Snack for 2 days
- PyCon ID 2025 Merchandise""",
        "Patron": """This ticket is for individual who wants to support our conference.
This ticket includes :
- Individual Patron recognition at the conference
- In Person and Online access for the conference
- Food and Snack for 2 days
- PyCon ID 2025 Merchandise""",
        "Online": """This ticket is for individual who wants to join our conference online.
This ticket includes :
- Online access for the conference""",
    }
    for name, desc in descriptions.items():
        op.execute(
            f"""
            UPDATE public.ticket
            SET description = '{desc.replace("'", "''")}'
            WHERE name = '{name.replace("'", "''")}'
            """
        )


def downgrade():
    op.execute("UPDATE public.ticket SET description = NULL")
