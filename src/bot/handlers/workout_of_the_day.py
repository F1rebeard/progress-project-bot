import logging
from datetime import datetime, timedelta

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.handlers.workout_calendar import extract_protocol_number
from src.bot.keyboards.main_menu import get_main_menu_button
from src.constants.warm_ups import DEFAULT_WARMUP, WARMUPS
from src.dao import UserDAO, WorkoutDAO
from src.database.config import connection

logger = logging.getLogger(__name__)

workout_of_the_day_router = Router()


@workout_of_the_day_router.callback_query(F.data.startswith("show_warmup_wod:"))
async def show_warmup_for_workout(callback: CallbackQuery):
    """
    Shows the warmup protocol for the current workout.
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


@workout_of_the_day_router.callback_query(F.data == "workout_of_the_day")
@connection(commit=False)
async def show_workout_of_the_day(callback: CallbackQuery, session: AsyncSession):
    """
    Show the today's workout if available, or next scheduled workout.
    """
    user_id = callback.from_user.id
    user = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
    if not user:
        logger.error(f"User with id {user_id} not found")
        await callback.message.edit_text(
            "Пожалуйста, завершите регистрацию или обратитесь к администратору.",
            reply_markup=get_main_menu_button(),
        )
        return
    # Check subscription status
    # TODO UNFREEZE BUTTON
    if not user.subscription or user.subscription.status.value in ["Истекла", "Заморожена"]:
        subscription_status = (
            "истекла"
            if not user.subscription or user.subscription.status.value == "Истекла"
            else "заморожена"
        )
        await callback.message.edit_text(
            f"⚠️ Ваша подписка {subscription_status}. "
            "Для доступа к тренировкам необходимо обновить или разморозить подписку.",
            reply_markup=get_main_menu_button(),
        )
        return

    today = datetime.now().date()
    workout = await WorkoutDAO.get_workout_for_date(
        session=session,
        workout_date=today,
        level=user.level,
    )
    if not workout:
        # Check for next workout in next 3 days:
        for days_ahead in range(1, 4):
            next_date = today + timedelta(days=days_ahead)
            next_workout = await WorkoutDAO.get_workout_for_date(
                session=session,
                workout_date=next_date,
                level=user.level,
            )
            if next_workout:
                workout = next_workout
                break
    # Case if it's weekend and no new workouts for next week yet
    if not workout:
        await callback.message.edit_text(
            "🔍 К сожалению на ближайшие 3 дня нет запланированных тренировок"
            " или их ещё не добавили в меня",
            reply_markup=get_main_menu_button(),
        )
        return

    is_today: bool = workout.date == today
    workout_date = workout.date.strftime("%d.%m.%Y")
    date_text = f"Сегодня {workout_date}" if is_today else f"{workout_date}"

    protocol_number = extract_protocol_number(workout.description)
    protocol_num_in_txt = str(protocol_number) if protocol_number else "0"
    workout_id = str(workout.id)
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
    message_text = f"🏋️‍♂️ <b>{date_text}</b>\n\n{workout.description}"

    await callback.message.edit_text(
        message_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
