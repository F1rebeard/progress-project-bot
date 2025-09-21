from typing import Any

from aiogram import Router, F
from aiogram.enums import ContentType
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, Window, Dialog, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Row, Back, Cancel, Select, Button
from aiogram_dialog.widgets.text import Const, Format
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.config import connection
from src.database.models.user import Gender, UserLevel
from src.services.registration.controller import RegistrationService
from src.services.registration.validation import FirstNameSchema, LastNameSchema, EmailSchema, \
    BirthdaySchema, HeightSchema, WeightSchema
from src.bot.handlers.utils import other_type_handler, on_select_clicked


registration_router = Router()

@registration_router.callback_query(F.data == "to_registration")
async def start_registration(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
):
    logger.debug(f"start_registration called with manager: {dialog_manager}")
    await dialog_manager.start(state=RegistrationSG.first_name, mode=StartMode.RESET_STACK)


class RegistrationSG(StatesGroup):
    first_name = State()
    last_name = State()
    email = State()
    level = State()
    gender = State()
    birthday = State()
    height = State()
    weight = State()
    confirm = State()


async def generic_input_handler(
        message: Message,
        widget: MessageInput,
        manager: DialogManager,
        schema_class: BaseModel,
        key: str,
):
    try:
        validated = schema_class.model_validate({key: message.text})
        manager.dialog_data[key] = getattr(validated, key)
        await manager.next()
    except Exception as e:
        logger.error(str(e))
        await message.answer(str(e))


def make_window(
        state: State,
        schema_class: BaseModel,
        key: str,
        prompt: str,
):
    """

    """
    return Window(
        Const(prompt),
        MessageInput(
            lambda m, w, mngr: generic_input_handler(m, w, mngr, schema_class, key),
            content_types=[ContentType.TEXT]),
        MessageInput(other_type_handler),
        Row(Back(Const("Назад")), Cancel(Const("Отмена"))),
        state=state,
    )


def make_select_window(
        state: State,
        prompt: str,
        key: str,
        options: list[tuple[str, str]],
):
    return Window(
        Const(prompt),
        Select(
            text=Format("{item[0]}"),
            items=options,
            item_id_getter=lambda item: item[1],
            id=key,
            on_click=on_select_clicked,
        ),
        Row(Back(Const("Назад")), Cancel(Const("Отмена"))),
        state=state,
    )

@connection(commit=True)
async def finish_registration(
        callback: CallbackQuery,
        button: Any,
        manager: DialogManager,
        session: AsyncSession,
):
    data = manager.dialog_data
    telegram_id = manager.event.from_user.id
    username = manager.event.from_user.username

    service = RegistrationService(session)
    await service.update_user_profile(
        telegram_id=telegram_id,
        username=username,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        email=data.get("email"),
        gender=data.get("gender"),
        level=data.get("level"),
        height=data.get("height"),
        weight=data.get("weight"),
        birthday=data.get("birthday"),
    )
    await manager.done()


async def confirm_registration_getter(manager: DialogManager, **kwargs):
    d = manager.dialog_data
    return {
        "info": (
            f"Имя: {d.get('first_name')}\n"
            f"Фамилия: {d.get('last_name')}\n"
            f"Email: {d.get('email')}\n"
            f"Пол: {d.get('gender')}\n"
            f"Уровень: {d.get('level')}\n"
            f"Дата рождения: {d.get('birthday')}\n"
            f"Рост: {d.get('height')}\n"
            f"Вес: {d.get('weight')}"
        )
    }

registration_dialog = Dialog(
    make_window(RegistrationSG.first_name, FirstNameSchema, "first_name", "✍ Введи своё имя"),
    make_window(RegistrationSG.last_name, LastNameSchema, "last_name", "✍ Введи фамилию"),
    make_window(RegistrationSG.email, EmailSchema, "email", "✍ Введи email"),
    make_select_window(
        RegistrationSG.gender,
        "🚻 Укажи пол",
        "gender",
        [(g.value, g.value) for g in Gender]
    ),
    make_select_window(
        RegistrationSG.level,
        "🧗 Уровень тренировок",
        "level",
        [(l.value, l.value) for l in UserLevel]
    ),
    make_window(RegistrationSG.birthday, BirthdaySchema, "birthday", "🎂 Дата рождения (ДД.ММ.ГГГГ)"),
    make_window(RegistrationSG.height, HeightSchema, "height", "📏 Рост (в см)"),
    make_window(RegistrationSG.weight, WeightSchema, "weight", "⚖️ Вес (в кг)"),
    Window(
        Format("📋 Проверь введённые данные:\n\n{info}"),
        Row(
            Button(Const("✅ Подтвердить"), id="confirm", on_click=finish_registration),
            Button(Const("🔄 Назад"), id="back", on_click=lambda c, b, m: m.back())
        ),
        state=RegistrationSG.confirm,
        getter=confirm_registration_getter,
    ),
)

