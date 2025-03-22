from datetime import date

from src.database.models.user import UserLevel

WEEKDAYS = {
    1: "пнд",  # Monday
    2: "втр",  # Tuesday
    3: "срд",  # Wednesday
    4: "чтв",  # Thursday
    5: "пнт",  # Friday
    6: "сбт",  # Saturday
    7: "вск",  # Sunday
}

PROGRESS_LEVELS = {
    UserLevel.FIRST.value: "1",  # "Первый"
    UserLevel.SECOND.value: "2",  # "Второй"
    UserLevel.MINKAIFA.value: "МКФ",  # "Минкайфа"
    UserLevel.COMPETITION.value: "СРВ",  # "Соревнования"
    UserLevel.START.value: "старт",  # "Старт"
}


def create_hashtag(
    workout_date: date, user_level: UserLevel, start_program_day: int | None = None
) -> str:
    """
    Creates a unique hashtag for a workout.

    Args:
        workout_date (date): The date of the workout.
        user_level (UserLevel): The level of the user.
        start_program_day (int, optional): The day of the program start. Defaults to None.

    Returns:
        str: The generated hashtag.
    """
    user_tag = PROGRESS_LEVELS.get(user_level.value, "")
    if user_level == UserLevel.START and start_program_day is not None:
        hashtag = f"#{user_tag}_день_{start_program_day}"
    else:
        iso_calendar = workout_date.isocalendar()
        weekday = iso_calendar[2]  # Day of week
        week_number = iso_calendar[1]  # Week number
        year = workout_date.year
        hashtag = f"#{user_tag}_{WEEKDAYS.get(weekday, '')}_{week_number}_{year}"
    return hashtag
