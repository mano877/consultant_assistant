"""baseline existing leads table

Revision ID: 20261003_01
Revises: 
Create Date: 2026-10-03 12:44:20.289967

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261003_01'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TEXT_FIELDS = (
    "session_id", "name", "email", "phone_whatsapp", "course_interest",
    "preferred_location", "current_education", "english_test_status",
    "budget_intake", "current_country_status", "lead_status",
)


def upgrade() -> None:
    """Create the legacy schema or adopt it without rewriting existing rows."""
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("leads"):
        columns = {c["name"] for c in inspector.get_columns("leads")}
        missing = (set(TEXT_FIELDS) | {"id", "created_at"}) - columns
        if missing:
            raise RuntimeError(f"Existing leads table is not the expected legacy schema; missing: {sorted(missing)}")
        return
    op.create_table(
        "leads",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        *(sa.Column(name, sa.String(), nullable=False) for name in TEXT_FIELDS),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_leads_session_id", "leads", ["session_id"])


def downgrade() -> None:
    # This baseline may have adopted a populated pre-Alembic table.
    raise RuntimeError("The adopted leads baseline cannot be downgraded automatically; preserve the existing table and data.")
