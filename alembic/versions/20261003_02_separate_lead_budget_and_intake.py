"""separate lead budget and intake

Revision ID: 20261003_02
Revises: 20261003_01
Create Date: 2026-10-03 12:44:21.383916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261003_02'
down_revision: Union[str, Sequence[str], None] = '20261003_01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add only missing columns; keep manually added columns and their data."""
    columns = {c["name"]: c for c in sa.inspect(op.get_bind()).get_columns("leads")}
    # Validate all adopted columns before making any changes.
    for name in ("budget", "intake"):
        if name in columns:
            column = columns[name]
            if not isinstance(column["type"], sa.String) or not column["nullable"] or column["type"].length is not None:
                raise RuntimeError(f"Existing leads.{name} must be an unbounded nullable string; manual review required")
    for name in ("budget", "intake"):
        if name not in columns:
            op.add_column("leads", sa.Column(name, sa.String(), nullable=True))


def downgrade() -> None:
    # The columns may predate Alembic and contain values from the manual fix.
    raise RuntimeError("Automatic downgrade would delete budget/intake data, including adopted columns; use an explicitly reviewed data-preserving migration.")
