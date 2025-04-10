"""empty message

Revision ID: 700357d1865d
Revises: d153e88f06d4
Create Date: 2025-03-30 12:58:55.696673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql



# revision identifiers, used by Alembic.
revision: str = '700357d1865d'
down_revision: Union[str, None] = 'd153e88f06d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###

    # Create the profile_categories table
    op.create_table('profile_categories',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('description', sa.String(length=300), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name')
                    )

    # The enum types will be created as part of the table creation
    # using the SQLAlchemy Enum types in the column definitions below

    # Create the profile_exercises table
    op.create_table('profile_exercises',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('name', sa.String(length=100), nullable=False),
                    sa.Column('category_name', sa.String(length=100), nullable=False),
                    sa.Column('description', sa.String(length=300), nullable=True),
                    sa.Column('unit',
                              sa.Enum('KILOGRAMS', 'REPS', 'METERS', 'SECONDS', 'MINUTES',
                                      'CALORIES', 'WATTS',
                                      name='measurementunit').with_variant(
                                  postgresql.ENUM('KILOGRAMS', 'REPS', 'METERS', 'SECONDS',
                                                  'MINUTES', 'CALORIES', 'WATTS',
                                                  name='measurementunit', create_type=False),
                                  'postgresql'
                              ),
                              nullable=False),
                    sa.Column('result_type',
                              sa.Enum('STM_TIME', 'ASAP_TIME', 'WEIGHT', 'REPS', 'DISTANCE',
                                      'CAPACITY', 'CALORIES', 'COEFFICIENT',
                                      name='resulttype').with_variant(
                                  postgresql.ENUM('STM_TIME', 'ASAP_TIME', 'WEIGHT', 'REPS',
                                                  'DISTANCE', 'CAPACITY', 'CALORIES', 'COEFFICIENT',
                                                  name='resulttype', create_type=False),
                                  'postgresql'
                              ),
                              nullable=False),
                    sa.Column('is_time_based', sa.Boolean(), nullable=False),
                    sa.Column('is_basic', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['category_name'], ['profile_categories.name'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Create the exercise_standards table
    op.create_table('exercise_standards',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('exercise_id', sa.Integer(), nullable=False),
                    sa.Column('user_level',
                              sa.Enum('FIRST', 'SECOND', 'MINKAIFA', 'COMPETITION', 'START',
                                      name='userlevel').with_variant(
                                  postgresql.ENUM('FIRST', 'SECOND', 'MINKAIFA', 'COMPETITION',
                                                  'START',
                                                  name='userlevel', create_type=False),
                                  'postgresql'
                              ),
                              nullable=False),
                    sa.Column('gender',
                              sa.Enum('MALE', 'FEMALE',
                                      name='gender').with_variant(
                                  postgresql.ENUM('MALE', 'FEMALE',
                                                  name='gender', create_type=False),
                                  'postgresql'
                              ),
                              nullable=False),
                    sa.Column('min_value', sa.Float(), nullable=False),
                    sa.Column('max_value', sa.Float(), nullable=False),
                    sa.ForeignKeyConstraint(['exercise_id'], ['profile_exercises.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    sa.CheckConstraint('min_value > 0'),
                    sa.CheckConstraint('max_value > 0')
                    )

    # Create the user_profile_results table
    op.create_table('user_profile_results',
                    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
                    sa.Column('user_id', sa.BigInteger(), nullable=False),
                    sa.Column('exercise_id', sa.Integer(), nullable=False),
                    sa.Column('result_value', sa.Float(), nullable=False),
                    sa.Column('date', sa.DateTime(), nullable=False),
                    sa.ForeignKeyConstraint(['exercise_id'], ['profile_exercises.id'], ),
                    sa.ForeignKeyConstraint(['user_id'], ['users.telegram_id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_profile_results')
    op.drop_table('exercise_standards')
    op.drop_table('profile_exercises')
    op.drop_table('profile_categories')
    # ### end Alembic commands ###
