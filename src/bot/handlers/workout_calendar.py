import re
from datetime import date, datetime, timedelta
from typing import Any

from aiogram import F, Router
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Back, Button, Calendar
from aiogram_dialog.widgets.kbd.calendar_kbd import (
    CalendarConfig,
    CalendarDaysView,
    CalendarMonthView,
    CalendarScope,
    CalendarScopeView,
    CalendarUserConfig,
    CalendarYearsView,
)
from aiogram_dialog.widgets.text import Const, Format, Text
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import ActiveSubscriptionFilter
from src.bot.handlers.main_menu import show_main_menu
from src.constants.warm_ups import DEFAULT_WARMUP, WARMUPS
from src.dao import StartWorkoutDAO, UserDAO, WorkoutDAO, UserSettingDAO
from src.database.config import connection
from src.database.models import User, Workout
from src.database.models.subscription import SubscriptionType

workout_calendar_router = Router()


class WorkoutCalendarSG(StatesGroup):
    calendar = State()
    workout_details = State()
    warmup_details = State()


class WorkoutDateText(Text):
    """
    Show the user's chosen workout-day emoji, or the day the number.
    """
    async def _render_text(self, data: dict[str, Any], manager: DialogManager) -> str:
        if data["date"] in data["data"].get("workout_dates", []):
            return data["workout_day_emoji"]
        return f"{data['date'].day}"


class WorkoutTodayText(Text):
    """
    Show the user's chosen ‘today’ icon depending on whether
    there's a workout today.
    """
    async def _render_text(self, data: dict[str, Any], manager: DialogManager) -> str:
        if data["date"] in data["data"].get("workout_dates", []):
            return data["today_with_workout_emoji"]
        return data["today_without_workout_emoji"]


class HeaderText(Text):
    """
    Rendering months up top and buttons.
    """

    async def _render_text(self, data: dict[str, Any], manager: DialogManager) -> str:
        month_names = [
            "Январь",
            "Февраль",
            "Март",
            "Апрель",
            "Май",
            "Июнь",
            "Июль",
            "Август",
            "Сентябрь",
            "Октябрь",
            "Ноябрь",
            "Декабрь",
        ]
        month_name = month_names[data["date"].month - 1]
        return f"{month_name} {data['date'].year}"


class CustomCalendar(Calendar):
    """
    Refactoring default calendar for custom view.
    """

    async def _get_user_config(self, data, manager: DialogManager) -> CalendarUserConfig:
        """
        Override to customize user config.
        """
        return CalendarUserConfig(firstweekday=0)

    def _init_views(self) -> dict[CalendarScope, CalendarScopeView]:
        """
        Override to customize calendar views.
        """
        # Using custom text for days view to mark workout days
        return {
            CalendarScope.DAYS: CalendarDaysView(
                self._item_callback_data,
                date_text=WorkoutDateText(),
                today_text=WorkoutTodayText(),
                header_text=HeaderText(),
            ),
            CalendarScope.MONTHS: CalendarMonthView(
                self._item_callback_data,
            ),
            CalendarScope.YEARS: CalendarYearsView(
                self._item_callback_data,
            ),
        }


@workout_calendar_router.callback_query(
    F.data == "workouts",
    ActiveSubscriptionFilter(silent=False)
)
async def show_workout_calendar(callback: CallbackQuery, dialog_manager: DialogManager):

    await dialog_manager.start(WorkoutCalendarSG.calendar)


async def on_date_selected(
    callback: CallbackQuery, widget, dialog_manager: DialogManager, selected_date: datetime.date
):
    """ """
    user_id = callback.from_user.id
    session = dialog_manager.middleware_data.get("session_without_commit")
    user: User | None = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)

    if not user:
        await callback.answer("Ошибка получения данных пользователя")
        return

    is_start_program = user.subscription and user.subscription.subscription_type in [
        SubscriptionType.START_PROGRAM,
        SubscriptionType.ONE_MONTH_START,
    ]
    if is_start_program and user.subscription.start_program_begin_date:
        start_date = user.subscription.start_program_begin_date
        day_number = (selected_date - start_date).days + 1
        if day_number > 0:
            start_workout = await StartWorkoutDAO.get_workout_by_day(session, day_number)
            if start_workout:
                dialog_manager.dialog_data["start_workout"] = start_workout
                dialog_manager.dialog_data["selected_date"] = selected_date
                dialog_manager.dialog_data["start_program_day"] = day_number
                dialog_manager.dialog_data["is_start_program"] = True
                await dialog_manager.switch_to(WorkoutCalendarSG.workout_details)
                return

    # Get workout for this date and user's level
    workout: Workout | None = await WorkoutDAO.get_workout_for_date(
        session=session, workout_date=selected_date, level=user.level
    )

    if workout:
        dialog_manager.dialog_data["selected_date"] = selected_date
        await dialog_manager.switch_to(WorkoutCalendarSG.workout_details)
    else:
        # No workout for this date, show message but stay on calendar
        await callback.answer(
            f"На {selected_date.strftime('%d.%m.%Y')} нет тренировки", show_alert=True
        )


async def go_to_main_menu(callback: CallbackQuery, button, dialog_manager: DialogManager):
    await dialog_manager.done()
    menu_text = await show_main_menu(callback.from_user.id)
    from src.bot.keyboards.main_menu import get_main_menu_keyboard

    await callback.message.edit_text(text=menu_text, reply_markup=get_main_menu_keyboard())

@connection(commit=False)
async def get_calendar_data(dialog_manager: DialogManager, session: AsyncSession, **kwargs) -> dict:
    """
    Getting data for current users available workouts according to his subscription date range.
    The date range is 2 weeks before today and till the subscription last day.

    Also getting the data for START workouts with the same date range.
    """
    user_id = dialog_manager.event.from_user.id
    user = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
    if not user or not user.subscription:
        return {}

    today = datetime.now().date()
    subscription_end = user.subscription.end_date
    two_weeks_ago = today - timedelta(days=14)

    workouts = await WorkoutDAO.get_workouts_by_date_range(
        session=session, level=user.level, start_date=two_weeks_ago, end_date=subscription_end
    )

    # Create the list of dates with workouts
    workout_dates = [w.date for w in workouts]

    # Custom emojis for user calendar
    setting = await UserSettingDAO.get_for_user(user_id=user_id, session=session)

    # Workout for START program
    is_start_program = user.subscription.subscription_type in [
        SubscriptionType.START_PROGRAM,
        SubscriptionType.ONE_MONTH_START,
    ]
    if is_start_program and user.subscription.start_program_begin_date:
        start_date: date = user.subscription.start_program_begin_date
        start_program_workout_days = await StartWorkoutDAO.get_workout_days(session)
        for day_number in start_program_workout_days:
            workout_date: date = start_date + timedelta(days=day_number - 1)
            if two_weeks_ago <= workout_date <= subscription_end:
                workout_dates.append(workout_date)

    return {
        "today": today,
        "workout_dates": workout_dates,
        "min_date": two_weeks_ago,
        "max_date": subscription_end,
        "calendar_emoji": setting.calendar_emoji.value,
        "workout_date_emoji": setting.workout_date_emoji.value,
        "today_with_workout_emoji": setting.today_with_workout_emoji.value,
        "today_without_workout_emoji": setting.today_without_workout_emoji.value,
    }


@connection(commit=False)
async def get_workout_details(
        dialog_manager: DialogManager,
        session: AsyncSession,
        **kwargs
) -> dict[str, Any]:
    """
    Selected workout date workout information getter.
    """
    selected_date = dialog_manager.dialog_data.get("selected_date")
    user_id = dialog_manager.event.from_user.id
    if not selected_date:
        return {"workout": None}


    is_start_program = dialog_manager.dialog_data.get("is_start_program", False)
    if is_start_program:
        start_program_day = dialog_manager.dialog_data.get("start_program_day")
        start_workout = dialog_manager.dialog_data.get("start_workout")
        if start_workout:
            return {
                "workout": start_workout,
                "is_start_program": True,
                "day_number": start_program_day,
                "date": selected_date.strftime("%d.%m.%Y"),
            }

    user: User | None = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
    if not user:
        return {"workout": None, "is_start_program": False}

    # Get a workout for this date and user's level
    workout: Workout | None = await WorkoutDAO.get_workout_for_date(
        session=session,
        workout_date=selected_date,
        level=user.level
    )
    if workout:
        dialog_manager.dialog_data["workout"] = workout
    return {
        "workout": workout,
        "is_start_program": False,
        "date": selected_date.strftime("%d.%m.%Y"),
    }


async def get_warmup_details(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    """
    Get data for a warm-up details dialog window to show it in text.
    """
    warmup_text = dialog_manager.dialog_data.get("warmup_text", DEFAULT_WARMUP)
    protocol_number = dialog_manager.dialog_data.get("protocol_number", "Unknown")
    return {
        "protocol_number": protocol_number,
        "warmup_text": warmup_text,
    }


def extract_protocol_number(workout_description: str) -> int | None:
    """
    Extract protocol number from workout description to show a proper warmup for chosen workout.
    """
    pattern = r"протокол\s+(\d+)"
    match = re.search(pattern, workout_description.lower())
    if match:
        return int(match.group(1))
    return None

async def show_warmup(
    callback: CallbackQuery,
    button: Any,
    dialog_manager: DialogManager,
):
    """
    Warm-up button click handler for both regular and START program workouts.
    """
    is_start_program = dialog_manager.dialog_data.get("is_start_program", False)
    if is_start_program:
        workout = dialog_manager.dialog_data.get("start_workout")
    else:
        workout = dialog_manager.dialog_data.get("workout")

    # Safety check to prevent the NoneType error
    if not workout or not hasattr(workout, "description"):
        await callback.answer("Не удалось найти информацию о разминке", show_alert=True)
        return

    workout_description = workout.description
    protocol_number = extract_protocol_number(workout_description)
    if not protocol_number:
        await callback.answer("В тренировке не указан протокол разминки", show_alert=True)
        warmup_text = DEFAULT_WARMUP
    else:
        warmup_text = WARMUPS.get(protocol_number, DEFAULT_WARMUP)

    dialog_manager.dialog_data["warmup_text"] = warmup_text
    dialog_manager.dialog_data["protocol_number"] = protocol_number or "Не указан"
    await dialog_manager.switch_to(WorkoutCalendarSG.warmup_details)


workout_calendar_dialog = Dialog(
    Window(
        Format("{calendar_emoji} <b>Календарь тренировок</b>"),
        Const("Выберите дату, чтобы увидеть тренировку:"),
        CustomCalendar(
            id="workout_calendar",
            on_click=on_date_selected,
            config=CalendarConfig(
                min_date=datetime(1900, 1, 1).date(),
                max_date=datetime(2100, 12, 31).date(),
            ),
        ),
        Button(Const("В главное меню"), id="to_main_menu", on_click=go_to_main_menu),
        state=WorkoutCalendarSG.calendar,
        getter=get_calendar_data,
    ),
    Window(
        Const("🏋️ Детали тренировки\n\n"),
        Format("Дата: {date}\n"),
        Format("<b>День {day_number} программы СТАРТ</b>\n", when="is_start_program"),
        Format(
            "{workout.hashtag}\n",
            when=lambda data, *args: (
                not data.get("is_start_program", False)
                and data.get("workout") is not None
                and getattr(data.get("workout"), "hashtag", None) is not None
            ),
        ),
        Format(
            "{workout.description}",
            when=lambda data, *args: data.get("workout") is not None
            and hasattr(data.get("workout"), "description"),
        ),
        Button(Const("🔥 Подсказать с разминкой"), id="show_warmup", on_click=show_warmup),
        Back(Const("Назад к календарю")),
        Button(Const("В главное меню"), id="to_main_menu", on_click=go_to_main_menu),
        state=WorkoutCalendarSG.workout_details,
        getter=get_workout_details,
    ),
    Window(
        Const("🔥 Разминка"),
        Format("{warmup_text}"),
        Back(Const("Назад к тренировке")),
        state=WorkoutCalendarSG.warmup_details,
        getter=get_warmup_details,
    ),
)
