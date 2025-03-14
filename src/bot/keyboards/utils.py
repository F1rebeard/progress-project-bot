from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_inline_keyboard(buttons: list[tuple[str, str]]):
    """
    Creates an inline keyboard dynamically.

    Args:
        buttons (List[Tuple[str, str]]): A list of tuples, where each tuple contains:
            - The button text (str)
            - The callback data (str)

    Returns:
        InlineKeyboardMarkup: The generated inline keyboard.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, callback_data=callback_data)]
            for text, callback_data in buttons
        ]
    )
