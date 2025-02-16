"""New updates

Revision ID: ab854574a970
Revises: 3a7209d8dc54
Create Date: 2025-02-16 19:13:13.887345

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ab854574a970'
down_revision: Union[str, None] = '3a7209d8dc54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
