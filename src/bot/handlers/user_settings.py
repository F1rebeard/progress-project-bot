from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram_dialog import Dialog, Window, DialogManager, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Row, Button, Back
from aiogram_dialog.widgets.text import Const, Format
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.filters import ActiveSubscriptionFilter
from dao.settings import UserSettingDAO
from src.database.config import connection
from src.utils.emojis import CalendarEmoji

settings_router = Router()


class SettingsSG(StatesGroup):
    """
    FSM states for the user settings menu.
    """
    settings_menu = State()
    awaiting_emoji_sequence = State()


@settings_router.message.filter(ActiveSubscriptionFilter(silent=False))
@settings_router.message(Command("settings"))
async def cmd_settings(message: Message, manager: DialogManager):
    """
    Entry point for /settings command.
    Start the Setting dialog menu.
    """
    await manager.start(
        state=SettingsSG.settings_menu,
        mode=StartMode.RESET_STACK,
    )


@connection(commit=False)
async def calendar_emojis_getter(
        manager: DialogManager,
        session: AsyncSession,
        **kwargs,
) -> dict:
    """
    Reads and gets the user's current calendar emojis.
    """
    user_id = manager.event.from_user.id
    setting = await UserSettingDAO.get_for_user(user_id=user_id, session=session)
    return {
        "calendar_emoji": setting.calendar_emoji.value,
        "workout_date_emoji": setting.workout_date_emoji.value,
        "today_with_workout_emoji": setting.today_with_workout_emoji.value,
        "today_without_workout_emoji": setting.today_without_workout_emoji.value,
        "available": " ".join(CalendarEmoji.list())
    }


@connection(commit=True)
async def process_emoji_sequence(
        message: Message,
        message_input: MessageInput,
        manager: DialogManager,
        session: AsyncSession,
):
    text = message.text.strip().replace(" ", "")
    user_id = manager.event.from_user.id
    emojis: list[str] = list(text)
    if len(emojis) != 4:
        await message.answer("❌ Нужно ровно 4 эмодзи, попробуй ещё раз")
    elif len(set(emojis)) != 4:
        await message.answer("❌ Эмодзи не должны повторяться")
    invalid = (e for e in emojis if e not in CalendarEmoji.list())
    if invalid:
        await message.answer(
            f"❌ Недопустимые эмодзи: {' '.join(invalid)}\n"
            f"Допустимые эмодзи {' '.join(CalendarEmoji.list())}"
        )
    field_order = (
        "calendar_emoji",
        "workout_date_emoji",
        "today_with_workout_emoji",
        "today_without_workout_emoji",
    )
    for field, emoji in zip(field_order, emojis):
        await UserSettingDAO.set_emoji(
            user_id=user_id,
            field=field,
            emoji=emoji,
            session=session,
        )
    await message.answer("✅ Эмодзи календаря обновлены!")
    await manager.done()



user_settings_dialogs = Dialog(
    Window(
        Const("⚙️ <b>Опции и настройки<b>"),
        Row(
            Button(
                Const("📅😎 Эмоджи в календаре"),
                id="to_calendar_emojis",
                on_click=lambda callback, button, manager: manager.switch_to(SettingsSG.awaiting_emoji_sequence)
            ),
        ),
        state=SettingsSG.settings_menu
    ),
    Window(
        Format(
            "<b>Настройки эмодзи календаря</b>\n\n"
            "Текущие эмодзи:\n"
            "1. Общий календарь: {calendar_emoji}\n"
            "2. Дата тренировки: {workout_date_emoji}\n"
            "3. Сегодня (с тренировкой): {today_with_workout_emoji}\n"
            "4. Сегодня (без тренировки): {today_without_workout_emoji}\n\n"
            "✏️ Отправьте <b>4 эмодзи</b> в одном сообщении, в порядке выше.\n\n"
            "Доступно: {available}"
        ),
        MessageInput(process_emoji_sequence, content_types=["text"]),
        Back(
            Const("⬅️ Назад"),
            id="back_to_settings",
            on_click=lambda c, b, m: m.switch_to(SettingsSG.settings_menu)
        ),
        state=SettingsSG.awaiting_emoji_sequence,
        getter=calendar_emojis_getter,
    ),
)


    
