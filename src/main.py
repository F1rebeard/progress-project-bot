import asyncio
import locale
import logging

from aiogram.exceptions import TelegramBadRequest, TelegramNotFound
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram_dialog import setup_dialogs

from src.bot.handlers.main_menu import main_menu_router
from src.bot.handlers.payment_dialog import (
    payment_router,
    subscription_selection_dialog,
)
from src.bot.handlers.registration_dialog import (
    registration_dialog,
    registration_router,
)
from src.bot.handlers.start_bot import start_command_router
from src.bot.handlers.workout_calendar import (
    workout_calendar_dialog,
    workout_calendar_router,
)
from src.config import admins, bot, dp
from src.logger import setup_logging
from src.middleware.database_middleware import (
    DatabaseMiddlewareWithCommit,
    DatabaseMiddlewareWithoutCommit,
)

setup_logging()
logger = logging.getLogger(__name__)


async def set_commands():
    """Set's the command menu for all users."""
    commands = [BotCommand(command="start", description="Запуск или перезапуска бота")]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def start_bot():
    """Methods with bot starting."""
    await set_commands()
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, "Я запущен 🥳")
        except TelegramNotFound:
            logging.error(f"Чат с {admin_id} не найден!")
        except TelegramBadRequest:
            logging.error(f"Чат с {admin_id} не найден!")
        logging.info("Бот успешно запущен!")


async def stop_bot():
    """Methods with bot stopping."""
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, "Я остановлен!")
        except TelegramNotFound:
            logging.error(f"Чат с {admin_id} не найден!")
        except TelegramBadRequest:
            logging.error(f"Чат с {admin_id} не найден!")
    logging.info("Бот остановлен!")


async def main():
    try:
        locale.setlocale(locale.LC_TIME, "Russian_Russia.1251")
        # -linux
        # locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
        logger.info("Locale установлен в русский режим.")
    except locale.Error:
        logger.warning("Не удалось установить Locale в русский режим")

    # Middleware connection
    dp.update.middleware.register(DatabaseMiddlewareWithoutCommit())
    dp.update.middleware.register(DatabaseMiddlewareWithCommit())

    # Functions register
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    # Routers  and dialogs register
    setup_dialogs(dp)

    dp.include_router(start_command_router)
    dp.include_router(main_menu_router)
    dp.include_router(payment_router)
    dp.include_router(registration_router)
    dp.include_router(workout_calendar_router)

    dp.include_router(subscription_selection_dialog)
    dp.include_router(registration_dialog)
    dp.include_router(workout_calendar_dialog)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
