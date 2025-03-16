"""empty message

Revision ID: 7a43273a71df
Revises: 1d002403c68f
Create Date: 2025-03-16 14:28:38.982772

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a43273a71df'
down_revision: Union[str, None] = '1d002403c68f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add UNREGISTERED value to subscriptionstatus enum"""
    op.execute("ALTER TYPE subscriptionstatus ADD VALUE IF NOT EXISTS 'UNREGISTERED'")


def downgrade() -> None:
    """
    Remove UNREGISTERED value from subscriptionstatus enum.
    This requires recreating the enum type without the value.
    """
    # Convert the column to text
    op.execute("ALTER TABLE subscriptions ALTER COLUMN status TYPE text")

    # Drop the enum type
    op.execute("DROP TYPE subscriptionstatus")

    # Recreate the enum without the removed value
    op.execute("CREATE TYPE subscriptionstatus AS ENUM ('ACTIVE', 'FROZEN', 'EXPIRED')")

    # Update any rows with the removed value
    op.execute("UPDATE subscriptions SET status = 'ACTIVE' WHERE status = 'UNREGISTERED'")

    # Convert the column back to the enum type
    op.execute(
        """
        ALTER TABLE subscriptions
         ALTER COLUMN status TYPE subscriptionstatus USING status::subscriptionstatus
        """
    )
