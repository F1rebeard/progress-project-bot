from collections.abc import Awaitable, Callable
from typing import Any

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message, TelegramObject
from aiogram.utils.serialization import deserialize_telegram_object_to_python

from src.bot.keyboards.main_menu import get_main_menu_button
from src.dao import UserDAO
from src.database.config import async_session_maker
from src.database.models import User
from src.database.models.subscription import SubscriptionStatus


class ActiveSubscriptionFilter(BaseFilter):
    """
    Filter allows only users with an active subscription.
    Can be used to both filter and send a message depending on the status.
    """

    def __init__(self, silent: bool = True):
        """
        Args:
            silent: if False, send users message if active status is not active.
        """
        self.silent = silent

    async def __call__(self, obj: TelegramObject) -> bool:
        """
        Handles the callable behavior for checking a user's subscription status, determining
        their eligibility based on the given TelegramObject, and optionally responding with
        messages if the user does not meet the required criteria.

        Args:
            obj (TelegramObject): The Telegram object containing user and context data
                necessary for processing.

        Returns:
            bool: True if the user is eligible and their subscription is active, False otherwise.

        Raises:
            None
        """
        user_id = getattr(obj.from_user, "id", None)
        if not user_id:
            return False

        async with async_session_maker() as session:
            user: User = await UserDAO.find_one_or_none_by_id(data_id=user_id, session=session)
            if not user or not user.subscription:
                if not self.silent:
                    await self._respond(obj, "У тебя нету подписки 😭")
                return False

            if user.subscription.status != SubscriptionStatus.ACTIVE:
                if not self.silent:
                    status_text: str = user.subscription.status.value.lower()
                    await self._respond(obj, f"⚠️ Подписка {status_text}")
                return False

            return True

    @staticmethod
    def _is_same_content(
        current_text: str,
        current_markup: InlineKeyboardMarkup | None,
        new_markup: InlineKeyboardMarkup | None,
        full_text: str,
    ) -> bool:
        """
        Determines if the provided text and markup contents are identical to the given
        reference text and markup. This method checks both the trimmed text and the
        equivalent dictionary representation of the provided markup objects.

        Args:
            current_text: The current text to compare with the reference full_text.
            current_markup: The current inline keyboard markup to compare with
                the new_markup. Can be None.
            new_markup: The new inline keyboard markup to compare with the
                current_markup. Can be None.
            full_text: The reference full text to compare with the current text.

        Returns:
            bool: True if both text and markup match; False otherwise.
        """
        current_markup_dict = deserialize_telegram_object_to_python(current_markup)
        new_markup_dict = deserialize_telegram_object_to_python(new_markup)
        return current_text.strip() == full_text.strip() and current_markup_dict == new_markup_dict

    @staticmethod
    async def _safe_edit_or_answer(
        send_func: Callable[[], Awaitable[Any]],
        fallback: Callable[[], Awaitable[Any]] | None = None,
    ) -> None:
        """
        Executes the provided send function asynchronously and handles any
        TelegramBadRequest exceptions that occur. If the error indicates
        that the message is not modified, the exception is re-raised.
        Optionally, a fallback function can be executed in case of such
        exceptions.

        Parameters:
        send_func (Callable[[], Awaitable[Any]]): A callable that, when
            invoked, returns an awaitable object representing the main send
            operation being attempted.
        fallback (Callable[[], Awaitable[Any]] | None): Optional. A callable
            that, if provided, will be invoked if the main send_func raises
            an exception that does not involve an unmodified message.

        Raises:
        TelegramBadRequest: If the exception indicates a situation other
            than the message is not modified, or if the fallback is not
            provided and cannot handle the exception.
        """
        try:
            await send_func()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                raise
            if fallback:
                await fallback()

    async def _respond(self, obj: TelegramObject, message: str):
        """
        Respond to a Telegram object with a predefined message and an action.

        This method handles Telegram CallbackQuery and Message objects to respond
        with a specific message text and a main menu button as the reply markup.

        Parameters:
            obj (TelegramObject): The Telegram object that triggered the event.
                This could be an instance of CallbackQuery or Message.
            message (str): The message text to include in the response.
        """
        full_text = f"{message}\nДля доступа необходимо обновить или разморозить подписку."
        reply_markup = get_main_menu_button()

        if isinstance(obj, CallbackQuery):
            current_text = obj.message.text or ""
            if self._is_same_content(
                current_text=current_text,
                current_markup=obj.message.reply_markup,
                new_markup=reply_markup,
                full_text=full_text,
            ):
                await obj.answer()
                return

            await self._safe_edit_or_answer(
                lambda: obj.message.edit_text(full_text, reply_markup=reply_markup)
            )

        elif isinstance(obj, Message):
            current_text = obj.message.text or ""
            if self._is_same_content(
                current_text=current_text,
                current_markup=obj.message.reply_markup,
                new_markup=reply_markup,
                full_text=full_text,
            ):
                return

            await self._safe_edit_or_answer(
                lambda: obj.answer(full_text, reply_markup=reply_markup)
            )
