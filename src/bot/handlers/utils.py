from aiogram.types import Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.input import MessageInput


async def other_type_handler(message: Message, message_input: MessageInput, manager: DialogManager):
    """
    Filters not text message from a user.
    """
    await message.answer("Это не текст! А нужен текст")


async def on_select_clicked(selected: str, _: any, manager: DialogManager, key: str):
    manager.dialog_data[key] = selected
    await manager.next()