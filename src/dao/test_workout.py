import logging

from aiogram_dialog import Dialog, Window
from sqlalchemy import select, Result, Sequence
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import BaseDAO
from src.database.models import UserSetting, TestWorkouts

logger = logging.getLogger(__name__)


class TestWorkoutDAO(BaseDAO[TestWorkouts]):

    model = TestWorkouts

    @classmethod
    async def get_test_workouts(cls, session: AsyncSession) -> list[TestWorkouts]:
        """
        Get all test days numbers.

        Args:
            session: Database session

        Returns:
            List of test days numbers
        """
        test_workouts: Sequence[TestWorkouts] = await cls.find_all(session=session, filters=None)
        return test_workouts
