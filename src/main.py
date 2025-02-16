import asyncio
import logging

from aiogram.exceptions import TelegramBadRequest, TelegramNotFound
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram_dialog import setup_dialogs

from src.bot.handlers.start_bot import start_command_router
from src.config import admins, bot, dp
from src.logger import setup_logging
from src.middleware.database_middleware import (
    DatabaseMiddlewareWithCommit,
    DatabaseMiddlewareWithoutCommit,
)

setup_logging()


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
    # Middleware connection
    dp.update.middleware.register(DatabaseMiddlewareWithoutCommit())
    dp.update.middleware.register(DatabaseMiddlewareWithCommit())

    # Functions register
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    # Routers  and dialogs register
    setup_dialogs(dp)
    dp.include_router(start_command_router)


    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


asyncio.run(main())
