import logging
from typing import Any

from src.database.models import ProfileExercise, UserProfileResult
from src.database.models.profile import MeasurementUnit

logger = logging.getLogger(__name__)


async def calculate_total_completion(total_filled: int, total_exercises: int) -> int:
    """
    Calculate total profile completion percentage.
    """
    return int((total_filled / total_exercises) * 100) if total_exercises > 0 else 0


async def time_format_for_time_based_exercise(
    exercise: ProfileExercise,
    history_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Format times appropriately if it's a time-based exercise.
    Also ensure all items have a formatted_value field.

    Args:
        exercise: ProfileExercise object
        history_data: List of dictionaries containing data about user's results

    Returns:
        List of dictionaries with formatted_value field
    """
    if exercise.is_time_based:
        for item in history_data:
            time_value = item["value"]
            if exercise.unit == MeasurementUnit.SECONDS:
                # Convert seconds to MM:SS format
                minutes = int(time_value) // 60
                seconds = int(time_value) % 60
                item["formatted_value"] = f"{minutes}:{seconds:02d}"
            elif exercise.unit == MeasurementUnit.MINUTES:
                # Keep minutes as is
                item["formatted_value"] = f"{time_value:.2f}"
    else:
        for item in history_data:
            if isinstance(item["value"], float) and float(item["value"]).is_integer():
                item["formatted_value"] = str(int(item["value"]))
            else:
                item["formatted_value"] = str(item["value"])
    return history_data


async def format_result_value(result: UserProfileResult) -> float | int:
    """
    Format the result value by truncating it to an integer if it is a float that is an integer.
    Otherwise, leave it as is.

    Args:
        result: UserProfileResult object

    Returns:
        The formatted result value as either a float or an int
    """
    if isinstance(result.result_value, float) and float(result.result_value).is_integer():
        return int(result.result_value)
    return result.result_value
