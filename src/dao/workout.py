from collections.abc import Sequence
from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import BaseDAO
from src.database.models import Workout
from src.database.models.user import UserLevel


class WorkoutDAO(BaseDAO[Workout]):
    model = Workout

    @classmethod
    async def get_workouts_by_date_range(
        cls,
        session: AsyncSession,
        level: UserLevel,
        start_date: date,
        end_date: date,
    ) -> Sequence[Workout]:
        """
        Get workout for a given leven and range of dates.
        """
        query = (
            select(cls.model)
            .where(
                and_(
                    cls.model.date >= start_date,
                    cls.model.date <= end_date,
                    cls.model.level == level,
                )
            )
            .order_by(cls.model.date)
        )

        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_workout_for_date(
        cls,
        session: AsyncSession,
        workout_date: date,
        level: UserLevel,
    ) -> Workout | None:
        """
        Get workout for a specific date and level.
        """
        query = select(cls.model).where(
            and_(
                cls.model.date == workout_date,
                cls.model.level == level,
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
