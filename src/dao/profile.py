import logging
from typing import Any

from sqlalchemy import Result, Select, Sequence, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import BaseDAO
from src.dao.user import UserDAO
from src.database.models import (
    ExerciseStandard,
    ProfileCategory,
    ProfileExercise,
    User,
    UserProfileResult,
)
from src.database.models.profile import ResultType
from src.database.models.user import Gender
from src.utils.profile import time_format_for_time_based_exercise

logger = logging.getLogger(__name__)


class ProfileCategoryDAO(BaseDAO):
    model = ProfileCategory


class ProfileExerciseDAO(BaseDAO):
    model = ProfileExercise

    @classmethod
    async def count_exercises_in_category(cls, session: AsyncSession, category_name: str) -> int:
        """
        Count the number of exercises in a specific category.

        Args:
            session: Database session
            category_name: Name of the category

        Returns:
            Number of exercises in the category
        """
        query = (
            select(func.count())
            .select_from(cls.model)
            .where(cls.model.category_name == category_name)
        )
        result = await session.execute(query)
        return result.scalar() or 0

    @classmethod
    async def get_exercises_by_category(
        cls, session: AsyncSession, category_name: str
    ) -> Sequence[ProfileExercise]:
        """
        Get all exercises in a specific category.
        Args:
            session: Database session
            category_name: Name of the category

        Returns:
            List of exercises in the category
        """
        query = select(cls.model).where(cls.model.category_name == category_name)
        result = await session.execute(query)
        return result.scalars().all()


class ExerciseStandardDAO(BaseDAO):
    model = ExerciseStandard


class UserProfileResultDAO(BaseDAO):
    model = UserProfileResult

    @classmethod
    async def count_results_in_category(
        cls,
        session: AsyncSession,
        user_id: int,
        category_name: str,
    ) -> int:
        """
        Count the number of exercise results for a user in a specific category.

        Args:
            session: Database session
            user_id: User's telegram ID
            category_name: Name of the category

        Returns:
            Number of exercise results the user has in the specified category
        """
        query = (
            select(func.count(func.distinct(UserProfileResult.id)))
            .join(ProfileExercise, UserProfileResult.exercise_id == ProfileExercise.id)
            .where(
                (UserProfileResult.user_id == user_id)
                & (ProfileExercise.category_name == category_name)
            )
        )
        result = await session.execute(query)
        return_data = result.scalar_one_or_none() if result else 0
        logger.debug(f"Results in category {category_name} for user {user_id}: {return_data}")
        return return_data

    @classmethod
    async def count_unique_exercises_with_results(
        cls,
        session: AsyncSession,
        user_id: int,
        category_name: str,
    ) -> int:
        """
        Count the number of unique exercises in a category where the user has at least one result.

        Args:
            session: Database session
            user_id: User's telegram ID
            category_name: Name of the category

        Returns:
            Number of unique exercises the user has results for in the specified category
        """
        query = (
            select(func.count(func.distinct(UserProfileResult.exercise_id)))
            .join(ProfileExercise, UserProfileResult.exercise_id == ProfileExercise.id)
            .where(
                (UserProfileResult.user_id == user_id)
                & (ProfileExercise.category_name == category_name)
            )
        )
        result = await session.execute(query)
        logger.debug(f"Unique exercises {result} in category {category_name} for user {user_id}")
        return result.scalar_one_or_none() or 0

    @classmethod
    async def get_latest_result(
        cls, session: AsyncSession, user_id: int, exercise_id: int
    ) -> UserProfileResult | None:
        """
        Get the most recent result for a specific exercise and user.

        Args:
            session: Database session
            user_id: User's telegram ID
            exercise_id: ID of the exercise

        Returns:
            The most recent result object or None if no results exist
        """
        query = (
            select(cls.model)
            .where((cls.model.user_id == user_id) & (cls.model.exercise_id == exercise_id))
            .order_by(cls.model.date.desc())
            .limit(1)
        )
        result = await session.execute(query)
        logger.debug(f"Latest result for exercise {exercise_id} for user {user_id}: {result}")
        return result.scalar_one_or_none()

    @classmethod
    async def get_history_for_exercise(
        cls,
        session: AsyncSession,
        user_id: int,
        exercise_id: int,
    ):
        """
        Get the history for a specific exercise and user.

        Args:
            session: Database session
            user_id: User's telegram ID
            exercise_id: ID of the exercise

        Returns:
            List of UserProfileResult objects
        """
        query = (
            select(UserProfileResult)
            .where(
                (UserProfileResult.user_id == user_id)
                & (UserProfileResult.exercise_id == exercise_id)
            )
            .order_by(UserProfileResult.date.desc())
        )
        result = await session.execute(query)
        logger.debug(f"History for exercise {exercise_id} for user {user_id}: {result}")
        return result.scalars().all()


class LeaderboardDAO(BaseDAO):
    """
    Data access object for leaderboard related exercise.
    """

    @classmethod
    async def get_exercise_leaderboard(
        cls, session: AsyncSession, exercise_id: int, gender: Gender
    ) -> dict[str, list[Any] | None] | list[dict[str, int | Any]]:
        """
        Get the leaderboard for a specific exercise.

        Args:
            session: Database session
            exercise_id: ID of the exercise to get leaderboard for
            gender: Filter by gender ('MALE', 'FEMALE')

        Returns:
            List of dictionaries with leaderboard data
        """
        exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none_by_id(
            data_id=exercise_id, session=session
        )
        if not exercise:
            return {"exercise": None, "results": []}

        leaderboard_query: Select = (
            select(
                UserProfileResult.user_id,
                User.first_name,
                User.last_name,
                User.username,
                User.gender,
                User.level,
                func.max(UserProfileResult.result_value).label("best_result"),
                func.max(UserProfileResult.date).label("latest_date"),
            )
            .join(User, UserProfileResult.user_id == User.telegram_id)
            .where(UserProfileResult.exercise_id == exercise_id)
            .where(User.gender == gender)
            .group_by(
                UserProfileResult.user_id,
                User.first_name,
                User.last_name,
                User.username,
                User.gender,
                User.level,
            )
        )

        # Time based as fast as possible to finish
        if exercise.is_time_based and exercise.result_type == ResultType.ASAP_TIME:
            leaderboard_query = leaderboard_query.order_by(
                func.max(UserProfileResult.result_value).asc()
            )
        # For weight, reps, distance, capacity and calories, best result is the highest
        # Also for time based but with result type STM_TIME and not ASAP_TIME
        else:
            leaderboard_query = leaderboard_query.order_by(
                func.max(UserProfileResult.result_value).desc()
            )
        leaderboard_result: Result = await session.execute(leaderboard_query)
        leaderboard_rows = leaderboard_result.all()
        results = []
        for position, row in enumerate(leaderboard_rows, 1):
            user_name = f"{row.first_name or ''} {row.last_name or ''}".strip()
            user_data = {
                "position": position,
                "user_id": row.user_id,
                "user_name": user_name,
                "username": row.username,
                "gender": row.gender.value if row.gender else None,
                "level": row.level.value if row.level else None,
                "value": row.best_result,
                "unit": exercise.unit.value,
                "latest_date": row.latest_date.strftime("%d.%m.%Y") if row.latest_date else None,
            }
            results.append(user_data)
        await time_format_for_time_based_exercise(
            exercise=exercise,
            history_data=results,
        )

        logger.debug(f"Leaderboard for exercise {exercise_id}: {len(results)} results")
        return results

    @classmethod
    async def get_user_ranking(cls, session: AsyncSession, user_id: int, exercise_id: int) -> dict:
        """
        Get a specific user's ranking for an exercise.

        Args:
            session: Database session
            user_id: User's Telegram ID
            exercise_id: Exercise ID

        Returns:
            Dictionary with user's ranking information or None if no result
        """
        try:
            exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none_by_id(
                data_id=exercise_id, session=session
            )
            if not exercise:
                logger.warning(f"Exercise with ID {exercise_id} not found")
                return None

            user: User = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                return None

            # Get the user's best result
            user_result_query = select(
                func.max(UserProfileResult.result_value).label("best_result"),
                func.max(UserProfileResult.date).label("latest_date"),
            ).where(
                UserProfileResult.user_id == user_id, UserProfileResult.exercise_id == exercise_id
            )
            user_result = await session.execute(user_result_query)
            user_best = user_result.first()

            if not user_best or user_best.best_result is None:
                logger.info(f"No results for user {user_id} and exercise {exercise_id}")
                return None

            # Count total participants
            total_users_query = (
                select(func.count(func.distinct(UserProfileResult.user_id)))
                .join(User, UserProfileResult.user_id == User.telegram_id)
                .where(UserProfileResult.exercise_id == exercise_id, User.gender == user.gender)
            )
            total_users_result = await session.execute(total_users_query)
            total_users = total_users_result.scalar() or 0

            # Count better results directly without using subqueries
            if exercise.is_time_based and exercise.result_type == ResultType.ASAP_TIME:
                # For time-based (lower is better)
                better_count_query = (
                    select(func.count(func.distinct(UserProfileResult.user_id)))
                    .join(User, UserProfileResult.user_id == User.telegram_id)
                    .where(
                        UserProfileResult.exercise_id == exercise_id,
                        User.gender == user.gender,
                        # Get users with better times (smaller values)
                        UserProfileResult.result_value < user_best.best_result,
                    )
                )
            else:
                # For all other types (higher is better)
                better_count_query = (
                    select(func.count(func.distinct(UserProfileResult.user_id)))
                    .join(User, UserProfileResult.user_id == User.telegram_id)
                    .where(
                        UserProfileResult.exercise_id == exercise_id,
                        User.gender == user.gender,
                        # Get users with better results (larger values)
                        UserProfileResult.result_value > user_best.best_result,
                    )
                )

            better_count_result = await session.execute(better_count_query)
            better_count = better_count_result.scalar() or 0
            position = better_count + 1

            result_data = {
                "position": position,
                "total_users": total_users,
                "user_id": user_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "gender": user.gender.value,
                "level": user.level.value,
                "best_result": user_best.best_result,
                "value": user_best.best_result,
                "latest_date": user_best.latest_date,
            }
            await time_format_for_time_based_exercise(
                exercise=exercise,
                history_data=[result_data],
            )
            logger.debug(f"User {user_id} ranking for exercise {exercise_id}: position {position}")
            return result_data
        except Exception as e:
            logger.error(f"Error getting user ranking for exercise {exercise_id}: {e}")
            return None
