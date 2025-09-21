from datetime import date, timedelta


def calculate_start_program_day(start_program_begin_date: date, workout_date: date) -> int:
    """
    Calculate which day in the START program a specific date corresponds to.

    Args:
        start_program_begin_date: The date when the START program begins (usually a Monday)
        workout_date: The date of the workout

    Returns:
        The day number in the START program (1-based)
    """
    return max((workout_date - start_program_begin_date).days + 1, 1)


def calculate_next_monday() -> date:
    """
    Calculate the next Monday after the current date, if today is not Monday already.

    Returns:
        The date of the next Monday.
    """
    days_in_week = 7
    today = date.today()
    return today + timedelta(days=days_in_week - today.weekday()) if today.weekday() != 0 else today
