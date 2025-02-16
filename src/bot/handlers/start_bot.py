from datetime import date

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.subscription import (
    renew_or_change_subscription_kb,
    subscription_selection_btn,
)
from src.config.bot import ADMIN_IDS
from src.database.base import connection
from src.database.dao import UserDAO
from src.database.models.subscription import SubscriptionStatus

start_command_router = Router()


@connection(commit=False)
async def check_user_status(
    telegram_id: int, session: AsyncSession
) -> tuple[str | None, str, str | None, str | None, date | None]:
    """
    Retrieves the user's name, system status, and subscription details.

    The function determines the user's state based on their database record:
    - **Admin**: If the user is in `ADMIN_IDS`, they are assigned "admin" status.
    - **New User**: If no record exists, they are considered a "new_user".
    - **Pending Registration**: If a record exists but lacks a first name, yet has an
     active subscription.
    - **Registered User**: If the user has both a first and last name, they are "registered",
      and their subscription status is retrieved.

    Args:
        telegram_id (int): The Telegram ID of the user.
        session (AsyncSession): The database session for asynchronous queries.

    Returns:
        tuple[str | None, str, str | None, date | None]:
            - The user's first name (or `None` if not available).
            - The user status (`"new_user"`, `"admin"`, `"pending_registration"`,
             or `"registered"`).
            - The subscription status as a string (`None` if no active subscription).
            - The subscription end date (`None` if no active subscription).
    """
    user = await UserDAO.find_one_or_none_by_id(telegram_id, session)
    user_status = "new_user"
    user_name = None
    sub_status = None
    sub_type = None
    sub_end_date = None

    if user:
        if telegram_id in ADMIN_IDS:
            user_status = "admin"
            user_name = user.first_name

        if user.first_name is None and user.subscription.status == SubscriptionStatus.ACTIVE:
            user_status = "pending_registration"

        if user.first_name and user.last_name:
            user_name = user.first_name
            user_status = "registered"
            sub_status = user.subscription.status.value
            sub_type = user.subscription.subscription_type.value
            sub_end_date = user.subscription.end_date

    return user_name, user_status, sub_status, sub_type, sub_end_date


@start_command_router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Handles the /start command, determining the user's status and responding accordingly.

    The function checks the user's status in the system and sends an appropriate response:
    - **Admin**: Displays an admin greeting with a control panel message.
    - **New User**: Guides them through the subscription and registration process.
    - **Pending Registration**: Reminds the user to complete registration.
    - **Registered User**: Provides subscription status and relevant instructions:
        - **Active**: Shows remaining days and encourages training.
        - **Frozen**: Informs the user about frozen status and suggests unfreezing.
        - **Expired**: Notifies the user that their subscription has ended and prompts renewal.

    Args:
        message (Message): The incoming Telegram message.
        session (AsyncSession): The database session for querying user details.

    Returns:
        None: Sends an appropriate message based on the user's status.
    """
    telegram_id = message.from_user.id
    (user_name, user_status, sub_status, sub_type, sub_end_date) = await check_user_status(
        telegram_id
    )
    for admin_id in ADMIN_IDS:
        await message.answer(text=str(admin_id))
    if user_status == "admin":
        await message.answer(
            text=f"💪 Привет, <b>админ</b> {user_name}!\n"
            f"🔧 Панель управления загружена.\n"
            f"📌 Скоро здесь будет доступно больше функций для управления программой."
        )
    if user_status == "new_user":
        await message.answer(
            text='🔥 Привет! Добро пожаловать в <b>"Прогресс"</b>!\n'
            "💪 Здесь ты тренируешься вместе с нами!\n\n"
            "🏋️‍♂️ Как начать?\n"
            "1️⃣ Выбери тип подписки 📋\n"
            "2️⃣ Оплати подписку 💳\n"
            "3️⃣ Пройди регистрацию 📝\n"
            "4️⃣ Тренируйся с нами ️ 🏋️‍♀️\n\n"
            "👉 Начни свой <b>прогресс</b> по кнопке ниже!",
            reply_markup=subscription_selection_btn(),
        )
    if user_status == "pending_registration":
        await message.answer(
            text="🏋️‍♂️ Почти готово!\n"
            "Ты уже оплатил(а) подписку, но еще не завершил(а) регистрацию.\n"
            "📝 Остался последний шаг – заполни данные, и мы начнем тренировки!"
        )
    if user_status == "registered":
        formated_subs_end_date = sub_end_date.strftime("%d.%m.%Y")
        days_till_end = (sub_end_date - date.today()).days
        if sub_status == "Активна" and days_till_end == 0:
            await message.answer(
                text=f"⚡️ <b>Внимание, {user_name}!</b>\n\n"
                f"Твоя подписка заканчивается <b>сегодня</b>!\n"
                f"🚀 <b>Не теряй темп!</b> Продли подписку, чтобы не прерывать тренировки.",
                reply_markup=renew_or_change_subscription_kb(),
            )
        elif sub_status == "Активна" and days_till_end in (1, 2):
            await message.answer(
                text=f"⚡️ <b>Внимание, {user_name}!</b>\n\n"
                f"Твоя подписка заканчивается <b>на днях</b>!\n"
                f"🚀 <b>Не теряй темп!</b> Продли подписку, чтобы не прерывать тренировки.",
                reply_markup=renew_or_change_subscription_kb(),
            )
        elif sub_status == "Активна":
            await message.answer(
                text=f"🏆 <b>Добро пожаловать обратно в Прогресс, {user_name}</b>!\n\n"
                f"Твоя подписка активна! Осталось дней: <b>{days_till_end}</b>\n"
                f"📅 <b>Дата окончания подписки: {formated_subs_end_date}</b>\n"
            )
        elif sub_status == "Заморожена":
            await message.answer(
                text="❄️ <b>Ой-ой, твоя подписка заморожена!</b>\n"
                "Мы скучаем по твоим рекордам, а штанга застоялась…\n"
                "👉 <b>Разморозь подписку</b> и возвращайся в игру! 🏋️‍♀️"
            )
        if sub_status == "Истекла":
            await message.answer(
                text=f"Твоя подписка <b>закончилась {formated_subs_end_date} 😢</b>.\n"
                f"🔥 Но ты можешь вернуться в Прогресс прямо сейчас!\n"
                f"📌 Обнови подписку и продолжай тренироваться с нами!\n"
            )
