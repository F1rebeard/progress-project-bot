from collections.abc import Sequence
from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import BaseDAO
from src.database.models import Workout
from src.database.models.user import UserLevel
from src.utils.workout_hashtags import create_hashtag


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

    @classmethod
    async def generate_hashtag(
        cls, wokrout_date: date, level: UserLevel, start_program_day: int | None = None
    ) -> str:
        """
        Generate hashtag for a workout based on date and level.
        For START programs also need the day number in program.
        """
        return create_hashtag(wokrout_date, level, start_program_day)

    @classmethod
    async def add_with_hashtag(
        cls, session: AsyncSession, data: dict, start_day: int | None = None
    ) -> Workout:
        """
        Add a new workout with automatically generated hashtag.
        """
        new_workout = cls.model(**data)
        if not new_workout.hashtag:
            new_workout.hashtag = await cls.generate_hashtag(
                new_workout.date, new_workout.level, start_day
            )
        session.add(new_workout)
        await session.flush()
        return new_workout

    @classmethod
    async def update_all_hashtags(cls, session: AsyncSession) -> int:
        """
        Update hashtags for all workouts that don't have one.

        Returns:
            int: Number of workouts updated
        """
        # Get all workouts without hashtags
        query = select(cls.model).where(cls.model.hashtag.is_(None))
        result = await session.execute(query)
        workouts = result.scalars().all()

        # Update each workout
        count = 0
        for workout in workouts:
            workout.hashtag = await cls.generate_hashtag(workout.date, workout.level)
            count += 1

        await session.flush()
        return count
