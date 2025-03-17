import logging
from datetime import date
from pprint import pprint

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards.main_menu import get_main_menu_keyboard
from src.bot.keyboards.subscription import (
    renew_or_change_subscription_kb,
    unfreeze_subscription_kb,
)
from src.dao import UserDAO
from src.database.config import connection

logger = logging.getLogger(__name__)

main_menu_router = Router()

START_NOTIFICATION_DAYS: int = 5


@connection(commit=False)
async def get_user_profile_info(telegram_id: int, session: AsyncSession):
    """

    :param telegram_id:
    :param session:
    :return:
    """
    user = await UserDAO.find_one_or_none_by_id(data_id=telegram_id, session=session)
    if not user:
        return None

    user_level = user.level.value if user.level else "Не выбран"
    if not user.subscription:
        return {
            "level": user_level,
            "has_subscription": False,
        }

    sub_end_date = user.subscription.end_date
    days_left = (sub_end_date - date.today()).days
    formatted_end_date = sub_end_date.strftime("%d.%m.%Y")
    result = {
        "level": user_level,
        "sub_end_date": formatted_end_date,
        "days_left": days_left,
        "sub_status": user.subscription.status.value,
        "has_subscription": True,
    }
    pprint(result)
    return {
        "level": user_level,
        "sub_end_date": formatted_end_date,
        "days_left": days_left,
        "sub_status": user.subscription.status.value,
        "has_subscription": True,
    }


async def show_main_menu(telegram_id: int):
    """
    Get the formatted main menu text with user info.
    :param telegram_id:
    :return:
    """
    user_info = await get_user_profile_info(telegram_id)
    if not user_info:
        return "❌ Ошибка получения данных. Попробуйте перезапустить бота командой /start"
    if not user_info["has_subscription"]:
        return "📱 <b>Главное меню</b>\n\n⚠️ У вас нет активной подписки"
    if user_info["sub_status"] == "Истекла":
        return "📱 <b>Главное меню</b>\n\n⚠️ Ваша подписка истекла"
    if user_info["sub_status"] == "Заморожена":
        return "📱 <b>Главное меню</b>\n\n❄️ Ваша подписка заморожена"
    menu_text = (
        f"📱 <b>Главное меню</b>\n\n"
        f"🏋️‍♂️ <b>Уровень:</b> {user_info['level']}\n"
        f"📅 <b>Подписка до:</b> {user_info['sub_end_date']}"
    )
    if user_info["days_left"] <= START_NOTIFICATION_DAYS:
        menu_text += f"\n⚠️ <b>Осталось дней:</b> {user_info['days_left']}"
    else:
        menu_text += f"\n✅ <b>Осталось дней:</b> {user_info['days_left']}"

    # Here you can add latest workout info in the future
    # menu_text += "\n\n🔄 <b>Последняя тренировка:</b> Not implemented yet"
    return menu_text


@main_menu_router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    """
    Handler for the main menu callback.
    """
    telegram_id = callback.from_user.id
    menu_text = await show_main_menu(telegram_id)
    user_info = await get_user_profile_info(telegram_id)
    if not user_info or not user_info["has_subscription"]:
        await callback.message.edit_text(
            text=menu_text, reply_markup=renew_or_change_subscription_kb
        )
        return
    if user_info["sub_status"] == "Истекла":
        await callback.message.edit_text(
            text=menu_text, reply_markup=renew_or_change_subscription_kb
        )
        return
    if user_info["sub_status"] == "Заморожена":
        await callback.message.edit_text(
            text=menu_text,
            reply_markup=unfreeze_subscription_kb,
        )
        return
    if user_info["days_left"] <= START_NOTIFICATION_DAYS:
        # Add warning about subscription ending soon
        footer_text = "\n\n⚠️ <b>Внимание!</b> Ваша подписка скоро закончится. Не забудьте продлить."
        menu_text += footer_text
    await callback.message.edit_text(menu_text, reply_markup=get_main_menu_keyboard())
    await callback.answer()
