from src.bot.keyboards.utils import create_inline_keyboard


def user_settings_keyboard():
    """
    Creates a user settings keyboard for /settings command.
    """
    return create_inline_keyboard([("📅😎 Эмоджи в календаре", "user_settings")])