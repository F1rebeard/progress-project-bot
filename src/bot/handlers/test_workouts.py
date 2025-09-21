import logging

from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, StartMode, Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.text import Format, Const
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import ActiveSubscriptionFilter
from src.bot.handlers.workout_calendar import go_to_main_menu
from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.constants.test_weeks import INSTRUCTION
from src.dao import TestWorkoutDAO
from src.database.config import connection
from src.database.models import TestWorkouts
from src.services.test_week_access import test_weeks_access

logger = logging.getLogger(__name__)

test_workouts_router = Router()


class TestWeekSG(StatesGroup):
    """
    FSM States for test weeks selection.
    """
    test_weeks = State()
    chosen_day = State()


@test_workouts_router.callback_query(F.data == "test_weeks", ActiveSubscriptionFilter(silent=False))
@connection(commit=False)
async def open_test_weeks_menu(
        callback: CallbackQuery,
        session: AsyncSession,
        manager: DialogManager
):
    """
    Handler for test week button from the main menu.
    """
    user_id = callback.from_user.id
    async with test_weeks_access() as access:
        if access.can_user_access_week(user_id=user_id, session=session):
            await manager.start(state=TestWeekSG.test_weeks, mode=StartMode.RESET_STACK)
            manager.dialog_data["test_weeks_instruction"] = INSTRUCTION
        else:
            await callback.answer(
                "Тестовая неделя в данный момент недоступна 🛑\n\n"
                "Следи за анонсами в чате, когда будем делать тесты 💪",
                show_alert=True,
                reply_markup=get_main_menu_keyboard(),
            )

@connection(commit=False)
async def test_weeks_getter(
        manager: DialogManager,
        session: AsyncSession,
        **kwargs,
) -> dict:
    workouts: list[TestWorkouts] = await TestWorkoutDAO.get_test_workouts(session=session)
    workout_days = []
    for workout in workouts:
        if "полного отдыха" in workout.description.lower():
            label = "🏝️"
        elif "Переделываем".lower() or "Доделываем".lower() in workout.description.lower():
            label = "🔁"
        else:
            label = str(workout.day_number)
        workout_days.append({"id": workout.day_number, "label": label})
    return {"workout_days": workout_days}


async def on_test_day_selected


test_weeks_dialog = Dialog(
    Window(
        Format("dialog_data[test_weeks_instruction]"),
        Select(
            Format("{{item[label]}"),
            items="workout_days",
            item_id_getter=lambda workout_days: workout_days["id"],
            id="test_weeks",
        ),
        Button(Const("В главное меню"), id="to_main_menu", on_click=go_to_main_menu),
        state=TestWeekSG.test_weeks,
        getter=test_weeks_getter,
    ),
)