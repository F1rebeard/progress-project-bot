import logging
from datetime import datetime, timedelta
from typing import Any

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import ActiveSubscriptionFilter
from src.bot.handlers.workout_calendar import extract_protocol_number
from src.bot.keyboards.main_menu import get_main_menu_button
from src.constants.warm_ups import DEFAULT_WARMUP, WARMUPS
from src.dao import StartWorkoutDAO, UserDAO, WorkoutDAO
from src.database.config import connection
from src.database.models import User
from src.database.models.user import UserLevel
from src.utils.workout_hashtags import create_hashtag

logger = logging.getLogger(__name__)

workout_of_the_day_router = Router()


async def show_error_message(callback: CallbackQuery, message: str):
    await callback.message.edit_text(message, reply_markup=get_main_menu_button())


async def show_no_workouts_message(callback: CallbackQuery):
    """
    Show a message when no workouts are found.
    """
    await callback.message.edit_text(
        "🔍 К сожалению на ближайшие 3 дня нет запланированных тренировок"
        " или их ещё не добавили в меню",
        reply_markup=get_main_menu_button(),
    )


async def find_start_workout(
    session: AsyncSession, start_date: datetime.date, today: datetime.date
) -> dict[str, Any]:
    """
    Find a START program workout for today or in the next few days.

    Args:
        session: Database session
        start_date: When the user started the START program
        today: Current date

    Returns:
        Dictionary with workout information including
        - workout: The found START workout or None
        - day_number: The day number in the START program
        - selected_date: The date of the workout
        - is_future: Whether the workout is for a future date
    """
    result = {"workout": None, "day_number": None, "selected_date": today, "is_future": False}

    day_number = (today - start_date).days + 1
    if day_number > 0:
        start_workout = await StartWorkoutDAO.get_workout_by_day(session, day_number)
        if start_workout:
            result["workout"] = start_workout
            result["day_number"] = day_number
            return result

    for days_ahead in range(1, 4):
        future_date = today + timedelta(days=days_ahead)
        future_day_number = (future_date - start_date).days + 1
        if future_day_number > 0:
            future_workout = await StartWorkoutDAO.get_workout_by_day(session, future_day_number)
            if future_workout:
                result["workout"] = future_workout
                result["day_number"] = future_day_number
                result["selected_date"] = future_date
                result["is_future"] = True
                break

    return result


async def _find_regular_workout(
    session: AsyncSession, user: User, today: datetime.date
) -> dict[str, Any]:
    """
    Find a regular workout for today or in the next few days.
    """

    result = {"workout": None, "selected_date": today, "is_future": False}
    regular_workout = await WorkoutDAO.get_workout_for_date(
        session=session,
        workout_date=today,
        level=user.level,
    )
    if regular_workout:
        result["workout"] = regular_workout
        return result

    # If no workout for today, check next 3 days
    for days_ahead in range(1, 4):
        next_date = today + timedelta(days=days_ahead)
        next_workout = await WorkoutDAO.get_workout_for_date(
            session=session,
            workout_date=next_date,
            level=user.level,
        )
        if next_workout:
            result["workout"] = next_workout
            result["selected_date"] = next_date
            result["is_future"] = True
            break

    return result


async def find_appropriate_workout(
    session: AsyncSession, user: User, today: datetime.date
) -> dict[str, Any]:
    """
    Find the most appropriate workout for the user based on their level and subscription.

    For START program users, try to find a START workout first, then fall back to regular workouts.
    For regular users, just find a regular workout.
    """
    result = {
        "found": False,
        "is_start": False,
        "workout": None,
        "selected_date": today,
        "is_future": False,
        "day_number": None,
        "user_level": user.level,
    }

    # For START program users with a start date set, try to get START workouts
    if user.level == UserLevel.START:
        start_result = await find_start_workout(
            session, user.subscription.start_program_begin_date, today
        )
        if start_result["workout"]:
            result["found"] = True
            result["is_start"] = True
            result["workout"] = start_result["workout"]
            result["day_number"] = start_result["day_number"]
            result["selected_date"] = start_result["selected_date"]
            result["is_future"] = start_result["is_future"]
            return result

    # If no START workout found or user is not on START program, try regular workouts
    regular_result = await _find_regular_workout(session, user, today)
    if regular_result["workout"]:
        result["found"] = True
        result["workout"] = regular_result["workout"]
        result["selected_date"] = regular_result["selected_date"]
        result["is_future"] = regular_result["is_future"]

    return result


async def prepare_start_workout_message(workout_data: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare a message and buttons for a START workout.
    """

    workout_date = workout_data["selected_date"].strftime("%d.%m.%Y")
    date_text = f"Сегодня {workout_date}" if not workout_data["is_future"] else f"{workout_date}"
    day_number = workout_data["day_number"]
    start_workout = workout_data["workout"]
    hashtag = f"#старт_день_{day_number}"
    protocol_number = extract_protocol_number(start_workout.description)
    protocol_num_in_txt = str(protocol_number) if protocol_number else "0"

    # Create message text and buttons with START program information
    message_text = (
        f"🏋️‍♂️ <b>{date_text}</b>\n\n"
        f"<b>День {day_number} программы СТАРТ</b>\n"
        f"{hashtag}\n\n"
        f"{start_workout.description}"
    )
    buttons = [
        [
            InlineKeyboardButton(
                text="🔥 Подсказать с разминкой",
                callback_data=f"show_warmup_wod:start_{day_number}:{protocol_num_in_txt}",
            )
        ],
        [
            InlineKeyboardButton(text="📅 Календарь тренировок", callback_data="workouts"),
            InlineKeyboardButton(text="📱 В главное меню", callback_data="main_menu"),
        ],
    ]
    return {"message_text": message_text, "buttons": buttons}


async def prepare_regular_workout_message(workout_data: dict[str, Any]) -> dict[str, Any]:
    """
    Prepare a message and buttons for a regular workout.
    """
    workout_date = workout_data["selected_date"].strftime("%d.%m.%Y")
    date_text = f"Сегодня {workout_date}" if not workout_data["is_future"] else f"{workout_date}"
    regular_workout = workout_data["workout"]
    user_level = workout_data["user_level"]

    # Extract protocol number for warmup suggestion
    protocol_number = extract_protocol_number(regular_workout.description)
    protocol_num_in_txt = str(protocol_number) if protocol_number else "0"
    workout_id = str(regular_workout.id)
    hashtag_text = ""
    if regular_workout.hashtag:
        hashtag_text = f"\n{regular_workout.hashtag}"
    else:
        hashtag = create_hashtag(workout_data["selected_date"], user_level)
        if hashtag:
            hashtag_text = f"\n{hashtag}"

    # Create message text and buttons for regular workout
    message_text = f"🏋️‍♂️ <b>{date_text}</b>\n\n{hashtag_text}\n\n{regular_workout.description}"
    buttons = [
        [
            InlineKeyboardButton(
                text="🔥 Подсказать с разминкой",
                callback_data=f"show_warmup_wod:{workout_id}:{protocol_num_in_txt}",
            )
        ],
        [
            InlineKeyboardButton(text="📅 Календарь тренировок", callback_data="workouts"),
            InlineKeyboardButton(text="📱 В главное меню", callback_data="main_menu"),
        ],
    ]
    return {"message_text": message_text, "buttons": buttons}


async def show_workout_details(callback: CallbackQuery, workout_data: dict[str, Any]):
    """
    Display the workout details to the user.
    """
    if workout_data["is_start"]:
        message_info = await prepare_start_workout_message(workout_data)
    else:
        message_info = await prepare_regular_workout_message(workout_data)
    await callback.message.edit_text(
        message_info["message_text"],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=message_info["buttons"]),
    )


@workout_of_the_day_router.callback_query(F.data.startswith("show_warmup_wod:"))
async def show_warmup_for_workout(callback: CallbackQuery):
    """
    Shows the warmup protocol for the current workout.
    Handles both regular workouts and START program workouts.
    """
    all_data_count = 3
    data_parts = callback.data.split(":")
    if len(data_parts) != all_data_count:
        await callback.answer("Ошибка: неверный формат данных", show_alert=True)
        return

    protocol_number = int(data_parts[2]) if data_parts[2] != "0" else None
    warmup_text = (
        WARMUPS.get(protocol_number, DEFAULT_WARMUP) if protocol_number else DEFAULT_WARMUP
    )
    keyboard = [
        [InlineKeyboardButton(text="⬅️ Назад к тренировке", callback_data="workout_of_the_day")],
        [InlineKeyboardButton(text="📱 В главное меню", callback_data="main_menu")],
    ]

    await callback.message.edit_text(
        f"🔥 <b>Разминка</b>\n\n{warmup_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


@workout_of_the_day_router.callback_query(
    F.data == "workout_of_the_day",
    ActiveSubscriptionFilter(silent=False)
)
@connection(commit=False)
async def show_workout_of_the_day(callback: CallbackQuery, session: AsyncSession):
    """
    Main handler for the 'workout of the day' button.
    Shows today's workout or the next upcoming workout.
    """
    user_id = callback.from_user.id
    user: User = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
    if not user:
        logger.error(f"User with id {user_id} not found")
        await show_error_message(
            callback, "Пожалуйста, завершите регистрацию или обратитесь к администратору."
        )
        return

    today = datetime.now().date()
    workout_data = await find_appropriate_workout(session, user, today)
    if not workout_data["found"]:
        await show_no_workouts_message(callback)
        return

    await show_workout_details(callback, workout_data)
