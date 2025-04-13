"""empty message

Revision ID: b54fa0aee959
Revises: 700357d1865d
Create Date: 2025-04-09 20:18:43.632313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b54fa0aee959'
down_revision: Union[str, None] = '700357d1865d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exercise_standards', sa.Column('male_min_value', sa.Float(), nullable=False))
    op.add_column('exercise_standards', sa.Column('male_max_value', sa.Float(), nullable=False))
    op.add_column('exercise_standards', sa.Column('female_min_value', sa.Float(), nullable=False))
    op.add_column('exercise_standards', sa.Column('female_max_value', sa.Float(), nullable=False))
    op.drop_column('exercise_standards', 'max_value')
    op.drop_column('exercise_standards', 'gender')
    op.drop_column('exercise_standards', 'min_value')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('exercise_standards', sa.Column('min_value', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.add_column('exercise_standards', sa.Column('gender', postgresql.ENUM('MALE', 'FEMALE', name='gender'), autoincrement=False, nullable=False))
    op.add_column('exercise_standards', sa.Column('max_value', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.drop_column('exercise_standards', 'female_max_value')
    op.drop_column('exercise_standards', 'female_min_value')
    op.drop_column('exercise_standards', 'male_max_value')
    op.drop_column('exercise_standards', 'male_min_value')
    # ### end Alembic commands ###
