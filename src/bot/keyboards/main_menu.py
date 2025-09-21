from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.keyboards.utils import create_inline_keyboard


def get_main_menu_keyboard():
    """Creates the main menu inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="🏋️‍♂️ Тренировка дня", callback_data="workout_of_the_day"),
            InlineKeyboardButton(text="📋 Тренировки", callback_data="workouts"),
        ],
        [
            InlineKeyboardButton(text="📊 Тесты", callback_data="test_weeks"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        ],
        [
            InlineKeyboardButton(text="❓ FAQ", callback_data="faq"),
            InlineKeyboardButton(text="📅 Подписка", callback_data="subscription"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_main_menu_button():
    """Creates a single button for accessing the main menu."""
    return create_inline_keyboard([("📱 Главное меню", "main_menu")])
