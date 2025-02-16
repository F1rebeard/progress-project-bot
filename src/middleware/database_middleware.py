from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from src.database.config import async_session_maker


class BaseDatabaseMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: dict[str, Any]
    ) -> Any:
        async with async_session_maker() as session:
            self.set_session(data, session)
            try:
                result = await handler(event, data)
                await self.after_handler(session)
                return result
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    def set_session(self, data: dict[str, Any], session) -> None:
        """Метод для установки сессии в словарь данных."""
        raise NotImplementedError("Этот метод должен быть реализован в подклассах.")

    async def after_handler(self, session) -> None:
        """Метод для выполнения действий после вызова хендлера (например, коммит)."""
        pass


class DatabaseMiddlewareWithoutCommit(BaseDatabaseMiddleware):
    def set_session(self, data: dict[str, Any], session) -> None:
        data['session_without_commit'] = session


class DatabaseMiddlewareWithCommit(BaseDatabaseMiddleware):
    def set_session(self, data: dict[str, Any], session) -> None:
        data['session_with_commit'] = session

    async def after_handler(self, session) -> None:
        await session.commit()
