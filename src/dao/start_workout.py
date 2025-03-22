from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import BaseDAO
from src.database.models import StartWorkout


class StartWorkoutDAO(BaseDAO[StartWorkout]):
    model = StartWorkout

    @classmethod
    async def get_workout_by_day(
        cls, session: AsyncSession, day_number: int
    ) -> StartWorkout | None:
        """
        Get a START program workout by day number

        Args:
            session: Database async session
            day_number: Day number in the START program (1-based)

        Returns:
            The StartWorkout for the specified day or None if not found
        """
        query = select(cls.model).where(cls.model.day_number == day_number)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_workout_days(cls, session: AsyncSession, max_days: int = 100) -> list[int]:
        """
        Get a list of all days that have workouts in the START program,
        up to a maximum number of days (default is maximum available)

        Args:
            session: Database async session
            max_days: Maximum number of days to consider

        Returns:
            List of day numbers (1-based) that have workouts
        """
        query = (
            select(cls.model.day_number)
            .where(cls.model.day_number <= max_days)
            .order_by(cls.model.day_number)
        )
        result = await session.execute(query)
        return [day_number for (day_number,) in result.fetchall()]
