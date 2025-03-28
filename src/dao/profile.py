import logging
from typing import Any

from sqlalchemy import Result, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import BaseDAO, UserDAO
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
            select(func.count(func.distnct(UserProfileResult.id)))
            .join(ProfileExercise, UserProfileResult.exercise_id == ProfileExercise.id)
            .where(
                (UserProfileResult.user_id == user_id)
                & (ProfileExercise.category_name == category_name)
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none() if result else 0

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
        logger.debug(
            f"History for exercise {exercise_id} for user {user_id}: {result.scalars().all()}"
        )
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
                User.gender,
                User.level,
                func.max(UserProfileResult.result_value).label("best_result"),
                func.max(UserProfileResult.date).label("latest_date"),
            )
            .join(User, UserProfileResult.user_id == User.telegram_id)
            .where(UserProfileResult.exercise_id == exercise_id)
            .group_by(
                UserProfileResult.user_id,
                User.first_name,
                User.last_name,
                User.gender,
                User.level,
            )
        )
        # Filtering by gender
        leaderboard_query = leaderboard_query.where(User.gender == gender)

        # Time based as fast as possible to finish
        if exercise.is_time_based and exercise.result_type == ResultType.ASAP_TIME:
            leaderboard_query = leaderboard_query.order_by(
                func.max(UserProfileResult.result_value.asc())
            )
        # For weight, reps, distance, capacity and calories, best result is the highest
        # Also for time based but with result type STM_TIME and not ASAP_TIME
        else:
            leaderboard_query = leaderboard_query.order_by(
                func.max(UserProfileResult.result_value.desc())
            )
        leaderboard_result: Result = await session.execute(leaderboard_query)
        leaderboard = leaderboard_result.all()
        results = []
        for position, row in enumerate(leaderboard, 1):
            user_data = {
                "position": position,
                "user_id": row.user_id,
                "first_name": row.first_name,
                "last_name": row.last_name,
                "gender": row.gender,
                "level": row.level,
                "best_result": row.best_result,
                "value": row.best_result,  # Adding this for time_format_for_time_based_exercise
                "latest_date": row.latest_date,
            }
            results.append(user_data)
        if exercise.is_time_based:
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
        exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none_by_id(
            data_id=exercise_id, session=session
        )
        if not exercise:
            return {"exercise": None, "results": []}

        user: User = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
        if not user:
            return {"exercise": exercise, "results": None}

        user_result_query: Select = select(
            func.max(UserProfileResult.result_value).label("best_result"),
            func.max(UserProfileResult.date).label("latest_date"),
        ).where(UserProfileResult.user_id == user_id, UserProfileResult.exercise_id == exercise_id)
        user_result: Result = await session.execute(user_result_query)
        user_best = user_result.first()
        if not user_best or not user_best.best_result:
            return {"exercise": exercise, "results": None}

        # Count users with the better result to get the ranking for current user
        better_results_query: Select = select(func.count()).select_from(
            select(
                UserProfileResult.user_id, func.max(UserProfileResult.result_value).label("best")
            )
            .join(User, UserProfileResult.user_id == User.telegram_id)
            .where(UserProfileResult.exercise_id == exercise_id, User.gender == user.gender)
            .group_by(UserProfileResult.user_id)
            .subquery()
        )
        # Apply the correct comparison based on the exercise type
        if exercise.is_time_based and exercise.result_type == ResultType.ASAP_TIME:
            better_results_query = better_results_query.where(
                better_results_query.c.best < user_best.best_result
            )
        else:
            better_results_query = better_results_query.where(
                better_results_query.c.best > user_best.best_result
            )
        better_count_result = await session.execute(better_results_query)
        better_count = better_count_result.scalar() or 0
        position = better_count + 1

        total_users_query = (
            select(func.count(func.distinct(UserProfileResult.user_id)))
            .join(User, UserProfileResult.user_id == User.telegram_id)
            .where(UserProfileResult.exercise_id == exercise_id, User.gender == user.gender)
        )
        total_users_result = await session.execute(total_users_query)
        total_users = total_users_result.scalar() or 0

        result_data = {
            "position": position,
            "total_users": total_users,
            "user_id": user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "gender": user.gender,
            "level": user.level,
            "best_result": user_best.best_result,
            "value": user_best.best_result,  # Adding this for time_format_for_time_based_exercise
            "latest_date": user_best.latest_date,
        }
        if exercise.is_time_based:
            await time_format_for_time_based_exercise(
                exercise=exercise,
                history_data=[result_data],
            )
        logger.debug(f"User {user_id} ranking for exercise {exercise_id}: position {position}")
        return result_data
