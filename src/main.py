import asyncio
import locale

from aiogram.exceptions import TelegramBadRequest, TelegramNotFound
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram_dialog import setup_dialogs
from loguru import logger

from src.bot.handlers.main_menu import main_menu_router
from src.bot.handlers.payment_dialog import (
    payment_router,
    subscription_selection_dialog,
)
from src.bot.handlers.profile_dialog import profile_dialog, profile_router
from src.bot.handlers.new_registration_dialog import (
    registration_dialog,
    registration_router,
)
from src.bot.handlers.start_bot import start_command_router
from src.bot.handlers.workout_calendar import (
    workout_calendar_dialog,
    workout_calendar_router,
)
from src.bot.handlers.workout_of_the_day import workout_of_the_day_router
from src.bot.handlers.workouts_for_start_program import start_program_router
from src.config import admins, bot, dp
from src.logger_config import setup_logging


setup_logging()


async def set_commands():
    commands = [
        BotCommand(command="progress", description="Поехали! 🚀"),
        BotCommand(command="settings", description="Настройки ⚙️"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


async def start_bot():
    await set_commands()
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, "Я запущен 🥳")
        except TelegramNotFound:
            logger.error(f"Чат с {admin_id} не найден!")
        except TelegramBadRequest:
            logger.error(f"Чат с {admin_id} не найден!")
        logger.info("Бот успешно запущен!")


async def stop_bot():
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, "Я остановлен!")
        except TelegramNotFound:
            logger.error(f"Чат с {admin_id} не найден!")
        except TelegramBadRequest:
            logger.error(f"Чат с {admin_id} не найден!")
    logger.info("Бот остановлен!")


async def main():
    try:
        locale.setlocale(locale.LC_TIME, "Russian_Russia.1251")
        # -linux
        # locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")
        logger.info("Locale установлен в русский режим.")
    except locale.Error:
        logger.warning("Не удалось установить Locale в русский режим")

    # Functions register
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    # Routers register
    setup_dialogs(dp)
    dp.include_router(start_command_router)
    dp.include_router(main_menu_router)
    dp.include_router(payment_router)
    dp.include_router(registration_router)
    dp.include_router(workout_calendar_router)
    dp.include_router(workout_of_the_day_router)
    dp.include_router(start_program_router)
    dp.include_router(profile_router)

    # Dialogs register
    dp.include_router(subscription_selection_dialog)
    dp.include_router(registration_dialog)
    dp.include_router(workout_calendar_dialog)
    dp.include_router(profile_dialog)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
