import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any

from aiogram import F, Router
from aiogram.enums import ContentType
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Column, Row, Select
from aiogram_dialog.widgets.text import Const, Format, Multi
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.main_menu import get_main_menu_button
from src.dao import BiometricDAO, SubscriptionDAO, UserDAO
from src.database.config import connection
from src.database.models import Subscription
from src.database.models.subscription import SubscriptionStatus
from src.database.models.user import Gender, UserLevel
from src.schemas import BiometricCreateSchema, UserUpdateSchema

logger = logging.getLogger(__name__)

registration_router = Router()


class RegistrationSG(StatesGroup):
    first_name = State()
    last_name = State()
    email = State()
    training_level = State()
    gender = State()
    birthday = State()
    height = State()
    weight = State()
    confirmation = State()


class ChoiceOption(BaseModel):
    """
    Base model for selectable options (level, gender and etc.)
    """

    name: str
    id: int


def generate_options(enum_class: Enum, exclude_values: list | None = None) -> tuple:
    """
    Dynamically generates list of choice dictionaries from an Enum.
    Excludes any enum values listed in exclude_values.
    """
    exclude_values = exclude_values or []
    options = []

    for index, item in enumerate(enum_class):
        if item.value not in exclude_values:
            options.append(ChoiceOption(name=item.value, id=index).model_dump(exclude_unset=True))

    return tuple(options)


# Generate options excluding "Старт" from levels
levels_to_choose = generate_options(UserLevel)
genders_to_choose = generate_options(Gender)


async def skip_level_choose_getter(dialog_manager: DialogManager, **kwargs):
    sub_type = dialog_manager.dialog_data.get("sub_type")
    return {
        "skip_level_choose": sub_type not in ("Базовая", "С куратором"),
    }


async def data_getter(dialog_manager: DialogManager, **kwargs):
    return dialog_manager.dialog_data


@registration_router.callback_query(F.data == "to_registration")
async def start_registration(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
):
    logger.debug(f"start_registration called with manager: {dialog_manager}")
    await dialog_manager.start(state=RegistrationSG.first_name, mode=StartMode.RESET_STACK)


async def other_type_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    """
    Filters not text message from user.
    """

    await message.answer("Это не текст! А нужен текст")


async def first_name_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    """
    Validates and saves user first name to dialog_manager data.
    """
    name_regex = r"^[A-ZА-ЯЁ][a-zа-яё]{2,25}$"
    if re.match(name_regex, message.text):
        manager.dialog_data["first_name"] = message.text
        await manager.switch_to(RegistrationSG.last_name)
    else:
        await message.answer("Имя должно начинаться с большой буквы, содержать только буквы")


async def last_name_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    """
    Validates and saves user last name to dialog_manager data.
    """

    surname_regex = r"^[A-ZА-ЯЁ][a-zа-яё]{2,30}$"
    if re.match(surname_regex, message.text):
        manager.dialog_data["last_name"] = message.text
        await manager.switch_to(RegistrationSG.email)
    else:
        await message.answer("Фамилия должна начинаться с большой буквы, содержать только буквы")


@connection(commit=False)
async def email_handler(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
    session: AsyncSession,
):
    """
    Validates and saves user email to dialog_manager data.
    If user subscription_type is in progress then switch to level choosing, else skip to gender.
    """

    telegram_id = int(message.from_user.id)
    email_regex = r"^[\w.\-]{1,64}@\w+\.(by|ru|ua|com|net)$"
    user_sub_data: Subscription = await SubscriptionDAO.find_one_or_none_by_id(
        data_id=telegram_id,
        session=session,
    )
    if re.match(email_regex, message.text):
        manager.dialog_data["email"] = message.text
        manager.dialog_data["sub_type"] = user_sub_data.subscription_type.value
        if user_sub_data.subscription_type.value in ("Базовая", "С куратором"):
            await manager.switch_to(RegistrationSG.training_level)
        else:
            start_level = next(
                (level for level in levels_to_choose if "Старт" in level["name"]), None
            )
            if start_level:
                manager.dialog_data["chosen_level"] = start_level
                logger.info(f"Automatically set level to START for telegram_id: {telegram_id}")
            await manager.switch_to(RegistrationSG.gender)
    else:
        await message.answer("Введи корректный e-mail (например, example@mail.ru)")


async def training_level_handler(
    callback: CallbackQuery, select: Any, manager: DialogManager, item_id: str
):
    """
    Saves the users selected training level according to UserLevel enum.
    """

    chosen_level = next(level for level in levels_to_choose if level["id"] == int(item_id))
    manager.dialog_data["chosen_level"] = chosen_level
    await manager.switch_to(RegistrationSG.gender)


async def gender_handler(
    callback: CallbackQuery, select: Any, manager: DialogManager, item_id: str
):
    """
    Saves the users selected gender according to UserLevel enum.
    """

    chosen_gender = next(gender for gender in genders_to_choose if gender["id"] == int(item_id))
    manager.dialog_data["chosen_gender"] = chosen_gender
    await manager.switch_to(RegistrationSG.birthday)


async def birthday_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    """
    Validates and saves user's birthday to dialog_manager data.
    """
    min_age = 16
    max_age = 80
    try:
        birthday = datetime.strptime(message.text, "%d.%m.%Y").date()
        age = (datetime.now().date() - birthday).days // 365

        # Age interval for users
        if min_age <= age <= max_age:
            manager.dialog_data["birthday"] = birthday
            await manager.switch_to(RegistrationSG.height)
        else:
            await message.answer("Введи корректную дату рождения, пожалуйста")
    except (TypeError, ValueError):
        logger.info(f"Дата рождения, введенная пользователем {message.text}")
        await message.answer("Введите в корректном формате ДД.ММ.ГГГГ.")
    except Exception as e:
        logger.error(f"Error birthday date enter: {e}")


async def height_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    """
    Validates and saves user's height to dialog_manager data.
    """
    min_height = 120
    max_height = 220
    try:
        height = int(message.text)

        if min_height <= height <= max_height:
            manager.dialog_data["height"] = height
            await manager.switch_to(RegistrationSG.weight)
        else:
            await message.answer(
                "Рост должен быть от 120 до 220 см. Пожалуйста, введи корректное значение."
            )
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректное числовое значение для роста в сантиметрах."
        )
        logger.info(f"User with id {message.from_user.id} enter {message.text} during height")
    except Exception as e:
        logger.error(f"Error in height handler during registration: {e}")


async def weight_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    """
    Validates and saves user's weight to dialog_manager data.
    """
    min_weight = 30
    max_weight = 160

    try:
        weight = float(message.text.replace(",", "."))
        if min_weight <= weight <= max_weight:
            manager.dialog_data["weight"] = weight
            await manager.switch_to(RegistrationSG.confirmation)
        else:
            await message.answer(
                "Вес должен быть от 30 до 200 кг. Пожалуйста, введите корректное значение."
            )
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректное числовое значение для веса в килограммах."
        )
    except Exception as e:
        logger.error(f"Error in weight handler during registration: {e}")


@connection(commit=True)
async def save_user_data(
    callback: CallbackQuery,
    button: Any,
    manager: DialogManager,
    session: AsyncSession,
):
    """
    Saves all collected user data from registration dialog to database.
    """

    telegram_id = callback.from_user.id
    data = manager.dialog_data

    try:
        chosen_level = data["chosen_level"].get("name")
        chosen_gender = data["chosen_gender"].get("name")
        user_update = UserUpdateSchema(
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            username=callback.from_user.username,
            e_mail=data.get("email"),
            gender=chosen_gender,
            level=chosen_level,
        )
        await UserDAO.update_one_by_id(
            session=session,
            data_id=telegram_id,
            data=user_update,
        )
        current_user = await UserDAO.find_one_or_none_by_id(data_id=telegram_id, session=session)

        # Changing subscription status
        if current_user.subscription:
            current_user.subscription.status = SubscriptionStatus.ACTIVE
            logger.debug(
                f"Updated subscription status {current_user.subscription.status}"
                f" for user: {telegram_id}"
            )
            await session.flush()

        # Adding biometrics status
        if current_user.biometrics is not None:
            logger.debug(f"Updating existing biometrics for user {telegram_id}")
            current_user.biometrics.height = data.get("height")
            current_user.biometrics.weight = data.get("weight")
            current_user.biometrics.birthday = data.get("birthday")
        else:
            logger.debug(f"Creating new biometrics for user {telegram_id}")
            biometric_create = BiometricCreateSchema(
                user_id=telegram_id,
                height=data.get("height"),
                weight=data.get("weight"),
                birthday=data.get("birthday"),
            )
            await BiometricDAO.add(session, data=biometric_create)
        if chosen_level == UserLevel.START.value:
            await callback.message.answer(
                "✅ Регистрация успешно завершена!\nДобро пожаловать в программу <b>СТАРТ</b>",
                reply_markup=get_main_menu_button(),
            )
        else:
            await callback.message.answer(
                "✅ Регистрация успешно завершена!\nДобро пожаловать в <b>Прогресс</b>!",
                reply_markup=get_main_menu_button(),
            )
        await manager.done()
    except Exception as e:
        logger.error(f"Error in saving user data: {e}")
        await callback.message.answer(
            "❌ Произошла ошибка при регистрации. Пожалуйста,"
            " попробуйте снова или свяжитесь с поддержкой."
        )


registration_dialog = Dialog(
    Window(
        Const("👤 Напиши своё <b>имя</b>:"),
        MessageInput(first_name_handler, content_types=[ContentType.TEXT]),
        MessageInput(other_type_handler),
        Cancel(Const("Отмена")),
        state=RegistrationSG.first_name,
    ),
    Window(
        Format("👤 Спасибо, а теперь <b>фамилию</b>:"),
        MessageInput(last_name_handler, content_types=[ContentType.TEXT]),
        MessageInput(other_type_handler),
        Row(
            Back(Const("Назад, к имени")),
            Cancel(Const("Отмена")),
        ),
        state=RegistrationSG.last_name,
    ),
    Window(
        Const("📧 <b>Email</b>, пожалуйста:"),
        MessageInput(email_handler, content_types=[ContentType.TEXT]),
        MessageInput(other_type_handler),
        Row(
            Back(Const("Назад, к фамилии")),
            Cancel(Const("Отмена")),
        ),
        state=RegistrationSG.email,
    ),
    Window(
        Const(
            "Выбери свой <b>уровень</b> для тренировок:\n\n"
            "⚠️ Соревновательный уровень используется непосредственно перед подготовкой"
            " к большим соревнованиям и в данный момент может не использоваться"
        ),
        Column(
            Select(
                Format("{item[name]}"),
                items=levels_to_choose,
                item_id_getter=lambda x: x["id"],
                id="select_training_level",
                on_click=training_level_handler,
            ),
        ),
        Row(
            Back(Const("Назад, к e-mail")),
            Cancel(Const("Отмена")),
        ),
        state=RegistrationSG.training_level,
    ),
    Window(
        Multi(
            Const("Отлично, осталось немного биометрии и всё"),
            Const("⚤ Укажи свой <b>пол</b>:"),
            sep="\n\n",
        ),
        Column(
            Select(
                Format("{item[name]}"),
                items=genders_to_choose,
                item_id_getter=lambda x: x["id"],
                id="select_gender",
                on_click=gender_handler,
            ),
        ),
        Row(
            Back(Const("Назад, к  выбору уровня"), when="skip_level_choose"),
            Back(Const("Назад, к e-mail"), when=lambda data, *args: not data["skip_level_choose"]),
            Cancel(Const("Отмена")),
        ),
        getter=skip_level_choose_getter,
        state=RegistrationSG.gender,
    ),
    Window(
        Const("Напиши, когда у тебя <b>день рождения</b> в формате ДД.ММ.ГГГГ:"),
        MessageInput(birthday_handler, content_types=[ContentType.TEXT]),
        MessageInput(other_type_handler),
        Row(
            Back(Const("Назад, к выбору пола")),
            Cancel(Const("Отмена")),
        ),
        state=RegistrationSG.birthday,
    ),
    Window(
        Const("📏 Введите свой <b>рост</b> в сантиметрах (например, 175):"),
        MessageInput(height_handler, content_types=[ContentType.TEXT]),
        MessageInput(other_type_handler),
        Row(
            Back(Const("Назад, к дате рождения")),
            Cancel(Const("Отмена")),
        ),
        state=RegistrationSG.height,
    ),
    Window(
        Const("⚖️ Введите свой <b>вес</b> в килограммах (например, 70.2):"),
        MessageInput(weight_handler, content_types=[ContentType.TEXT]),
        MessageInput(other_type_handler),
        Row(
            Back(Const("Назад, к росту")),
            Cancel(Const("Отмена")),
        ),
        state=RegistrationSG.weight,
    ),
    Window(
        Const("✅ Проверь введенные данные:\n"),
        Format(
            "👤 <b>Имя:</b> {dialog_data[first_name]}\n"
            "👤 <b>Фамилия:</b> {dialog_data[last_name]}\n"
            "📧 <b>Email:</b> {dialog_data[email]}\n"
            "⚤ <b>Пол:</b> {dialog_data[chosen_gender][name]}\n"
            "🏋️‍♂️ <b>Уровень:</b> {dialog_data[chosen_level][name]}\n"
            "🗓 <b>Дата рождения:</b> {dialog_data[birthday]:%d.%m.%Y}\n"
            "📏 <b>Рост:</b> {dialog_data[height]} см\n"
            "⚖️ <b>Вес:</b> {dialog_data[weight]} кг\n"
        ),
        Button(
            Const("✅ Подтвердить"),
            id="confirm_registration",
            on_click=save_user_data,
        ),
        Row(
            Back(Const("⬅️ Назад")),
            Cancel(Const("❌ Отмена")),
        ),
        state=RegistrationSG.confirmation,
        getter=data_getter,
    ),
)
