import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.constants.sinkler_coefficients import COEFFICIENT_BASE_EXERCISES
from src.dao import ProfileExerciseDAO, UserDAO, UserProfileResultDAO
from src.database.models import ProfileExercise, User, UserProfileResult
from src.schemas.coefficent import CoefficientData, ExerciseNameFilter

logger = logging.getLogger(__name__)


async def get_coefficient_data(
    session: AsyncSession,
    user_id: int,
    exercise_id: int,
) -> tuple[CoefficientData, bool, str] | None:
    """
    Get all necessary data for coefficient calculation in one database call.

    Args:
        session: Database session
        user_id: User's telegram id
        exercise_id: Coefficient exercise id

    Returns:
        Tuple of (data, ready, message)
    """
    data = CoefficientData()

    user: User = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
    if not user or not user.biometrics or not user.biometrics.weight:
        return data, False, "Для расчёта коэффициента необходимо указать весь тела в биометрии"

    data.user = user
    data.weight = user.biometrics.weight

    coefficient_exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none_by_id(
        data_id=exercise_id,
        session=session,
    )
    data.coefficient_exercise = coefficient_exercise
    if not coefficient_exercise:
        return data, False, "Упражнение не найдено"

    base_exercise_name = COEFFICIENT_BASE_EXERCISES.get(coefficient_exercise.name)
    if not base_exercise_name:
        return data, False, f"Силовое упражнение для {coefficient_exercise.name} не задано!"

    filter_model = ExerciseNameFilter(name=base_exercise_name)
    base_exercise: ProfileExercise = await ProfileExerciseDAO.find_one_or_none(
        session=session,
        filters=filter_model,
    )
    data.base_exercise = base_exercise
    if not base_exercise:
        return data, False, f"Базовое упражнение {base_exercise.name} нету в базе данных"

    base_result: UserProfileResult = await UserProfileResultDAO.get_latest_result(
        session=session,
        user_id=user_id,
        exercise_id=base_exercise.id,
    )
    if not base_result:
        return data, False, f"Сперва необходимо указать результат для {base_exercise.name}"

    user_weight = float(user.biometrics.weight)
    base_value = float(base_result.result_value)
    if "подвесом" in coefficient_exercise.name.lower():
        weight = (base_value + user_weight) * 0.7 - user_weight
        weight = max(weight, 0)
    else:
        weight = base_value * 0.7
    data.workout_weight = weight

    return data, True, "Готово к расчёту коэффициента" if data.is_complete() else None


def calculate_coefficient_value(data: CoefficientData, reps: int) -> float:
    """
    Calculate coefficient value using collected data.
    Args:
        data: Coefficient data containing all necessary information
        reps: Number or repetitions

    Returns:
        Calculated coefficient value
    """
    print("some data", data)
    coefficient_exercise = data.coefficient_exercise
    workout_weight = data.workout_weight
    user_weight = float(data.weight)
    if "подвесом" in coefficient_exercise.name.lower():
        if workout_weight == 0:
            coefficient = reps
        else:
            coefficient = reps * workout_weight
    else:
        coefficient = reps * workout_weight / user_weight

    logger.info(f"Coefficient value: {coefficient}")
    return round(coefficient, 2)
