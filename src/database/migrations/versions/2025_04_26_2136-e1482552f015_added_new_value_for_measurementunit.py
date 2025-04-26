"""Added new value for MeasurementUnit

Revision ID: e1482552f015
Revises: 87e6c4d9e885
Create Date: 2025-04-26 21:36:26.427267

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1482552f015'
down_revision: Union[str, None] = '87e6c4d9e885'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE measurementunit ADD VALUE IF NOT EXISTS 'COEFFICIENT';")


def downgrade() -> None:
    pass
