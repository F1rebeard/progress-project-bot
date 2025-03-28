from typing import Any

from src.database.models import ProfileExercise
from src.database.models.profile import MeasurementUnit


async def calculate_total_completion(total_filled: int, total_exercises: int) -> int:
    """
    Calculate total profile completion percentage.
    """
    return int((total_filled / total_exercises) * 100) if total_exercises > 0 else 0


async def time_format_for_time_based_exercise(
    exercise: ProfileExercise,
    history_data: list[dict[str, Any]],
):
    """
    Format times appropriately if it's a time-based exercise.

    Args:
        exercise: ProfileExercise object
        history_data: List of dictionaries containing data about user's results
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
