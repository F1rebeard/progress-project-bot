"""empty message

Revision ID: 4af474d781b3
Revises: 7a43273a71df
Create Date: 2025-03-22 16:32:43.397955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4af474d781b3'
down_revision: Union[str, None] = '7a43273a71df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('workouts', sa.Column('hashtag', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('workouts', 'hashtag')
