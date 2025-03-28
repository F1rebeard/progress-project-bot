import logging
from typing import Any

from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from sqlalchemy.ext.asyncio import AsyncSession

from src.dao import (
    ProfileCategoryDAO,
    ProfileExerciseDAO,
    UserDAO,
    UserProfileResultDAO,
)
from src.database.config import connection
from src.database.models import ProfileCategory, ProfileExercise, User, UserProfileResult
from src.utils.profile import calculate_total_completion, time_format_for_time_based_exercise

logger = logging.getLogger(__name__)

profile_router = Router()

CATEGORY_PREFIX = "profile_cat:"
EXERCISE_PREFIX = "profile_ex:"
LEADERBOARD_PREFIX = "leaderboard:"


class ProfileSG(StatesGroup):
    profiles = State()
    category = State()
    exercise = State()
    add_result = State()
    biometrics = State()
    leaderboard = State()
    # TODO delete and edit for ADMIN


@profile_router.callback_query(F.data == "profile")
async def open_profile_menu(callback: CallbackQuery, dialog_manager: DialogManager):
    """
    Open profile menu on clicking profile button in main menu.
    """
    await dialog_manager.start(state=ProfileSG.profiles)


async def get_category_completion_for_user(
    session: AsyncSession,
    user_id: int,
    category: ProfileCategory,
) -> dict[str, Any] | None:
    """
    Calculate completion percentage for a single category for current user.

    Args:
        session: Database session
        user_id: User's telegram ID
        category: Category object from database

    Returns:
        Tuple of (completion_data, filled_count, exercises_count)
    """
    total_exercises_in_cat = len(category.exercises)
    if total_exercises_in_cat == 0:
        logger.debug(f"Category {category.name} has no exercises")
        return None
    count_filled_exercises = await UserProfileResultDAO.count_results_in_category(
        session=session,
        user_id=user_id,
        category_name=category.name,
    )
    completion_percentage = (
        int((count_filled_exercises / total_exercises_in_cat) * 100)
        if count_filled_exercises > 0
        else 0
    )
    category_completion_data = {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "exercises_count": total_exercises_in_cat,
        "filled_count": count_filled_exercises,
        "percentage": completion_percentage,
    }
    logger.debug(f"Category {category.name} completion data: {category_completion_data}")
    return category_completion_data


@connection(commit=False)
async def get_profile_categories(
    dialog_manager: DialogManager, session: AsyncSession, **kwargs
) -> dict[str, Any]:
    """
    Get all profile categories and calculate completion percentages.

    Args:
        dialog_manager: Dialog manager
        session: Database session

    Returns:
        Dictionary of category completion data.
    """
    user_id = dialog_manager.event.from_user.id
    categories = await ProfileCategoryDAO.find_all(session=session, filters=None)
    total_filled = 0
    total_exercises = 0
    total_data = []
    for category in categories:
        category_completion_data = await get_category_completion_for_user(
            session=session,
            user_id=user_id,
            category=category,
        )
        if category_completion_data:
            total_data.append(category_completion_data)
            total_filled += category_completion_data.get("filled_count", 0)
            total_exercises += category_completion_data.get("exercises_count", 0)

    biometrics_data = await UserDAO.get_user_biometrics(session=session, user_id=user_id)
    total_complete_percentage = await calculate_total_completion(
        total_filled=total_filled,
        total_exercises=total_exercises,
    )
    profile_data: dict = {
        "categories": total_data,
        "biometrics": biometrics_data,
        "total_complete_percentage": total_complete_percentage,
        "total_exercises": total_exercises,
        "total_filled": total_filled,
    }
    logger.debug(f"Profile data: {profile_data} for user {user_id}")
    return profile_data


@connection(commit=False)
async def get_exercises_for_category(
    dialog_manager: DialogManager, session: AsyncSession, **kwargs
):
    """
    Get all exercises for the selected category with current user results.

    Args:
        dialog_manager: Dialog manager
        session: Database session

    Returns:
        Dictionary of exercises data for the selected category.
    """

    user_id = dialog_manager.event.from_user.id
    category_id = dialog_manager.dialog_data.get("selected_category_id")

    if not category_id:
        return {"exercises": [], "category_name": "Нету id категории"}

    category: ProfileCategory = await ProfileCategoryDAO.find_one_or_none_by_id(
        data_id=category_id, session=session
    )
    if not category:
        return {"exercises": [], "category_name": f"Категория c id {category_id} не найдена!"}

    exercises_data = []
    for exercise in category.exercises:
        latest_result = await UserProfileResultDAO.get_latest_result(
            session=session,
            user_id=user_id,
            exercise_id=exercise.id,
        )
        exercises_data.append(
            {
                "id": exercise.id,
                "name": exercise.name,
                "has_result": latest_result is not None,
                "result_value": latest_result.result_value if latest_result else None,
                "unit": exercise.unit,
            }
        )
    category_data = {
        "exercises": exercises_data,
        "category_name": category.name,
        "description": category.description,
    }
    logger.debug(f"Category {category.name} data: {category_data}")
    return category_data


@connection(commit=False)
async def get_exercise_history(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    """
    Get details and history for a specific exercise.

    Args:
        dialog_manager: Dialog manager
        session: Database session

    Returns:
        Dictionary of exercise details and history.
    """
    user_id = dialog_manager.event.from_user.id
    exercise_id = dialog_manager.dialog_data.get("selected_exercise_id")
    if not exercise_id:
        return {"exercise": None, "results": []}

    exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none_by_id(
        data_id=exercise_id, session=session
    )
    if not exercise:
        return {"exercise": None, "results": []}

    history: list[UserProfileResult] = await UserProfileResultDAO.get_history_for_exercise(
        session=session,
        user_id=user_id,
        exercise_id=exercise_id,
    )
    history_data = [
        {
            "date": result.date.strftime("%d.%m.%Y"),
            "value": result.result_value,
            "unit": exercise.unit,
        }
        for result in history
    ]
    # TODO WHAT ABOUT AN HOUR?
    await time_format_for_time_based_exercise(
        history_data=history_data,
        exercise=exercise,
    )
    exercise_data = {
        "exercise": {
            "id": exercise.id,
            "name": exercise.name,
            "description": exercise.description,
            "unit": exercise.unit,
            "result_type": exercise.result_type,
            "is_time_based": exercise.is_time_based,
            "category": exercise.category_name,
        },
        "results": history_data,
    }
    logger.debug(f"Exercise {exercise.name} for user {user_id} with history: {history_data}")
    return exercise_data


@connection(commit=False)
async def get_exercise_leaderboard(dialog_manager: DialogManager, session: AsyncSession, **kwargs):
    """
    Get leaderboard data for a specific exercise.

    Args:
        dialog_manager: Dialog manager
        session: Database session

    Returns:
        Dictionary of leaderboard data.
    """
    exercise_id = dialog_manager.dialog_data.get("selected_exercise_id")
    user_id = dialog_manager.event.from_user.id
    exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none_by_id(
        data_id=exercise_id, session=session
    )
    if not exercise:
        return {"exercise": None, "leaderboard": [], "user_ranking": None}

    user: User = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
    if not user or not user.gender:
        return {"exercise": exercise, "leaderboard": [], "user_ranking": None}
